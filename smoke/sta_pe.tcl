# Smoke STA of the pe netlist (after synth_pe.ys) in OpenSTA, SKY130 HD typical corner.
read_liberty sky130_fd_sc_hd__tt_025C_1v80.lib
read_verilog pe_netlist.v
link_design pe
read_sdc pe_smoke.sdc
report_checks -path_delay max -fields {slew cap input_pins} -digits 3
report_checks -path_delay min -digits 3
report_wns
report_tns
exit
