# Smoke SDC for pe: 100 MHz, 2 ns external delay on inputs and outputs.
create_clock -name clk -period 10.0 [get_ports clk]
set_input_delay  2.0 -clock clk [delete_from_list [all_inputs] [get_ports clk]]
set_output_delay 2.0 -clock clk [all_outputs]
set_load 0.01 [all_outputs]
