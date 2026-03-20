"""PostGIS spatial analysis queries."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SpatialAnalyzer:
    """Run PostGIS spatial analysis queries against the Nigehbaan database."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_incidents_near_kilns(self, radius_m: int = 10_000) -> list[dict[str, Any]]:
        """Find incidents within *radius_m* metres of any brick kiln.

        Returns a list of dicts with ``incident_id``, ``kiln_id``, and ``distance_m``.
        """
        query = text(
            """
            SELECT
                i.id   AS incident_id,
                k.id   AS kiln_id,
                ST_Distance(i.geometry::geography, k.geometry::geography) AS distance_m
            FROM incidents i
            JOIN brick_kilns k
              ON ST_DWithin(i.geometry::geography, k.geometry::geography, :radius)
            WHERE i.geometry IS NOT NULL
              AND k.geometry IS NOT NULL
            ORDER BY distance_m
            """
        )
        result = await self.session.execute(query, {"radius": radius_m})
        return [dict(row._mapping) for row in result.fetchall()]

    async def calculate_district_density(self) -> list[dict[str, Any]]:
        """Calculate incident density per 100K population by district.

        Returns a list of dicts with ``district_pcode``, ``incident_count``,
        ``population``, and ``per_100k``.
        """
        query = text(
            """
            SELECT
                b.pcode        AS district_pcode,
                b.name_en,
                COUNT(i.id)    AS incident_count,
                b.population_total AS population,
                CASE
                    WHEN b.population_total > 0
                    THEN ROUND(COUNT(i.id)::numeric / b.population_total * 100000, 2)
                    ELSE 0
                END AS per_100k
            FROM boundaries b
            LEFT JOIN incidents i ON i.district_pcode = b.pcode
            WHERE b.admin_level = 4
            GROUP BY b.pcode, b.name_en, b.population_total
            ORDER BY per_100k DESC
            """
        )
        result = await self.session.execute(query)
        return [dict(row._mapping) for row in result.fetchall()]

    async def identify_hotspot_clusters(
        self,
        eps_km: float = 20.0,
        min_samples: int = 5,
    ) -> list[dict[str, Any]]:
        """Run DBSCAN clustering on geocoded incidents.

        Uses ST_ClusterDBSCAN as a PostGIS window function.
        *eps_km* is the maximum distance between two samples in kilometres.
        *min_samples* is the minimum cluster size.

        Returns a list of dicts with ``cluster_id``, ``incident_count``,
        ``centroid_lat``, and ``centroid_lon``.
        """
        eps_metres = eps_km * 1000
        query = text(
            """
            WITH clustered AS (
                SELECT
                    id,
                    geometry,
                    ST_ClusterDBSCAN(geometry, eps := :eps, minpoints := :minpts)
                        OVER () AS cluster_id
                FROM incidents
                WHERE geometry IS NOT NULL
            )
            SELECT
                cluster_id,
                COUNT(*)                                     AS incident_count,
                ST_Y(ST_Centroid(ST_Collect(geometry)))      AS centroid_lat,
                ST_X(ST_Centroid(ST_Collect(geometry)))      AS centroid_lon
            FROM clustered
            WHERE cluster_id IS NOT NULL
            GROUP BY cluster_id
            ORDER BY incident_count DESC
            """
        )
        result = await self.session.execute(query, {"eps": eps_metres, "minpts": min_samples})
        return [dict(row._mapping) for row in result.fetchall()]
