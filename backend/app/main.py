import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.db.session import engine, Base, SessionLocal
from app.services.seeds import seed_database
from app.api import auth, shows, seasons, episodes, artwork, admin, catalog

# Create all tables and seed data
Base.metadata.create_all(bind=engine)
_db = SessionLocal()
try:
    seed_database(_db)
except Exception as e:
    print(f"Warning: Seed failed: {e}")
finally:
    _db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create required directories on startup."""
    os.makedirs(settings.STORAGE_PATH, exist_ok=True)
    os.makedirs(settings.CATALOGUE_DIR, exist_ok=True)
    yield


app = FastAPI(title="Peblo TV Mini API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(shows.router)
app.include_router(seasons.router)
app.include_router(episodes.router)
app.include_router(artwork.router)
app.include_router(admin.router)
app.include_router(catalog.router)


@app.get("/health")
def health():
    return {"status": "ok"}


# Serve stored artwork files
storage_path = settings.STORAGE_PATH
if os.path.exists(os.path.join(storage_path, "uploads")):
    app.mount("/storage", StaticFiles(directory=storage_path), name="storage")
