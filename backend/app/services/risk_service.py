import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.risk import Risk
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)


# Rule-based risk catalog for Dutch underground infrastructure
STANDARD_RISKS = {
    "Gas": [
        {
            "description": "Aanwezigheid van asbest in bestaande gasleidingen (pre-1980 tracés)",
            "category": "Technisch",
            "probability": 3,
            "impact": 4,
            "mitigation_measure": "Asbest-inventarisatie uitvoeren voorafgaand aan graafwerkzaamheden",
        },
        {
            "description": "Interferentie met bestaande kabels en leidingen (KLIC)",
            "category": "Technisch",
            "probability": 4,
            "impact": 3,
            "mitigation_measure": "KLIC-melding tijdig aanvragen, proefsleuven uitvoeren",
        },
        {
            "description": "Vertraging vergunningverlening gemeente",
            "category": "Vergunning",
            "probability": 3,
            "impact": 4,
            "mitigation_measure": "Vroeg starten met vergunningprocedure, regelmatig contact met gemeente",
        },
    ],
    "Elektra": [
        {
            "description": "Kabelschade aan bestaande LS/MS kabels tijdens uitvoering",
            "category": "Technisch",
            "probability": 3,
            "impact": 5,
            "mitigation_measure": "Proefsleuven en handdegraving nabij bestaande kabels",
        },
        {
            "description": "Stroomonderbreking bij bestaande aansluitingen",
            "category": "Technisch",
            "probability": 2,
            "impact": 5,
            "mitigation_measure": "Noodvoeding plannen, bewoners/bedrijven tijdig informeren",
        },
    ],
    "LS_MS": [
        {
            "description": "Complexe kabelkruisingen met andere nutsleidingen",
            "category": "Technisch",
            "probability": 4,
            "impact": 4,
            "mitigation_measure": "Gedetailleerde KLIC-analyse en kruisingtekeningen maken",
        },
        {
            "description": "Spanningsklasse wijzigingen vereisen extra engineering",
            "category": "Technisch",
            "probability": 3,
            "impact": 4,
            "mitigation_measure": "Vroeg engineering review met netontwerp",
        },
    ],
    "Stations": [
        {
            "description": "Leveringstijden schakelmateriaal en transformatoren (>6 maanden)",
            "category": "Planning",
            "probability": 4,
            "impact": 5,
            "mitigation_measure": "Vroeg bestellen, leveranciers commitment laten geven",
        },
        {
            "description": "Complexe coordinatie met meerdere aannemers",
            "category": "Omgeving",
            "probability": 4,
            "impact": 3,
            "mitigation_measure": "Duidelijk projectplan met verantwoordelijkheden per partij",
        },
    ],
}

UNIVERSAL_RISKS = [
    {
        "description": "Bodemverontreiniging aangetroffen op het tracé",
        "category": "Omgeving",
        "probability": 2,
        "impact": 5,
        "mitigation_measure": "Bodemonderzoek uitvoeren (fase 1 en 2) voor start werkzaamheden",
    },
    {
        "description": "Stakeholdersweerstand bij omwonenden of bedrijven",
        "category": "Stakeholder",
        "probability": 3,
        "impact": 3,
        "mitigation_measure": "Omgevingsmanagement plan opstellen, vroeg communiceren",
    },
    {
        "description": "Archeologie en cultuurhistorische waarden op het tracé",
        "category": "Omgeving",
        "probability": 2,
        "impact": 4,
        "mitigation_measure": "Bureauonderzoek archeologie, eventueel proefsleuven",
    },
    {
        "description": "Scope creep door ontbrekende informatie in definitiefase",
        "category": "Financieel",
        "probability": 3,
        "impact": 3,
        "mitigation_measure": "Duidelijke scope-afbakening, change management procedure instellen",
    },
]


class RiskService:
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()

    def _get_rule_based_risks(self, project: Project) -> List[Dict[str, Any]]:
        risks = []
        discipline_risks = STANDARD_RISKS.get(project.discipline, [])
        risks.extend(discipline_risks)
        risks.extend(UNIVERSAL_RISKS)
        return risks

    def auto_detect_risks(self, project: Project) -> List[Risk]:
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self._async_auto_detect_risks(project))
        finally:
            loop.close()

    async def _async_auto_detect_risks(self, project: Project) -> List[Risk]:
        project_context = {
            "discipline": project.discipline,
            "location": project.location,
            "scope_description": project.scope_description,
            "phase": project.phase,
        }

        risks_data = None
        if self.ai_service.is_available:
            risks_data = await self.ai_service.detect_risks(project_context)

        if not risks_data:
            risks_data = self._get_rule_based_risks(project)

        created_risks = []
        existing_descriptions = {
            r.description for r in
            self.db.query(Risk.description).filter(Risk.project_id == project.id).all()
        }

        for risk_data in risks_data:
            description = risk_data.get("description", "")
            if description in existing_descriptions:
                continue
            risk = Risk(
                project_id=project.id,
                description=description,
                category=risk_data.get("category", "Overig"),
                probability=min(5, max(1, int(risk_data.get("probability", 3)))),
                impact=min(5, max(1, int(risk_data.get("impact", 3)))),
                score=int(risk_data.get("probability", 3)) * int(risk_data.get("impact", 3)),
                mitigation_measure=risk_data.get("mitigation_measure"),
                auto_detected=True,
                source=risk_data.get("source", "ai" if self.ai_service.is_available else "manual"),
                status="open",
            )
            self.db.add(risk)
            created_risks.append(risk)
            existing_descriptions.add(description)

        self.db.commit()
        for r in created_risks:
            self.db.refresh(r)
        return created_risks
