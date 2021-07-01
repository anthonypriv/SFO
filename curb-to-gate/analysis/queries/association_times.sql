with
	A as (
		select
			event_timestamp at time zone 'utc' at time zone 'US/Pacific' as local_timestamp
		from client_association
		where event_timestamp > current_timestamp + interval '-1 days'
	),
	B as (
		select
			local_timestamp,
			count(*)
		from A
		group by local_timestamp
	)
select
	local_timestamp, count, extract('minute' from local_timestamp) as minute, extract('second' from local_timestamp) as second
from B
where count > 100
order by local_timestamp;
