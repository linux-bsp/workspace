# Repository Guidelines

## Project Structure & Module Organization

SadBoard develops on the `SadBoard` branch of `linux-bsp/workspace`, using existing BSP submodules. AM6254 defaults to TFTP kernel/DTB and NFS root, with independent U-Boot switches and local SD A/B fallback. It provides systemd, SSH and 106 manual scenarios, including: crash, FD exhaustion, cgroup OOM, CPU hotspot, mutex wait, isolated networking, startup panic recovery, periodic drift, queue backlog and TCP batching. The handbook covers 35 basic, 24 advanced, 8 A64 and 39 kernel-subsystem cases: 104 target commands and two host UART controllers for real AM625 RAM boot faults. All validation uses AM625 hardware; do not substitute QEMU. Random scenario orchestration and general automatic grading are not implemented. Record image build and board validation status separately.

- `README.md`: project scope, status, and documentation index.
- `obsidian-sadboard/`: independent Chinese handbook repository and Git submodule, tracking `linux-bsp/obsidian-sadboard` on `master`. Start at `README.md`, the only Markdown note at the vault root. Chapters 01–06 follow hardware, OS foundations, compiler/build systems, assembly, kernel subsystems, and system debugging/optimization. Experiment preparation is nested under chapter 06. Case and tool indexes live in `06-系统调试与优化/00-实验准备与通用方法/`; the 35 basic and 24 advanced cases live under ten units in `06-系统调试与优化/`. Unit `11-综合工程复盘/` combines canonical cases in five engineering routes without increasing scenario totals. Each scenario unit keeps its own navigation named after the directory, e.g. `01-应用崩溃/01-应用崩溃.md`. Each `<case-id>-<specific-problem>/<case-id>：<actual-title>.md` contains the complete scenario, exercises, principles, kernel/assembly flow, diagnosis and repair evidence; use the full-width colon, for example `B-CPU04：错误订阅 EPOLLOUT 导致空转.md`. Shared tool parameters live once in `附录C-工具手册/<tool>.md`, with reciprocal links to concrete cases. Appendix A combines experiment reports/build practice, B covers Bootlin, and C contains tools. Add content to its owning note; keep source-derived paths distinct from captured stacks.
- `docs/am625-debug-validation.md`: dated build and board evidence, separate from learning instructions.
- `docs/workspace-toolchain.md`: current shared directory layout and standalone SDK workflow.
- `docs/am62x/`, `docs/imx6ull/`, `docs/h200/`: board and hardware references; i.MX6ULL examples do not imply a supported SadBoard profile.
- `buildroot/`, `linux/`, `uboot/`: build system and versioned source submodules.
- `bsp-base-external/`: board support; keep the `LINUX_BSP` external identifier.
- `sadboard-external/`: `SADBOARD` external with the AM6254 defconfig, diagnostic fragments, native build hooks, and target overlay.
- `edk/`, `libbmc/`: existing software submodules.

Put learning guides in `obsidian-sadboard/`, workspace guides in `docs/`, board references in `docs/<board>/`, and generated builds in ignored `output/`. Link new guides from `README.md`. Read submodule-specific instructions before changing their contents.
Keep firmware and device-management architecture in `edk/docs/`; link to it instead of maintaining another copy in this workspace. Completed phase results belong in the validation archive.

## Build, Test, and Development Commands

Initialize source submodules, then use the standard Buildroot entry:

```sh
git submodule update --init --recursive
cd buildroot
BR2_EXTERNAL="../bsp-base-external ../sadboard-external" \
  make sadboard_am625_debug_defconfig && make all
```

Without `O=`, artifacts go to `buildroot/output/`; the current board validation uses workspace `output/am625-debug-systemd/`. Keep output trees separate when changing toolchains. Configure SDKs, download paths and diagnostic fragments with Buildroot menuconfig. Maintain the portable profile with native savedefconfig in a fresh output directory; see the vault build appendix. Production builds and device/Device Manager programs must not use custom Python tooling; Python is limited to host tests, documentation checks and the serial validation controller. Upstream host dependencies such as U-Boot binman remain managed by Buildroot. Run `python3 sadboard-external/tests/test-labs.py` for scenario regressions. `sadboard list`, `sadboard run crash` and `sadboard verify crash` are target commands; verification checks the reference repair. Use `sadboard evaluate crash /absolute/candidate` for a learner's B-CR01 ELF snapshot; its ten-input contract is not a general grader. Bootlin commands remain external lab instructions.

