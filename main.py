from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
import os
from dotenv import load_dotenv
from agents.tracking_agent import run as tracking_run
from agents.intelligence_agent import run as intelligence_run
from agents.strategy_agent import run as strategy_run
from agents.recommendation_agent import run as recommendation_run
from agents.prediction_agent import run as prediction_run

# Load environment variables from .env file
load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Connect to Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

@app.get("/")
def home():
    return {"message": "Backend is running ✅"}

@app.get("/competitors")
def get_competitors():
    response = supabase.table("competitors").select("*").execute()
    return response.data

@app.post("/analyze/{competitor_id}")
def analyze(competitor_id: str):

    # Step 1: Run agents
    tracking_data = tracking_run(competitor_id)
    intelligence_data = intelligence_run(tracking_data)
    strategy_data = strategy_run(intelligence_data)
    recommendation_data = recommendation_run(strategy_data)
    prediction_data = prediction_run(intelligence_data)

    # Step 2: Save to Supabase
    supabase.table("reports").insert({
        "competitor_id": competitor_id,
        "tracking_data": tracking_data,
        "intelligence_data": intelligence_data,
        "strategy_data": strategy_data,
        "recommendation_data": recommendation_data,
        "prediction_data": prediction_data
    }).execute()

    # Step 3: Return response
    return {
        "tracking": tracking_data,
        "intelligence": intelligence_data,
        "strategy": strategy_data,
        "recommendation": recommendation_data,
        "prediction": prediction_data
    }