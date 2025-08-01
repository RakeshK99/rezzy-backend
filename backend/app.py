from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
router = APIRouter()

# Allow CORS from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dummy user plan storage
user_plans = {
    "user_123": "premium",
    "user_456": "free",
}

@router.get("/api/get-plan")
def get_user_plan(user_id: str):
    plan = user_plans.get(user_id, "free")
    return {"plan": plan}

app.include_router(router)
