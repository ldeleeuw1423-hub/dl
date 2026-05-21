from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict, List
import httpx

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.gis_service import GISService

router = APIRouter()

PDOK_BASE_URL = "https://service.pdok.nl"


@router.get("/layers")
def get_available_layers(current_user: User = Depends(get_current_user)):
    return {
        "layers": [
            {
                "id": "bgt",
                "name": "BGT - Basisregistratie Grootschalige Topografie",
                "url": f"{PDOK_BASE_URL}/lv/bgt/wms/v1_0",
                "type": "WMS",
                "layers": ["BGT"],
            },
            {
                "id": "bag",
                "name": "BAG - Basisregistratie Adressen en Gebouwen",
                "url": f"{PDOK_BASE_URL}/lv/bag/wms/v2_0",
                "type": "WMS",
                "layers": ["pand", "ligplaats", "standplaats"],
            },
            {
                "id": "ahn",
                "name": "AHN - Actueel Hoogtebestand Nederland",
                "url": f"{PDOK_BASE_URL}/rws/ahn/wms/v1_0",
                "type": "WMS",
                "layers": ["dtm_05m"],
            },
            {
                "id": "bestuurlijkegrenzen",
                "name": "Bestuurlijke Grenzen",
                "url": f"{PDOK_BASE_URL}/kadaster/bestuurlijkegrenzen/wms/v1_0",
                "type": "WMS",
                "layers": ["gemeenten", "provincies"],
            },
            {
                "id": "natura2000",
                "name": "Natura 2000 gebieden",
                "url": "https://geodata.nationaalgeoregister.nl/natura2000/wms",
                "type": "WMS",
                "layers": ["natura2000"],
            },
        ]
    }


@router.post("/analyze")
def analyze_area(
    body: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    geometry = body.get("geometry")
    if not geometry:
        raise HTTPException(status_code=400, detail="geometry is required")
    service = GISService(db)
    analysis = service.analyze_geometry(geometry)
    return analysis


@router.get("/pdok/{layer_id}")
async def proxy_pdok_layer(
    layer_id: str,
    current_user: User = Depends(get_current_user),
):
    layer_map = {
        "bgt": f"{PDOK_BASE_URL}/lv/bgt/wms/v1_0?service=WMS&request=GetCapabilities",
        "bag": f"{PDOK_BASE_URL}/lv/bag/wms/v2_0?service=WMS&request=GetCapabilities",
    }
    url = layer_map.get(layer_id)
    if not url:
        raise HTTPException(status_code=404, detail=f"Layer {layer_id} not found")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url)
            return {"status": resp.status_code, "content_type": resp.headers.get("content-type")}
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"PDOK service unavailable: {str(e)}")
