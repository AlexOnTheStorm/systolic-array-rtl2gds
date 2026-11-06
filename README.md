# systolic_array 4×4 — open-source RTL-to-GDS on SKY130

My INT8 systolic array (16 MAC processing elements, from
[`systolic-gemm-kernelgen`](https://github.com/AlexOnTheStorm/systolic-gemm-kernelgen); RTL written with an AI assistant — see Authorship) taken through the open-source LibreLane flow to a
DRC/LVS-clean GDS on the SkyWater SKY130 PDK, with per-corner timing, area and a power estimate.

**This is not a tape-out.** Nothing was fabricated or sent to a shuttle. It is a learning exercise
on an open PDK with open tools: it shows that I can drive a full RTL→GDS flow and read its reports,
not that the block is production-ready. Timing in the slow corner is **not** closed (see below).

## Result (run `r1_14ns`, tuned)

LibreLane 3.0.17 Classic flow, SKY130A `sky130_fd_sc_hd`, clock period 14 ns (≈71.4 MHz),
`FP_CORE_UTIL` 40 %. All numbers are copied from [`reports/r1_14ns/summary.md`](reports/r1_14ns/summary.md).

| Metric | Value |
|---|---|
| Wall time (Apple Silicon Mac, Docker VM 10 CPU / 7.65 GiB) | 520 s, rc=0 |
| Die / core area | 564.97 × 575.69 µm = 0.325 mm² / 0.306 mm² |
| Standard cells incl. tap cells, excl. fill | 18 243 cells, 151 788 µm², utilization 49.6 % |
| Flip-flops | 1 024 (`dfxtp_2`), 21 781 µm² (14 % of cell area) |
| Timing-repair buffers / hold buffers | 2 056 cells, 20 322 µm² / 456 hold buffers |
| Setup worst slack: tt / ss / ff (worst of min/nom/max RC) | **+4.695 / −0.962 / +6.894 ns** |
| Setup TNS, violating endpoints (ss) | −26.917 ns and 44 endpoints in the worst corner (max_ss), 23 of them reg-to-reg (123 summed over the three ss RC corners, not unique) |
| Hold worst slack: tt / ss / ff | +0.323 / +0.885 / +0.108 ns, 0 violations in all 9 corners |
| Power estimate, nom tt (no activity file) | 8.254 mW (internal 5.619, switching 2.635, leakage < 0.001) |
| Magic DRC / KLayout DRC / LVS / antenna / XOR | 0 / 0 / 0 errors / 0 violating nets (13 diodes) / 0 |
| Max slew / max cap / max fanout violations (max_ss) | 4 205 / 3 / 2 (non-fatal by LibreLane default policy) |

Layout render (LibreLane `klayout-render` step, all layers, headless):
[`reports/r1_14ns/layout.png`](reports/r1_14ns/layout.png).

### What is and is not closed

- **Closed:** setup and hold in the typical (tt_025C_1v80) and fast (ff_n40C_1v95) corners with large
  margins; hold in all nine corners (3 PVT × 3 RC); DRC, LVS, antenna, XOR clean.
- **Not closed:** setup in the slow corner ss_100C_1v60 (all three RC corners), worst −0.962 ns.
  The worst path starts at the input port `en` (2.8 ns external input delay + a buffer tree;
  `en` has a fanout of 1 216 before buffering); the worst register-to-register path is the INT8 multiplier
  (`a` operand register → `prod_r[15]`), −0.893 ns.
- `rc=0` does **not** mean "timing met everywhere": with the default checker settings of this LibreLane/PDK
  combination (`TIMING_VIOLATION_CORNERS: ["*tt*"]` in `resolved.json`) setup violations are fatal only in tt corners; hold is
  fatal in all corners; slew/cap are warnings ([`reports/r1_14ns/path_notes.txt`](reports/r1_14ns/path_notes.txt)).

## Tuning cycle (one iteration, documented)

| | `r0_10ns` (baseline) | `r1_14ns` (tuned) |
|---|---|---|
| Clock period | 10 ns | 14 ns |
| Wall time | 677 s | 520 s |
| Setup WS tt / ss / ff, ns | +2.715 / −1.929 / +4.470 | +4.695 / −0.962 / +6.894 |
| Setup violating endpoints in max_ss (reg-to-reg) | 524 (39) | 44 (23) |
| Worst ss path | `en` port → buffer tree, −1.929 | `en` port → buffer tree, −0.962 |
| Worst ss reg-to-reg | multiplier, −0.667 | multiplier, −0.893 |
| Post-CTS resizer: setup endpoints found / cells upsized | 220 / 1 448 | 11 / 29 |
| Std-cell area | 152 125 µm² | 151 788 µm² |
| Power estimate nom tt | 11.556 mW | 8.254 mW |

1. **Read the failing path** (`reports/r0_10ns/worst_setup__max_ss_100C_1v60.rpt`): input `en`
   with 2.0 ns external delay, then ≈10.8 ns from the port to the last buffer of the tree (mostly `clkdlybuf4s25_1` cells that
   `repair_design` chose as fanout buffers), then the D-input mux. Reg-to-reg in ss was −0.667 ns.
   From these numbers the `en` path needed ≈12.4 ns at fixed netlist (IO delay is 20 % of the period).
2. **Change:** clock period 10 → 14 ns (≈1.5 ns margin over the estimate). IO-delay budget,
   uncertainty and all other constraints were left at LibreLane defaults on purpose — shrinking the
   assumed external delay would make the number look better without making the block faster.
3. **Outcome:** ss improved from −1.93 to −0.96 ns but did not close. The synthesis netlist is
   byte-identical in both runs (`reports/r1_14ns/synth_notes.txt`), so every difference comes from
   place-and-route. With a relaxed target the post-CTS resizer saw only 11 violating endpoints (its
   placement-based parasitic estimate), resized 29 cells instead of 1 448, and stopped at +0.037 ns
   (target margin `PL_RESIZER_SETUP_SLACK_MARGIN` = 0.05 ns, hence warning RSZ-0062); after routing
   and RC extraction the slow corner lost about 1 ns again. Same-path evidence
   ([`reports/tuning_path_evidence.txt`](reports/tuning_path_evidence.txt)): the worst path is
   `en` → `_21926_/D` in both runs, and its port-to-D delay grew 11.53 → 13.78 ns. In r0 the resizer
   had swapped en-tree buffers to faster cells (`fanout1425`: `clkbuf_4`, 0.93 ns); in r1 it left the
   `repair_design` delay cells in place (`clkdlybuf4s25_1`, 2.01 ns). So the 12.4 ns forecast failed
   because it was computed on r0's already-optimized netlist. The worst reg-to-reg slack also got
   worse (−0.667 → −0.893 ns, on a different endpoint; data-path delay 10.1 vs 14.3 ns). Lesson:
   the slack an open flow reports is a property of the optimization run, not a fixed property of the RTL.

Not tried (next iterations): post-global-route resizer (`RUN_POST_GRT_RESIZER_TIMING`), a larger
`PL_RESIZER_SETUP_SLACK_MARGIN`, registering `en`/`clear` per row in a wrapper, excluding delay
cells from fanout buffering. None of these is claimed to work until run.

## Reproduce

Prerequisites (tested on macOS Apple Silicon with Docker Desktop; full install log with real
output in [`env.md`](env.md)):

```sh
docker pull ghcr.io/librelane/librelane:3.0.17           # arm64 image, ~7.5 GB (see note 1)
python3.12 -m venv ~/tools/librelane-venv
~/tools/librelane-venv/bin/python -m pip install librelane==3.0.17     # provides `ciel`
~/tools/librelane-venv/bin/ciel enable --pdk-family sky130 8afc8346a57fe1ab7934ba5a6056ea8b43078e71
                                                         # SKY130A pinned by LibreLane 3.0.17 -> ~/.ciel
```

Required layout: this folder and the RTL repo must be **siblings**, because `run_flow.sh` resolves
`../gemm_kernelgen/rtl` (clone [systolic-gemm-kernelgen](https://github.com/AlexOnTheStorm/systolic-gemm-kernelgen) into a folder named `gemm_kernelgen`):

```text
<parent>/systolic-array-rtl2gds/   (this repo; the folder name does not matter)
<parent>/gemm_kernelgen/rtl/pe.sv, systolic_array.sv
```

Both folders and `~/.ciel` must be inside Docker Desktop's file-sharing paths (by default `/Users`).

Note 1: on the author's Mac the `docker pull` CLI hung with no network activity; pulling through
the Docker Engine API socket worked:
`curl -s --unix-socket ~/.docker/run/docker.sock -X POST "http://localhost/v1.53/images/create?fromImage=ghcr.io/librelane/librelane&tag=3.0.17"`
(details in `env.md` §5.1).

```sh
cd systolic-array-rtl2gds/flow
./run_flow.sh r1_14ns                       # tuned run, ~9 min; writes runs/r1_14ns/ and r1_14ns.log
./run_flow.sh r0_10ns CLOCK_PERIOD=10       # baseline, ~11 min
python3 extract_reports.py r1_14ns          # -> ../reports/r1_14ns/
python3 tools/slew_roots.py runs/r1_14ns max_ss_100C_1v60   # which nets the slew violations belong to
```

`run_flow.sh` uses a plain `docker run` with narrow bind mounts (this folder read-write, the gemm
RTL read-only, `~/.ciel`), not `librelane --dockerized`, which mounts all of `$HOME` and crashed
Docker Desktop on this machine. A repeat run reproduced the same metrics once: the baseline here matched the
timing and area metrics of the earlier smoke run (`env.md` §4) exactly. Determinism in general is not claimed.

Power-activity check (shows the estimate equals an explicit input activity of 0.1 toggles/cycle,
duty 0.5): the `docker run … sta` command is in the header of `flow/tools/power_default_check.tcl`; result in [`reports/r1_14ns/power_activity_check.txt`](reports/r1_14ns/power_activity_check.txt).

## Files

| Path | What |
|---|---|
| `flow/config.yaml` | LibreLane config (design, RTL files, `ARRAY_M/N=4`, period, core utilization) |
| `flow/run_flow.sh` | Docker invocation, wall-time logging to `reports/walltime.txt` |
| `flow/extract_reports.py` | Copies small text extracts out of a run directory |
| `flow/tools/` | Slew-violation attribution script, OpenSTA power-activity check |
| `reports/<run>/summary.md` | Area, per-corner timing, power, DRC/LVS/antenna, run info |
| `reports/<run>/sta_summary.rpt` | LibreLane post-route STA summary table (9 corners) |
| `reports/<run>/worst_*.rpt` | Worst setup / reg-to-reg / hold paths, full OpenSTA text |
| `reports/tuning_path_evidence.txt` | Same-path comparison r0 vs r1 (en tree buffers, delays) |
| `reports/<run>/path_notes.txt` | Which registers those paths connect; resizer log lines; checker policy |
| `reports/r1_14ns/synth_notes.txt` | Synthesis facts: excluded `_1` cells, drive strengths, r0/r1 netlist identity |
| `reports/r1_14ns/power_activity_check.txt` | Power with default vs explicit switching activity |
| `reports/walltime.txt` | Wall time and exit code of every run |
| `reports/<run>/slew_roots__*.txt` | Max-slew violations grouped by the net their buffer tree serves |
| `reports/<run>/step_runtimes.txt` | Per-step runtime |
| `reports/<run>/layout.png` | Layout render |

Run directories (`flow/runs/`, GDS, DEF, ODB, SPEF, logs; hundreds of MB) are gitignored.

## Limitations (read before quoting any number)

- **Open PDK, open tools.** SKY130 is a 130 nm node; OpenROAD/OpenSTA/Magic/KLayout/Netgen are not
  the signoff tools a foundry flow would use. Only a flat ±5 % OCV derate (`TIME_DERATING_CONSTRAINT: 5`
  in `resolved.json`); no AOCV/POCV, no SI/crosstalk analysis.
- **Block, not chip.** No pads, no I/O ring, no package; IO constraints are LibreLane defaults
  (input/output delay 20 % of the period, `inv_2` driver, 33 fF load). IR-drop numbers are
  meaningless here (no power-source locations were given).
- **Power is an estimate without real activity.** No VCD/SAIF; OpenSTA propagates a default
  input activity (0.1 toggles per cycle, duty 0.5). Setting it to 0.5 changes the total from
  8.25 to 18.0 mW. Use it only for relative comparisons.
- **Slow-corner setup is not met** at 14 ns (−0.962 ns). Max-slew violations remain (non-fatal by
  default policy). The block is not signoff-clean.
- **No DFT** (no scan insertion), gate-level simulation of the routed netlist only in the tt corner
  (Icarus, no timing checks; textbook lab, not in this folder), no formal equivalence between RTL
  and the routed netlist in this run.
- **Authorship.** The `gemm_kernelgen` RTL was written with an AI assistant (disclosed in that
  repo). The flow scripts and this README were also prepared with an AI assistant; the runs were
  executed locally and every number comes from the files in `reports/`.

Versions change: LibreLane, OpenROAD and PDK revisions move quickly; check
[LibreLane releases](https://github.com/librelane/librelane/releases) and the
[SKY130 PDK docs](https://skywater-pdk.readthedocs.io/) before reusing the commands.
