-- session length by terminal
with
	A as (
		select client_id, ap_id, event_timestamp
		from client_association
		where event_timestamp > current_timestamp + interval '-1 day'
		order by client_id, event_timestamp
	),
	B as (
		select
			*,
			lag(client_id) over (order by client_id, event_timestamp) as first_client_id,
			lag(ap_id) over (order by client_id, event_timestamp) as first_ap_id,
			lag(event_timestamp) over (order by client_id, event_timestamp) as first_event_timestamp
		from A
	),
	C as (
		select client_id, ap_id, extract(epoch from event_timestamp - first_event_timestamp) as session_len
		from B
		where first_client_id = client_id
		and first_ap_id = ap_id
	),
	D as (
		select
			C.session_len,
			case
				when doors.ap_id is not null then doors.ap_id
				when gates.ap_id is not null then gates.ap_id
				else null end as ap_id,
			case
				when gates.terminal is not null then gates.terminal
				when doors.terminal is not null then doors.terminal
				else null end as terminal
		from C
		left join vw_ap_doors as doors on doors.ap_id = C.ap_id
		left join vw_ap_gates as gates on gates.ap_id = C.ap_id
	)
select session_len, count(*), case when terminal like 'IT%' then 'ITB' else terminal end as terminal
from D
where session_len < 1250
and terminal is not null
group by case when terminal like 'IT%' then 'ITB' else terminal end, session_len
order by session_len, terminal;