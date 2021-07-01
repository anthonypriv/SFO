select
	terminal_code,
	gate_display_name,
	sum(dwell_sample_size) as sample,
	sum(travel_time * dwell_sample_size) / sum(dwell_sample_size) as travel
from curb_to_gate_matrix
where batch_timestamp = (select max(batch_timestamp) from curb_to_gate_matrix)
group by terminal_code, gate_display_name
order by terminal_code, dwell;
