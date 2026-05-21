import logging
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from decimal import Decimal

from app.models.estimation import Estimation
from app.models.historical import HistoricalProject
from app.models.project import Project
from app.schemas.estimation import EstimationGenerateRequest
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)


# Rule-based estimation parameters per discipline
DISCIPLINE_PARAMS = {
    "Gas": {
        "engineering_per_100m": 8.0,
        "pm_per_100m": 3.0,
        "om_per_100m": 2.5,
        "workprep_per_100m": 4.0,
        "execution_per_100m": 6.0,
        "cost_material_per_m": 85.0,
        "base_hours_engineering": 40,
        "base_hours_pm": 20,
    },
    "Elektra": {
        "engineering_per_100m": 7.0,
        "pm_per_100m": 2.5,
        "om_per_100m": 2.0,
        "workprep_per_100m": 3.5,
        "execution_per_100m": 5.0,
        "cost_material_per_m": 65.0,
        "base_hours_engineering": 32,
        "base_hours_pm": 16,
    },
    "LS_MS": {
        "engineering_per_100m": 10.0,
        "pm_per_100m": 4.0,
        "om_per_100m": 3.5,
        "workprep_per_100m": 5.0,
        "execution_per_100m": 8.0,
        "cost_material_per_m": 150.0,
        "base_hours_engineering": 80,
        "base_hours_pm": 32,
    },
    "Stations": {
        "engineering_per_100m": 15.0,
        "pm_per_100m": 6.0,
        "om_per_100m": 5.0,
        "workprep_per_100m": 8.0,
        "execution_per_100m": 12.0,
        "cost_material_per_m": 300.0,
        "base_hours_engineering": 160,
        "base_hours_pm": 60,
    },
}

HOURLY_RATES = {
    "engineering": 105.0,
    "pm": 115.0,
    "om": 102.0,
    "workprep": 92.0,
    "execution": 88.0,
}

LOCATION_MULTIPLIER = {
    "urban": 1.35,
    "rural": 1.0,
    "mixed": 1.18,
}

PHASE_CONFIDENCE = {
    "VO": 65.0,
    "DO": 75.0,
    "UO": 85.0,
    "Realisatie": 90.0,
}

CROSSING_HOURS = 12.0  # extra hours per crossing


