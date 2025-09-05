from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.core.config import get_settings
from app.db.session import init_db
from app.routers import auth as auth_router
from app.routers import tasks as tasks_router

settings = get_settings()

app = FastAPI(
    title="Task Manager (FastAPI + Firebase + SQL)",
    version="0.1.0",
    description="A task management API written in python showing Firebase Authentication with FastAPI and SQL data storage."
)

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",")] if settings.cors_origins else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router.router)
app.include_router(tasks_router.router)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "message": "Welcome to the Task Manager API"}

# 🔑 Custom OpenAPI with Bearer Auth for Swagger
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    # Add Bearer authentication
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    # Apply it globally
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", [{"bearerAuth": []}])
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
