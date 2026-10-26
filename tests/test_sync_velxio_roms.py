import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from sync_velxio_roms import ROM_ASSETS, select_roms, sync


def manifest_and_blobs():
    blobs = {key: (key.encode() * 20) for key in ROM_ASSETS}
    assets = [dict(asset_name=key, version='1.0.0', size_bytes=len(data), sha256=hashlib.sha256(data).hexdigest()) for key, data in blobs.items()]
    # Non-ROM assets exist in the real manifest and must be ignored.
    assets.append(dict(asset_name='qemu-source-63b37f5e', version='2026-10-15+63b37f5e', size_bytes=123, sha256='0'*64))
    return {'plan': 'personal', 'assets': assets[::-1]}, blobs

class RomSyncTest(unittest.TestCase):
    def test_exact_manifest_shape(self):
        listing, blobs = manifest_and_blobs()
        self.assertEqual(set(select_roms(listing)), set(blobs))

    def test_bootstrap_and_idempotence(self):
        listing, blobs = manifest_and_blobs()
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'roms'
            self.assertTrue(sync(target, listing, lambda name: blobs[name]))
            self.assertTrue((target / 'SHA256SUMS').is_file())
            for name, filename in ROM_ASSETS.items():
                self.assertEqual((target / filename).read_bytes(), blobs[name])
            self.assertFalse(sync(target, listing, lambda name: self.fail('unexpected download')))

    def test_reject_mismatched_sha_without_writes(self):
        listing, blobs = manifest_and_blobs()
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'roms'
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                sync(target, listing, lambda name: b'Z'*len(blobs[name]))
            self.assertFalse(target.exists())

    def test_reject_missing_asset(self):
        listing, _ = manifest_and_blobs()
        listing['assets'] = [a for a in listing['assets'] if a['asset_name'] != 'esp32-v3-rom']
        with self.assertRaisesRegex(ValueError, 'Manifest missing ROMs'):
            select_roms(listing)

    def test_reject_duplicate_asset(self):
        listing, _ = manifest_and_blobs()
        listing['assets'].append(next(a.copy() for a in listing['assets'] if a['asset_name'] == 'esp32c3-rom'))
        with self.assertRaisesRegex(ValueError, 'Duplicate ROM'):
            select_roms(listing)

if __name__ == '__main__':
    unittest.main()