Use `git diff --check`, `git diff --cached --check`, and `git status --short`. Review untracked files separately.
For learning-document changes, run `python3 obsidian-sadboard/scripts/check-obsidian.py --workspace .` from the workspace to validate wiki links, headings, case coverage, source paths and navigation reachability. A standalone handbook checkout can run `python3 scripts/check-obsidian.py` for documentation checks without BSP sources. Maintain the Obsidian vault directly; do not recreate a consolidated handbook or an export pipeline. Preserve the user's Obsidian settings; do not commit window state, caches or personal reports. Chinese chapter/note names are intentional in this vault.
Obsidian displays the filename as the note title; do not repeat it as a level-one heading in the body or add YAML note properties. Body sections start at `##`. Case IDs come from descriptive directory names and must match the filename prefix; personal reports belong in an optional ignored `实验记录/` directory. Avoid standalone pages that only repeat navigation or a small section of their parent topic.
Number body headings locally within each note: `## 1. Title`, `### 1.1 Title`, `#### 1.1.1 Title`. Keep siblings consecutive and nested under their parent; chapter directory numbers and case IDs remain separate. Every course, subsystem, scenario-unit and appendix navigation uses its directory's exact basename, e.g. `05-内核子系统/05-内核子系统.md`; do not recreate `00-章节导航.md`. Update heading links together and leave fenced commands and captured evidence unchanged.
Kernel learning material is not restricted to a particular commit. Use the kernel repository's `master` branch for reading links and the actual checked-out sources for local study. Keep historical evidence tied to its recorded build; addresses and disassembly require that firmware's matching sources and symbols.
Kernel teaching lives under `obsidian-sadboard/05-内核子系统/`, with a shared navigation note and numbered subsystem directories `01-进程管理/` through `14-运行时电源管理/`. Each subsystem has a framework/principles note and 5–10 progressive studies, covering design goals, core objects, conditional source paths, evidence, diagnosis and repair. Reuse a case's canonical note and link back to every learning route; do not inflate scenario totals for reuse. Distinguish implemented experiments from proposed driver, IRQ, RCU, power-management and storage-fault extensions. A single API demonstration does not constitute a subsystem course. Keep SMP CPU topology and lifecycle distinct from AMP remote firmware; AM625 A53 read-only observations do not prove M4F/R5F RPMsg or CPU-hotplug validation. Do not change CPU online, management IRQ/RPS or remote firmware for documentation exercises.
Assembly teaching lives under `obsidian-sadboard/04-汇编与体系结构/`, with second-level directories for fundamentals, x86, ARMv7, ARMv8, RV32, RV64, compilation/debugging, and AM625 experiments. Keep one canonical note per topic and preserve all case IDs and command blocks when moving notes. ABI/data-model reference lives in `02-操作系统原理/01-ABI与数据模型/` and is linked from the assembly course.
OS foundations live under `obsidian-sadboard/02-操作系统原理/`, hardware foundations under `01-常用硬件知识/`, both grouped by topic with case backlinks. OS study starts with ABI/data models. Compiler principles, cross-compilation, Buildroot and Yocto have their own `03-编译原理与构建系统/` chapter; distinguish compiler/build responsibilities from OS execution and resource management. Keep Yocto teaching-version and host/BSP compatibility distinct from current Buildroot product support. Mark host-run exercises separately from cross-compiled objects and AM625 execution. Explain mechanisms and assumptions before implementation details. Electrical limits and protocol timings need primary vendor/specification sources; label teaching calculations and distinguish schematic/DTS review from physical measurement. Do not treat GPIO polarity as output topology, software enumeration as electrical validation, or SD evidence as proof for other storage media. Theory notes do not increase runnable case totals.

## Coding Style & Naming Conventions

Write learning documentation in Chinese; preserve official identifiers and commands. Use descriptive headings, hyphenated lowercase filenames, and language-tagged code fences. Follow existing language conventions in source submodules; otherwise use four-space indentation for new source files. No workspace-wide formatter is configured.
In the Obsidian vault, group safe related configuration commands such as consecutive U-Boot setenv or GDB settings. Keep build, connection, fault-trigger, validation and inspection steps separate when their results must be checked. Keep background launch/PID capture and exit-status capture together. Precede every code block with a concise purpose and execution context or interpretation note. Preserve complete continuations, pipelines, quoted subprocess bodies, source, configuration and output examples.

