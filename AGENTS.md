# Repository Guidelines

## Project Structure & Module Organization

SadBoard develops on the `SadBoard` branch of `linux-bsp/workspace`, using existing BSP submodules. Learning scenarios, experiment images, automated checks, and CLI commands are not implemented yet.

- `README.md`: project scope, status, and documentation index.
- `docs/bootlin-linux-debugging-guide.md`: Chinese Bootlin study guide.
- `docs/workspace-guide.md`: inherited workspace operations; check historical platform examples before use.
- `buildroot/`, `linux/`, `uboot/`: build system and versioned source submodules.
- `bsp-base-external/`: board support; keep the `LINUX_BSP` external identifier.
- `sadboard-external/`: minimal `SADBOARD` external skeleton for future experiments.
- `edk/`, `libbmc/`, `zd_interface/`: existing software submodules.

Put learning guides in `docs/`, board references in `docs/<board>/`, and generated builds in ignored `output/`. Link new guides from `README.md`. Read submodule-specific instructions before changing their contents.

## Build, Test, and Development Commands

Initialize the build configuration layers:

```sh
git submodule update --init -- buildroot bsp-base-external sadboard-external
make -C buildroot O="$PWD/output/sadboard" \
  BR2_EXTERNAL="$PWD/bsp-base-external $PWD/sadboard-external" list-defconfigs
```

This lists configurations; it does not build firmware or enable debugging tools. Full builds require the selected board's source submodules and configuration. No SadBoard test runner exists. Bootlin guide commands are external lab instructions.

Use `git diff --check`, `git diff --cached --check`, and `git status --short`. Review untracked files separately.

## Coding Style & Naming Conventions

Write learning documentation in Chinese; preserve official identifiers and commands. Use descriptive headings, hyphenated lowercase filenames, and language-tagged code fences. Follow existing language conventions in source submodules; otherwise use four-space indentation for new source files. No workspace-wide formatter is configured.

## Validation and Scenario Guidelines

Check relative links, citations, platform assumptions, and configuration loading. Report the actual environment and distinguish reviewed instructions from executed experiments. Proposed scenarios should specify symptoms, prerequisites, triggers, expected evidence, root cause, repair verification, and reset procedures. Keep planned behavior distinct from implemented functionality. Use each submodule's own testing instructions for code changes.

## Commit & Pull Request Guidelines

Use focused `docs:`, `chore:`, `feat:`, or `fix:` commits. PRs should explain the change, affected components, validation, and related issues. Commit and push submodule changes before publishing parent pointers. Preserve unrelated work and reproducible commit pins.

## Sources & Attribution

Preserve Bootlin source links and CC BY-SA 3.0 attribution. Separate project proposals from official course content. SadBoard's code license remains undecided; existing submodule licenses still apply.
