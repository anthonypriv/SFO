select
	gate_id,
	boarding_area_code as ba,
	latitude as lat,
	longitude as lon
from vw_gate_ref
where latitude is not null
and longitude is not null
and boarding_area_code is not null;
