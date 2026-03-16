# /app/backend/utils/database.py
# Configuration de la base de données MongoDB

import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# Connexion MongoDB
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Collections disponibles
users_collection = db.users
projects_collection = db.projects
macro_categories_collection = db.macro_categories
micro_items_collection = db.micro_items
pricing_entries_collection = db.pricing_entries
reference_ratios_collection = db.reference_ratios
scenarios_collection = db.scenarios
arbitrations_collection = db.arbitrations
alerts_collection = db.alerts
tasks_collection = db.tasks
workflow_stages_collection = db.workflow_stages
comments_collection = db.comments
feasibility_analyses_collection = db.feasibility_analyses
plan_analyses_collection = db.plan_analyses
dpgf_collection = db.dpgf
cost_optimizations_collection = db.cost_optimizations

# Nouvelles collections pour les modules avancés
senior_economist_collection = db.senior_economist
benchmarks_collection = db.benchmarks
market_intelligence_collection = db.market_intelligence
cost_predictions_collection = db.cost_predictions
design_optimizations_collection = db.design_optimizations
quantity_takeoffs_collection = db.quantity_takeoffs
multi_scenarios_collection = db.multi_scenarios

async def get_user_by_token(token: str) -> dict:
    """Récupère un utilisateur par son token"""
    from .helpers import decode_token
    payload = decode_token(token)
    user = await users_collection.find_one({"id": payload["user_id"]}, {"_id": 0})
    return user

async def shutdown_db_client():
    """Ferme la connexion à la base de données"""
    client.close()
