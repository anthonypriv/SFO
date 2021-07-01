with
	ca as (
		select
			client_id,
			ap_id,
			lag(ap_id) over (order by client_id, event_timestamp) as last_ap,
			event_timestamp
		from client_association
		where event_timestamp > current_timestamp + interval '-12 hour'
		and ap_id != -1
	),
	trip_features as (
		select
			ca.client_id,
			ca.ap_id,
			ca.event_timestamp,
			doors.door_number as door,
			doors.terminal as door_terminal,
			gates.gate_display_name as gate,
			gates.terminal as gate_terminal,
			ap.latitude,
			ap.longitude,
			client.client_mac,
			ap.nyansa_mac
		from ca
		left join vw_ap_doors as doors on doors.ap_id = ca.ap_id
		left join vw_ap_gates as gates on gates.ap_id = ca.ap_id
		left join ap_ref as ap on ap.ap_id = ca.ap_id
		left join client_mac_ref as client on client.client_id = ca.client_id
		where ca.ap_id != ca.last_ap
		and ap.latitude is not null and ap.longitude is not null
	)
select * from trip_features
order by client_id, event_timestamp;
