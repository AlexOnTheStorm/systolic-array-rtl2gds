# LibreLane run `r0_10ns` — extracted metrics

Source: `flow/runs/r0_10ns/final/metrics.json`, `resolved.json`, step `55-openroad-stapostpnr` (not in git; regenerate with `flow/run_flow.sh`). LibreLane 3.0.17, SKY130A `sky130_fd_sc_hd`.

## Run

- wall time: 2026-11-03 21:16 tag=r0_10ns overrides=[CLOCK_PERIOD=10] rc=0 wall_s=677
- sum of step runtimes: 675 s, steps: 76
- `DESIGN_NAME` = systolic_array
- `SYNTH_PARAMETERS` = ['ARRAY_M=4', 'ARRAY_N=4']
- `CLOCK_PERIOD` = 10
- `FP_CORE_UTIL` = 40
- `IO_DELAY_CONSTRAINT` = 20
- `CLOCK_UNCERTAINTY_CONSTRAINT` = 0.25
- `SYNTH_DRIVING_CELL` = sky130_fd_sc_hd__inv_2/Y
- `OUTPUT_CAP_LOAD` = 33.442
- `MAX_TRANSITION_CONSTRAINT` = 0.75
- `MAX_FANOUT_CONSTRAINT` = 10
- `DEFAULT_CORNER` = nom_tt_025C_1v80

## Area

| metric | value |
|---|---|
| synthesis cell area (Yosys stat, before PnR), um^2 | 122735.212800 |
| of which sequential (synthesis), um^2 | 21780.889600 (17.75 %) |
| die bbox, um | 0.0 0.0 564.97 575.69 |
| die area, um^2 | 325248 |
| core area, um^2 | 305808 |
| std cells (excl. fill/decap), count / area um^2 | 18268 / 152125 |
| utilization (std-cell area / core area) | 0.497 |
| class sequential_cell: count / area um^2 | 1024 / 21848.5 |
| class multi_input_combinational_cell: count / area um^2 | 10428 / 101217 |
| class inverter: count / area um^2 | 175 / 656.88 |
| class timing_repair_buffer: count / area um^2 | 2082 / 19655.1 |
| class clock_buffer: count / area um^2 | 211 / 2882.76 |
| class clock_inverter: count / area um^2 | 31 / 447.93 |
| class tap_cell: count / area um^2 | 4305 / 5386.42 |
| class antenna_cell: count / area um^2 | 12 / 30.0288 |
| class fill_cell: count / area um^2 | 44842 / 153684 |
| setup buffers / hold buffers inserted | 113 / 469 |
| routed wirelength, um | 341338 |

## Timing per corner (post-route STA with extracted parasitics)

Slack in ns; WS = worst slack (negative = violated); r2r = register-to-register only.

| corner | setup WS | setup TNS | setup vio | r2r setup WS | hold WS | hold TNS | hold vio | max slew vio | max cap vio | max fanout vio |
|---|---|---|---|---|---|---|---|---|---|---|
| nom_tt_025C_1v80 | 2.820 | 0.000 | 0 | 4.509 | 0.329 | 0.000 | 0 | 53 | 0 | 2 |
| nom_ss_100C_1v60 | -1.727 | -274.694 | 452 | -0.539 | 0.517 | 0.000 | 0 | 1602 | 1 | 2 |
| nom_ff_n40C_1v95 | 4.541 | 0.000 | 0 | inf | 0.111 | 0.000 | 0 | 0 | 0 | 2 |
| min_tt_025C_1v80 | 2.981 | 0.000 | 0 | 4.548 | 0.325 | 0.000 | 0 | 25 | 0 | 2 |
| min_ss_100C_1v60 | -1.421 | -177.261 | 341 | -0.414 | 0.604 | 0.000 | 0 | 1162 | 0 | 2 |
| min_ff_n40C_1v95 | 4.646 | 0.000 | 0 | inf | 0.109 | 0.000 | 0 | 0 | 0 | 2 |
| max_tt_025C_1v80 | 2.715 | 0.000 | 0 | 4.468 | 0.335 | 0.000 | 0 | 61 | 0 | 2 |
| max_ss_100C_1v60 | -1.929 | -346.696 | 524 | -0.667 | 0.414 | 0.000 | 0 | 2217 | 2 | 2 |
| max_ff_n40C_1v95 | 4.470 | 0.000 | 0 | inf | 0.113 | 0.000 | 0 | 8 | 0 | 2 |

LibreLane overall metrics (violation counts are SUMMED over corners, not unique endpoints): setup vio 1317 (r2r 118), hold vio 0 (r2r 0); clock skew worst setup/hold 0.315 / -0.404 ns.

## Power estimate per corner (OpenSTA `report_power`, no VCD/SAIF, default activity)

| corner | internal, mW | switching, mW | leakage, mW | total, mW |
|---|---|---|---|---|
| nom_tt_025C_1v80 | 7.858 | 3.698 | 0.000 | 11.556 |
| nom_ss_100C_1v60 | 6.240 | 2.873 | 0.082 | 9.195 |
| nom_ff_n40C_1v95 | 9.049 | 4.386 | 0.000 | 13.435 |
| min_tt_025C_1v80 | 7.858 | 3.557 | 0.000 | 11.415 |
| min_ss_100C_1v60 | 6.239 | 2.762 | 0.082 | 9.084 |
| min_ff_n40C_1v95 | 9.048 | 4.221 | 0.000 | 13.269 |
| max_tt_025C_1v80 | 7.859 | 3.843 | 0.000 | 11.702 |
| max_ss_100C_1v60 | 6.240 | 2.988 | 0.082 | 9.311 |
| max_ff_n40C_1v95 | 9.049 | 4.556 | 0.000 | 13.606 |

## Signoff-style checks

| check | value |
|---|---|
| `magic__drc_error__count` | 0 |
| `klayout__drc_error__count` | 0 |
| `magic__illegal_overlap__count` | 0 |
| `design__lvs_error__count` | 0 |
| `design__lvs_unmatched_device__count` | 0 |
| `design__lvs_unmatched_net__count` | 0 |
| `design__lvs_unmatched_pin__count` | 0 |
| `design__xor_difference__count` | 0 |
| `route__drc_errors` | 0 |
| `antenna__violating__nets` | 0 |
| `antenna__violating__pins` | 0 |
| `route__antenna_violation__count` | 0 |
| `antenna_diodes_count` | 12 |
| `design__disconnected_pin__count` | 0 |
| `design__power_grid_violation__count` | 0 |
| `ir__drop__worst` | 0.000468 |
| `ir__drop__avg` | 9.03e-05 |
| `design__lint_error__count` | 0 |
| `design__lint_warning__count` | 446 |
| `design__inferred_latch__count` | 0 |
| `flow__errors__count` | 0 |
| `flow__warnings__count` | 1 |