class EstimationService:
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()

    def _find_similar_projects(
        self,
        discipline: str,
        location_type: Optional[str],
        trace_length_m: Optional[float],
    ) -> List[HistoricalProject]:
        query = self.db.query(HistoricalProject).filter(
            HistoricalProject.discipline == discipline
        )
        if location_type:
            query = query.filter(HistoricalProject.location_type == location_type)
        if trace_length_m:
            query = query.filter(
                HistoricalProject.trace_length_m.between(
                    trace_length_m * 0.4, trace_length_m * 2.0
                )
            )
        return query.limit(5).all()

    async def find_similar_projects(
        self,
        project_data: Dict[str, Any],
        top_k: int = 5,
    ) -> List[Tuple[HistoricalProject, float]]:
        """Find the top_k most similar historical projects using pgvector cosine similarity.

        Returns a list of (HistoricalProject, similarity_score) tuples ordered by
        descending similarity. Falls back to rule-based filter when no embeddings
        are stored.
        """
        embedding = await self.ai_service.generate_project_embedding(project_data)
        embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"

        try:
            rows = self.db.execute(
                text(
                    """
                    SELECT id, 1 - (embedding <=> CAST(:emb AS vector)) AS similarity
                    FROM historical_projects
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> CAST(:emb AS vector)
                    LIMIT :k
                    """
                ),
                {"emb": embedding_str, "k": top_k},
            ).fetchall()

            if rows:
                ids = [str(row[0]) for row in rows]
                similarity_map = {str(row[0]): float(row[1]) for row in rows}
                projects = self.db.query(HistoricalProject).filter(
                    HistoricalProject.id.in_(ids)
                ).all()
                result = [(p, similarity_map.get(str(p.id), 0.0)) for p in projects]
                result.sort(key=lambda x: x[1], reverse=True)
                return result
        except Exception as exc:
            logger.warning(f"pgvector similarity search failed, using rule-based: {exc}")

        # Fallback: rule-based filter
        fallback = self._find_similar_projects(
            project_data.get("discipline", "Elektra"),
            project_data.get("location_type"),
            project_data.get("trace_length_m"),
        )
        return [(p, 0.75) for p in fallback]

    def _rule_based_estimation(
        self,
        project: Project,
        request: EstimationGenerateRequest,
    ) -> Dict[str, Any]:
        discipline = request.discipline or project.discipline
        params = DISCIPLINE_PARAMS.get(discipline, DISCIPLINE_PARAMS["Elektra"])
        trace_m = float(request.trace_length_m or 500)
        trace_100m = trace_m / 100.0
        num_crossings = request.num_crossings or 0
        num_permits = request.num_permits or 2
        location_type = request.location_type or "urban"
        phase = request.phase or project.phase

        location_mult = LOCATION_MULTIPLIER.get(location_type, 1.0)
        permit_hours = num_permits * 8.0

        hours_eng = (
            params["base_hours_engineering"]
            + params["engineering_per_100m"] * trace_100m
            + num_crossings * CROSSING_HOURS * 0.5
        ) * location_mult

        hours_pm = (
            params["base_hours_pm"]
            + params["pm_per_100m"] * trace_100m
        )

        hours_om = (
            params["om_per_100m"] * trace_100m
            + permit_hours
        ) * location_mult

        hours_workprep = (
            params["workprep_per_100m"] * trace_100m
            + num_crossings * CROSSING_HOURS * 0.3
        )

        hours_exec = (
            params["execution_per_100m"] * trace_100m
            + num_crossings * CROSSING_HOURS
        ) * location_mult

        cost_materials = params["cost_material_per_m"] * trace_m * location_mult

        labor_cost = (
            hours_eng * HOURLY_RATES["engineering"]
            + hours_pm * HOURLY_RATES["pm"]
            + hours_om * HOURLY_RATES["om"]
            + hours_workprep * HOURLY_RATES["workprep"]
            + hours_exec * HOURLY_RATES["execution"]
        )
        cost_total = labor_cost + cost_materials

        confidence = PHASE_CONFIDENCE.get(phase, 70.0)

        return {
            "hours_engineering": round(hours_eng, 1),
            "hours_pm": round(hours_pm, 1),
            "hours_om": round(hours_om, 1),
            "hours_workprep": round(hours_workprep, 1),
            "hours_execution": round(hours_exec, 1),
            "cost_materials": round(cost_materials, 2),
            "cost_total": round(cost_total, 2),
            "bandwidth_low": round(cost_total * 0.85, 2),
            "bandwidth_high": round(cost_total * 1.25, 2),
            "confidence_score": confidence,
            "methodology": "Regelgebaseerd",
            "reasoning": (
                f"Inschatting gebaseerd op {discipline} parameters, {trace_m}m tracé, "
                f"{num_crossings} kruisingen, locatietype {location_type}. "
                f"Uurtarieven conform marktstandaard Nederlandse netbeheerders."
            ),
        }

    async def generate_estimation(
        self,
        project: Project,
        request: EstimationGenerateRequest,
    ) -> Estimation:
        discipline = request.discipline or project.discipline

        project_lookup = {
            "discipline": discipline,
            "location_type": request.location_type or "urban",
            "trace_length_m": float(request.trace_length_m or 0),
            "num_crossings": request.num_crossings or 0,
            "num_permits": request.num_permits or 0,
            "num_stakeholders": request.num_stakeholders or 0,
        }
        similar_with_scores = await self.find_similar_projects(project_lookup, top_k=5)

        similar_projects_data = []
        for sp, sim_score in similar_with_scores:
            similar_projects_data.append({
                "reference_number": sp.reference_number,
                "name": sp.name,
                "discipline": sp.discipline,
                "location_type": sp.location_type,
                "trace_length_m": float(sp.trace_length_m) if sp.trace_length_m else None,
                "duration_days": sp.duration_days,
                "hours_engineering": float(sp.hours_engineering) if sp.hours_engineering else None,
                "hours_pm": float(sp.hours_pm) if sp.hours_pm else None,
                "hours_om": float(sp.hours_om) if sp.hours_om else None,
                "hours_workprep": float(sp.hours_workprep) if sp.hours_workprep else None,
                "cost_total": float(sp.cost_total) if sp.cost_total else None,
                "similarity_score": round(sim_score, 4),
            })

        project_context = {
            "name": project.name,
            "discipline": project.discipline,
            "phase": project.phase,
            "location": project.location,
            "scope_description": project.scope_description,
            "trace_length_m": request.trace_length_m,
            "num_crossings": request.num_crossings,
            "num_permits": request.num_permits,
            "location_type": request.location_type,
        }

        # Try AI first, fall back to rule-based
        estimation_data = None
        if self.ai_service.is_available:
            estimation_data = await self.ai_service.generate_estimation(
                project_context, similar_projects_data
            )

        if estimation_data is None:
            estimation_data = self._rule_based_estimation(project, request)

        # Get current max version
        from sqlalchemy import func
        max_version = self.db.query(func.max(Estimation.version)).filter(
            Estimation.project_id == project.id
        ).scalar() or 0

        estimation = Estimation(
            project_id=project.id,
            version=max_version + 1,
            discipline=discipline,
            hours_engineering=Decimal(str(estimation_data["hours_engineering"])),
            hours_pm=Decimal(str(estimation_data["hours_pm"])),
            hours_om=Decimal(str(estimation_data["hours_om"])),
            hours_workprep=Decimal(str(estimation_data["hours_workprep"])),
            hours_execution=Decimal(str(estimation_data["hours_execution"])),
            cost_materials=Decimal(str(estimation_data["cost_materials"])),
            cost_total=Decimal(str(estimation_data["cost_total"])),
            bandwidth_low=Decimal(str(estimation_data["bandwidth_low"])),
            bandwidth_high=Decimal(str(estimation_data["bandwidth_high"])),
            confidence_score=Decimal(str(estimation_data["confidence_score"])),
            methodology=estimation_data.get("methodology", "Regelgebaseerd"),
            similar_projects=similar_projects_data if similar_projects_data else None,
            reasoning=estimation_data.get("reasoning"),
            is_current=True,
        )
        self.db.add(estimation)

        # Update project totals
        total_hours = (
            float(estimation.hours_engineering or 0)
            + float(estimation.hours_pm or 0)
            + float(estimation.hours_om or 0)
            + float(estimation.hours_workprep or 0)
            + float(estimation.hours_execution or 0)
        )
        project.hours_estimated = Decimal(str(total_hours))
        project.budget_estimated = estimation.cost_total

        self.db.commit()
        self.db.refresh(estimation)
        return estimation
