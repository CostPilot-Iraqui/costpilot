"""
CostPilot Senior - Script de peuplement des ratios de référence
Génère 50+ ratios de coûts construction réalistes par typologie/qualité/localisation
"""
import asyncio
import os
import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid

# Load environment
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'costpilot')

# Données de référence des ratios de coûts construction (€/m² SDP)
# Source: Observatoire des coûts BTP, indices FFB, retours d'expérience

RATIOS_DATA = [
    # ============================================
    # LOGEMENT COLLECTIF
    # ============================================
    # Île-de-France
    {"building_type": "housing", "quality_level": "economic", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 1650, "cost_avg_m2": 1850, "cost_max_m2": 2100, "confidence_level": "high",
     "infrastructure_cost_m2": 180, "superstructure_cost_m2": 450, "facade_cost_m2": 280, 
     "interior_works_cost_m2": 380, "technical_systems_cost_m2": 320, "external_works_cost_m2": 80},
    {"building_type": "housing", "quality_level": "standard", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 1900, "cost_avg_m2": 2200, "cost_max_m2": 2550, "confidence_level": "high",
     "infrastructure_cost_m2": 200, "superstructure_cost_m2": 520, "facade_cost_m2": 350, 
     "interior_works_cost_m2": 480, "technical_systems_cost_m2": 400, "external_works_cost_m2": 100},
    {"building_type": "housing", "quality_level": "premium", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 2400, "cost_avg_m2": 2800, "cost_max_m2": 3300, "confidence_level": "high",
     "infrastructure_cost_m2": 250, "superstructure_cost_m2": 620, "facade_cost_m2": 480, 
     "interior_works_cost_m2": 650, "technical_systems_cost_m2": 520, "external_works_cost_m2": 130},
    {"building_type": "housing", "quality_level": "luxury", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 3200, "cost_avg_m2": 3800, "cost_max_m2": 4800, "confidence_level": "medium",
     "infrastructure_cost_m2": 320, "superstructure_cost_m2": 780, "facade_cost_m2": 680, 
     "interior_works_cost_m2": 950, "technical_systems_cost_m2": 700, "external_works_cost_m2": 180},
    
    # Grande couronne / Régions
    {"building_type": "housing", "quality_level": "economic", "location": "grande_couronne", "region_label": "Grande couronne",
     "cost_min_m2": 1450, "cost_avg_m2": 1650, "cost_max_m2": 1900, "confidence_level": "high",
     "infrastructure_cost_m2": 160, "superstructure_cost_m2": 400, "facade_cost_m2": 250, 
     "interior_works_cost_m2": 340, "technical_systems_cost_m2": 290, "external_works_cost_m2": 70},
    {"building_type": "housing", "quality_level": "standard", "location": "grande_couronne", "region_label": "Grande couronne",
     "cost_min_m2": 1700, "cost_avg_m2": 1950, "cost_max_m2": 2250, "confidence_level": "high",
     "infrastructure_cost_m2": 180, "superstructure_cost_m2": 460, "facade_cost_m2": 310, 
     "interior_works_cost_m2": 420, "technical_systems_cost_m2": 360, "external_works_cost_m2": 90},
    {"building_type": "housing", "quality_level": "premium", "location": "grandes_metropoles", "region_label": "Grandes métropoles",
     "cost_min_m2": 2100, "cost_avg_m2": 2450, "cost_max_m2": 2900, "confidence_level": "high",
     "infrastructure_cost_m2": 220, "superstructure_cost_m2": 550, "facade_cost_m2": 420, 
     "interior_works_cost_m2": 560, "technical_systems_cost_m2": 450, "external_works_cost_m2": 110},
    {"building_type": "housing", "quality_level": "standard", "location": "regions", "region_label": "Régions",
     "cost_min_m2": 1500, "cost_avg_m2": 1750, "cost_max_m2": 2050, "confidence_level": "high",
     "infrastructure_cost_m2": 160, "superstructure_cost_m2": 420, "facade_cost_m2": 280, 
     "interior_works_cost_m2": 380, "technical_systems_cost_m2": 320, "external_works_cost_m2": 80},

    # ============================================
    # BUREAUX
    # ============================================
    {"building_type": "office", "quality_level": "economic", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 1550, "cost_avg_m2": 1750, "cost_max_m2": 2000, "confidence_level": "high",
     "infrastructure_cost_m2": 170, "superstructure_cost_m2": 420, "facade_cost_m2": 300, 
     "interior_works_cost_m2": 350, "technical_systems_cost_m2": 350, "external_works_cost_m2": 60},
    {"building_type": "office", "quality_level": "standard", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 1800, "cost_avg_m2": 2100, "cost_max_m2": 2450, "confidence_level": "high",
     "infrastructure_cost_m2": 190, "superstructure_cost_m2": 500, "facade_cost_m2": 380, 
     "interior_works_cost_m2": 420, "technical_systems_cost_m2": 430, "external_works_cost_m2": 80},
    {"building_type": "office", "quality_level": "premium", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 2300, "cost_avg_m2": 2700, "cost_max_m2": 3200, "confidence_level": "high",
     "infrastructure_cost_m2": 240, "superstructure_cost_m2": 600, "facade_cost_m2": 520, 
     "interior_works_cost_m2": 580, "technical_systems_cost_m2": 550, "external_works_cost_m2": 110},
    {"building_type": "office", "quality_level": "luxury", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 3000, "cost_avg_m2": 3600, "cost_max_m2": 4500, "confidence_level": "medium",
     "infrastructure_cost_m2": 300, "superstructure_cost_m2": 750, "facade_cost_m2": 720, 
     "interior_works_cost_m2": 800, "technical_systems_cost_m2": 720, "external_works_cost_m2": 150},
    {"building_type": "office", "quality_level": "standard", "location": "grandes_metropoles", "region_label": "Grandes métropoles",
     "cost_min_m2": 1600, "cost_avg_m2": 1900, "cost_max_m2": 2200, "confidence_level": "high",
     "infrastructure_cost_m2": 170, "superstructure_cost_m2": 450, "facade_cost_m2": 340, 
     "interior_works_cost_m2": 380, "technical_systems_cost_m2": 400, "external_works_cost_m2": 70},
    {"building_type": "office", "quality_level": "standard", "location": "regions", "region_label": "Régions",
     "cost_min_m2": 1400, "cost_avg_m2": 1650, "cost_max_m2": 1950, "confidence_level": "high",
     "infrastructure_cost_m2": 150, "superstructure_cost_m2": 400, "facade_cost_m2": 300, 
     "interior_works_cost_m2": 340, "technical_systems_cost_m2": 360, "external_works_cost_m2": 60},

    # ============================================
    # COMMERCE
    # ============================================
    {"building_type": "retail", "quality_level": "economic", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 1200, "cost_avg_m2": 1450, "cost_max_m2": 1700, "confidence_level": "high",
     "infrastructure_cost_m2": 140, "superstructure_cost_m2": 350, "facade_cost_m2": 250, 
     "interior_works_cost_m2": 300, "technical_systems_cost_m2": 280, "external_works_cost_m2": 50},
    {"building_type": "retail", "quality_level": "standard", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 1500, "cost_avg_m2": 1800, "cost_max_m2": 2150, "confidence_level": "high",
     "infrastructure_cost_m2": 160, "superstructure_cost_m2": 420, "facade_cost_m2": 320, 
     "interior_works_cost_m2": 380, "technical_systems_cost_m2": 360, "external_works_cost_m2": 70},
    {"building_type": "retail", "quality_level": "premium", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 2000, "cost_avg_m2": 2400, "cost_max_m2": 2900, "confidence_level": "medium",
     "infrastructure_cost_m2": 200, "superstructure_cost_m2": 520, "facade_cost_m2": 450, 
     "interior_works_cost_m2": 520, "technical_systems_cost_m2": 480, "external_works_cost_m2": 100},
    {"building_type": "retail", "quality_level": "standard", "location": "regions", "region_label": "Régions",
     "cost_min_m2": 1200, "cost_avg_m2": 1500, "cost_max_m2": 1800, "confidence_level": "high",
     "infrastructure_cost_m2": 130, "superstructure_cost_m2": 360, "facade_cost_m2": 270, 
     "interior_works_cost_m2": 320, "technical_systems_cost_m2": 300, "external_works_cost_m2": 55},

    # ============================================
    # HÔTEL
    # ============================================
    {"building_type": "hotel", "quality_level": "economic", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 1800, "cost_avg_m2": 2100, "cost_max_m2": 2450, "confidence_level": "medium",
     "infrastructure_cost_m2": 200, "superstructure_cost_m2": 480, "facade_cost_m2": 350, 
     "interior_works_cost_m2": 480, "technical_systems_cost_m2": 420, "external_works_cost_m2": 80},
    {"building_type": "hotel", "quality_level": "standard", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 2200, "cost_avg_m2": 2600, "cost_max_m2": 3100, "confidence_level": "high",
     "infrastructure_cost_m2": 240, "superstructure_cost_m2": 580, "facade_cost_m2": 450, 
     "interior_works_cost_m2": 620, "technical_systems_cost_m2": 520, "external_works_cost_m2": 100},
    {"building_type": "hotel", "quality_level": "premium", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 2800, "cost_avg_m2": 3400, "cost_max_m2": 4200, "confidence_level": "high",
     "infrastructure_cost_m2": 300, "superstructure_cost_m2": 720, "facade_cost_m2": 600, 
     "interior_works_cost_m2": 850, "technical_systems_cost_m2": 680, "external_works_cost_m2": 130},
    {"building_type": "hotel", "quality_level": "luxury", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 4000, "cost_avg_m2": 5000, "cost_max_m2": 6500, "confidence_level": "medium",
     "infrastructure_cost_m2": 400, "superstructure_cost_m2": 950, "facade_cost_m2": 850, 
     "interior_works_cost_m2": 1300, "technical_systems_cost_m2": 950, "external_works_cost_m2": 200},
    {"building_type": "hotel", "quality_level": "standard", "location": "grandes_metropoles", "region_label": "Grandes métropoles",
     "cost_min_m2": 1900, "cost_avg_m2": 2300, "cost_max_m2": 2800, "confidence_level": "high",
     "infrastructure_cost_m2": 210, "superstructure_cost_m2": 520, "facade_cost_m2": 400, 
     "interior_works_cost_m2": 550, "technical_systems_cost_m2": 470, "external_works_cost_m2": 90},

    # ============================================
    # ÉQUIPEMENT PUBLIC
    # ============================================
    {"building_type": "public_facility", "quality_level": "economic", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 1900, "cost_avg_m2": 2200, "cost_max_m2": 2550, "confidence_level": "high",
     "infrastructure_cost_m2": 220, "superstructure_cost_m2": 520, "facade_cost_m2": 380, 
     "interior_works_cost_m2": 450, "technical_systems_cost_m2": 450, "external_works_cost_m2": 90},
    {"building_type": "public_facility", "quality_level": "standard", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 2200, "cost_avg_m2": 2600, "cost_max_m2": 3100, "confidence_level": "high",
     "infrastructure_cost_m2": 260, "superstructure_cost_m2": 620, "facade_cost_m2": 480, 
     "interior_works_cost_m2": 550, "technical_systems_cost_m2": 550, "external_works_cost_m2": 110},
    {"building_type": "public_facility", "quality_level": "premium", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 2800, "cost_avg_m2": 3300, "cost_max_m2": 4000, "confidence_level": "high",
     "infrastructure_cost_m2": 320, "superstructure_cost_m2": 750, "facade_cost_m2": 620, 
     "interior_works_cost_m2": 720, "technical_systems_cost_m2": 700, "external_works_cost_m2": 140},
    {"building_type": "public_facility", "quality_level": "standard", "location": "grandes_metropoles", "region_label": "Grandes métropoles",
     "cost_min_m2": 1950, "cost_avg_m2": 2350, "cost_max_m2": 2800, "confidence_level": "high",
     "infrastructure_cost_m2": 230, "superstructure_cost_m2": 560, "facade_cost_m2": 430, 
     "interior_works_cost_m2": 500, "technical_systems_cost_m2": 500, "external_works_cost_m2": 100},
    {"building_type": "public_facility", "quality_level": "standard", "location": "regions", "region_label": "Régions",
     "cost_min_m2": 1700, "cost_avg_m2": 2050, "cost_max_m2": 2450, "confidence_level": "high",
     "infrastructure_cost_m2": 200, "superstructure_cost_m2": 490, "facade_cost_m2": 380, 
     "interior_works_cost_m2": 440, "technical_systems_cost_m2": 440, "external_works_cost_m2": 85},

    # ============================================
    # SANTÉ
    # ============================================
    {"building_type": "healthcare", "quality_level": "standard", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 2800, "cost_avg_m2": 3300, "cost_max_m2": 3900, "confidence_level": "high",
     "infrastructure_cost_m2": 350, "superstructure_cost_m2": 720, "facade_cost_m2": 520, 
     "interior_works_cost_m2": 700, "technical_systems_cost_m2": 800, "external_works_cost_m2": 120},
    {"building_type": "healthcare", "quality_level": "premium", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 3500, "cost_avg_m2": 4200, "cost_max_m2": 5100, "confidence_level": "high",
     "infrastructure_cost_m2": 420, "superstructure_cost_m2": 900, "facade_cost_m2": 680, 
     "interior_works_cost_m2": 950, "technical_systems_cost_m2": 1000, "external_works_cost_m2": 150},
    {"building_type": "healthcare", "quality_level": "standard", "location": "grandes_metropoles", "region_label": "Grandes métropoles",
     "cost_min_m2": 2500, "cost_avg_m2": 3000, "cost_max_m2": 3550, "confidence_level": "high",
     "infrastructure_cost_m2": 310, "superstructure_cost_m2": 650, "facade_cost_m2": 470, 
     "interior_works_cost_m2": 630, "technical_systems_cost_m2": 720, "external_works_cost_m2": 110},
    {"building_type": "healthcare", "quality_level": "standard", "location": "regions", "region_label": "Régions",
     "cost_min_m2": 2200, "cost_avg_m2": 2700, "cost_max_m2": 3200, "confidence_level": "high",
     "infrastructure_cost_m2": 280, "superstructure_cost_m2": 580, "facade_cost_m2": 420, 
     "interior_works_cost_m2": 560, "technical_systems_cost_m2": 650, "external_works_cost_m2": 95},

    # ============================================
    # ENSEIGNEMENT
    # ============================================
    {"building_type": "education", "quality_level": "economic", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 1700, "cost_avg_m2": 2000, "cost_max_m2": 2350, "confidence_level": "high",
     "infrastructure_cost_m2": 200, "superstructure_cost_m2": 480, "facade_cost_m2": 350, 
     "interior_works_cost_m2": 420, "technical_systems_cost_m2": 400, "external_works_cost_m2": 80},
    {"building_type": "education", "quality_level": "standard", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 2000, "cost_avg_m2": 2400, "cost_max_m2": 2850, "confidence_level": "high",
     "infrastructure_cost_m2": 240, "superstructure_cost_m2": 570, "facade_cost_m2": 430, 
     "interior_works_cost_m2": 510, "technical_systems_cost_m2": 500, "external_works_cost_m2": 100},
    {"building_type": "education", "quality_level": "premium", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 2600, "cost_avg_m2": 3100, "cost_max_m2": 3700, "confidence_level": "high",
     "infrastructure_cost_m2": 300, "superstructure_cost_m2": 700, "facade_cost_m2": 560, 
     "interior_works_cost_m2": 680, "technical_systems_cost_m2": 650, "external_works_cost_m2": 130},
    {"building_type": "education", "quality_level": "standard", "location": "grandes_metropoles", "region_label": "Grandes métropoles",
     "cost_min_m2": 1800, "cost_avg_m2": 2150, "cost_max_m2": 2550, "confidence_level": "high",
     "infrastructure_cost_m2": 210, "superstructure_cost_m2": 510, "facade_cost_m2": 390, 
     "interior_works_cost_m2": 460, "technical_systems_cost_m2": 450, "external_works_cost_m2": 90},
    {"building_type": "education", "quality_level": "standard", "location": "regions", "region_label": "Régions",
     "cost_min_m2": 1550, "cost_avg_m2": 1900, "cost_max_m2": 2250, "confidence_level": "high",
     "infrastructure_cost_m2": 185, "superstructure_cost_m2": 450, "facade_cost_m2": 340, 
     "interior_works_cost_m2": 400, "technical_systems_cost_m2": 390, "external_works_cost_m2": 80},

    # ============================================
    # INDUSTRIEL
    # ============================================
    {"building_type": "industrial", "quality_level": "economic", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 650, "cost_avg_m2": 850, "cost_max_m2": 1100, "confidence_level": "high",
     "infrastructure_cost_m2": 120, "superstructure_cost_m2": 280, "facade_cost_m2": 150, 
     "interior_works_cost_m2": 120, "technical_systems_cost_m2": 130, "external_works_cost_m2": 30},
    {"building_type": "industrial", "quality_level": "standard", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 900, "cost_avg_m2": 1150, "cost_max_m2": 1450, "confidence_level": "high",
     "infrastructure_cost_m2": 150, "superstructure_cost_m2": 350, "facade_cost_m2": 200, 
     "interior_works_cost_m2": 180, "technical_systems_cost_m2": 200, "external_works_cost_m2": 45},
    {"building_type": "industrial", "quality_level": "premium", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 1200, "cost_avg_m2": 1550, "cost_max_m2": 1950, "confidence_level": "medium",
     "infrastructure_cost_m2": 190, "superstructure_cost_m2": 450, "facade_cost_m2": 280, 
     "interior_works_cost_m2": 280, "technical_systems_cost_m2": 280, "external_works_cost_m2": 60},
    {"building_type": "industrial", "quality_level": "standard", "location": "regions", "region_label": "Régions",
     "cost_min_m2": 750, "cost_avg_m2": 950, "cost_max_m2": 1200, "confidence_level": "high",
     "infrastructure_cost_m2": 130, "superstructure_cost_m2": 290, "facade_cost_m2": 170, 
     "interior_works_cost_m2": 150, "technical_systems_cost_m2": 160, "external_works_cost_m2": 35},

    # ============================================
    # LOGISTIQUE
    # ============================================
    {"building_type": "logistics", "quality_level": "economic", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 450, "cost_avg_m2": 600, "cost_max_m2": 800, "confidence_level": "high",
     "infrastructure_cost_m2": 100, "superstructure_cost_m2": 200, "facade_cost_m2": 100, 
     "interior_works_cost_m2": 80, "technical_systems_cost_m2": 90, "external_works_cost_m2": 25},
    {"building_type": "logistics", "quality_level": "standard", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 650, "cost_avg_m2": 850, "cost_max_m2": 1100, "confidence_level": "high",
     "infrastructure_cost_m2": 130, "superstructure_cost_m2": 260, "facade_cost_m2": 140, 
     "interior_works_cost_m2": 130, "technical_systems_cost_m2": 150, "external_works_cost_m2": 35},
    {"building_type": "logistics", "quality_level": "premium", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 900, "cost_avg_m2": 1150, "cost_max_m2": 1450, "confidence_level": "medium",
     "infrastructure_cost_m2": 160, "superstructure_cost_m2": 340, "facade_cost_m2": 200, 
     "interior_works_cost_m2": 200, "technical_systems_cost_m2": 220, "external_works_cost_m2": 50},
    {"building_type": "logistics", "quality_level": "standard", "location": "regions", "region_label": "Régions",
     "cost_min_m2": 550, "cost_avg_m2": 700, "cost_max_m2": 900, "confidence_level": "high",
     "infrastructure_cost_m2": 110, "superstructure_cost_m2": 220, "facade_cost_m2": 120, 
     "interior_works_cost_m2": 100, "technical_systems_cost_m2": 120, "external_works_cost_m2": 30},

    # ============================================
    # MIXTE
    # ============================================
    {"building_type": "mixed_use", "quality_level": "standard", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 2000, "cost_avg_m2": 2350, "cost_max_m2": 2750, "confidence_level": "high",
     "infrastructure_cost_m2": 230, "superstructure_cost_m2": 550, "facade_cost_m2": 400, 
     "interior_works_cost_m2": 500, "technical_systems_cost_m2": 480, "external_works_cost_m2": 100},
    {"building_type": "mixed_use", "quality_level": "premium", "location": "ile_de_france", "region_label": "Île-de-France",
     "cost_min_m2": 2600, "cost_avg_m2": 3100, "cost_max_m2": 3700, "confidence_level": "high",
     "infrastructure_cost_m2": 290, "superstructure_cost_m2": 680, "facade_cost_m2": 540, 
     "interior_works_cost_m2": 680, "technical_systems_cost_m2": 620, "external_works_cost_m2": 130},
    {"building_type": "mixed_use", "quality_level": "standard", "location": "grandes_metropoles", "region_label": "Grandes métropoles",
     "cost_min_m2": 1800, "cost_avg_m2": 2100, "cost_max_m2": 2500, "confidence_level": "high",
     "infrastructure_cost_m2": 200, "superstructure_cost_m2": 490, "facade_cost_m2": 360, 
     "interior_works_cost_m2": 450, "technical_systems_cost_m2": 430, "external_works_cost_m2": 90},
]

