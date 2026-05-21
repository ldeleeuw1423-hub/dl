"""GIS service — local geometry analysis plus live PDOK API calls."""
import logging
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PDOK WFS endpoints (Dutch open-data APIs)
# ---------------------------------------------------------------------------
PDOK_BAG_WFS = "https://service.pdok.nl/lv/bag/wfs/v2_0"
PDOK_BGT_WFS = "https://service.pdok.nl/lv/bgt/wfs/v1_0"
PDOK_BESTUURLIJKEGRENZEN = "https://service.pdok.nl/kadaster/bestuurlijkegrenzen/wfs/v1_0"
PDOK_NATURA2000 = "https://service.pdok.nl/rvo/natura2000/wfs/v1_0"
PDOK_WATERKERINGEN = "https://service.pdok.nl/ws/nwb-wegen/wfs/v1_0"

_HTTPX_TIMEOUT = 15.0


def _wfs_params(type_name: str, cql_filter: str, output_format: str = "application/json") -> Dict[str, str]:
    return {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeName": type_name,
        "outputFormat": output_format,
        "CQL_FILTER": cql_filter,
        "count": "50",
    }


async def get_municipality_for_point(lon: float, lat: float) -> Optional[str]:
    """Query PDOK bestuurlijke grenzen to get municipality name for a WGS84 point."""
    cql = f"INTERSECTS(geom,POINT({lon} {lat}))"
    params = _wfs_params("bestuurlijkegrenzen:gemeenten", cql)
    try:
        async with httpx.AsyncClient(timeout=_HTTPX_TIMEOUT) as client:
            resp = await client.get(PDOK_BESTUURLIJKEGRENZEN, params=params)
            resp.raise_for_status()
            data = resp.json()
            features = data.get("features", [])
            if features:
                props = features[0].get("properties", {})
                return props.get("gemeentenaam") or props.get("naam")
    except Exception as exc:
        logger.warning("PDOK gemeente lookup failed: %s", exc)
    return None


async def check_natura2000_proximity(geometry_wkt: str, buffer_m: int = 500) -> bool:
    """Check if the given WKT geometry (WGS84) is within buffer_m of a Natura 2000 area."""
    cql = f"DWITHIN(geom,{geometry_wkt},{buffer_m},meters)"
    params = _wfs_params("natura2000:natura2000gebieden", cql)
    params["count"] = "1"
    try:
        async with httpx.AsyncClient(timeout=_HTTPX_TIMEOUT) as client:
            resp = await client.get(PDOK_NATURA2000, params=params)
            resp.raise_for_status()
            data = resp.json()
            return len(data.get("features", [])) > 0
    except Exception as exc:
        logger.warning("PDOK Natura2000 check failed: %s", exc)
    return False


