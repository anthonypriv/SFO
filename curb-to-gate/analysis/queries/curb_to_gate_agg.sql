select
	gates.terminal_code as terminal,
	___,
	sum(c2g.travel_time * c2g.dwell_sample_size) / sum(c2g.dwell_sample_size) as travel,
	sum(c2g.dwell_sample_size) as sample
from curb_to_gate_matrix as c2g
left join vw_door_ref as doors on doors.door_id = c2g.door_id
left join vw_gate_ref as gates on gates.gate_id = c2g.gate_id
where c2g.batch_timestamp = (select max(batch_timestamp) from curb_to_gate_matrix)
group by gates.terminal_code, ___
order by gates.terminal_code, ___;

/* placeholder ___ can be filled with:
	doors.door_number (door)
	gates.gate_display_name (gate)
	c2g.day_of_week (day of week)
	c2g.hour_of_day (hour of day)
*/
