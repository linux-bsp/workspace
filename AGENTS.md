# Repository Guidelines

## Project Structure & Module Organization
This repository is currently empty aside from Git metadata. Keep the root clean and introduce a predictable layout as code is added:

- `src/` for application or library code
- `tests/` for automated tests
- `docs/` for design notes or usage documentation
- `assets/` for static files such as sample data or images

Use small, focused modules and group related files by feature or subsystem. Avoid mixing source files, scripts, and documentation at the repository root.

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
