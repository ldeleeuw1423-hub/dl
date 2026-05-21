import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class GISService:
    def __init__(self, db: Session):
        self.db = db

    def analyze_geometry(self, geometry: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a GeoJSON geometry and return relevant infrastructure context."""
        result = {
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

        # General checks
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

    def _estimate_line_length(self, coordinates: List) -> float:
        """Estimate line length in meters from coordinate pairs."""
        if not coordinates or len(coordinates) < 2:
            return 0.0
        total = 0.0
        for i in range(len(coordinates) - 1):
            p1 = coordinates[i]
            p2 = coordinates[i + 1]
            if len(p1) >= 2 and len(p2) >= 2:
                # Simple Euclidean approximation in degrees -> meters
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