## Validation and Scenario Guidelines

Check relative links, citations, platform assumptions, and configuration loading. Report the actual environment and distinguish reviewed instructions from executed experiments. Proposed scenarios should specify symptoms, prerequisites, triggers, expected evidence, root cause, repair verification, and reset procedures. Keep planned behavior distinct from implemented functionality. Use each submodule's own testing instructions for code changes.

## Commit & Pull Request Guidelines

Use focused `docs:`, `chore:`, `feat:`, or `fix:` commits. PRs should explain the change, affected components, validation, and related issues. Commit and push submodule changes before publishing parent pointers. Preserve unrelated work and reproducible commit pins.

## Sources & Attribution

Preserve Bootlin source links and CC BY-SA 3.0 attribution. Separate project proposals from official course content. SadBoard's code license remains undecided; existing submodule licenses still apply.

## Experiment Release Workflow

Keep firmware at v0.0.1 and distinguish builds with full content IDs. Preserve matched vmlinux, source, configuration and symbols under images/debug/. Debug programs retain symbols; generic target binaries are stripped to fit the unchanged A/B slots. No scenario starts at boot. Verify the image, validate kernel/rootfs OTA in local A/B mode, then deploy the matching images/netboot/ and rootfs.tar for network-mode checks before committing and pushing. Wait for the server to receive fwctld success before restoring network boot; local confirmation alone can precede the next reporting poll. Network debug boots skip production OTA/slot confirmation; their BSPNET1 reference build ID does not prove a mutable NFS tree is unchanged. Do not interpret saved SD metadata as the running network image. Never flash the generated factory image, change the partition layout, or bypass the production bootloader-update restriction for a debugging exercise. State separately whether a new U-Boot was built, its generated environment tested, or its binary actually installed.

Use `sadboard status/check/reset RUN_DIRECTORY` for managed evidence. Network faults belong to owned namespaces, never the management eth0. The manual panic/Oops/lockup exercises require a previously confirmed firmware, an extra reboot and an unsealed startup; pause confirmation with SIGSTOP/SIGCONT, since stopping its unit triggers OnFailure. Verify failed and healthy SPL/U-Boot/kernel archives, pstore and local recovery before committing that case. Preserve BusyBox configuration as well as kernel configuration: tool availability alone does not prove option support.

Use `sadboard results` to locate artifacts: NFS roots default to `/srv/sadboard` (host `/srv/nfs/sadboard-am625/srv/sadboard`), local roots to `/data/sadboard`. Check space on the selected result filesystem. Completed NFS runs grant host read access; `sadboard share DIRECTORY` handles manual captures without following symlinks. Keep device logs, OTA state and boot confirmation on SD data. Preserve existing SD evidence when copying it to NFS. Run `tests/test-results.py` for storage policy changes.

Advanced cases preserve completed work and checksums. Validate raw timestamp/queue CSV against summaries; do not equate send calls with wire packets or treat low CPU as proof of low latency. Separate repeatable correctness/resource contracts from measured performance. Keep production-inspired synthetic designs distinct from documented public incidents and actual hardware evidence.

Run native scenario tests in their temporary build directory. Buildroot must recompile local lab binaries with TARGET_CC even if synchronized files have newer timestamps; verify AArch64 ELF machine/class/endianness as well as debug sections before deployment.

Kernel laboratories use a shared inherited flock, an idle manually loaded module, bounded owned DMA allocations and exact-firmware recovery checks. Prove actual hardware watchdog reset with `sadboard-external/scripts/sadboard-board.py watchdog-probe` in network mode or the documented recorded SD probe before an all-CPU lockup; the proof must match the running content ID. RAM boot exercises never save bad U-Boot arguments or write partitions. The USB UART does not forward BREAK; the complete laboratory initramfs includes an independent timeout rescue child and a tested short-deadline reference.

K-ASY laboratories own a private module, bounded workqueues/kthreads and a trace instance. Validate event order, outcome, independent function trace, trace-loss statistics and resource cleanup together; preserve unrelated/global tracing configuration. Reference-count faults quarantine memory until callbacks finish. Ordinary worker execution does not prove physical IRQ, RCU or lockdep behavior, and controlled gates do not establish production latency guarantees.
