# Velxio IoT — QEMU source and ROM maintenance

This ZIP contains a scheduled workflow that updates the Git submodule pointer for QEMU and retrieves the four boot ROM binaries from the Velxio asset catalog. Both changes are proposed as a pull request, **never automatically merged**.

## Required once — add the source submodule locally

```bash
git clone https://github.com/AlbertoCruzRuiz/velxio_iot.git
cd velxio_iot
# If these exist, delete only the placeholder tracked files (e.g. third-party/velxio-qemu/.gitkeep).
git submodule add -b main https://github.com/AlbertoCruzRuiz/velxio-qemu.git third-party/velxio-qemu
git add .gitmodules third-party/velxio-qemu
git commit -m 'Add pinned QEMU sources as submodule'
git push origin main
```

Note: if the remote source repository is private, your local Git credentials must grant access. Your parent repo will point to a specific source commit; updating QEMU does not happen without updating that pointer.

## Copy the ZIP contents into velxio_iot

- `.github/workflows/sync-qemu-dependencies.yml` (new daily updater)
- `scripts/sync_velxio_roms.py`
- `tests/test_sync_velxio_roms.py`
- `.github/workflows/build-qemu.yml` (replaces existing build workflow, with optional private submodule checkout support)

## GitHub settings

1. Create **VELXIO_LICENSE_KEY** in `velxio_iot` > Settings > Secrets and variables > Actions (regenerate the license key that was previously exposed).
2. If `velxio-qemu` is private, create **QEMU_REPO_READ_TOKEN** as a fine-grained personal access token scoped only to the `velxio-qemu` repository with **Contents: Read-only** and store it as a secret in `velxio_iot`. Public repository: omit this secret.
3. Enable `Settings > Actions > General > Allow GitHub Actions to create and approve pull requests` for `velxio_iot`.
4. Run **Propose QEMU Source and ROM Updates** manually once from `Actions > Run workflow` (main). This bootstraps `qemu-assets/roms/` via a PR and updates the submodule only if needed.
5. Review and merge the PR. The existing **Build QEMU Image** workflow should run on the merged push to main and publish the new QEMU image.

The schedule is 08:37 UTC daily. GitHub scheduling may be delayed, and an inactive public repo may have schedules disabled.

## ROM manifest

The updater downloads four named assets: `esp32-v3-rom`, `esp32-v3-rom-app`, `esp32c3-rom`, `esp32s3_rev0_rom`. The API returns `assets` with `asset_name`, `version`, `sha256` and `size_bytes`. Both size and SHA-256 are verified before any file is updated. The updater records each binary, `SHA256SUMS` and `rom-manifest.json` in Git for durability. No license keys or authenticated URLs enter source control.

## Limitations & safety

- Verify the applicable Espressif and third-party ROM redistribution rights before publishing the ROM binaries publicly. The ESP ROM ELF files are available from Espressif under Apache-2.0 (compiled-object form), but do not assume the origin of the `*.bin` files is identical without verification.
- Source archive authenticity derives from the upstream Velxio manifest; SHA-256 protects integrity against that manifest, not against a compromised upstream publisher.
- A successful checksum check and Docker build do **not** prove flash/PSRAM, WiFi, MQTT, or peripherals work; require functional tests before merging/deploying updates.
- PRs created with the built-in `GITHUB_TOKEN` will not automatically trigger a separate `pull_request` CI workflow. If required, use a GitHub App token for PR creation or run verification from a human-initiated event. The post-merge `push` will trigger the Docker build.
- If `velxio-qemu` only has an open import PR, merge the verified source PR into its `main` before updating the submodule.
- The ROM sync has not been exercised against the live authenticated API here. Its manifest parser was tested locally against the exact object schema provided in chat, with mock binary content.
