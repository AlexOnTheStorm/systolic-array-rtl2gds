# Lab environment: installation and smoke tests

> Recorded 2026-11-02 on the author's Mac: macOS 26.6.2 (25G83), Apple Silicon (arm64), 10 cores, 32 GB RAM; Docker Desktop 4.64.0 (Engine 29.2.1, VM: 10 CPU / 7.65 GiB). Every command below **was actually run**; outputs are excerpts from the real logs. Where a command was not run, this is said explicitly: "not verified locally: <reason>".
>
> ⚠️ This changes: nightly build versions, the LibreLane image tag, the PDK pin, flag names (sv-elab ← yosys-slang, OpenSTA `define_scene`). Primary sources: [OSS CAD Suite releases](https://github.com/YosysHQ/oss-cad-suite-build/releases), [LibreLane releases](https://github.com/librelane/librelane/releases), [LibreLane Docker install (macOS)](https://github.com/librelane/librelane/blob/main/docs/source/installation/docker_installation/installation_macos.md), [ciel](https://github.com/fossi-foundation/ciel).
>
> RTL for the smoke tests is `gemm_kernelgen/rtl/{pe,systolic_array}.sv` from the sibling repo [systolic-gemm-kernelgen](https://github.com/AlexOnTheStorm/systolic-gemm-kernelgen) (read-only: nothing is changed or written there). Folder layout — see `README.md` → Reproduce. Below, `P` is the parent folder that contains both `asic_rtl2gds/` and `gemm_kernelgen/`.

## 0. Summary: which tool does what

| Task | Tool and version | Environment (§1) | Verified in |
|---|---|---|---|
| Lint | Verilator 5.055-devel `--lint-only -Wall`; `slang` (sv-elab); Verible v0.0-4080-ga0a8d8eb | A (OSS CAD Suite); Verible — tarball in `~/tools`, on PATH via the shell profile (§2.1) | §3.1 |
| Synthesis | Yosys 0.70+290, `read_slang` frontend built in | A | §3.2 |
| STA | OpenSTA 2.7.0 (`sta`) | B (LibreLane container) | §3.3 |
| Formal | SymbiYosys + smtbmc | A | §3.4 |
| Equivalence | EQY v0.70 | A | §3.5 |
| Simulation (RTL, gate-level + SDF) | Icarus Verilog 14.0-devel | A | version — §2.1; runs are in the companion labs, not here |
| RTL→GDS flow | LibreLane 3.0.17, Classic flow (inside: Yosys 0.62, OpenROAD, OpenSTA 2.7.0, Magic 8.3.623, KLayout 0.30.7, Netgen) | B | §4 |
| PDK | SKY130A, commit `8afc8346a57fe1ab7934ba5a6056ea8b43078e71`, `sky130_fd_sc_hd` | `~/.ciel` (read by A and B) | §2.3 |

## 1. Three environments — do not mix them in one shell

`~/tools/oss-cad-suite/environment` overrides `PATH` and **`python3`** (with its own 3.11.6), as well as `verilator` (5.055-devel instead of Homebrew 5.050) and `iverilog` (14.0-devel instead of Homebrew 13.0). Therefore:

- **A — OSS CAD Suite** (lint, synthesis, formal, EQY, Icarus). Separate terminal window:
  ```sh
  source ~/tools/oss-cad-suite/environment   # prompt gets the (oss-cad-suite) prefix
  # ... work ...
  deactivate                                  # restore the original PATH/python3
  ```
- **B — LibreLane in Docker** (STA, RTL→GDS flow). Run from a plain shell (without A); Docker Desktop must be up (`open -a Docker`, then `docker info`). The command is an explicit `docker run` with narrow bind mounts (why not `librelane --dockerized` — §5.2):
  ```sh
  P=/path/to/parent            # contains asic_rtl2gds/ and gemm_kernelgen/
  docker run --rm -i \
    -v "$P:$P" -v "$HOME/.ciel:$HOME/.ciel" -e PDK_ROOT="$HOME/.ciel" \
    -w "$PWD" ghcr.io/librelane/librelane:3.0.17 <command>
  ```
  The working directory (`$PWD`) must be inside `$P`, otherwise the container cannot see it.

  Mount pitfall (observed, cause not investigated): mounting the whole parent folder with `:ro` showed up inside the container as an **empty directory**, while mounting `asic_rtl2gds` itself with `:ro` worked. So mount narrowly: the working folder (rw) + the specific subfolders you need (`:ro`) + `~/.ciel`. `flow/run_flow.sh` does exactly that.

  Run dependency: anything that reads a routed design (power analysis, gate-level simulation of the routed netlist) needs `flow/runs/r1_14ns/`, which is **gitignored** (`**/runs/`, hundreds of MB). On a fresh clone, recreate it first: `flow/run_flow.sh r1_14ns` (~9 min, see `reports/walltime.txt`).
- **C — Homebrew stack** (Verilator 5.050, Icarus 13.0, cocotb 2.0.1 in a separate venv) — used by the author's companion RTL labs (cocotb + Verilator), not by anything in this repo. Do not activate together with A.

## 2. Installation (what was done; all in user space)

Policy: user space only. No Nix, no `sudo`, shell profiles (`~/.zshrc` etc.) untouched by the install.

### 2.1. OSS CAD Suite (nightly 2026-11-02, darwin-arm64)

```sh
cd ~/tools
curl -sSL -o oss-cad-suite-darwin-arm64-20261102.tgz \
  https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2026-11-02/oss-cad-suite-darwin-arm64-20261102.tgz
shasum -a 256 oss-cad-suite-darwin-arm64-20261102.tgz
tar -xzf oss-cad-suite-darwin-arm64-20261102.tgz        # → ~/tools/oss-cad-suite (1.8 GB)
```
Output: 525 289 896 bytes in 1 min 32 s; `d1191cdc3be3b63f52d0adbddb64436a4538897a193d157d1ca714706cc4ccf0`; unpacking took 5 s.

Quarantine: the README suggests `./activate`, but that script runs `sudo find . -exec xattr -d com.apple.quarantine` — **not run** (no sudo). It is not needed either: `curl` does not set the quarantine attribute; the check returned 0 files:
```sh
xattr -r -p com.apple.quarantine ~/tools/oss-cad-suite 2>/dev/null | wc -l    # → 0
```
(If the archive was downloaded with a browser, the attribute will be set; then, without sudo: `xattr -dr com.apple.quarantine ~/tools/oss-cad-suite` — not verified locally: not needed.)

Versions (environment A):
```text
$ yosys -V
Yosys 0.70+290 (git sha1 e8968a4f7, Release, Clang ... 21.1.8)
$ eqy --version
EQY v0.70-2-g3301516
$ iverilog -V
Icarus Verilog version 14.0 (devel) (s20260301-802-g61dbc3c28-dirty)
$ verilator --version
Verilator 5.055 devel rev v5.054-27-g88607c2f8 (mod)
$ which sta openroad
sta not found
openroad not found
```
OpenSTA and OpenROAD are **not** in OSS CAD Suite, and Homebrew has no `opensta` formula (`brew info opensta` → `No available formula`). So STA runs from the LibreLane container (§3.3).

`read_slang` is built into Yosys 0.70: `yosys -p "help read_slang"` works without `-m slang`. The `-m slang` flag from older tutorials is no longer required; whether it still works — not verified locally: not run.

Verible (lint/format; does not need environment A) — a separate macOS release tarball, unpacked into `~/tools`:
```sh
cd ~/tools
curl -sSL -o verible-v0.0-4080-ga0a8d8eb-macOS.tar.gz \
  https://github.com/chipsalliance/verible/releases/download/v0.0-4080-ga0a8d8eb/verible-v0.0-4080-ga0a8d8eb-macOS.tar.gz
shasum -a 256 verible-v0.0-4080-ga0a8d8eb-macOS.tar.gz
tar -xzf verible-v0.0-4080-ga0a8d8eb-macOS.tar.gz       # → ~/tools/verible-v0.0-4080-ga0a8d8eb-macOS/bin/
export PATH="$HOME/tools/verible-v0.0-4080-ga0a8d8eb-macOS/bin:$PATH"
verible-verilog-lint --version                         # → Version v0.0-4080-ga0a8d8eb
```
Verible was already installed before this setup (the `PATH` line was already in `~/.zshrc`). Checked 2026-11-05: the URL serves the archive (7 941 752 bytes, sha256 `96115cd3fa3e5a1172e3be834ba5d0fd15d310441ee8580a833d25f89d43638e`) containing `verible-v0.0-4080-ga0a8d8eb-macOS/bin/`; it was not re-unpacked over the existing install. ⚠️ This changes: [Verible releases](https://github.com/chipsalliance/verible/releases).

### 2.2. LibreLane 3.0.17 (pip in a venv + Docker image)

```sh
/opt/homebrew/bin/python3.12 -m venv ~/tools/librelane-venv
~/tools/librelane-venv/bin/python -m pip install --upgrade pip
~/tools/librelane-venv/bin/python -m pip install librelane==3.0.17
~/tools/librelane-venv/bin/python -m pip show librelane | head -2   # Name: librelane / Version: 3.0.17
```
The venv is there for `ciel` (PDK manager, §2.3) and `librelane --help` on the host; the flow itself runs in the container.

Image (arm64, native, no x86 emulation):
```sh
curl -s --unix-socket ~/.docker/run/docker.sock -X POST \
  "http://localhost/v1.53/images/create?fromImage=ghcr.io/librelane/librelane&tag=3.0.17"
docker image inspect ghcr.io/librelane/librelane:3.0.17 --format '{{.Architecture}} {{.Os}}'   # → arm64 linux
```
Output: `Status: Downloaded newer image for ghcr.io/librelane/librelane:3.0.17`, 764 s (≈13 min), 7.5 GB on disk (1.47 GB compressed). Why the socket and not `docker pull` — §5.1.

Tools inside the image:
```text
$ docker run --rm ghcr.io/librelane/librelane:3.0.17 zsh -c 'sta -version; yosys -V; klayout -v; magic --version; librelane --version'
2.7.0
Yosys 0.62 (git sha1 7326bb7d6641500ecb285c291a54a662cb1e76cf, clang++ 21.1.2 -fPIC -O3)
KLayout 0.30.7
8.3.623
LibreLane v3.0.17
```
(`openroad -version` prints only the git hash `dcf36133a369abc8f3c5e5738cd4d82e4903c0e0`.)

LibreLane smoke test (the `spm` example, SKY130):
```sh
docker run --rm -i -v "$HOME/.ciel:$HOME/.ciel" -e PDK_ROOT="$HOME/.ciel" \
  ghcr.io/librelane/librelane:3.0.17 librelane --smoke-test
```
```text
[13:34:52] INFO     Starting a new run of the 'Classic' flow with ...
[13:35:45] INFO     Smoke test passed.                           __main__.py:297
```
rc=0, 54 s.

### 2.3. SKY130 PDK via ciel

LibreLane 3.0.17 pins the PDK commit in `librelane/pdk_hashes.yaml` (`sky130: 8afc8346a57fe1ab7934ba5a6056ea8b43078e71`). Install exactly that:
```sh
~/tools/librelane-venv/bin/ciel enable --pdk-family sky130 8afc8346a57fe1ab7934ba5a6056ea8b43078e71
```
```text
Ciel v2.6.1 ©2022-2025 Efabless Corporation and Contributors
Downloading common.tar.zst… ━━━━━━━━━━ 100%
Downloading sky130_fd_sc_hd.tar.zst… ━━━━━━━━━━ 100%
...
Version 8afc8346a57fe1ab7934ba5a6056ea8b43078e71 enabled for the sky130 PDK.
```
67 s, `~/.ciel` = 2.1 GB (`sky130A`, `sky130B`). The typical-corner Liberty used by the smoke tests:
`~/.ciel/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib`
(the folder also has `ss_100C_1v60`, `ff_n40C_1v95` and others — for multi-corner STA).

## 3. Smoke tests

Files are in `smoke/` (generated outputs are gitignored). All commands run from that folder.

### 3.1. Lint (environment A)

```sh
source ~/tools/oss-cad-suite/environment
G=../../gemm_kernelgen/rtl
verilator --lint-only -Wall $G/pe.sv $G/systolic_array.sv --top-module systolic_array
slang $G/pe.sv $G/systolic_array.sv --top systolic_array
verible-verilog-lint $G/pe.sv $G/systolic_array.sv
```
```text
- V e r i l a t i o n   R e p o r t: Verilator 5.055 devel rev v5.054-27-g88607c2f8 (mod)
- Verilator: Built from 0.052 MB sources in 4 modules, into 0.094 MB in 5 C++ files needing 0.000 MB
rc=0
Top level design units:
    systolic_array
Build succeeded: 0 errors, 0 warnings
rc=0
(verible-verilog-lint: empty output) rc=0
```
All three linters are clean on gemm with default settings.

### 3.2. Synthesis of `pe.sv` for SKY130 HD (environment A)

`smoke/synth_pe.ys`:
```tcl
read_slang ../../gemm_kernelgen/rtl/pe.sv --top pe
synth -top pe -flatten
dfflibmap -liberty sky130_fd_sc_hd__tt_025C_1v80.lib
abc -liberty sky130_fd_sc_hd__tt_025C_1v80.lib -dont_use *lpflow* -D 10000
opt_clean -purge
hilomap -hicell sky130_fd_sc_hd__conb_1 HI -locell sky130_fd_sc_hd__conb_1 LO
tee -o synth_pe_stat.txt stat -liberty sky130_fd_sc_hd__tt_025C_1v80.lib
write_verilog -noattr pe_netlist.v
```
```sh
ln -sf ~/.ciel/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib .
yosys -q -l synth_pe.log synth_pe.ys        # 0.6 s
```
```text
      678   5004.8 cells
       64 1.28E+03   sky130_fd_sc_hd__dfxtp_1
       81   709.43   sky130_fd_sc_hd__xnor2_1
       64  560.538   sky130_fd_sc_hd__xor2_1
       96  480.461   sky130_fd_sc_hd__o21ai_0
   Chip area for module '\pe': 5004.800000
     of which used for sequential elements: 1281.228800 (25.60%)
```
Observations (real, from this run):
- **64 flip-flops, not 80**: the pairs `a_r` ≡ `a_out` and `b_r` ≡ `b_out` have identical next-state logic, and `opt_merge` merged each pair into one register (8+8+16+32 = 64). Explanation, not observation (no Vivado netlist was inspected here): on an FPGA such copies usually stay separate because one goes into the DSP48 AREG/BREG and the other continues along the array; here there is nothing to pack into. The same merge breaks EQY without `keep` (§3.5).
- All flip-flops are `dfxtp_1` (no reset pin): the synchronous reset went into the logic in front of D, as intended in gemm.
- Without `-dont_use *lpflow*`, ABC picks `lpflow_inputiso*`/`lpflow_isobufsrc` (low-power isolation cells) as ordinary gates — the first run produced 18 of them. LibreLane excludes them itself; in a hand-written script, use the flag.

### 3.3. STA of the `pe` netlist in OpenSTA (environment B)

`smoke/pe_smoke.sdc` (100 MHz, 2 ns external delay, 10 fF load) and `smoke/sta_pe.tcl` (`read_liberty` → `read_verilog pe_netlist.v` → `link_design pe` → `read_sdc` → `report_checks` max/min → `report_wns`/`report_tns`). The netlist comes from §3.2. `~/.ciel` is mounted at **the same path** as on the host: `sky130_fd_sc_hd__tt_025C_1v80.lib` in `smoke/` is the §3.2 symlink to the absolute `~/.ciel/...` path, and with a different mount path `read_liberty` inside the container will not find it.
```sh
cd "$P/asic_rtl2gds/smoke"
docker run --rm -i -v "$P:$P" -v "$HOME/.ciel:$HOME/.ciel" -w "$PWD" \
  ghcr.io/librelane/librelane:3.0.17 sta -no_init -exit sta_pe.tcl > sta_pe.log 2>&1
```
```text
OpenSTA 2.7.0 GITDIR-NOT Copyright (c) 2025, Parallax Software, Inc.
Startpoint: _1229_ (rising edge-triggered flip-flop clocked by clk)
Endpoint: _1258_ (rising edge-triggered flip-flop clocked by clk)
Path Type: max
            0.000    0.000 ^ _1229_/CLK (sky130_fd_sc_hd__dfxtp_1)
   0.019    0.186    0.388    0.388 ^ _1229_/Q (sky130_fd_sc_hd__dfxtp_1)
            0.115    0.000    0.703 v _0899_/C (sky130_fd_sc_hd__maj3_1)
   ...      (a chain of maj3_1 — the 32-bit accumulator carry)
                              7.307   data arrival time
                    -0.076    9.924   library setup time
                              2.617   slack (MET)
Path Type: min
                              0.471   slack (MET)
wns max 0.00
tns max 0.00
```
The critical path is the **accumulator loop** `acc → acc` (ripple carry through the `maj3` chain), not the multiplier. Checked in the netlist: `_1229_` is flip-flop `acc[1]`, `_1258_` is `acc[30]` (`grep -A5 " _1229_ (" pe_netlist.v`). *(Corrected 2026-11-03: an earlier version of this file named the multiplier — a misreading of the report.)* Pre-placement timing: ideal clock, no wire parasitics.

Caveat: this is a property of **this particular synthesis script** (generic `synth` + `abc -D`). In the full LibreLane flow (§4, `flow/`) the synthesized netlist is different (0 `maj3` cells, ABC script `AREA_0`), and after place-and-route the worst register-to-register path in the ss corner is in the multiplier: operand register `a_h[131]` → `prod_r[14]` (`reports/r0_10ns/path_notes.txt`).

### 3.4. SymbiYosys "hello" (environment A)

`smoke/pe_hello_props.sv` wraps `pe`: start from reset (`assume`), then an immediate `assert`: "one cycle after `clear` (with reset deasserted) `acc`, `a_out`, `b_out` are zero". `smoke/pe_hello.sby`: `mode prove`, engine `smtbmc`, `read -formal` (Yosys native frontend).
```sh
sby -f pe_hello.sby
```
```text
SBY 14:07:02 [pe_hello] engine_0.basecase: Status returned by engine for basecase: pass
SBY 14:07:02 [pe_hello] summary: engine_0 (smtbmc) returned pass for basecase
SBY 14:07:02 [pe_hello] summary: engine_0 (smtbmc) returned pass for induction
SBY 14:07:02 [pe_hello] summary: successful proof by k-induction.
SBY 14:07:02 [pe_hello] DONE (PASS, rc=0)
```
2 s. Vacuity control: a copy with a deliberately false `acc == 1` (in a temp folder) gives `returned FAIL for basecase`, `counterexample trace [basecase]: .../trace.vcd`, `DONE (FAIL, rc=2)`.

⚠️ Open-source Yosys understands immediate asserts and a limited SVA subset; full SVA (sequences, `throughout`) needs the commercial Verific frontend (Tabby CAD). Source: [sby + Verific](https://yosyshq.readthedocs.io/projects/sby/en/latest/verific.html).

### 3.5. EQY "hello": RTL vs netlist (environment A)

`smoke/pe_eqy.eqy`: gold = `read_slang pe.sv; prep`; gate = `read_slang pe.sv; proc; setattr -set keep 1 t:*dff*; synth -flatten`; strategy `sby` (smtbmc + bitwuzla, depth 5). EQY has no `[files]` section (it is commented out in the source) — paths go directly into `read_slang`.
```sh
eqy -f pe_eqy.eqy
```
```text
EQY 14:38:02 [pe_eqy] Successfully proved equivalence of partition pe.acc
EQY 14:38:02 [pe_eqy] Successfully proved designs equivalent
EQY 14:38:02 [pe_eqy] DONE (PASS, rc=0)
```
30 s. **Without** `setattr keep` the same run fails: `Failed to prove equivalence of partition pe.prod_r`, `DONE (FAIL, rc=2)` — `opt_merge` merged `a_r` into `a_out`, the gold register `a_r` has no counterpart in the gate design, and induction starts from an arbitrary value. This is exactly why commercial LEC needs register matching (key points) and has to know about flip-flop merging/duplication. Comparison against the SKY130 cell-level netlist (needs cell models) — not verified locally: out of scope for this smoke test.

## 4. RTL→GDS flow: trial runs of `systolic_array` (environment B)

Config `smoke/flow_2x2/config.yaml`:
```yaml
# Trial RTL->GDS run: systolic_array 2x2, SKY130, LibreLane.
# RTL is read from the sibling gemm_kernelgen repo (read-only).
DESIGN_NAME: systolic_array
VERILOG_FILES:
  - dir::../../../gemm_kernelgen/rtl/pe.sv
  - dir::../../../gemm_kernelgen/rtl/systolic_array.sv
USE_SLANG: true              # SV frontend sv-elab (ex yosys-slang)
SYNTH_PARAMETERS:
  - ARRAY_M=2
  - ARRAY_N=2
CLOCK_PORT: clk
CLOCK_PERIOD: 10             # ns (100 MHz), conservative for a trial
FP_CORE_UTIL: 40
```
Run (2×2; other sizes via a `-c` override with a comma-separated list: `-c 'SYNTH_PARAMETERS=ARRAY_M=4,ARRAY_N=4'`; a JSON list `["…","…"]` in `-c` does **not** work — slang receives `'["ARRAY_M=4"'` and fails):
```sh
D=$P/asic_rtl2gds/smoke/flow_2x2
cd "$D"
time docker run --rm -i -v "$P:$P" -v "$HOME/.ciel:$HOME/.ciel" -e PDK_ROOT="$HOME/.ciel" -w "$D" \
  ghcr.io/librelane/librelane:3.0.17 librelane --pdk sky130A --run-tag t1_2x2 config.yaml > flow_2x2.log 2>&1
```
**4×4 (the size used in `flow/`)** — same config, `-c` goes before `config.yaml`, its own run tag:
```sh
D=$P/asic_rtl2gds/smoke/flow_2x2
cd "$D"
rm -rf runs/t1_4x4          # if the tag is taken (it was: the first attempt with a JSON list in -c failed)
docker run --rm -i -v "$P:$P" -v "$HOME/.ciel:$HOME/.ciel" -e PDK_ROOT="$HOME/.ciel" -w "$D" \
  ghcr.io/librelane/librelane:3.0.17 librelane --pdk sky130A --run-tag t1_4x4 \
  -c 'SYNTH_PARAMETERS=ARRAY_M=4,ARRAY_N=4' config.yaml > flow_4x4.log 2>&1
```
Exactly this was run, with two differences in notation: the paths were literal absolute paths, and the wall time was measured with a wrapper `START=$(date +%s); …; echo "rc=$? WALL=$(( $(date +%s) - START ))s"` instead of `time` → `rc=0 WALL=670s`. Check that the parameter got through: `runs/t1_4x4/resolved.json` has `"SYNTH_PARAMETERS": ["ARRAY_M=4", "ARRAY_N=4"]`. 8×8 was run the same way with `--run-tag t1_8x8 -c 'SYNTH_PARAMETERS=ARRAY_M=8,ARRAY_N=8'` (no `rm -rf`).

Results (`runs/<tag>/final/metrics.json`; 76 Classic-flow steps, `final/gds/systolic_array.gds`):

| Metric | 2×2 | 4×4 | 8×8 |
|---|---|---|---|
| Wall time | **179 s (3.0 min)**, rc=0 | **670 s (11.2 min)**, rc=0 | **3257 s (54.3 min)**, rc=2 — see below |
| Standard cells / cell area, µm² | 4 576 / 38 220 | 18 268 / 152 125 | 73 229 / 605 099 |
| Die, µm | 287.7 × 298.4 | 565.0 × 575.7 | 1120.4 × 1131.1 |
| Setup WS: tt_025C_1v80 / ss_100C_1v60 / ff_n40C_1v95, ns | +2.84 / −1.52 / +4.58 | +2.82 / −1.73 / +4.54 | +1.89 / −3.44 / +3.97 |
| Hold WS (worst corner), ns | +0.106 | +0.109 | **−0.835** (ss) |
| Setup / hold violations (all corners) | 188 / 0 | 1 317 / 0 | 8 505 / 190 |
| Max slew / max cap / max fanout violations | 680 / 0 / 2 | 2 217 / 2 / 2 | 14 062 / 21 / 19 |
| DRC Magic / KLayout, LVS, antenna | 0 / 0, 0, 0 | 0 / 0, 0, 0 | 0 / 0, 0, 0 |
| Power (STA estimate), mW | 3.39 | 13.6 | 54.1 |
| Longest steps | detailed routing 38 s, resizer post-CTS 31 s, KLayout DRC 19 s | resizer post-CTS 2:41, detailed routing 2:27, KLayout DRC 1:19, Magic DRC 1:02 | detailed routing 14:41, resizer post-CTS 9:54, Magic DRC 7:30, KLayout DRC 7:18 |

What the trial already shows:
- GDS is produced and DRC/LVS are clean, but **timing is closed only in the typical and fast corners**: in the slow corner (ss, 100 °C, 1.60 V) setup does not close at 100 MHz, and there are slew violations. This is an untuned trial config; the `flow/` project then either sizes the period for the ss corner or works on the fanout of `en`/`clear`/`rst_n` (they drive every flip-flop in the array). **Outcome (2026-11-03):** the `flow/` run `r0_10ns` reproduced the timing and area metrics of `t1_4x4` exactly; a 14 ns period improved ss from −1.93 to −0.96 ns but did not close it. Analysis — `README.md`.
- **8×8 did not reach `rc=0`**: the GDS was written (steps 57–58 streamout, DRC/LVS clean), but the `Checker.HoldViolations` step stopped the flow — `Hold violations found in the following corners: max_ss_100C_1v60, min_ss_100C_1v60, nom_ss_100C_1v60`, `LibreLane will now quit.` (rc=2). In 2×2/4×4 setup violations were only warnings and there were no hold violations. The `clock__skew__worst_hold` metric in 8×8 is −0.51 ns (1.1 × 1.1 mm die, untuned CTS); root cause not analysed.
- Runtime grows faster than the PE count: 4× PEs → 3.7× time (2×2→4×4), then 4× PEs → 4.9× (4×4→8×8). A single `docker stats` sample on 8×8 during detailed routing showed 3.4 GiB of the 7.65 GiB VM (not the peak over the run).

Warnings that are not flow errors (from the 2×2 log): `[RSZ-0020] found 2 floating nets`, `[DRT-0349] LEF58_ENCLOSURE with no CUTCLASS is not supported`, `'VSRC_LOC_FILES' was not given a value` (IR drop without power-source locations — fine for a block, not for a chip).

## 5. Pitfalls on this Mac (reproduced)

### 5.1. `docker pull` from the CLI hangs

`docker pull hello-world` and `docker pull ghcr.io/librelane/librelane:3.0.17` hung at `Using default tag: latest` with no network activity (`Docker.raw` did not grow); restarting Docker Desktop did not help. The network itself was fine: from an existing container, `wget https://ghcr.io/v2/` → `401 Unauthorized` (expected). The same request sent **directly to the Docker Engine API over the socket** goes through immediately:
```sh
curl -s --unix-socket ~/.docker/run/docker.sock -X POST \
  "http://localhost/v1.53/images/create?fromImage=hello-world&tag=latest"
# → {"status":"Status: Downloaded newer image for hello-world:latest"}
```
The cause is on the CLI client side (`~/.docker/config.json` has `"credsStore": "desktop"`; hypothesis: the credential helper hangs; not verified: the cause was not diagnosed and the config was not changed). The LibreLane image is public, so an anonymous pull through the API is enough. Once the image is local, neither LibreLane nor `docker run` pulls it again.

### 5.2. `librelane --dockerized` crashed Docker Desktop

The official path `python -m librelane --dockerized --smoke-test` mounts **all of `$HOME`**. On this Mac the run reached the RCX step (2 min 24 s) and died: `level=error msg="error waiting for container: unexpected EOF"`, after which `docker info` → `Docker Desktop is unable to start`; the backend log had `service fs failed: injecting event blocked for 60s`. After restarting Docker Desktop, the same smoke test through an explicit `docker run` mounting **only** `~/.ciel` passed in 54 s (§2.2), and all §3.3 and §4 runs mounting the parent folder + `~/.ciel` passed without failures. Conclusion: mount narrowly. What exactly overloads the Docker Desktop file service when all of `$HOME` is mounted was not investigated — one failure, one working alternative.

If Docker Desktop does crash: `osascript -e 'quit app "Docker Desktop"'`, then `open -a Docker` and wait for `docker info` (not verified locally: after the §5.2 crash Docker Desktop was restarted by hand; this command was not run).

### 5.3. Docker VM memory

The Docker Desktop VM defaults to 7.65 GiB here (the Mac has 32 GB; LibreLane recommends ≥16 GB host RAM). All three trial runs (2×2/4×4/8×8) fit into those 7.65 GiB (a single `docker stats` sample on 8×8 during detailed routing: 3.4 GiB). Docker Desktop resource settings were not changed.

## 6. Not verified locally

- Nix installation of LibreLane (officially recommended for macOS) — excluded by the install policy (no Nix).
- OpenROAD `dft`: verified outside this repo, in the author's companion lab — open scan insertion (scan replace + stitch) on one PE plus a scan test in Icarus. ATPG (pattern generation, fault coverage) was not run — there is no open ATPG in this stack.
- OpenROAD `upf` and gate-level simulation with SDF in Icarus: run in the author's companion labs, not in this repo.
- ORFS in Docker and SiliconCompiler — fallback options, not installed (LibreLane worked).
- Removing quarantine without sudo (`xattr -dr ...`) — not needed.
