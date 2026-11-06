#!/usr/bin/env python3
"""Extract small, git-friendly text reports from a LibreLane run directory.

    python3 extract_reports.py <run_tag>

Reads  flow/runs/<run_tag>/ (gitignored, hundreds of MB) and flow/<run_tag>.log,
writes ../reports/<run_tag>/ : summary.md, sta_summary.rpt, worst paths, power,
step runtimes, a resolved-config excerpt, flow-log excerpt and the layout PNG.
Every number quoted in README.md must come from these files.
"""
import json, re, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
tag = sys.argv[1]
run = HERE / "runs" / tag
out = HERE.parent / "reports" / tag
out.mkdir(parents=True, exist_ok=True)

m = json.loads((run / "final/metrics.json").read_text())
cfg = json.loads((run / "resolved.json").read_text())
steps = sorted(p for p in run.iterdir() if p.is_dir() and re.match(r"\d+-", p.name))
step = lambda suffix: next(p for p in steps if p.name.endswith(suffix))
sta_post = step("openroad-stapostpnr")
CORNERS = cfg["STA_CORNERS"]


def g(key, default="n/a"):
    return m.get(key, default)


def f(x, nd=3):
    return f"{x:.{nd}f}" if isinstance(x, (int, float)) else str(x)


def runtime_s(p):
    t = (p / "runtime.txt").read_text().strip()          # HH:MM:SS.mmm
    h, mi, s = t.split(":")
    return int(h) * 3600 + int(mi) * 60 + float(s)


wall = [l.strip() for l in (HERE.parent / "reports/walltime.txt").read_text().splitlines()
        if f"tag={tag} " in l] if (HERE.parent / "reports/walltime.txt").exists() else []

L = []
L.append(f"# LibreLane run `{tag}` — extracted metrics\n")
L.append("Source: `flow/runs/%s/final/metrics.json`, `resolved.json`, step `%s` (not in git; "
         "regenerate with `flow/run_flow.sh`). LibreLane 3.0.17, SKY130A `sky130_fd_sc_hd`.\n" % (tag, sta_post.name))
L.append("## Run\n")
L.append(f"- wall time: {wall[-1] if wall else 'n/a'}")
L.append(f"- sum of step runtimes: {sum(runtime_s(p) for p in steps if (p / 'runtime.txt').exists()):.0f} s, steps: {len(steps)}")
for k in ("DESIGN_NAME", "SYNTH_PARAMETERS", "CLOCK_PERIOD", "FP_CORE_UTIL", "IO_DELAY_CONSTRAINT",
          "CLOCK_UNCERTAINTY_CONSTRAINT", "SYNTH_DRIVING_CELL", "OUTPUT_CAP_LOAD",
          "MAX_TRANSITION_CONSTRAINT", "MAX_FANOUT_CONSTRAINT", "DEFAULT_CORNER"):
    L.append(f"- `{k}` = {cfg.get(k)}")

L.append("\n## Area\n")
syn = (step("yosys-synthesis") / "reports/stat.rpt").read_text()
syn_area = re.search(r"Chip area for module .*?: ([\d.]+)", syn)
syn_seq = re.search(r"used for sequential elements: ([\d.]+) \(([\d.]+)%\)", syn)
L.append("| metric | value |\n|---|---|")
L.append(f"| synthesis cell area (Yosys stat, before PnR), um^2 | {syn_area.group(1) if syn_area else 'n/a'} |")
if syn_seq:
    L.append(f"| of which sequential (synthesis), um^2 | {syn_seq.group(1)} ({syn_seq.group(2)} %) |")
L.append(f"| die bbox, um | {g('design__die__bbox')} |")
L.append(f"| die area, um^2 | {g('design__die__area')} |")
L.append(f"| core area, um^2 | {g('design__core__area')} |")
L.append(f"| std cells (excl. fill/decap), count / area um^2 | {g('design__instance__count__stdcell')} / {g('design__instance__area__stdcell')} |")
L.append(f"| utilization (std-cell area / core area) | {f(g('design__instance__utilization'))} |")
for cls in ("sequential_cell", "multi_input_combinational_cell", "inverter", "timing_repair_buffer",
            "clock_buffer", "clock_inverter", "tap_cell", "antenna_cell", "fill_cell"):
    c, a = g(f"design__instance__count__class:{cls}"), g(f"design__instance__area__class:{cls}")
    L.append(f"| class {cls}: count / area um^2 | {c} / {a} |")
L.append(f"| setup buffers / hold buffers inserted | {g('design__instance__count__setup_buffer')} / {g('design__instance__count__hold_buffer')} |")
L.append(f"| routed wirelength, um | {g('route__wirelength')} |")

L.append("\n## Timing per corner (post-route STA with extracted parasitics)\n")
L.append("Slack in ns; WS = worst slack (negative = violated); r2r = register-to-register only.\n")
L.append("| corner | setup WS | setup TNS | setup vio | r2r setup WS | hold WS | hold TNS | hold vio | max slew vio | max cap vio | max fanout vio |")
L.append("|---|---|---|---|---|---|---|---|---|---|---|")
for c in CORNERS:
    k = lambda n: g(f"{n}__corner:{c}")
    L.append(f"| {c} | {f(k('timing__setup__ws'))} | {f(k('timing__setup__tns'))} | {k('timing__setup_vio__count')} | "
             f"{f(k('timing__setup_r2r__ws'))} | {f(k('timing__hold__ws'))} | {f(k('timing__hold__tns'))} | "
             f"{k('timing__hold_vio__count')} | {k('design__max_slew_violation__count')} | "
             f"{k('design__max_cap_violation__count')} | {k('design__max_fanout_violation__count')} |")
