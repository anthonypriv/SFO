-- 10 min session trips
with
	client_ass as (
		select
			client_id,
			ap_id,
			event_timestamp,
			lag(client_id) over (order by client_id, event_timestamp) as last_client,
			lag(ap_id) over (order by client_id, event_timestamp) as last_ap,
			lag(event_timestamp) over (order by client_id, event_timestamp) as last_time
		from client_association
		where event_timestamp > current_timestamp + interval '-1 hour'
	),
	session_10 as (
		select
			client_id,
			ap_id,
			event_timestamp,
			extract(epoch from event_timestamp - last_time) as delta
		from client_ass
		where extract(epoch from event_timestamp - last_time) between 600 and 615
	),
	trips_10 as (
		select
			client_id,
			ap_id,
			event_timestamp,
			case when client_id = last_client then extract(epoch from event_timestamp - last_time) else null end as delta
		from client_ass
		where client_id in (select distinct client_id from session_10)
	)
select
	trips.*,
	client.client_mac,
	ap.nyansa_mac,
	case when doors.terminal is not null then doors.terminal else gates.terminal end as terminal,
	ap.latitude as lat,
	ap.longitude as lon
from trips_10 as trips
left join ap_ref as ap on ap.ap_id = trips.ap_id
left join client_mac_ref as client on client.client_id = trips.client_id
left join vw_ap_doors as doors on doors.ap_id = trips.ap_id
left join vw_ap_gates as gates on gates.ap_id = trips.ap_id
where delta > 0 or delta is null
order by client_id, event_timestamp;


/*
-- 10 min session trips
with
	client_ass as (
		select
			client_id,
			ap_id,
			event_timestamp,
			lag(client_id) over (order by client_id, ap_id, event_timestamp) as last_client,
			lag(ap_id) over (order by client_id, ap_id, event_timestamp) as last_ap,
			lag(event_timestamp) over (order by client_id, ap_id, event_timestamp) as last_time
		from client_association
		where event_timestamp > current_timestamp + interval '-1 hour'
	),
	sessions as (
		select
			client_id,
			ap_id,
			last_time as connect_time,
			event_timestamp as disconnect_time,
			extract(epoch from event_timestamp - last_time) as session_len
		from client_ass
		where client_id = last_client
		and ap_id = last_ap
	)
select *
from sessions
where client_id in (select distinct client_id from sessions where session_len between 600 and 615)
order by client_id, connect_time;
*/
