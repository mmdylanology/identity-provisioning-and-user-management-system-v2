from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, users, roles, groups

app = FastAPI(
    title="IAM Admin Portal API",
    version="2.0.0",
    description="REST API for Keycloak Identity and Access Management"
)

# CORS configuration for separate frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",  # Frontend on port 3001
        "http://localhost:3000",  # React/Vite dev server
        "http://localhost:5173",  # Alternative Vite port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}

# Include API routers
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1", tags=["Users"])
app.include_router(roles.router, prefix="/api/v1", tags=["Roles"])
app.include_router(groups.router, prefix="/api/v1", tags=["Groups"])
