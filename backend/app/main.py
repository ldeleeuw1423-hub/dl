from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import settings
from app.routers import auth, projects, estimations, risks, permits, gis, historical, files, exports, organizations

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(projects.router, prefix=f"{settings.API_V1_STR}/projects", tags=["projects"])
app.include_router(estimations.router, prefix=f"{settings.API_V1_STR}/projects", tags=["estimations"])
app.include_router(risks.router, prefix=f"{settings.API_V1_STR}/projects", tags=["risks"])
app.include_router(permits.router, prefix=f"{settings.API_V1_STR}/projects", tags=["permits"])
app.include_router(files.router, prefix=f"{settings.API_V1_STR}/projects", tags=["files"])
app.include_router(gis.router, prefix=f"{settings.API_V1_STR}/gis", tags=["gis"])
app.include_router(historical.router, prefix=f"{settings.API_V1_STR}/historical", tags=["historical"])
app.include_router(exports.router, prefix=f"{settings.API_V1_STR}/projects", tags=["exports"])
app.include_router(organizations.router, prefix=f"{settings.API_V1_STR}/organizations", tags=["organizations"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.VERSION}


@app.get("/")
async def root():
    return {"message": settings.PROJECT_NAME, "version": settings.VERSION, "docs": f"{settings.API_V1_STR}/docs"}
