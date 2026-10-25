"""The real simulator reproduction gate for the silicon-DV extension.

For each of the 8 real OpenTitan blocks (blocks.py), this compiles and runs a genuine Verilator
simulation twice: once against the "suspect" RTL (third_party/buggy/<file>, one planted defect)
and once against the "fix" RTL (third_party/opentitan_prim/<file>, unmodified upstream). An
attribution is accepted only when the suspect run's self-checking testbench fails (nonzero exit)
and the fix run's passes (exit 0), mirroring repro_gate.py's subprocess-isolation discipline one
level down: here the isolation is a full Verilator build plus a real simulation binary, not a
Python subprocess running a generated script.

Verilator is not installed on Windows; every build and run happens inside WSL2 Ubuntu-22.04 via
`wsl.exe`, per BUILDER section 3. Each call gets a fresh --Mdir so suspect and fix builds of the
same block never share object files.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from .blocks import BLOCKS, Block

REPO_ROOT = Path(__file__).resolve().parents[3]
THIRD_PARTY_FIXED = REPO_ROOT / "third_party" / "opentitan_prim"
THIRD_PARTY_BUGGY = REPO_ROOT / "third_party" / "buggy"
CPP_TB_DIR = Path(__file__).resolve().parent / "cpp_tb"

WSL_DISTRO = "Ubuntu-22.04"

# `prim_assert.sv` and the macro headers it includes are shared infrastructure every block that
# uses `` `include "prim_assert.sv" `` needs on its include path; they are not one of the 8
# blocks themselves (see third_party/opentitan_prim/PROVENANCE.md).
ASSERT_SUPPORT_FILES = (
    "prim_assert.sv",
    "prim_assert_dummy_macros.svh",
    "prim_assert_standard_macros.svh",
    "prim_assert_yosys_macros.svh",
    "prim_assert_sec_cm.svh",
    "prim_flop_macros.sv",
)


def _to_wsl_path(windows_path: Path) -> str:
    s = str(windows_path.resolve())
    drive, rest = s.split(":", 1)
    return "/mnt/" + drive.lower() + rest.replace("\\", "/")


@dataclass
class SimResult:
    variant: str  # "suspect" or "fix"
    passed: bool  # True iff the testbench binary exited 0
    stdout: str
    stderr: str
    elapsed_s: float


def _run_wsl_bash(script: str, timeout_s: int = 120) -> subprocess.CompletedProcess:
    """Runs `script` as a real file inside WSL, not as a `bash -lc "<string>"` argument.

    `bash -lc "cmd1; cmd2; echo $?"` passed inline through wsl.exe was observed, during this
    build, to sometimes report a stale or wrong `$?` for the final command in a multi-statement
    string (reproduced even with a trivial `false; echo $?`), while the exact same statements
    run as a script file behave correctly every time. This writes the script to a file inside
    WSL first (over stdin, so no Windows path or quoting is involved) and then runs that file.
    """
    write = subprocess.run(
        ["wsl.exe", "-d", WSL_DISTRO, "--", "bash", "-c", "mkdir -p ~/dv_build && cat > ~/dv_build/_run.sh"],
        input=script,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if write.returncode != 0:
        return write
    return subprocess.run(
        ["wsl.exe", "-d", WSL_DISTRO, "--", "bash", "~/dv_build/_run.sh"],
        capture_output=True,
        text=True,
        timeout=timeout_s,
    )


def build_and_run(block: Block, variant: str, build_root: Path) -> SimResult:
    """variant is "suspect" (buggy RTL) or "fix" (unmodified RTL).

    GNU Make (which `verilator --build` shells out to) refuses to build in a directory
    containing spaces, and this repo's own path does ("Total Job Application process flow"),
    so the actual Verilator --Mdir lives under the WSL home directory instead of under
    `build_root` (per BUILDER section 3's "use native /tmp or ~/build/<name>" guidance);
    `build_root` is kept only as the caller-facing handle for where logs get copied back.
    """
    assert variant in ("suspect", "fix")
    rtl_dir = THIRD_PARTY_BUGGY if variant == "suspect" else THIRD_PARTY_FIXED
    rtl_path = rtl_dir / block.rtl_file
    tb_path = CPP_TB_DIR / block.testbench

    rtl_wsl = _to_wsl_path(rtl_path)
    tb_wsl = _to_wsl_path(tb_path)
    mdir_wsl = f"~/dv_build/{block.name}_{variant}"

    extra_src_paths = [_to_wsl_path(THIRD_PARTY_FIXED / s) for s in block.extra_sources]
    param_flags = " ".join(f"-G{p}" for p in block.params)
    define_flags = " ".join(f"-D{d}" for d in block.defines)

    # Verilator 4.038's generated Makefile does not robustly escape spaces in source paths
    # (this repo's own path has spaces: "Total Job Application process flow"), so every source
    # file is copied into the space-free build directory first and referenced by bare filename.
    copy_cmds = [f"cp '{rtl_wsl}' .", f"cp '{tb_wsl}' ."]
    for p in extra_src_paths:
        copy_cmds.append(f"cp '{p}' .")
    for support_file in ASSERT_SUPPORT_FILES:
        copy_cmds.append(f"cp '{_to_wsl_path(THIRD_PARTY_FIXED / support_file)}' .")
    copy_script = " && ".join(copy_cmds)
    extra_src_names = " ".join(Path(s).name for s in block.extra_sources)

    script = (
        f"mkdir -p {mdir_wsl} && cd {mdir_wsl} && {copy_script} && "
        f"verilator --cc -sv -Wno-fatal -Wno-UNOPTFLAT +incdir+. {define_flags} {param_flags} "
        # Packages (extra_src_names) must precede the file that `import`s them; Verilator (and
        # SystemVerilog generally) does not forward-reference packages across files.
        f"{extra_src_names} {block.rtl_file} --top-module {block.top_module} "
        f"--exe {Path(block.testbench).name} --build -o sim -j 4 > build.log 2>&1; "
        f"BUILD_RC=$?; "
        f"if [ \"$BUILD_RC\" -ne 0 ]; then echo SIM_EXIT:$BUILD_RC; echo ---BUILD_LOG---; tail -c 4000 build.log; "
        f"else ./obj_dir/sim; echo SIM_EXIT:$?; fi"
    )

    start = time.perf_counter()
    try:
        proc = _run_wsl_bash(script)
        elapsed = time.perf_counter() - start
        sim_exit = None
        for line in proc.stdout.splitlines():
            if line.startswith("SIM_EXIT:"):
                sim_exit = int(line.split(":", 1)[1].strip())
        passed = sim_exit == 0
        return SimResult(
            variant=variant,
            passed=passed,
            stdout=proc.stdout,
            stderr=proc.stderr,
            elapsed_s=elapsed,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = time.perf_counter() - start
        return SimResult(
            variant=variant,
            passed=False,
            stdout=(exc.stdout or ""),
            stderr=f"TIMEOUT after {elapsed:.1f}s",
            elapsed_s=elapsed,
        )


@dataclass
class GateDecision:
    block: str
    suspect: SimResult
    fix: SimResult

    @property
    def accepted(self) -> bool:
        """An attribution is accepted only if the suspect build fails and the fix build passes."""
        return (not self.suspect.passed) and self.fix.passed


def run_repro_gate(block_name: str, build_root: Path) -> GateDecision:
    block = next(b for b in BLOCKS if b.name == block_name)
    suspect = build_and_run(block, "suspect", build_root)
    fix = build_and_run(block, "fix", build_root)
    return GateDecision(block=block_name, suspect=suspect, fix=fix)


def run_all(build_root: Path) -> list[GateDecision]:
    return [run_repro_gate(b.name, build_root) for b in BLOCKS]
