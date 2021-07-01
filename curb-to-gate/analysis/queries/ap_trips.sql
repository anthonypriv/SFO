-- clients per ap (by terminal) - door ap's only
with
	trips as (
		select
			ca.client_id,
			ca.ap_id,
			doors.terminal,
			doors.door_number as door
		from client_association as ca
		left join ap_ref as ap on ap.ap_id = ca.ap_id
		left join vw_ap_doors as doors on doors.ap_id = ca.ap_id
		where ca.event_timestamp between '2019-02-25 11:00:00' and '2019-02-26 11:00:00'
		and doors.door_number is not null
	),
	ap_count as (
		select terminal, ap_id, count(*)
		from trips
		group by terminal, ap_id
	)
select terminal, avg(count) as avg_clients
from ap_count
group by terminal
order by terminal;
