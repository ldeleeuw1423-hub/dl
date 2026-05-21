import json
import math
import logging
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI, OpenAIError
from app.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMS = 1536


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

    async def generate_project_embedding(self, project_data: Dict[str, Any]) -> List[float]:
        """Generate a 1536-dim embedding for a project using OpenAI text-embedding-3-small.

        Falls back to a rule-based feature vector if OpenAI is unavailable.
        """
        if self.is_available:
            text = (
                f"discipline:{project_data.get('discipline', 'onbekend')} "
                f"locatie:{project_data.get('location_type', 'urban')} "
                f"tracé:{project_data.get('trace_length_m', 0)}m "
                f"kruisingen:{project_data.get('num_crossings', 0)} "
                f"vergunningen:{project_data.get('num_permits', 0)} "
                f"stakeholders:{project_data.get('num_stakeholders', 0)}"
            )
            try:
                response = await self.client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=text,
                )
                return response.data[0].embedding
            except OpenAIError as e:
                logger.warning(f"OpenAI embedding error, using fallback: {e}")

        return self._rule_based_embedding(project_data)

    def _rule_based_embedding(self, project_data: Dict[str, Any]) -> List[float]:
        """Return a zero-padded feature vector when OpenAI is unavailable.

        Key fields are normalised and placed in the first positions so cosine
        similarity still reflects real project similarity.
        """
        DISCIPLINE_MAP = {"Gas": 0.1, "Elektra": 0.3, "LS_MS": 0.6, "Stations": 0.9}
        LOCATION_MAP = {"rural": 0.1, "mixed": 0.5, "urban": 0.9}

        trace = float(project_data.get("trace_length_m") or 0)
        crossings = float(project_data.get("num_crossings") or 0)
        permits = float(project_data.get("num_permits") or 0)
        stakeholders = float(project_data.get("num_stakeholders") or 0)

        vec = [0.0] * EMBEDDING_DIMS
        vec[0] = DISCIPLINE_MAP.get(project_data.get("discipline", ""), 0.5)
        vec[1] = LOCATION_MAP.get(project_data.get("location_type", "urban"), 0.5)
        vec[2] = min(1.0, trace / 5000.0)
        vec[3] = min(1.0, crossings / 20.0)
        vec[4] = min(1.0, permits / 10.0)
        vec[5] = min(1.0, stakeholders / 15.0)

        # Normalise
        magnitude = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / magnitude for v in vec]

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
