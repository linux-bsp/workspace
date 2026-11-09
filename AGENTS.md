# Repository Guidelines

## Project Structure & Module Organization

SadBoard develops on the `SadBoard` branch of `linux-bsp/workspace`, using existing BSP submodules. AM6254 defaults to TFTP kernel/DTB and NFS root, with independent U-Boot switches and local SD A/B fallback. It provides systemd, SSH and ten manual scenarios: crash, FD exhaustion, cgroup OOM, CPU hotspot, mutex wait, isolated networking, startup panic recovery, periodic drift, queue backlog and TCP batching. The handbook has 59 case designs (35 basic and 24 advanced); 49 have no implementation yet. Random scenario orchestration and general automatic grading are not implemented. Record image build and board validation status separately.

- `README.md`: project scope, status, and documentation index.
- `docs/sadboard-debugging-handbook.md`: consolidated Chinese textbook, organized by case; includes preparation, tools, kernel reading, graded exercises, report template and Bootlin references. Extend the corresponding chapter rather than creating separate learning manuals. Distinguish source-derived paths from captured stacks.
- `docs/am625-debug-validation.md`: dated build and board evidence, separate from learning instructions.
- `docs/workspace-toolchain.md`: current shared directory layout and standalone SDK workflow.
- `docs/am62x/`, `docs/imx6ull/`, `docs/h200/`: board and hardware references; i.MX6ULL examples do not imply a supported SadBoard profile.
- `buildroot/`, `linux/`, `uboot/`: build system and versioned source submodules.
- `bsp-base-external/`: board support; keep the `LINUX_BSP` external identifier.
- `sadboard-external/`: `SADBOARD` external with AM6254 debugging fragments, setup script, and target overlay.
- `edk/`, `libbmc/`: existing software submodules.

Put learning guides in `docs/`, board references in `docs/<board>/`, and generated builds in ignored `output/`. Link new guides from `README.md`. Read submodule-specific instructions before changing their contents.
Keep firmware and device-management architecture in `edk/docs/`; link to it instead of maintaining another copy in this workspace. Completed phase results belong in the validation archive.

## Build, Test, and Development Commands

Initialize source submodules, then use the standard Buildroot entry:

```sh
git submodule update --init --recursive
cd buildroot
BR2_EXTERNAL="../bsp-base-external ../sadboard-external" \
  make sadboard_am625_debug_defconfig && make all
```

Without `O=`, artifacts go to `buildroot/output/`; the current board validation uses workspace `output/am625-debug-systemd/`. Keep output trees separate when changing toolchains. The Python helper remains optional for local toolchains and diagnostic variants. After changing baseline fragments, regenerate the checked-in defconfig with `--export-defconfig` in a fresh output directory and verify configuration equivalence; see the handbook's build appendix. Run `python3 sadboard-external/tests/test-labs.py` for scenario regressions. `sadboard list`, `sadboard run crash` and `sadboard verify crash` are target commands; verification checks the reference repair, not an arbitrary learner patch. Bootlin commands remain external lab instructions.

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

Keep firmware at v0.0.1 and distinguish builds with full content IDs. Preserve matched vmlinux, source, configuration and symbols under images/debug/. Debug programs retain symbols; generic target binaries are stripped to fit the unchanged A/B slots. No scenario starts at boot. Verify the image, validate kernel/rootfs OTA in local A/B mode, then deploy the matching images/netboot/ and rootfs.tar for network-mode checks before committing and pushing. Network debug boots skip production OTA/slot confirmation; their SBNET1 reference build ID does not prove a mutable NFS tree is unchanged. Do not interpret saved SD metadata as the running network image. Never flash the generated factory image, change the partition layout, or bypass the production bootloader-update restriction for a debugging exercise. State separately whether a new U-Boot was built, its generated environment tested, or its binary actually installed.

Use `sadboard status/check/reset RUN_DIRECTORY` for managed evidence. Network faults belong to owned namespaces, never the management eth0. The manual panic exercise requires a previously confirmed firmware, an extra reboot and an unsealed startup; pause confirmation with SIGSTOP/SIGCONT, since stopping its unit triggers OnFailure. Verify failed and healthy SPL/U-Boot/kernel archives, pstore and local recovery before committing that case. Preserve BusyBox configuration as well as kernel configuration: tool availability alone does not prove option support.

Use `sadboard results` to locate artifacts: NFS roots default to `/srv/sadboard` (host `/srv/nfs/sadboard-am625/srv/sadboard`), local roots to `/data/sadboard`. Check space on the selected result filesystem. Completed NFS runs grant host read access; `sadboard share DIRECTORY` handles manual captures without following symlinks. Keep device logs, OTA state and boot confirmation on SD data. Preserve existing SD evidence when copying it to NFS. Run `tests/test-results.py` for storage policy changes.

Advanced cases preserve completed work and checksums. Validate raw timestamp/queue CSV against summaries; do not equate send calls with wire packets or treat low CPU as proof of low latency. Separate repeatable correctness/resource contracts from measured performance. Keep production-inspired synthetic designs distinct from documented public incidents and actual hardware evidence.

Run native scenario tests in their temporary build directory. Buildroot must recompile local lab binaries with TARGET_CC even if synchronized files have newer timestamps; verify AArch64 ELF machine/class/endianness as well as debug sections before deployment.
