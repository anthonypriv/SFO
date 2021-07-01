-- door to post security time
with
	trips as (  -- min, max time for each door/gate, label trips
		select
			door,
			door_terminal,
			post_terminal,
			min(et_local),
			dense_rank() over (order by client_id, date) as trip_id
		from (  -- get date (3am cutoff)
			select *, case when date_part('hour', et_local) < 3 then et_local::date - interval '1 day' else et_local::date end as date
			from (  -- convert to local time zone
				select
					ca.client_id,
					ca.event_timestamp at time zone 'utc' at time zone 'america/los_angeles' as et_local,
					doors.door_id as door,
					doors.terminal as door_terminal,
					ap.terminal_code as post_terminal
				from client_association as ca
				left join vw_ap_doors as doors on doors.ap_id = ca.ap_id  -- join door ap's
				left join ap_ref as ap on ap.ap_id = ca.ap_id
				where ca.event_timestamp > current_timestamp + interval 'INTERVAL'  -- time interval (study period)
				and ca.ap_id != -1
				and (ca.ap_id in (select ap_id from vw_ap_departures where pre_post_security like 'Post-Security') or doors.terminal is not null)  -- must be door or post ap
			) as A
		) as B
		group by client_id, date, door, door_terminal, post_terminal
	),
	doors as (  -- first time at first door
		select
			first_door.trip_id,
			first_door.door_time,
			trips.door,
			trips.door_terminal as terminal
		from (  -- first door time for each trip
			select trip_id, min(min) as door_time
			from trips
			where door is not null
			group by trip_id
		) as first_door
		inner join trips on trips.trip_id = first_door.trip_id and trips.min = first_door.door_time
	),
	post as (  -- first time at post security
		select
			first_post.trip_id,
			trips.min as post_time,
			trips.post_terminal as terminal
		from (  -- last gate time for each trip
			select trip_id, min(min) as min_post_time
			from trips
			where door_terminal is null
			group by trip_id
		) as first_post
		inner join trips on trips.trip_id = first_post.trip_id and trips.min = first_post.min_post_time
	)
select
	doors.trip_id,
	post.terminal,
	doors.door,
	extract(dow from doors.door_time) as dow,
	extract(hour from doors.door_time) as hour,
	extract(epoch from post.post_time - doors.door_time) as delta
from doors
left join post on post.trip_id = doors.trip_id
where doors.door is not null  -- trip must have door
and post.terminal is not null  -- trip must have post security
and extract(epoch from post.post_time - doors.door_time) between 60 and 7200  -- curb to gate between 1 min and 2 hours
and (doors.terminal = post.terminal or (doors.terminal like 'IT%' and post.terminal like 'IT%'));  -- door and gate must be in same terminal
