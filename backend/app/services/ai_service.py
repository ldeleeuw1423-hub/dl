import json
import logging
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI, OpenAIError
from app.config import settings

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.client: Optional[AsyncOpenAI] = None
        if settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    @property
    def is_available(self) -> bool:
        return self.client is not None

    async def generate_estimation(
        self,
        project_context: Dict[str, Any],
        similar_projects: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if not self.is_available:
            return None

        similar_text = ""
        if similar_projects:
            similar_text = "\n\nVergelijkbare historische projecten:\n"
            for sp in similar_projects[:3]:
                similar_text += (
                    f"- {sp.get('name', 'Onbekend')} ({sp.get('discipline', '')}, "
                    f"{sp.get('location_type', '')}): "
                    f"engineering={sp.get('hours_engineering', 'N/A')}u, "
                    f"PM={sp.get('hours_pm', 'N/A')}u, "
                    f"uitvoering={sp.get('hours_workprep', 'N/A')}u, "
                    f"kosten=€{sp.get('cost_total', 'N/A')}\n"
                )

        prompt = f"""Je bent een expert projectkostenraming voor ondergrondse infrastructuur in Nederland (gas/elektra netbeheer).

Projectgegevens:
- Naam: {project_context.get('name', 'Onbekend')}
- Discipline: {project_context.get('discipline', 'Onbekend')}
- Fase: {project_context.get('phase', 'VO')}
- Locatie: {project_context.get('location', 'Onbekend')}
- Beschrijving: {project_context.get('scope_description', 'Niet opgegeven')}
- Tracelengte: {project_context.get('trace_length_m', 'Onbekend')} meter
- Aantal kruisingen: {project_context.get('num_crossings', 'Onbekend')}
- Aantal vergunningen: {project_context.get('num_permits', 'Onbekend')}
- Locatietype: {project_context.get('location_type', 'urban')}
{similar_text}

Geef een gedetailleerde ureninschatting en kostenraming in JSON formaat met de volgende structuur:
{{
  "hours_engineering": <getal>,
  "hours_pm": <getal>,
  "hours_om": <getal>,
  "hours_workprep": <getal>,
  "hours_execution": <getal>,
  "cost_materials": <getal in euro>,
  "cost_total": <getal in euro>,
  "bandwidth_low": <getal in euro, -15%>,
  "bandwidth_high": <getal in euro, +25%>,
  "confidence_score": <getal 0-100>,
  "methodology": "AI + historische data" or "Regelgebaseerd",
  "reasoning": "<uitleg van de inschatting in 2-3 zinnen>"
}}

Gebruik realistische Nederlandse netbeheer tarieven:
- Engineering: €95-€115/uur
- PM: €105-€125/uur
- Omgevingsmanagement: €95-€110/uur
- Werkvoorbereiding: €85-€100/uur
- Uitvoering: afhankelijk van discipline en lengte

Geef alleen het JSON object terug, geen andere tekst."""

        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Je bent een expert in projectkostenraming voor netbeheerders in Nederland.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
                max_tokens=1000,
            )
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
        except OpenAIError as e:
            logger.warning(f"OpenAI API error: {e}")
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response: {e}")
        return None

    async def detect_risks(self, project_context: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        if not self.is_available:
            return None

        prompt = f"""Analyseer dit infrastructuurproject en identificeer de top risico's.

Project:
- Discipline: {project_context.get('discipline')}
- Locatie: {project_context.get('location')}
- Beschrijving: {project_context.get('scope_description', '')}
- Fase: {project_context.get('phase')}
- Tracelengte: {project_context.get('trace_length_m', 'onbekend')} meter

Geef een JSON array met risico's in dit formaat:
[
  {{
    "description": "<beschrijving>",
    "category": "<Technisch|Planning|Financieel|Omgeving|Vergunning|Stakeholder>",
    "probability": <1-5>,
    "impact": <1-5>,
    "mitigation_measure": "<maatregel>",
    "source": "ai"
  }}
]

Geef 3-6 relevante risico's. Alleen de JSON array, geen andere tekst."""

        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Je bent een risicoexpert voor ondergrondse infrastructuurprojecten in Nederland.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                response_format={"type": "json_object"},
                max_tokens=1500,
            )
            content = response.choices[0].message.content
            if content:
                parsed = json.loads(content)
                # Handle both {"risks": [...]} and direct array wrapped in object
                if isinstance(parsed, dict):
                    return parsed.get("risks", list(parsed.values())[0] if parsed else [])
                return parsed
        except (OpenAIError, json.JSONDecodeError) as e:
            logger.warning(f"AI risk detection error: {e}")
        return None

    async def detect_permits(self, project_context: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        if not self.is_available:
            return None

        prompt = f"""Analyseer dit infrastructuurproject en identificeer benodigde vergunningen.

Project:
- Discipline: {project_context.get('discipline')}
- Locatie: {project_context.get('location')}
- Beschrijving: {project_context.get('scope_description', '')}
- Fase: {project_context.get('phase')}

Identificeer de benodigde vergunningen. Geef een JSON object met een "permits" array:
{{
  "permits": [
    {{
      "permit_type": "<type vergunning>",
      "description": "<beschrijving>",
      "authority": "<gemeente|provincie|waterschap|prorail|rws|overig>",
      "risk_level": "<low|medium|high|critical>",
      "delay_probability": <0-100>
    }}
  ]
}}

Wees specifiek voor Nederlandse netbeheer context. Alleen het JSON object, geen andere tekst."""

        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Je bent een omgevingsmanager gespecialiseerd in Nederlandse vergunningenprocedures voor netbeheerders.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
                max_tokens=1200,
            )
            content = response.choices[0].message.content
            if content:
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    return parsed.get("permits", [])
                return parsed
        except (OpenAIError, json.JSONDecodeError) as e:
            logger.warning(f"AI permit detection error: {e}")
        return None
