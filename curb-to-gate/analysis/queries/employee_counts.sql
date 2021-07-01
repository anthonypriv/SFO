with
	A as (  -- local timestamp conversion
		select client_id, event_timestamp at time zone 'utc' at time zone 'america/los_angeles' as et_local
		from client_association
		where event_timestamp < current_timestamp + interval '-30 days'
	),
	B as (  -- count of distinct dates per client
		select client_id, count(distinct et_local::date)
		from A
		group by client_id
	),
	C as (  -- number of clients showing up n days
		select count as days, count(*) as n_clients
		from B
		group by count
	)
select days, n_clients, round(n_clients / (select sum(n_clients) from C) * 100, 2) as perc
from C
order by days;
