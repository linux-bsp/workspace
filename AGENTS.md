# Repository Guidelines

## Project Structure & Module Organization

SadBoard develops on the `SadBoard` branch of `linux-bsp/workspace`, using existing BSP submodules. AM6254 debugging configuration, a systemd preparation service, a capability check and the first manual crash scenario exist. Random scenario orchestration and general automatic grading are not implemented. Record image build and board validation status separately.

- `README.md`: project scope, status, and documentation index.
- `docs/am625-quickstart.md`: board startup and first experiment walkthrough.
- `docs/bootlin-linux-debugging-guide.md`: Chinese Bootlin study guide.
- `docs/workspace-guide.md`: inherited workspace operations; check historical platform examples before use.
- `buildroot/`, `linux/`, `uboot/`: build system and versioned source submodules.
- `bsp-base-external/`: board support; keep the `LINUX_BSP` external identifier.
- `sadboard-external/`: `SADBOARD` external with AM6254 debugging fragments, setup script, and target overlay.
- `edk/`, `libbmc/`: existing software submodules.

Put learning guides in `docs/`, board references in `docs/<board>/`, and generated builds in ignored `output/`. Link new guides from `README.md`. Read submodule-specific instructions before changing their contents.

## Build, Test, and Development Commands

Initialize source submodules, then use the standard Buildroot entry:

```sh
git submodule update --init --recursive
cd buildroot
BR2_EXTERNAL="../bsp-base-external ../sadboard-external" \
  make sadboard_am625_debug_defconfig && make all
```

Without `O=`, artifacts go to `buildroot/output/`; existing guides also use workspace `output/am625-debug/`. Keep output trees separate when changing toolchains. The Python helper remains optional for local toolchains and diagnostic variants. After changing baseline fragments, regenerate the checked-in defconfig with `--export-defconfig` in a fresh output directory and verify configuration equivalence. See `docs/am625-bootlin-debug-environment.md`. Run `python3 sadboard-external/tests/test-labs.py` for scenario regressions. `sadboard list`, `sadboard run crash` and `sadboard verify crash` are target commands; verification checks the reference repair, not an arbitrary learner patch. Bootlin commands remain external lab instructions.

Use `git diff --check`, `git diff --cached --check`, and `git status --short`. Review untracked files separately.

## Coding Style & Naming Conventions

Write learning documentation in Chinese; preserve official identifiers and commands. Use descriptive headings, hyphenated lowercase filenames, and language-tagged code fences. Follow existing language conventions in source submodules; otherwise use four-space indentation for new source files. No workspace-wide formatter is configured.

## Validation and Scenario Guidelines

Check relative links, citations, platform assumptions, and configuration loading. Report the actual environment and distinguish reviewed instructions from executed experiments. Proposed scenarios should specify symptoms, prerequisites, triggers, expected evidence, root cause, repair verification, and reset procedures. Keep planned behavior distinct from implemented functionality. Use each submodule's own testing instructions for code changes.

## Commit & Pull Request Guidelines

Use focused `docs:`, `chore:`, `feat:`, or `fix:` commits. PRs should explain the change, affected components, validation, and related issues. Commit and push submodule changes before publishing parent pointers. Preserve unrelated work and reproducible commit pins.

## Sources & Attribution

Preserve Bootlin source links and CC BY-SA 3.0 attribution. Separate project proposals from official course content. SadBoard's code license remains undecided; existing submodule licenses still apply.

## Experiment Release Workflow

Keep firmware at v0.0.1 and distinguish builds with full content IDs. Preserve matched vmlinux, source, configuration and symbols under images/debug/. Debug programs retain symbols; generic target binaries are stripped to fit the unchanged A/B slots. No scenario starts at boot. Verify the image and publish kernel/rootfs only, wait for the AM625 to report OTA success and pass scenario validation, then commit and push the scenario submodule before the SadBoard workspace branch. Never flash the generated factory image over the current device or change its partition layout as part of a debugging exercise.
