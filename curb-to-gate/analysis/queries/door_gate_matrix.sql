select
	terminal_code as terminal,
	door_number as door,
	gate_display_name as gate,
	sum(dwell_time * dwell_sample_size) / sum(dwell_sample_size) as dwell_time,
	sum(travel_time * dwell_sample_size) / sum(dwell_sample_size) as travel_time,
	sum(dwell_sample_size) as sample_size
from curb_to_gate_matrix
where batch_timestamp = (select max(batch_timestamp) from curb_to_gate_matrix)
group by terminal_code, door_number, gate_display_name
order by terminal, door, gate;
