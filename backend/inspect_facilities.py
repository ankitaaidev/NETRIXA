from app.database.session import session_scope
from app.models.facility import Facility
from sqlalchemy import text


with session_scope() as db:
    result = db.execute(text("""
        SELECT
            COUNT(*) AS legacy_total,
            COUNT(*) FILTER (
                WHERE EXISTS (
                    SELECT 1
                    FROM facilities n
                    WHERE (
                        n.facility_id LIKE 'OSM-NODE-%'
                        OR n.facility_id LIKE 'OSM-WAY-%'
                        OR n.facility_id LIKE 'OSM-RELATION-%'
                    )
                    AND ST_DWithin(
                        ST_Transform(f.geom, 3857),
                        ST_Transform(n.geom, 3857),
                        100
                    )
                )
            ) AS legacy_with_national_match
        FROM facilities f
        WHERE NOT (
            f.facility_id LIKE 'OSM-NODE-%'
            OR f.facility_id LIKE 'OSM-WAY-%'
            OR f.facility_id LIKE 'OSM-RELATION-%'
        )
    """)).one()

    print("LEGACY TOTAL:", result.legacy_total)
    print("LEGACY WITH NATIONAL MATCH WITHIN 100M:", result.legacy_with_national_match)