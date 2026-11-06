# LibreLane run `r1_14ns` — extracted metrics

Source: `flow/runs/r1_14ns/final/metrics.json`, `resolved.json`, step `55-openroad-stapostpnr` (not in git; regenerate with `flow/run_flow.sh`). LibreLane 3.0.17, SKY130A `sky130_fd_sc_hd`.

## Run

- wall time: 2026-11-03 21:25 tag=r1_14ns overrides=[] rc=0 wall_s=520
- sum of step runtimes: 518 s, steps: 76
- `DESIGN_NAME` = systolic_array
- `SYNTH_PARAMETERS` = ['ARRAY_M=4', 'ARRAY_N=4']
- `CLOCK_PERIOD` = 14
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
| std cells (excl. fill/decap), count / area um^2 | 18243 / 151788 |
| utilization (std-cell area / core area) | 0.496 |
| class sequential_cell: count / area um^2 | 1024 / 21780.9 |
| class multi_input_combinational_cell: count / area um^2 | 10428 / 100279 |
| class inverter: count / area um^2 | 175 / 656.88 |
| class timing_repair_buffer: count / area um^2 | 2056 / 20322 |
| class clock_buffer: count / area um^2 | 211 / 2882.76 |
| class clock_inverter: count / area um^2 | 31 / 447.93 |
| class tap_cell: count / area um^2 | 4305 / 5386.42 |
| class antenna_cell: count / area um^2 | 13 / 32.5312 |
| class fill_cell: count / area um^2 | 44878 / 154020 |
| setup buffers / hold buffers inserted | 0 / 456 |
| routed wirelength, um | 339066 |

## Timing per corner (post-route STA with extracted parasitics)

Slack in ns; WS = worst slack (negative = violated); r2r = register-to-register only.

| corner | setup WS | setup TNS | setup vio | r2r setup WS | hold WS | hold TNS | hold vio | max slew vio | max cap vio | max fanout vio |
|---|---|---|---|---|---|---|---|---|---|---|
| nom_tt_025C_1v80 | 4.820 | 0.000 | 0 | 6.783 | 0.327 | 0.000 | 0 | 50 | 0 | 2 |
| nom_ss_100C_1v60 | -0.727 | -19.119 | 42 | -0.722 | 0.888 | 0.000 | 0 | 3369 | 2 | 2 |
| nom_ff_n40C_1v95 | 6.970 | 0.000 | 0 | inf | 0.110 | 0.000 | 0 | 7 | 0 | 2 |
| min_tt_025C_1v80 | 5.027 | 0.000 | 0 | 6.881 | 0.323 | 0.000 | 0 | 33 | 0 | 2 |
| min_ss_100C_1v60 | -0.550 | -8.867 | 37 | -0.550 | 0.885 | 0.000 | 0 | 2502 | 1 | 2 |
| min_ff_n40C_1v95 | 7.103 | 0.000 | 0 | inf | 0.108 | 0.000 | 0 | 0 | 0 | 2 |
| max_tt_025C_1v80 | 4.695 | 0.000 | 0 | 6.692 | 0.332 | 0.000 | 0 | 78 | 0 | 2 |
| max_ss_100C_1v60 | -0.962 | -26.917 | 44 | -0.893 | 0.893 | 0.000 | 0 | 4205 | 3 | 2 |
| max_ff_n40C_1v95 | 6.894 | 0.000 | 0 | inf | 0.112 | 0.000 | 0 | 15 | 0 | 2 |

LibreLane overall metrics (violation counts are SUMMED over corners, not unique endpoints): setup vio 123 (r2r 62), hold vio 0 (r2r 0); clock skew worst setup/hold 0.312 / -0.406 ns.

## Power estimate per corner (OpenSTA `report_power`, no VCD/SAIF, default activity)

| corner | internal, mW | switching, mW | leakage, mW | total, mW |
|---|---|---|---|---|
| nom_tt_025C_1v80 | 5.619 | 2.635 | 0.000 | 8.254 |
| nom_ss_100C_1v60 | 4.461 | 2.047 | 0.080 | 6.588 |
| nom_ff_n40C_1v95 | 6.471 | 3.125 | 0.000 | 9.597 |
| min_tt_025C_1v80 | 5.618 | 2.534 | 0.000 | 8.153 |
| min_ss_100C_1v60 | 4.460 | 1.968 | 0.080 | 6.508 |
| min_ff_n40C_1v95 | 6.471 | 3.007 | 0.000 | 9.478 |
| max_tt_025C_1v80 | 5.619 | 2.738 | 0.000 | 8.357 |
| max_ss_100C_1v60 | 4.462 | 2.129 | 0.080 | 6.670 |
| max_ff_n40C_1v95 | 6.471 | 3.246 | 0.000 | 9.718 |

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
| `antenna_diodes_count` | 13 |
| `design__disconnected_pin__count` | 0 |
| `design__power_grid_violation__count` | 0 |
| `ir__drop__worst` | 0.000336 |
| `ir__drop__avg` | 6.45e-05 |
| `design__lint_error__count` | 0 |
| `design__lint_warning__count` | 446 |
| `design__inferred_latch__count` | 0 |
| `flow__errors__count` | 0 |
| `flow__warnings__count` | 1 |