L.append(f"\nLibreLane overall metrics (violation counts are SUMMED over corners, not unique endpoints): setup vio {g('timing__setup_vio__count')} (r2r {g('timing__setup_r2r_vio__count')}), "
         f"hold vio {g('timing__hold_vio__count')} (r2r {g('timing__hold_r2r_vio__count')}); "
         f"clock skew worst setup/hold {f(g('clock__skew__worst_setup'))} / {f(g('clock__skew__worst_hold'))} ns.")

L.append("\n## Power estimate per corner (OpenSTA `report_power`, no VCD/SAIF, default activity)\n")
L.append("| corner | internal, mW | switching, mW | leakage, mW | total, mW |\n|---|---|---|---|---|")
for c in CORNERS:
    t = re.search(r"^Total\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)", (sta_post / c / "power.rpt").read_text(), re.M)
    if t:
        L.append(f"| {c} | " + " | ".join(f"{float(v)*1e3:.3f}" for v in t.groups()) + " |")

L.append("\n## Signoff-style checks\n")
L.append("| check | value |\n|---|---|")
for k in ("magic__drc_error__count", "klayout__drc_error__count", "magic__illegal_overlap__count",
          "design__lvs_error__count", "design__lvs_unmatched_device__count", "design__lvs_unmatched_net__count",
          "design__lvs_unmatched_pin__count", "design__xor_difference__count", "route__drc_errors",
          "antenna__violating__nets", "antenna__violating__pins", "route__antenna_violation__count",
          "antenna_diodes_count", "design__disconnected_pin__count", "design__power_grid_violation__count",
          "ir__drop__worst", "ir__drop__avg", "design__lint_error__count", "design__lint_warning__count",
          "design__inferred_latch__count", "flow__errors__count", "flow__warnings__count"):
    L.append(f"| `{k}` | {g(k)} |")
(out / "summary.md").write_text("\n".join(L) + "\n")

# --- STA summary table + worst paths -------------------------------------------------------
shutil.copy(sta_post / "summary.rpt", out / "sta_summary.rpt")


def paths(rpt):
    """Split an OpenSTA report_checks file into (slack, startpoint, text) per path."""
    txt = rpt.read_text()
    res = []
    for chunk in re.split(r"\n(?=Startpoint: )", txt):
        if not chunk.startswith("Startpoint:"):
            continue
        sl = re.search(r"(-?[\d.]+)\s+slack \((?:MET|VIOLATED)\)", chunk)
        if sl:
            end = chunk.find("slack (")
            res.append((float(sl.group(1)), chunk.splitlines()[0], chunk[: chunk.find("\n", end)]))
    return res


def worst(kind, metric, filt=None):
    c = min(CORNERS, key=lambda c: g(f"{metric}__corner:{c}", 1e9))
    ps = paths(sta_post / c / ("max.rpt" if kind == "setup" else "min.rpt"))
    if filt:
        ps = [p for p in ps if filt(p)]
    return c, (min(ps, key=lambda p: p[0]) if ps else None)


is_r2r = lambda p: "input port" not in p[1] and "(input" not in p[2].split("\n")[0]
for name, kind, metric, filt in (("worst_setup", "setup", "timing__setup__ws", None),
                                 ("worst_setup_r2r", "setup", "timing__setup_r2r__ws", is_r2r),
                                 ("worst_hold", "hold", "timing__hold__ws", None)):
    c, p = worst(kind, metric, filt)
    if p:
        (out / f"{name}__{c}.rpt").write_text(f"# {kind} path, corner {c}, from {sta_post.name}/{c}/"
                                             f"{'max' if kind == 'setup' else 'min'}.rpt\n" + p[2] + "\n")

shutil.copy(sta_post / "nom_tt_025C_1v80" / "power.rpt", out / "power_nom_tt_025C_1v80.rpt")

# --- step runtimes ----------------------------------------------------------------------
rt = [(runtime_s(p), p.name) for p in steps if (p / "runtime.txt").exists()]
(out / "step_runtimes.txt").write_text(
    f"# per-step runtime, s (sorted), run {tag}; total {sum(r for r, _ in rt):.0f} s\n"
    + "\n".join(f"{r:8.1f}  {n}" for r, n in sorted(rt, reverse=True)) + "\n")

# --- flow log excerpt (warnings/errors/checkers) -----------------------------------------
log = HERE / f"{tag}.log"
if log.exists():
    keep = [l.rstrip() for l in log.read_text(errors="replace").splitlines()
            if re.search(r"WARNING|ERROR|Checker|violation|Flow complete|quit|^\s+\* \w+_\w+C_", l)]
    (out / "flow_log_excerpt.txt").write_text(f"# grep WARNING|ERROR|Checker|violation from flow/{tag}.log\n"
                                              + "\n".join(keep[:200]) + "\n")

png = run / "final/render/systolic_array.png"
if png.exists():
    shutil.copy(png, out / "layout.png")
print(f"wrote {out}")