async def get_bag_addresses_near_trace(geometry_wkt: str) -> int:
    """Count BAG address objects (verblijfsobject) near the trace geometry (WGS84)."""
    cql = f"INTERSECTS(geometrie,{geometry_wkt})"
    params = _wfs_params("bag:verblijfsobject", cql)
    params["resultType"] = "hits"
    try:
        async with httpx.AsyncClient(timeout=_HTTPX_TIMEOUT) as client:
            resp = await client.get(
                PDOK_BAG_WFS,
                params={**params, "outputFormat": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("totalFeatures", len(data.get("features", [])))
    except Exception as exc:
        logger.warning("PDOK BAG address count failed: %s", exc)
    return 0


async def analyze_trace_crossings(geometry_wkt: str) -> Dict[str, int]:
    """Analyse crossings of a WKT linestring (WGS84) using BGT WFS.

    Returns a dict with counts per feature type.  Falls back to zeros on
    network errors so the rest of the analysis is never blocked.
    """
    result = {
        "waterways": 0,
        "major_roads": 0,
        "railways": 0,
        "cycle_paths": 0,
    }

    cql_base = f"INTERSECTS(geometrie,{geometry_wkt})"

    layer_map: Dict[str, str] = {
        "waterways": "bgt:waterdeel",
        "major_roads": "bgt:wegdeel",
        "cycle_paths": "bgt:wegdeel",
    }

    async with httpx.AsyncClient(timeout=_HTTPX_TIMEOUT) as client:
        # Waterways
        try:
            resp = await client.get(
                PDOK_BGT_WFS,
                params=_wfs_params(
                    "bgt:waterdeel",
                    cql_base,
                ),
            )
            if resp.status_code == 200:
                data = resp.json()
                result["waterways"] = len(data.get("features", []))
        except Exception as exc:
            logger.warning("PDOK BGT waterway crossing check failed: %s", exc)

        # Roads — try to filter on function
        try:
            road_cql = f"INTERSECTS(geometrie,{geometry_wkt})"
            resp = await client.get(
                PDOK_BGT_WFS,
                params=_wfs_params("bgt:wegdeel", road_cql),
            )
            if resp.status_code == 200:
                data = resp.json()
                features = data.get("features", [])
                major = 0
                cycle = 0
                for f in features:
                    func = (
                        f.get("properties", {}).get("functie", "")
                        or f.get("properties", {}).get("function", "")
                    ).lower()
                    if any(k in func for k in ("rijbaan", "autoweg", "hoofdrijbaan")):
                        major += 1
                    if any(k in func for k in ("fiets", "voetpad")):
                        cycle += 1
                result["major_roads"] = major
                result["cycle_paths"] = cycle
        except Exception as exc:
            logger.warning("PDOK BGT road crossing check failed: %s", exc)

        # Railways via NWB
        try:
            rail_cql = f"INTERSECTS(geometrie,{geometry_wkt})"
            resp = await client.get(
                PDOK_WATERKERINGEN,
                params=_wfs_params("nwb:spoorwegen", rail_cql),
            )
            if resp.status_code == 200:
                data = resp.json()
                result["railways"] = len(data.get("features", []))
        except Exception as exc:
            logger.warning("PDOK NWB railway crossing check failed: %s", exc)

    return result


# ---------------------------------------------------------------------------
# GISService class — combines local + PDOK analysis
# ---------------------------------------------------------------------------


class GISService:
    def __init__(self, db: Session):
        self.db = db

    def analyze_geometry(self, geometry: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse a GeoJSON geometry and return infrastructure context.

        Local analysis only — for live PDOK analysis use analyze_with_pdok().
        """
        result: Dict[str, Any] = {
            "geometry_type": geometry.get("type", "Unknown"),
            "analysis": {},
            "risks": [],
            "permits_likely": [],
            "notes": [],
        }

        geo_type = geometry.get("type", "")
        coordinates = geometry.get("coordinates", [])

        if geo_type == "LineString":
            length_m = self._estimate_line_length(coordinates)
            result["analysis"]["estimated_length_m"] = round(length_m, 0)
            result["analysis"]["num_points"] = len(coordinates)

            if length_m > 1000:
                result["risks"].append({
                    "description": "Lang tracé (>1km) verhoogt de kans op onverwachte obstakels",
                    "category": "Technisch",
                    "probability": 3,
                    "impact": 3,
                })
                result["permits_likely"].append("Meerdere instemmingsbesluiten mogelijk vereist")

            result["notes"].append(f"Geschatte tracelengte: {round(length_m, 0)}m")

        elif geo_type == "Polygon":
            area_m2 = self._estimate_polygon_area(coordinates)
            result["analysis"]["estimated_area_m2"] = round(area_m2, 0)
            result["notes"].append(f"Geschatte oppervlakte: {round(area_m2, 0)}m²")

        elif geo_type == "Point":
            result["analysis"]["location"] = {
                "longitude": coordinates[0] if len(coordinates) > 0 else None,
                "latitude": coordinates[1] if len(coordinates) > 1 else None,
            }

        # Universal KLIC note
        result["risks"].append({
            "description": "KLIC-controle vereist voor alle grondroerende werkzaamheden",
            "category": "Technisch",
            "probability": 4,
            "impact": 4,
            "source": "gis",
        })
        result["notes"].append(
            "Voer KLIC-melding in minimaal 3 werkdagen voor start werkzaamheden"
        )

        return result

    async def analyze_with_pdok(self, geometry: Dict[str, Any]) -> Dict[str, Any]:
        """Run full PDOK API analysis on a GeoJSON geometry.

        Returns structured analysis suitable for risk and permit auto-detection.
        """
        base = self.analyze_geometry(geometry)
        pdok_result: Dict[str, Any] = {**base, "pdok": {}}

        geo_type = geometry.get("type", "")
        coords = geometry.get("coordinates", [])

        # Build WKT representation for PDOK queries
        wkt = _geojson_to_wkt(geometry)
        if not wkt:
            pdok_result["pdok"]["error"] = "Geometrie kon niet worden omgezet naar WKT"
            return pdok_result

        # Gemeente lookup — use centroid for Point or first coordinate for LineString
        centroid = _geometry_centroid(geometry)
        if centroid:
            gemeente = await get_municipality_for_point(centroid[0], centroid[1])
            pdok_result["pdok"]["gemeente"] = gemeente or "Onbekend"

        # Natura 2000
        near_natura2000 = await check_natura2000_proximity(wkt, buffer_m=500)
        pdok_result["pdok"]["natura2000_proximity"] = near_natura2000
        if near_natura2000:
            pdok_result["risks"].append({
                "description": "Tracé ligt binnen 500m van Natura 2000 gebied — passende beoordeling vereist",
                "category": "Omgeving",
                "probability": 4,
                "impact": 5,
                "source": "gis",
            })
            pdok_result["permits_likely"].append("Passende beoordeling / Wnb-vergunning")

        # BAG address density
        address_count = await get_bag_addresses_near_trace(wkt)
        pdok_result["pdok"]["address_count"] = address_count
        if address_count > 50:
            pdok_result["pdok"]["urban_density"] = "hoog"
        elif address_count > 10:
            pdok_result["pdok"]["urban_density"] = "gemiddeld"
        else:
            pdok_result["pdok"]["urban_density"] = "laag"

        # Crossings analysis (only for LineString)
        if geo_type == "LineString":
            crossings = await analyze_trace_crossings(wkt)
            pdok_result["pdok"]["crossings"] = crossings

            if crossings["waterways"] > 0:
                pdok_result["risks"].append({
                    "description": f"Tracé kruist {crossings['waterways']} watergang(en) — watervergunning vereist",
                    "category": "Vergunning",
                    "probability": 3,
                    "impact": 4,
                    "source": "gis",
                })
                pdok_result["permits_likely"].append("Watervergunning (waterschap)")

            if crossings["railways"] > 0:
                pdok_result["risks"].append({
                    "description": f"Tracé kruist {crossings['railways']} spoorlijn(en) — ProRail toestemming vereist",
                    "category": "Vergunning",
                    "probability": 4,
                    "impact": 5,
                    "source": "gis",
                })
                pdok_result["permits_likely"].append("ProRail instemmingsverklaring")

            if crossings["major_roads"] > 0:
                pdok_result["risks"].append({
                    "description": f"Tracé kruist {crossings['major_roads']} hoofdweg(en) — uitvoeringsrisico verkeershinder",
                    "category": "Omgeving",
                    "probability": 3,
                    "impact": 3,
                    "source": "gis",
                })

        return pdok_result

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _estimate_line_length(self, coordinates: List) -> float:
        """Estimate line length in meters from WGS84 coordinate pairs."""
        if not coordinates or len(coordinates) < 2:
            return 0.0
        total = 0.0
        for i in range(len(coordinates) - 1):
            p1 = coordinates[i]
            p2 = coordinates[i + 1]
            if len(p1) >= 2 and len(p2) >= 2:
                # At Dutch latitudes: 1 degree lat ~ 111,320m, 1 degree lon ~ 70,000m
                dlat = (p2[1] - p1[1]) * 111320
                dlon = (p2[0] - p1[0]) * 70000
                total += (dlat ** 2 + dlon ** 2) ** 0.5
        return total

    def _estimate_polygon_area(self, coordinates: List) -> float:
        """Estimate polygon area in m² using shoelace formula."""
        if not coordinates or not coordinates[0]:
            return 0.0
        ring = coordinates[0]
        if len(ring) < 3:
            return 0.0
        n = len(ring)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            xi = ring[i][0] * 70000
            yi = ring[i][1] * 111320
            xj = ring[j][0] * 70000
            yj = ring[j][1] * 111320
            area += xi * yj
            area -= xj * yi
        return abs(area) / 2.0


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def _geojson_to_wkt(geometry: Dict[str, Any]) -> Optional[str]:
    """Convert a simple GeoJSON geometry dict to WKT (WGS84)."""
    geo_type = geometry.get("type", "")
    coords = geometry.get("coordinates", [])
    try:
        if geo_type == "Point":
            return f"POINT({coords[0]} {coords[1]})"
        elif geo_type == "LineString":
            pts = " ".join(f"{c[0]} {c[1]}" for c in coords)
            return f"LINESTRING({pts})"
        elif geo_type == "Polygon":
            ring = coords[0]
            pts = " ".join(f"{c[0]} {c[1]}" for c in ring)
            return f"POLYGON(({pts}))"
    except (IndexError, TypeError) as exc:
        logger.warning("WKT conversion failed: %s", exc)
    return None


def _geometry_centroid(geometry: Dict[str, Any]) -> Optional[List[float]]:
    """Return the approximate centroid [lon, lat] of a GeoJSON geometry."""
    geo_type = geometry.get("type", "")
    coords = geometry.get("coordinates", [])
    try:
        if geo_type == "Point":
            return [coords[0], coords[1]]
        elif geo_type == "LineString":
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            return [sum(lons) / len(lons), sum(lats) / len(lats)]
        elif geo_type == "Polygon":
            ring = coords[0]
            lons = [c[0] for c in ring]
            lats = [c[1] for c in ring]
            return [sum(lons) / len(lons), sum(lats) / len(lats)]
    except (IndexError, TypeError, ZeroDivisionError) as exc:
        logger.warning("Centroid calculation failed: %s", exc)
    return None
