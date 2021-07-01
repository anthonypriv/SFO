-- client counts
with
	employee as (
		select client_id, case when count > 5 then 'employee' else null end as employee
		from (
			select client_id, count(distinct trip_id)
			from (
				select client_id, count(distinct event_timestamp::date)
				from client_association
				where event_timestamp < current_timestamp + interval '-30 days'
				) as A
			group by client_id
			) as B
		),
	trips as (
		select
			ca.client_id,
			ca.ap_id,
			ca.event_timestamp,
			ap.terminal_code as terminal,
			doors.door_number as door,
			gates.gate_display_name as gate,
			emp.employee
		from client_association as ca
		left join ap_ref as ap on ap.ap_id = ca.ap_id
		left join vw_ap_doors as doors on doors.ap_id = ca.ap_id
		left join vw_ap_gates as gates on gates.ap_id = ca.ap_id
		left join employee as emp on emp.client_id = ca.client_id
		where ca.event_timestamp  between '2019-02-25 11:00:00' and '2019-02-26 11:00:00'
		and ca.ap_id != -1
		and ca.ap_id in (select distinct ap_id from vw_ap_departures)
	)
select * from trips
order by client_id, event_timestamp;
