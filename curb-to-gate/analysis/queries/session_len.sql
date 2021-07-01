-- session length
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
		where first_client_id = client_id  -- same client
		and first_ap_id = ap_id  -- same ap
	)
select session_len, count(*)
from C
where session_len < 1250
group by session_len
order by session_len;