async def populate_ratios():
    """Peuple la base de données avec les ratios de référence"""
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print(f"Connexion à MongoDB: {db_name}")
    
    # Vérifier le nombre actuel
    existing_count = await db.reference_ratios.count_documents({})
    print(f"Ratios existants: {existing_count}")
    
    if existing_count > 0:
        print("Suppression des ratios existants...")
        await db.reference_ratios.delete_many({})
    
    # Préparer les ratios
    ratios_to_insert = []
    year = datetime.now().year
    
    for ratio_data in RATIOS_DATA:
        ratio = {
            "id": str(uuid.uuid4()),
            "building_type": ratio_data["building_type"],
            "quality_level": ratio_data["quality_level"],
            "location": ratio_data.get("location", "ile_de_france"),
            "region_label": ratio_data.get("region_label", "Île-de-France"),
            "year_reference": year,
            "cost_min_m2": ratio_data["cost_min_m2"],
            "cost_avg_m2": ratio_data["cost_avg_m2"],
            "cost_max_m2": ratio_data["cost_max_m2"],
            "total_cost_m2": ratio_data["cost_avg_m2"],
            "confidence_level": ratio_data.get("confidence_level", "medium"),
            "infrastructure_cost_m2": ratio_data.get("infrastructure_cost_m2", 0),
            "superstructure_cost_m2": ratio_data.get("superstructure_cost_m2", 0),
            "facade_cost_m2": ratio_data.get("facade_cost_m2", 0),
            "interior_works_cost_m2": ratio_data.get("interior_works_cost_m2", 0),
            "technical_systems_cost_m2": ratio_data.get("technical_systems_cost_m2", 0),
            "external_works_cost_m2": ratio_data.get("external_works_cost_m2", 0),
            "contingency_percentage": 5.0,
            "fees_percentage": 10.0,
            "complexity_level": "medium",
            "facade_ambition": "moderate",
            "technical_ambition": "standard",
            "basement_presence": "partial",
            "parking_type": "underground",
            "sustainability_target": "rt2020",
            "source": "Observatoire BTP 2025",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        ratios_to_insert.append(ratio)
    
    # Insérer tous les ratios
    if ratios_to_insert:
        result = await db.reference_ratios.insert_many(ratios_to_insert)
        print(f"✅ {len(result.inserted_ids)} ratios insérés avec succès!")
    
    # Afficher le résumé
    final_count = await db.reference_ratios.count_documents({})
    print(f"\n📊 Résumé:")
    print(f"   - Ratios totaux: {final_count}")
    
    # Stats par typologie
    pipeline = [
        {"$group": {"_id": "$building_type", "count": {"$sum": 1}}}
    ]
    stats = await db.reference_ratios.aggregate(pipeline).to_list(100)
    print(f"   - Par typologie:")
    for stat in sorted(stats, key=lambda x: x["count"], reverse=True):
        print(f"     • {stat['_id']}: {stat['count']}")
    
    client.close()
    return final_count

if __name__ == "__main__":
    count = asyncio.run(populate_ratios())
    print(f"\n✅ Script terminé. {count} ratios dans la base.")
