#!/usr/bin/env python3
"""Import the four Velxio QEMU ROM files, verifying upstream size and SHA-256.

No secrets or authenticated URLs are written to disk or printed.
The upstream listing shape is {"plan": ..., "assets": [{"asset_name": ..., ...}]}.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

API_BASE = 'https://velxio.dev/api/pro/license/downloads'
ROM_ASSETS = {
    'esp32-v3-rom': 'esp32-v3-rom.bin',
    'esp32-v3-rom-app': 'esp32-v3-rom-app.bin',
    'esp32c3-rom': 'esp32c3-rom.bin',
    'esp32s3_rev0_rom': 'esp32s3_rev0_rom.bin',
}
SHA256_RE = re.compile(r'^[0-9a-f]{64}$')
MAX_ROM_BYTES = 32 * 1024 * 1024


def select_roms(manifest):
    if not isinstance(manifest, dict) or not isinstance(manifest.get('assets'), list):
        raise ValueError('Unexpected Velxio manifest structure (missing assets array)')
    records = {}
    for item in manifest['assets']:
        if not isinstance(item, dict) or item.get('asset_name') not in ROM_ASSETS:
            continue
        name = item['asset_name']
        if name in records:
            raise ValueError(f'Duplicate ROM asset: {name}')
        checksum = item.get('sha256')
        size = item.get('size_bytes')
        version = item.get('version')
        if not isinstance(checksum, str) or not SHA256_RE.fullmatch(checksum):
            raise ValueError(f'Missing/invalid SHA-256 for {name}')
        if type(size) is not int or not (0 < size <= MAX_ROM_BYTES):
            raise ValueError(f'Missing/invalid size for {name}')
        if not isinstance(version, str) or not version:
            raise ValueError(f'Missing/invalid version for {name}')
        records[name] = {
            'asset_name': name, 'filename': ROM_ASSETS[name],
            'version': version, 'size_bytes': size, 'sha256': checksum,
        }
    missing = sorted(set(ROM_ASSETS) - set(records))
    if missing:
        raise ValueError('Manifest missing ROMs: ' + ', '.join(missing))
    return records


def fetch(url):
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'velxio-iot-rom-sync/1.0'})
        with urllib.request.urlopen(request, timeout=90) as response:
            return response.read(MAX_ROM_BYTES + 1)
    except urllib.error.HTTPError as exc:
        # Never print exc or request URL: it contains the license key.
        raise RuntimeError(f'Velxio API HTTP status {exc.code}') from None
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f'Velxio API connection error ({type(exc).__name__})') from None


def validate_payload(data, record):
    if len(data) != record['size_bytes']:
        raise ValueError(f"Size mismatch for {record['asset_name']}")
    if hashlib.sha256(data).hexdigest() != record['sha256']:
        raise ValueError(f"SHA-256 mismatch for {record['asset_name']}")


def write_if_changed(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() == content:
        return False
    with tempfile.NamedTemporaryFile(mode='wb', dir=path.parent, delete=False) as staged:
        staged.write(content)
        staged_name = staged.name
    os.replace(staged_name, path)
    return True


def sync(target, listing, download):
    records = select_roms(listing)
    blobs = {}
    for name, item in sorted(records.items()):
        destination = target / item['filename']
        existing = destination.read_bytes() if destination.exists() else None
        if existing is not None and len(existing) == item['size_bytes'] and hashlib.sha256(existing).hexdigest() == item['sha256']:
            blobs[name] = existing
            print(f"Verified locally: {item['filename']} ({item['version']})")
        else:
            print(f"Fetching: {item['filename']} ({item['version']})")
            data = download(name)
            validate_payload(data, item)
            blobs[name] = data
    # Only update working tree once ALL downloads and hashes have passed.
    changed = False
    for name, item in sorted(records.items()):
        changed |= write_if_changed(target / item['filename'], blobs[name])
    sha_lines = ''.join(f"{records[name]['sha256']}  {records[name]['filename']}\n" for name in sorted(records))
    changed |= write_if_changed(target / 'SHA256SUMS', sha_lines.encode())
    metadata = {'source': 'Velxio QEMU asset catalog', 'assets': [records[name] for name in sorted(records)]}
    changed |= write_if_changed(target / 'rom-manifest.json', (json.dumps(metadata, indent=2, sort_keys=True) + '\n').encode())
    return changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='qemu-assets/roms')
    args = parser.parse_args()
    secret = os.getenv('VELXIO_LICENSE_KEY')
    if not secret:
        raise ValueError('VELXIO_LICENSE_KEY repository secret is not configured')
    # The official endpoint only accepts a query-string key. Never log the URL.
    query = urllib.parse.urlencode({'key': secret})
    listing = json.loads(fetch(f'{API_BASE}?{query}').decode('utf-8'))
    def download(name):
        return fetch(f'{API_BASE}/{name}?{query}')
    changed = sync(Path(args.output), listing, download)
    print('ROM assets changed' if changed else 'All ROM assets already current')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)
