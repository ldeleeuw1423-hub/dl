import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.permit import Permit
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)


# Standard permit requirements for Dutch underground infrastructure
STANDARD_PERMITS = {
    "Gas": [
        {
            "permit_type": "Instemmingsbesluit",
            "description": "Instemming van de gemeente voor graafwerkzaamheden in de openbare ruimte (WION)",
            "authority": "gemeente",
            "risk_level": "medium",
            "delay_probability": 20,
        },
        {
            "permit_type": "KLIC-melding",
            "description": "Kabel- en leidinginformatie opvragen voor grondroerende werkzaamheden",
            "authority": "overig",
            "risk_level": "low",
            "delay_probability": 5,
        },
    ],
    "Elektra": [
        {
            "permit_type": "Instemmingsbesluit",
            "description": "Instemming van de gemeente voor graafwerkzaamheden",
            "authority": "gemeente",
            "risk_level": "medium",
            "delay_probability": 20,
        },
        {
            "permit_type": "Omgevingsvergunning activiteit kabels en leidingen",
            "description": "Omgevingsvergunning voor aanleggen van kabels",
            "authority": "gemeente",
            "risk_level": "medium",
            "delay_probability": 30,
        },
    ],
    "LS_MS": [
        {
            "permit_type": "Instemmingsbesluit",
            "description": "Instemming gemeente voor aanleg LS/MS kabels in openbare ruimte",
            "authority": "gemeente",
            "risk_level": "medium",
            "delay_probability": 25,
        },
        {
            "permit_type": "Omgevingsvergunning",
            "description": "Omgevingsvergunning voor aanleg middenspanning kabels",
            "authority": "gemeente",
            "risk_level": "high",
            "delay_probability": 35,
        },
        {
            "permit_type": "Watervergunning",
            "description": "Vergunning waterschap voor kruising watergangen",
            "authority": "waterschap",
            "risk_level": "medium",
            "delay_probability": 30,
        },
    ],
    "Stations": [
        {
            "permit_type": "Omgevingsvergunning bouwen",
            "description": "Bouwvergunning voor nieuw of uitgebreid schakelstation",
            "authority": "gemeente",
            "risk_level": "high",
            "delay_probability": 40,
        },
        {
            "permit_type": "Omgevingsvergunning milieu",
            "description": "Milieuvergunning voor transformator met olie",
            "authority": "gemeente",
            "risk_level": "high",
            "delay_probability": 45,
        },
        {
            "permit_type": "Instemmingsbesluit",
            "description": "Instemming voor aanleg kabelverbindingen naar station",
            "authority": "gemeente",
            "risk_level": "medium",
            "delay_probability": 20,
        },
    ],
}

UNIVERSAL_PERMITS = [
    {
        "permit_type": "Melding Activiteitenbesluit",
        "description": "Melding bij bevoegd gezag voor werkzaamheden op/nabij druk bezochte locaties",
        "authority": "gemeente",
        "risk_level": "low",
        "delay_probability": 10,
    },
]


class PermitService:
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()

    def _get_rule_based_permits(self, project: Project) -> List[Dict[str, Any]]:
        permits = []
        discipline_permits = STANDARD_PERMITS.get(project.discipline, [])
        permits.extend(discipline_permits)
        permits.extend(UNIVERSAL_PERMITS)
        return permits

    def auto_detect_permits(self, project: Project) -> List[Permit]:
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self._async_auto_detect_permits(project))
        finally:
            loop.close()

    async def _async_auto_detect_permits(self, project: Project) -> List[Permit]:
        project_context = {
            "discipline": project.discipline,
            "location": project.location,
            "scope_description": project.scope_description,
            "phase": project.phase,
        }

        permits_data = None
        if self.ai_service.is_available:
            permits_data = await self.ai_service.detect_permits(project_context)

        if not permits_data:
            permits_data = self._get_rule_based_permits(project)

        created_permits = []
        existing_types = {
            p.permit_type for p in
            self.db.query(Permit.permit_type).filter(Permit.project_id == project.id).all()
        }

        for permit_data in permits_data:
            permit_type = permit_data.get("permit_type", "")
            if permit_type in existing_types:
                continue
            permit = Permit(
                project_id=project.id,
                permit_type=permit_type,
                description=permit_data.get("description"),
                authority=permit_data.get("authority", "gemeente"),
                risk_level=permit_data.get("risk_level", "medium"),
                delay_probability=permit_data.get("delay_probability", 25),
                auto_detected=True,
                status="required",
            )
            self.db.add(permit)
            created_permits.append(permit)
            existing_types.add(permit_type)

        self.db.commit()
        for p in created_permits:
            self.db.refresh(p)
        return created_permits
