#!/usr/bin/env python3
"""Attribute max-slew violations to the root net of the buffer tree they sit in.

    python3 slew_roots.py <run_dir> <corner>     # e.g. ../runs/r0_10ns max_ss_100C_1v60

Reads <run_dir>/final/nl/systolic_array.nl.v and the post-PnR STA checks.rpt of <corner>.
For every violating pin, walks back through buffer-like cells (buf/clkbuf/clkdlybuf/dlymetal/
dlygate) to the first non-buffer driver or top-level port, and counts violations per root.
Also prints the cell types the resizer used for buffer trees.
"""
import re, sys
from collections import Counter
from pathlib import Path

run, corner = Path(sys.argv[1]), sys.argv[2]
nl = (run / "final/nl/systolic_array.nl.v").read_text()
sta = next(run.glob("*-openroad-stapostpnr"))
checks = (sta / corner / "checks.rpt").read_text()

OUT = {"X", "Y", "Q", "Q_N", "HI", "LO", "COUT", "SUM", "GCLK"}
BUF = re.compile(r"__(buf|clkbuf|clkdlybuf\w*|dlymetal\w*|dlygate\w*|bufbuf)_\d+$")
inst = {}                      # name -> (cell, {pin: net})
drv = {}                       # net  -> instance driving it
for cell, name, body in re.findall(r"(sky130_fd_sc_hd__\w+)\s+(\S+)\s*\((.*?)\);", nl, re.S):
    pins = {p: n.strip() for p, n in re.findall(r"\.(\w+)\(([^()]*)\)", body)}
    inst[name] = (cell, pins)
    for p, n in pins.items():
        if p in OUT:
            drv[n] = name


def root(net, depth=0):
    d = drv.get(net)
    if d is None or depth > 50:
        return f"port/undriven:{net}"
    cell, pins = inst[d]
    if BUF.search(cell) and "A" in pins:
        return root(pins["A"], depth + 1)
    srcs = sorted({bufsrc(n) or "logic" for p, n in pins.items() if p not in OUT})
    return f"{d} ({cell.replace('sky130_fd_sc_hd__', '')}) -> net {net}; inputs from {srcs}"


def bufsrc(net, depth=0):
    """Top-level port reached from `net` through buffers only, else None."""
    d = drv.get(net)
    if d is None:
        return net
    cell, pins = inst[d]
    if BUF.search(cell) and "A" in pins and depth < 50:
        return bufsrc(pins["A"], depth + 1)
    return None


sec = checks[checks.find("max slew"):checks.find("max fanout")]
viol = re.findall(r"^(\S+)/(\w+)\s+[\d.]+\s+[\d.]+\s+-[\d.]+ \(VIOLATED\)", sec, re.M)
roots = Counter()
for i, pin in viol:
    if i not in inst:
        roots["(not found)"] += 1
        continue
    cell, pins = inst[i]
    n = pins.get(pin)
    roots[root(n) if pin not in OUT else root(pins.get("A", n)) if BUF.search(cell) else root(n)] += 1
print(f"# max-slew violating pins in {corner}: {len(viol)}; grouped by root driver of their buffer tree")
for r, c in roots.most_common(15):
    print(f"{c:6d}  {r}")
cat = Counter()
for r, c in roots.items():
    k = ("en" if "'en'" in r or r.endswith(":en") else "clear/rst_n" if "'clear'" in r or "'rst_n'" in r
         else "prod_r[15] (product sign bit)" if "prod_r[15]" in r
         else "operand regs a_h/b_v/a_r/b_r" if re.search(r"net \\(a_h|b_v|g_row\S*\.(a_r|b_r))\[", r)
         else "other")
    cat[k] += c
print("\n# by category: " + ", ".join(f"{k}: {v}" for k, v in cat.most_common()))
bufcells = Counter(c.replace("sky130_fd_sc_hd__", "") for n, (c, _) in inst.items()
                   if re.match(r"(fanout|input|output|load_slew|max_cap|wire|split|rebuffer)\d+", n))
print("\n# cell types of resizer-inserted buffers (instances named fanout*/input*/output*/load_slew*/max_cap*/wire*)")
for c, k in bufcells.most_common(12):
    print(f"{k:6d}  {c}")
