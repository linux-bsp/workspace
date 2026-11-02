# Repository Guidelines

## Project Structure & Module Organization
This repository is a BSP workspace that aggregates the main source trees as Git submodules. Keep the repository root focused on workspace metadata, documentation, and submodule entries.

- `buildroot/` for the Buildroot source tree
- `bsp-base-external/` for board-specific Buildroot external configuration
- `linux/` for Linux kernel source trees, grouped by version such as `linux/linux-7.0/` and `linux/ti-linux-kernel-6.18.13/`
- `uboot/` for U-Boot source trees, grouped by version such as `uboot/uboot-2024.10/` and `uboot/ti-u-boot-2025.10/`
- `edk/` for EDK embedded device kit code
- `docs/<board>/` for board-specific reference manuals, datasheets, schematics, and related documents

Do not mix generated build outputs into the repository root. Put new root-level documentation in `README.md`; put board-specific documents under `docs/<board>/` unless a tool requires a specific file at the root.

## Build, Test, and Development Commands
No build system or test runner is configured yet. Until one is added, use standard Git commands for local workflow:

- `git status` to inspect changes
- `git diff` to review edits before commit
- `git add <path>` to stage specific files
- `git commit -m "type: short summary"` to create a commit

When build or test tooling is introduced, document the canonical commands here and keep them reproducible from the repository root.

## Coding Style & Naming Conventions
Use 4-space indentation for new text-based source files unless the chosen language has a stronger community standard. Prefer ASCII-only content unless non-ASCII is required.

Naming guidance:

- Directories: lowercase, hyphenated when needed
- Files: descriptive and consistent with the language ecosystem
- Classes/types: `PascalCase`
- Functions/variables: `camelCase` or `snake_case`, matching the language

Add formatting or lint configuration with the first language/toolchain added to the repo.

## Testing Guidelines
Place tests under `tests/` and mirror the source layout where practical. Name tests after the unit under test, such as `tests/parser_test.*` or `tests/test_parser.*`, depending on the framework.

Every new feature or bug fix should include automated tests once a test framework exists.

## Commit & Pull Request Guidelines
There is no existing commit history yet, so establish a simple convention now: `type: imperative summary` (for example, `docs: add contributor guide`).

Pull requests should include a short description, the reason for the change, and notes about validation performed. If the change affects user-visible behavior, include example output or screenshots where relevant.

## Firmware Release Workflow

For firmware changes, complete the applicable tests and AM625 image validation, then publish the new OTA release automatically. The user has authorized this workflow; a separate publication confirmation is unnecessary.

Commit the exact corresponding source changes only after the intended device reports `success` for that publication and running version following reboot and health confirmation. Download, installation, reboot, and boot-testing are not success. Preserve the release identity, device transaction, test results, and source snapshot for audit. If the release fails, rolls back, or is quarantined, retain the changes and investigate; do not commit it as a successful release or bypass quarantine.

Commit affected submodules before updating their workspace gitlinks. Do not include generated firmware or unrelated concurrent edits. Hardware confirmation of a kernel/rootfs OTA does not validate an uninstalled bootloader. Publishing firmware does not imply pushing Git commits; push only when requested.

Keep the firmware tag fixed at `v0.0.1` (packed version 1). Change it only when the user explicitly requests a version change. Content changes produce a new full SHA256 identity; publication numbers remain distinct audit identifiers. Store each build in a unique output directory so repeated tags never overwrite earlier artifacts.
