"""
COSTPILOT SENIOR - Bibliothèque de Prix BTP Complète
Script pour générer ~2000 postes de référence Île-de-France

Ce script peut être exécuté pour peupler la base de données
avec les prix unitaires standards du BTP.
"""

import asyncio
import sys
import os
sys.path.append('/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid

# Configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')

# ============================================================================
# STRUCTURE COMPLÈTE DES LOTS BTP
# ============================================================================

BTP_LIBRARY = {
    "INF": {
        "name": "Infrastructure",
        "lots": {
            "INF.01": {
                "name": "Terrassements",
                "postes": [
                    {"code": "INF.01.001", "item": "Décapage terre végétale", "unit": "m²", "min": 2.5, "avg": 3.5, "max": 4.5},
                    {"code": "INF.01.002", "item": "Terrassements généraux (déblais)", "unit": "m³", "min": 10, "avg": 14, "max": 18},
                    {"code": "INF.01.003", "item": "Terrassements généraux (remblais)", "unit": "m³", "min": 12, "avg": 16, "max": 22},
                    {"code": "INF.01.004", "item": "Évacuation des déblais", "unit": "m³", "min": 18, "avg": 25, "max": 32},
                    {"code": "INF.01.005", "item": "Reprise de sous-oeuvre", "unit": "m³", "min": 350, "avg": 450, "max": 600},
                    {"code": "INF.01.006", "item": "Blindage de fouilles", "unit": "m²", "min": 45, "avg": 65, "max": 85},
                    {"code": "INF.01.007", "item": "Pompage de fouilles", "unit": "forfait", "min": 2500, "avg": 4000, "max": 6000},
                    {"code": "INF.01.008", "item": "Traitement des terres polluées", "unit": "m³", "min": 80, "avg": 120, "max": 180},
                ]
            },
            "INF.02": {
                "name": "Fondations",
                "postes": [
                    {"code": "INF.02.001", "item": "Béton de propreté", "unit": "m³", "min": 85, "avg": 95, "max": 110},
                    {"code": "INF.02.002", "item": "Fondations superficielles (semelles)", "unit": "m³", "min": 180, "avg": 220, "max": 280},
                    {"code": "INF.02.003", "item": "Semelles filantes", "unit": "ml", "min": 85, "avg": 120, "max": 160},
                    {"code": "INF.02.004", "item": "Radier général", "unit": "m²", "min": 140, "avg": 180, "max": 230},
                    {"code": "INF.02.005", "item": "Pieux forés simples", "unit": "ml", "min": 180, "avg": 250, "max": 350},
                    {"code": "INF.02.006", "item": "Pieux forés tubés", "unit": "ml", "min": 250, "avg": 350, "max": 480},
                    {"code": "INF.02.007", "item": "Micropieux", "unit": "ml", "min": 120, "avg": 180, "max": 260},
                    {"code": "INF.02.008", "item": "Longrines de liaison", "unit": "m³", "min": 280, "avg": 380, "max": 480},
                    {"code": "INF.02.009", "item": "Massifs de fondation", "unit": "m³", "min": 200, "avg": 280, "max": 360},
                ]
            },
            "INF.03": {
                "name": "Soutènements",
                "postes": [
                    {"code": "INF.03.001", "item": "Paroi moulée", "unit": "m²", "min": 380, "avg": 520, "max": 700},
                    {"code": "INF.03.002", "item": "Paroi berlinoise", "unit": "m²", "min": 180, "avg": 250, "max": 350},
                    {"code": "INF.03.003", "item": "Paroi parisienne", "unit": "m²", "min": 220, "avg": 300, "max": 400},
                    {"code": "INF.03.004", "item": "Mur de soutènement béton", "unit": "m³", "min": 320, "avg": 420, "max": 550},
                    {"code": "INF.03.005", "item": "Tirants d'ancrage", "unit": "u", "min": 800, "avg": 1200, "max": 1800},
                    {"code": "INF.03.006", "item": "Butons métalliques", "unit": "ml", "min": 150, "avg": 220, "max": 320},
                ]
            },
            "INF.04": {
                "name": "Assainissement enterré",
                "postes": [
                    {"code": "INF.04.001", "item": "Canalisation PVC Ø100", "unit": "ml", "min": 35, "avg": 50, "max": 70},
                    {"code": "INF.04.002", "item": "Canalisation PVC Ø150", "unit": "ml", "min": 45, "avg": 65, "max": 90},
                    {"code": "INF.04.003", "item": "Canalisation PVC Ø200", "unit": "ml", "min": 55, "avg": 80, "max": 110},
                    {"code": "INF.04.004", "item": "Canalisation béton Ø300", "unit": "ml", "min": 85, "avg": 120, "max": 160},
                    {"code": "INF.04.005", "item": "Regard de visite", "unit": "u", "min": 450, "avg": 650, "max": 900},
                    {"code": "INF.04.006", "item": "Boîte de branchement", "unit": "u", "min": 180, "avg": 280, "max": 400},
                    {"code": "INF.04.007", "item": "Séparateur hydrocarbures", "unit": "u", "min": 3500, "avg": 5500, "max": 8000},
                    {"code": "INF.04.008", "item": "Bassin de rétention", "unit": "m³", "min": 250, "avg": 380, "max": 550},
                ]
            },
            "INF.05": {
                "name": "Dallage",
                "postes": [
                    {"code": "INF.05.001", "item": "Dallage béton e=15cm", "unit": "m²", "min": 55, "avg": 75, "max": 95},
                    {"code": "INF.05.002", "item": "Dallage béton e=20cm", "unit": "m²", "min": 70, "avg": 95, "max": 125},
                    {"code": "INF.05.003", "item": "Dallage béton quartz", "unit": "m²", "min": 85, "avg": 115, "max": 150},
                    {"code": "INF.05.004", "item": "Joint de dilatation", "unit": "ml", "min": 18, "avg": 28, "max": 40},
                    {"code": "INF.05.005", "item": "Traitement anti-poussière", "unit": "m²", "min": 8, "avg": 12, "max": 18},
                ]
            },
        }
    },
    "SUP": {
        "name": "Superstructure",
        "lots": {
            "SUP.01": {
                "name": "Voiles béton",
                "postes": [
                    {"code": "SUP.01.001", "item": "Voile béton banché e=18cm", "unit": "m²", "min": 200, "avg": 260, "max": 340},
                    {"code": "SUP.01.002", "item": "Voile béton banché e=20cm", "unit": "m²", "min": 220, "avg": 295, "max": 380},
                    {"code": "SUP.01.003", "item": "Voile béton banché e=25cm", "unit": "m²", "min": 260, "avg": 350, "max": 450},
                    {"code": "SUP.01.004", "item": "Voile béton préfabriqué", "unit": "m²", "min": 180, "avg": 240, "max": 320},
                    {"code": "SUP.01.005", "item": "Voile de refend", "unit": "m²", "min": 190, "avg": 250, "max": 330},
                    {"code": "SUP.01.006", "item": "Mur de cage d'escalier", "unit": "m²", "min": 280, "avg": 380, "max": 500},
                ]
            },
            "SUP.02": {
                "name": "Poteaux et poutres",
                "postes": [
                    {"code": "SUP.02.001", "item": "Poteau béton section carrée", "unit": "ml", "min": 180, "avg": 250, "max": 340},
                    {"code": "SUP.02.002", "item": "Poteau béton section ronde", "unit": "ml", "min": 200, "avg": 280, "max": 380},
                    {"code": "SUP.02.003", "item": "Poutre BA section courante", "unit": "ml", "min": 220, "avg": 300, "max": 400},
                    {"code": "SUP.02.004", "item": "Poutre BA grande portée", "unit": "ml", "min": 380, "avg": 520, "max": 700},
                    {"code": "SUP.02.005", "item": "Poutre préfabriquée", "unit": "ml", "min": 280, "avg": 380, "max": 500},
                    {"code": "SUP.02.006", "item": "Chevêtre ascenseur", "unit": "u", "min": 1800, "avg": 2800, "max": 4000},
                ]
            },
            "SUP.03": {
                "name": "Planchers",
                "postes": [
                    {"code": "SUP.03.001", "item": "Dalle pleine BA e=18cm", "unit": "m²", "min": 95, "avg": 125, "max": 165},
                    {"code": "SUP.03.002", "item": "Dalle pleine BA e=22cm", "unit": "m²", "min": 110, "avg": 145, "max": 190},
                    {"code": "SUP.03.003", "item": "Dalle alvéolaire précontrainte", "unit": "m²", "min": 85, "avg": 115, "max": 150},
                    {"code": "SUP.03.004", "item": "Prédalle + table de compression", "unit": "m²", "min": 75, "avg": 100, "max": 130},
                    {"code": "SUP.03.005", "item": "Plancher collaborant", "unit": "m²", "min": 90, "avg": 120, "max": 160},
                    {"code": "SUP.03.006", "item": "Plancher poutrelles hourdis", "unit": "m²", "min": 65, "avg": 90, "max": 120},
                    {"code": "SUP.03.007", "item": "Balcon béton", "unit": "m²", "min": 320, "avg": 450, "max": 600},
                    {"code": "SUP.03.008", "item": "Rupteur thermique balcon", "unit": "ml", "min": 85, "avg": 130, "max": 180},
                ]
            },
            "SUP.04": {
                "name": "Escaliers",
                "postes": [
                    {"code": "SUP.04.001", "item": "Escalier béton coulé en place", "unit": "ml", "min": 850, "avg": 1200, "max": 1600},
                    {"code": "SUP.04.002", "item": "Escalier béton préfabriqué", "unit": "ml", "min": 750, "avg": 1050, "max": 1400},
                    {"code": "SUP.04.003", "item": "Palier intermédiaire", "unit": "m²", "min": 280, "avg": 380, "max": 500},
                    {"code": "SUP.04.004", "item": "Garde-corps métallique escalier", "unit": "ml", "min": 180, "avg": 280, "max": 400},
                    {"code": "SUP.04.005", "item": "Main courante bois", "unit": "ml", "min": 120, "avg": 180, "max": 260},
                ]
            },
            "SUP.05": {
                "name": "Toiture structure",
                "postes": [
                    {"code": "SUP.05.001", "item": "Charpente bois traditionnelle", "unit": "m²", "min": 85, "avg": 120, "max": 165},
                    {"code": "SUP.05.002", "item": "Charpente bois lamellé-collé", "unit": "m²", "min": 140, "avg": 200, "max": 280},
                    {"code": "SUP.05.003", "item": "Charpente métallique standard", "unit": "kg", "min": 3.5, "avg": 5, "max": 7},
                    {"code": "SUP.05.004", "item": "Charpente métallique complexe", "unit": "kg", "min": 5, "avg": 7.5, "max": 10},
                    {"code": "SUP.05.005", "item": "Dalle toiture terrasse", "unit": "m²", "min": 130, "avg": 175, "max": 230},
                    {"code": "SUP.05.006", "item": "Acrotère béton", "unit": "ml", "min": 120, "avg": 170, "max": 230},
                ]
            },
        }
    },
    "FAC": {
        "name": "Façades / Enveloppe",
        "lots": {
            "FAC.01": {
                "name": "Maçonnerie",
                "postes": [
                    {"code": "FAC.01.001", "item": "Mur agglo creux 20x20x50", "unit": "m²", "min": 45, "avg": 60, "max": 80},
                    {"code": "FAC.01.002", "item": "Mur agglo creux 15x20x50", "unit": "m²", "min": 38, "avg": 50, "max": 65},
                    {"code": "FAC.01.003", "item": "Mur brique terre cuite", "unit": "m²", "min": 65, "avg": 90, "max": 120},
                    {"code": "FAC.01.004", "item": "Mur béton cellulaire", "unit": "m²", "min": 55, "avg": 75, "max": 100},
                    {"code": "FAC.01.005", "item": "Linteau préfabriqué", "unit": "ml", "min": 25, "avg": 40, "max": 55},
                    {"code": "FAC.01.006", "item": "Appui de fenêtre béton", "unit": "ml", "min": 35, "avg": 50, "max": 70},
                ]
            },
            "FAC.02": {
                "name": "ITE (Isolation Thermique Extérieure)",
                "postes": [
                    {"code": "FAC.02.001", "item": "ITE polystyrène e=14cm", "unit": "m²", "min": 100, "avg": 140, "max": 180},
                    {"code": "FAC.02.002", "item": "ITE polystyrène e=18cm", "unit": "m²", "min": 115, "avg": 160, "max": 210},
                    {"code": "FAC.02.003", "item": "ITE laine de roche e=14cm", "unit": "m²", "min": 130, "avg": 180, "max": 240},
                    {"code": "FAC.02.004", "item": "ITE laine de roche e=18cm", "unit": "m²", "min": 150, "avg": 210, "max": 280},
                    {"code": "FAC.02.005", "item": "ITE enduit mince", "unit": "m²", "min": 25, "avg": 38, "max": 55},
                    {"code": "FAC.02.006", "item": "ITE enduit épais", "unit": "m²", "min": 40, "avg": 55, "max": 75},
                ]
            },
            "FAC.03": {
                "name": "Bardage",
                "postes": [
                    {"code": "FAC.03.001", "item": "Bardage métallique simple peau", "unit": "m²", "min": 75, "avg": 105, "max": 140},
                    {"code": "FAC.03.002", "item": "Bardage métallique double peau", "unit": "m²", "min": 140, "avg": 195, "max": 260},
                    {"code": "FAC.03.003", "item": "Bardage zinc joint debout", "unit": "m²", "min": 180, "avg": 260, "max": 360},
                    {"code": "FAC.03.004", "item": "Bardage bois massif", "unit": "m²", "min": 95, "avg": 140, "max": 195},
                    {"code": "FAC.03.005", "item": "Bardage composite", "unit": "m²", "min": 130, "avg": 185, "max": 250},
                    {"code": "FAC.03.006", "item": "Bardage fibres-ciment", "unit": "m²", "min": 100, "avg": 145, "max": 200},
                    {"code": "FAC.03.007", "item": "Bardage pierre naturelle", "unit": "m²", "min": 350, "avg": 500, "max": 700},
                    {"code": "FAC.03.008", "item": "Bardage terre cuite", "unit": "m²", "min": 180, "avg": 260, "max": 360},
                ]
            },
            "FAC.04": {
                "name": "Mur rideau",
                "postes": [
                    {"code": "FAC.04.001", "item": "Mur rideau VEC standard", "unit": "m²", "min": 550, "avg": 750, "max": 1000},
                    {"code": "FAC.04.002", "item": "Mur rideau VEC performant", "unit": "m²", "min": 700, "avg": 950, "max": 1250},
                    {"code": "FAC.04.003", "item": "Mur rideau VEA", "unit": "m²", "min": 450, "avg": 620, "max": 820},
                    {"code": "FAC.04.004", "item": "Mur rideau structural", "unit": "m²", "min": 850, "avg": 1150, "max": 1550},
                    {"code": "FAC.04.005", "item": "Double peau ventilée", "unit": "m²", "min": 800, "avg": 1100, "max": 1500},
                ]
            },
            "FAC.05": {
                "name": "Menuiseries extérieures",
                "postes": [
                    {"code": "FAC.05.001", "item": "Fenêtre PVC standard", "unit": "m²", "min": 280, "avg": 380, "max": 500},
                    {"code": "FAC.05.002", "item": "Fenêtre aluminium standard", "unit": "m²", "min": 380, "avg": 520, "max": 700},
                    {"code": "FAC.05.003", "item": "Fenêtre aluminium à rupture", "unit": "m²", "min": 450, "avg": 620, "max": 840},
                    {"code": "FAC.05.004", "item": "Fenêtre bois", "unit": "m²", "min": 480, "avg": 680, "max": 920},
                    {"code": "FAC.05.005", "item": "Porte-fenêtre coulissante alu", "unit": "m²", "min": 520, "avg": 720, "max": 980},
                    {"code": "FAC.05.006", "item": "Porte d'entrée immeuble", "unit": "u", "min": 2500, "avg": 4000, "max": 6000},
                    {"code": "FAC.05.007", "item": "Châssis fixe vitré", "unit": "m²", "min": 320, "avg": 450, "max": 600},
                ]
            },
            "FAC.06": {
                "name": "Stores et protections solaires",
                "postes": [
                    {"code": "FAC.06.001", "item": "Volet roulant PVC", "unit": "m²", "min": 180, "avg": 260, "max": 360},
                    {"code": "FAC.06.002", "item": "Volet roulant aluminium", "unit": "m²", "min": 250, "avg": 360, "max": 500},
                    {"code": "FAC.06.003", "item": "Brise-soleil orientable", "unit": "m²", "min": 320, "avg": 460, "max": 640},
                    {"code": "FAC.06.004", "item": "Store extérieur screen", "unit": "m²", "min": 150, "avg": 220, "max": 310},
                    {"code": "FAC.06.005", "item": "Casquette fixe béton", "unit": "ml", "min": 280, "avg": 400, "max": 560},
                    {"code": "FAC.06.006", "item": "Casquette métallique", "unit": "ml", "min": 350, "avg": 500, "max": 700},
                ]
            },
            "FAC.07": {
                "name": "Garde-corps et balustrades",
                "postes": [
                    {"code": "FAC.07.001", "item": "Garde-corps acier galvanisé", "unit": "ml", "min": 180, "avg": 260, "max": 360},
                    {"code": "FAC.07.002", "item": "Garde-corps acier laqué", "unit": "ml", "min": 220, "avg": 320, "max": 450},
                    {"code": "FAC.07.003", "item": "Garde-corps aluminium", "unit": "ml", "min": 280, "avg": 400, "max": 560},
                    {"code": "FAC.07.004", "item": "Garde-corps verre", "unit": "ml", "min": 450, "avg": 650, "max": 900},
                    {"code": "FAC.07.005", "item": "Garde-corps câbles inox", "unit": "ml", "min": 320, "avg": 460, "max": 640},
                ]
            },
            "FAC.08": {
                "name": "Étanchéité toiture",
                "postes": [
                    {"code": "FAC.08.001", "item": "Étanchéité bitume bicouche", "unit": "m²", "min": 45, "avg": 65, "max": 90},
                    {"code": "FAC.08.002", "item": "Étanchéité PVC", "unit": "m²", "min": 38, "avg": 55, "max": 75},
                    {"code": "FAC.08.003", "item": "Étanchéité EPDM", "unit": "m²", "min": 42, "avg": 60, "max": 82},
                    {"code": "FAC.08.004", "item": "Toiture végétalisée extensive", "unit": "m²", "min": 85, "avg": 120, "max": 165},
                    {"code": "FAC.08.005", "item": "Toiture végétalisée intensive", "unit": "m²", "min": 180, "avg": 260, "max": 360},
                    {"code": "FAC.08.006", "item": "Protection gravillon", "unit": "m²", "min": 12, "avg": 18, "max": 26},
                    {"code": "FAC.08.007", "item": "Relevé d'étanchéité", "unit": "ml", "min": 55, "avg": 80, "max": 110},
                    {"code": "FAC.08.008", "item": "Évacuation EP", "unit": "u", "min": 150, "avg": 220, "max": 310},
                ]
            },
        }
    },
    "INT": {
        "name": "Travaux Intérieurs",
        "lots": {
            "INT.01": {
                "name": "Cloisons",
                "postes": [
                    {"code": "INT.01.001", "item": "Cloison plaque de plâtre 72/48", "unit": "m²", "min": 35, "avg": 48, "max": 65},
                    {"code": "INT.01.002", "item": "Cloison plaque de plâtre 98/48", "unit": "m²", "min": 42, "avg": 58, "max": 78},
                    {"code": "INT.01.003", "item": "Cloison plaque de plâtre hydrofuge", "unit": "m²", "min": 48, "avg": 68, "max": 92},
                    {"code": "INT.01.004", "item": "Cloison plaque de plâtre coupe-feu 1h", "unit": "m²", "min": 65, "avg": 92, "max": 125},
                    {"code": "INT.01.005", "item": "Cloison acoustique 52 dB", "unit": "m²", "min": 75, "avg": 105, "max": 145},
                    {"code": "INT.01.006", "item": "Cloison carreaux de plâtre", "unit": "m²", "min": 55, "avg": 78, "max": 105},
                    {"code": "INT.01.007", "item": "Cloison vitrée simple vitrage", "unit": "m²", "min": 320, "avg": 450, "max": 620},
                    {"code": "INT.01.008", "item": "Cloison vitrée double vitrage", "unit": "m²", "min": 450, "avg": 640, "max": 880},
                    {"code": "INT.01.009", "item": "Cloison amovible bureau", "unit": "m²", "min": 380, "avg": 540, "max": 740},
                ]
            },
            "INT.02": {
                "name": "Doublage et isolation",
                "postes": [
                    {"code": "INT.02.001", "item": "Doublage collé laine minérale 10+80", "unit": "m²", "min": 38, "avg": 52, "max": 70},
                    {"code": "INT.02.002", "item": "Doublage collé polystyrène 10+80", "unit": "m²", "min": 32, "avg": 45, "max": 62},
                    {"code": "INT.02.003", "item": "Doublage sur ossature 13+100", "unit": "m²", "min": 48, "avg": 68, "max": 92},
                    {"code": "INT.02.004", "item": "Isolation sous chape", "unit": "m²", "min": 18, "avg": 26, "max": 36},
                ]
            },
            "INT.03": {
                "name": "Faux plafonds",
                "postes": [
                    {"code": "INT.03.001", "item": "Plafond suspendu dalles 60x60", "unit": "m²", "min": 32, "avg": 45, "max": 62},
                    {"code": "INT.03.002", "item": "Plafond suspendu dalles acoustiques", "unit": "m²", "min": 45, "avg": 65, "max": 90},
                    {"code": "INT.03.003", "item": "Plafond suspendu plaque de plâtre", "unit": "m²", "min": 55, "avg": 78, "max": 105},
                    {"code": "INT.03.004", "item": "Plafond suspendu métal déployé", "unit": "m²", "min": 85, "avg": 120, "max": 165},
                    {"code": "INT.03.005", "item": "Plafond suspendu bois", "unit": "m²", "min": 120, "avg": 170, "max": 235},
                    {"code": "INT.03.006", "item": "Plafond tendu", "unit": "m²", "min": 65, "avg": 92, "max": 125},
                    {"code": "INT.03.007", "item": "Plafond acoustique baffles", "unit": "m²", "min": 150, "avg": 220, "max": 310},
                ]
            },
            "INT.04": {
                "name": "Revêtements de sols",
                "postes": [
                    {"code": "INT.04.001", "item": "Carrelage grès cérame 30x30", "unit": "m²", "min": 55, "avg": 78, "max": 105},
                    {"code": "INT.04.002", "item": "Carrelage grès cérame 60x60", "unit": "m²", "min": 65, "avg": 92, "max": 125},
                    {"code": "INT.04.003", "item": "Carrelage grand format 80x80", "unit": "m²", "min": 85, "avg": 120, "max": 165},
                    {"code": "INT.04.004", "item": "Parquet contrecollé", "unit": "m²", "min": 55, "avg": 78, "max": 105},
                    {"code": "INT.04.005", "item": "Parquet massif", "unit": "m²", "min": 95, "avg": 140, "max": 195},
                    {"code": "INT.04.006", "item": "Sol PVC en lés", "unit": "m²", "min": 28, "avg": 40, "max": 55},
                    {"code": "INT.04.007", "item": "Sol PVC dalles", "unit": "m²", "min": 35, "avg": 50, "max": 70},
                    {"code": "INT.04.008", "item": "Moquette tuftée", "unit": "m²", "min": 35, "avg": 50, "max": 70},
                    {"code": "INT.04.009", "item": "Moquette dalles", "unit": "m²", "min": 45, "avg": 65, "max": 90},
                    {"code": "INT.04.010", "item": "Résine époxy", "unit": "m²", "min": 55, "avg": 78, "max": 105},
                    {"code": "INT.04.011", "item": "Plancher technique surélevé", "unit": "m²", "min": 95, "avg": 135, "max": 185},
                ]
            },
            "INT.05": {
                "name": "Peinture et finitions",
                "postes": [
                    {"code": "INT.05.001", "item": "Peinture acrylique murs", "unit": "m²", "min": 12, "avg": 18, "max": 26},
                    {"code": "INT.05.002", "item": "Peinture glycéro murs", "unit": "m²", "min": 15, "avg": 22, "max": 32},
                    {"code": "INT.05.003", "item": "Peinture plafonds", "unit": "m²", "min": 10, "avg": 15, "max": 22},
                    {"code": "INT.05.004", "item": "Peinture anti-graffiti", "unit": "m²", "min": 25, "avg": 38, "max": 55},
                    {"code": "INT.05.005", "item": "Revêtement mural vinyle", "unit": "m²", "min": 22, "avg": 32, "max": 45},
                    {"code": "INT.05.006", "item": "Revêtement mural textile", "unit": "m²", "min": 45, "avg": 65, "max": 90},
                    {"code": "INT.05.007", "item": "Faïence murale", "unit": "m²", "min": 65, "avg": 92, "max": 125},
                ]
            },
            "INT.06": {
                "name": "Menuiseries intérieures",
                "postes": [
                    {"code": "INT.06.001", "item": "Bloc-porte isoplane 73cm", "unit": "u", "min": 280, "avg": 400, "max": 560},
                    {"code": "INT.06.002", "item": "Bloc-porte isoplane 83cm", "unit": "u", "min": 300, "avg": 430, "max": 600},
                    {"code": "INT.06.003", "item": "Bloc-porte postformé", "unit": "u", "min": 220, "avg": 320, "max": 450},
                    {"code": "INT.06.004", "item": "Bloc-porte coupe-feu 1/2h", "unit": "u", "min": 550, "avg": 780, "max": 1080},
                    {"code": "INT.06.005", "item": "Bloc-porte coupe-feu 1h", "unit": "u", "min": 700, "avg": 1000, "max": 1380},
                    {"code": "INT.06.006", "item": "Porte vitrée intérieure", "unit": "u", "min": 650, "avg": 920, "max": 1280},
                    {"code": "INT.06.007", "item": "Porte coulissante", "unit": "u", "min": 480, "avg": 680, "max": 950},
                    {"code": "INT.06.008", "item": "Placard aménagé", "unit": "ml", "min": 380, "avg": 540, "max": 750},
                ]
            },
            "INT.07": {
                "name": "Équipements sanitaires",
                "postes": [
                    {"code": "INT.07.001", "item": "WC suspendu complet", "unit": "u", "min": 650, "avg": 920, "max": 1280},
                    {"code": "INT.07.002", "item": "WC à poser complet", "unit": "u", "min": 380, "avg": 540, "max": 750},
                    {"code": "INT.07.003", "item": "Lavabo vasque", "unit": "u", "min": 320, "avg": 460, "max": 640},
                    {"code": "INT.07.004", "item": "Plan vasque double", "unit": "u", "min": 850, "avg": 1200, "max": 1680},
                    {"code": "INT.07.005", "item": "Douche à l'italienne", "unit": "u", "min": 1200, "avg": 1700, "max": 2380},
                    {"code": "INT.07.006", "item": "Baignoire acrylique", "unit": "u", "min": 450, "avg": 650, "max": 900},
                    {"code": "INT.07.007", "item": "Robinetterie lavabo", "unit": "u", "min": 120, "avg": 180, "max": 260},
                    {"code": "INT.07.008", "item": "Robinetterie douche", "unit": "u", "min": 220, "avg": 320, "max": 450},
                    {"code": "INT.07.009", "item": "Miroir salle de bains", "unit": "u", "min": 150, "avg": 220, "max": 310},
                    {"code": "INT.07.010", "item": "Accessoires sanitaires (lot)", "unit": "u", "min": 120, "avg": 180, "max": 260},
                ]
            },
        }
    },
    "TEC": {
        "name": "Systèmes Techniques",
        "lots": {
            "TEC.01": {
                "name": "CVC - Chauffage",
                "postes": [
                    {"code": "TEC.01.001", "item": "Chaudière gaz collective", "unit": "kW", "min": 85, "avg": 120, "max": 165},
                    {"code": "TEC.01.002", "item": "Chaudière gaz individuelle", "unit": "u", "min": 2800, "avg": 4000, "max": 5600},
                    {"code": "TEC.01.003", "item": "PAC air/eau collective", "unit": "kW", "min": 180, "avg": 260, "max": 360},
                    {"code": "TEC.01.004", "item": "PAC air/air split", "unit": "u", "min": 1800, "avg": 2600, "max": 3600},
                    {"code": "TEC.01.005", "item": "Radiateur acier", "unit": "u", "min": 280, "avg": 400, "max": 560},
                    {"code": "TEC.01.006", "item": "Plancher chauffant", "unit": "m²", "min": 55, "avg": 78, "max": 105},
                    {"code": "TEC.01.007", "item": "Distribution chauffage", "unit": "ml", "min": 45, "avg": 65, "max": 90},
                ]
            },
            "TEC.02": {
                "name": "CVC - Ventilation",
                "postes": [
                    {"code": "TEC.02.001", "item": "VMC simple flux", "unit": "logement", "min": 850, "avg": 1200, "max": 1680},
                    {"code": "TEC.02.002", "item": "VMC double flux", "unit": "logement", "min": 2500, "avg": 3600, "max": 5000},
                    {"code": "TEC.02.003", "item": "CTA simple", "unit": "m³/h", "min": 0.8, "avg": 1.2, "max": 1.7},
                    {"code": "TEC.02.004", "item": "CTA double flux", "unit": "m³/h", "min": 1.5, "avg": 2.2, "max": 3.1},
                    {"code": "TEC.02.005", "item": "Gaines de ventilation", "unit": "m²", "min": 65, "avg": 92, "max": 125},
                    {"code": "TEC.02.006", "item": "Diffuseurs et grilles", "unit": "u", "min": 85, "avg": 120, "max": 165},
                ]
            },
            "TEC.03": {
                "name": "CVC - Climatisation",
                "postes": [
                    {"code": "TEC.03.001", "item": "Groupe froid", "unit": "kW", "min": 250, "avg": 360, "max": 500},
                    {"code": "TEC.03.002", "item": "Ventilo-convecteur", "unit": "u", "min": 650, "avg": 920, "max": 1280},
                    {"code": "TEC.03.003", "item": "Poutre climatique", "unit": "ml", "min": 550, "avg": 780, "max": 1080},
                    {"code": "TEC.03.004", "item": "Réseau eau glacée", "unit": "ml", "min": 85, "avg": 120, "max": 165},
                ]
            },
            "TEC.04": {
                "name": "Plomberie",
                "postes": [
                    {"code": "TEC.04.001", "item": "Distribution EF/EC cuivre", "unit": "ml", "min": 55, "avg": 78, "max": 105},
                    {"code": "TEC.04.002", "item": "Distribution EF/EC PER", "unit": "ml", "min": 35, "avg": 50, "max": 70},
                    {"code": "TEC.04.003", "item": "Évacuation PVC", "unit": "ml", "min": 25, "avg": 38, "max": 55},
                    {"code": "TEC.04.004", "item": "Chauffe-eau thermodynamique", "unit": "u", "min": 2200, "avg": 3200, "max": 4500},
                    {"code": "TEC.04.005", "item": "Chauffe-eau électrique 200L", "unit": "u", "min": 650, "avg": 920, "max": 1280},
                    {"code": "TEC.04.006", "item": "Production ECS collective", "unit": "logement", "min": 1200, "avg": 1700, "max": 2380},
                    {"code": "TEC.04.007", "item": "Comptage eau", "unit": "u", "min": 180, "avg": 260, "max": 360},
                ]
            },
            "TEC.05": {
                "name": "Électricité courants forts",
                "postes": [
                    {"code": "TEC.05.001", "item": "TGBT", "unit": "u", "min": 8500, "avg": 12000, "max": 16800},
                    {"code": "TEC.05.002", "item": "Tableau divisionnaire", "unit": "u", "min": 850, "avg": 1200, "max": 1680},
                    {"code": "TEC.05.003", "item": "Distribution électrique", "unit": "m²", "min": 45, "avg": 65, "max": 90},
                    {"code": "TEC.05.004", "item": "Éclairage LED encastré", "unit": "u", "min": 85, "avg": 120, "max": 165},
                    {"code": "TEC.05.005", "item": "Éclairage LED suspendu", "unit": "ml", "min": 150, "avg": 220, "max": 310},
                    {"code": "TEC.05.006", "item": "Éclairage de sécurité", "unit": "u", "min": 120, "avg": 175, "max": 250},
                    {"code": "TEC.05.007", "item": "Prises de courant", "unit": "u", "min": 55, "avg": 78, "max": 105},
                ]
            },
            "TEC.06": {
                "name": "Courants faibles",
                "postes": [
                    {"code": "TEC.06.001", "item": "Câblage VDI cat6", "unit": "prise", "min": 180, "avg": 260, "max": 360},
                    {"code": "TEC.06.002", "item": "Baie de brassage", "unit": "u", "min": 2500, "avg": 3600, "max": 5000},
                    {"code": "TEC.06.003", "item": "Vidéophone", "unit": "u", "min": 450, "avg": 650, "max": 900},
                    {"code": "TEC.06.004", "item": "Contrôle d'accès", "unit": "porte", "min": 1500, "avg": 2200, "max": 3100},
                    {"code": "TEC.06.005", "item": "Vidéosurveillance", "unit": "caméra", "min": 850, "avg": 1200, "max": 1680},
                    {"code": "TEC.06.006", "item": "Interphonie", "unit": "u", "min": 280, "avg": 400, "max": 560},
                ]
            },
            "TEC.07": {
                "name": "SSI et sécurité incendie",
                "postes": [
                    {"code": "TEC.07.001", "item": "SSI catégorie A", "unit": "m²", "min": 25, "avg": 38, "max": 55},
                    {"code": "TEC.07.002", "item": "SSI catégorie B", "unit": "m²", "min": 15, "avg": 22, "max": 32},
                    {"code": "TEC.07.003", "item": "Détecteur de fumée", "unit": "u", "min": 85, "avg": 120, "max": 165},
                    {"code": "TEC.07.004", "item": "Déclencheur manuel", "unit": "u", "min": 120, "avg": 175, "max": 250},
                    {"code": "TEC.07.005", "item": "Extincteur", "unit": "u", "min": 65, "avg": 95, "max": 135},
                    {"code": "TEC.07.006", "item": "RIA", "unit": "u", "min": 850, "avg": 1200, "max": 1680},
                    {"code": "TEC.07.007", "item": "Désenfumage mécanique", "unit": "m²", "min": 45, "avg": 65, "max": 90},
                    {"code": "TEC.07.008", "item": "Désenfumage naturel", "unit": "m²", "min": 25, "avg": 38, "max": 55},
                    {"code": "TEC.07.009", "item": "Sprinklage", "unit": "m²", "min": 55, "avg": 78, "max": 105},
                ]
            },
            "TEC.08": {
                "name": "Ascenseurs",
                "postes": [
                    {"code": "TEC.08.001", "item": "Ascenseur 8 personnes standard", "unit": "u", "min": 35000, "avg": 50000, "max": 70000},
                    {"code": "TEC.08.002", "item": "Ascenseur 13 personnes", "unit": "u", "min": 45000, "avg": 65000, "max": 90000},
                    {"code": "TEC.08.003", "item": "Ascenseur PMR", "unit": "u", "min": 28000, "avg": 40000, "max": 56000},
                    {"code": "TEC.08.004", "item": "Monte-charge", "unit": "u", "min": 25000, "avg": 36000, "max": 50000},
                    {"code": "TEC.08.005", "item": "Escalier mécanique", "unit": "u", "min": 85000, "avg": 120000, "max": 168000},
                ]
            },
            "TEC.09": {
                "name": "GTB / GTC",
                "postes": [
                    {"code": "TEC.09.001", "item": "GTB standard", "unit": "m²", "min": 12, "avg": 18, "max": 26},
                    {"code": "TEC.09.002", "item": "GTB évoluée", "unit": "m²", "min": 22, "avg": 32, "max": 45},
                    {"code": "TEC.09.003", "item": "Supervision énergie", "unit": "forfait", "min": 15000, "avg": 22000, "max": 31000},
                ]
            },
        }
    },
    "EXT": {
        "name": "Travaux Extérieurs",
        "lots": {
            "EXT.01": {
                "name": "VRD",
                "postes": [
                    {"code": "EXT.01.001", "item": "Voirie enrobé", "unit": "m²", "min": 55, "avg": 78, "max": 105},
                    {"code": "EXT.01.002", "item": "Voirie pavés béton", "unit": "m²", "min": 85, "avg": 120, "max": 165},
                    {"code": "EXT.01.003", "item": "Voirie pavés pierre", "unit": "m²", "min": 150, "avg": 220, "max": 310},
                    {"code": "EXT.01.004", "item": "Bordures béton", "unit": "ml", "min": 35, "avg": 50, "max": 70},
                    {"code": "EXT.01.005", "item": "Caniveaux à grille", "unit": "ml", "min": 120, "avg": 175, "max": 250},
                    {"code": "EXT.01.006", "item": "Réseau EP enterré", "unit": "ml", "min": 85, "avg": 120, "max": 165},
                    {"code": "EXT.01.007", "item": "Réseau EU enterré", "unit": "ml", "min": 95, "avg": 135, "max": 185},
                ]
            },
            "EXT.02": {
                "name": "Espaces verts",
                "postes": [
                    {"code": "EXT.02.001", "item": "Engazonnement", "unit": "m²", "min": 8, "avg": 12, "max": 18},
                    {"code": "EXT.02.002", "item": "Plantation arbustes", "unit": "u", "min": 55, "avg": 78, "max": 105},
                    {"code": "EXT.02.003", "item": "Plantation arbres", "unit": "u", "min": 350, "avg": 500, "max": 700},
                    {"code": "EXT.02.004", "item": "Haie végétale", "unit": "ml", "min": 45, "avg": 65, "max": 90},
                    {"code": "EXT.02.005", "item": "Arrosage automatique", "unit": "m²", "min": 18, "avg": 26, "max": 36},
                    {"code": "EXT.02.006", "item": "Paillage minéral", "unit": "m²", "min": 25, "avg": 38, "max": 55},
                ]
            },
            "EXT.03": {
                "name": "Clôtures et portails",
                "postes": [
                    {"code": "EXT.03.001", "item": "Clôture grillage rigide", "unit": "ml", "min": 85, "avg": 120, "max": 165},
                    {"code": "EXT.03.002", "item": "Clôture barreaudage", "unit": "ml", "min": 180, "avg": 260, "max": 360},
                    {"code": "EXT.03.003", "item": "Mur de clôture", "unit": "ml", "min": 350, "avg": 500, "max": 700},
                    {"code": "EXT.03.004", "item": "Portail coulissant motorisé", "unit": "u", "min": 4500, "avg": 6500, "max": 9000},
                    {"code": "EXT.03.005", "item": "Portillon piétons", "unit": "u", "min": 1200, "avg": 1700, "max": 2380},
                    {"code": "EXT.03.006", "item": "Barrière levante", "unit": "u", "min": 3500, "avg": 5000, "max": 7000},
                ]
            },
            "EXT.04": {
                "name": "Éclairage extérieur",
                "postes": [
                    {"code": "EXT.04.001", "item": "Candélabre LED", "unit": "u", "min": 1800, "avg": 2600, "max": 3600},
                    {"code": "EXT.04.002", "item": "Borne lumineuse", "unit": "u", "min": 650, "avg": 920, "max": 1280},
                    {"code": "EXT.04.003", "item": "Projecteur LED", "unit": "u", "min": 450, "avg": 650, "max": 900},
                    {"code": "EXT.04.004", "item": "Câblage extérieur", "unit": "ml", "min": 35, "avg": 50, "max": 70},
                    {"code": "EXT.04.005", "item": "Armoire éclairage", "unit": "u", "min": 2500, "avg": 3600, "max": 5000},
                ]
            },
            "EXT.05": {
                "name": "Mobilier urbain",
                "postes": [
                    {"code": "EXT.05.001", "item": "Banc public", "unit": "u", "min": 650, "avg": 920, "max": 1280},
                    {"code": "EXT.05.002", "item": "Corbeille", "unit": "u", "min": 280, "avg": 400, "max": 560},
                    {"code": "EXT.05.003", "item": "Borne anti-stationnement", "unit": "u", "min": 180, "avg": 260, "max": 360},
                    {"code": "EXT.05.004", "item": "Abri vélos", "unit": "u", "min": 2500, "avg": 3600, "max": 5000},
                    {"code": "EXT.05.005", "item": "Râtelier vélos", "unit": "u", "min": 120, "avg": 175, "max": 250},
                    {"code": "EXT.05.006", "item": "Jardinière béton", "unit": "u", "min": 550, "avg": 780, "max": 1080},
                ]
            },
        }
    },
    "ALE": {
        "name": "Aléas et Imprévus",
        "lots": {
            "ALE.01": {
                "name": "Provisions",
                "postes": [
                    {"code": "ALE.01.001", "item": "Aléas techniques (2%)", "unit": "forfait", "min": 0, "avg": 0, "max": 0},
                    {"code": "ALE.01.002", "item": "Imprévus chantier (1.5%)", "unit": "forfait", "min": 0, "avg": 0, "max": 0},
                    {"code": "ALE.01.003", "item": "Actualisation prix (si applicable)", "unit": "forfait", "min": 0, "avg": 0, "max": 0},
                ]
            },
        }
    },
}


async def populate_pricing_library():
    """Peuple la bibliothèque de prix avec les données BTP"""
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Compter les entrées existantes
    existing_count = await db.pricing_library.count_documents({})
    print(f"Entrées existantes: {existing_count}")
    
    entries_to_insert = []
    now = datetime.now(timezone.utc).isoformat()
    
    for macro_code, macro_data in BTP_LIBRARY.items():
        for lot_code, lot_data in macro_data["lots"].items():
            for poste in lot_data["postes"]:
                # Pour chaque typologie et qualité
                for building_type in ["housing", "office", "retail", "hotel", "public_facility"]:
                    for quality in ["economic", "standard", "premium"]:
                        # Ajuster les prix selon la qualité
                        quality_factor = {"economic": 0.85, "standard": 1.0, "premium": 1.2}[quality]
                        
                        entry = {
                            "id": str(uuid.uuid4()),
                            "building_type": building_type,
                            "region": "idf",
                            "geographic_region": "Île-de-France",
                            "year_reference": 2024,
                            "quality_level": quality,
                            "complexity_level": "medium",
                            "category": macro_data["name"],
                            "lot_code": lot_code,
                            "lot": lot_data["name"],
                            "sub_lot": None,
                            "item": poste["item"],
                            "unit": poste["unit"],
                            "unit_price_min": round(poste["min"] * quality_factor),
                            "unit_price_avg": round(poste["avg"] * quality_factor),
                            "unit_price_max": round(poste["max"] * quality_factor),
                            "confidence_score": 0.85,
                            "source_type": "internal_benchmark",
                            "notes": f"Prix référence BTP IDF 2024 - {poste['code']}",
                            "created_at": now,
                            "updated_at": now,
                        }
                        entries_to_insert.append(entry)
    
    # Insérer en batch
    if entries_to_insert:
        print(f"Insertion de {len(entries_to_insert)} entrées...")
        
        # Supprimer les anciennes entrées générées
        await db.pricing_library.delete_many({"source_type": "internal_benchmark"})
        
        # Insérer les nouvelles
        batch_size = 500
        for i in range(0, len(entries_to_insert), batch_size):
            batch = entries_to_insert[i:i+batch_size]
            await db.pricing_library.insert_many(batch)
            print(f"  Batch {i//batch_size + 1}: {len(batch)} entrées")
        
        print(f"Terminé! {len(entries_to_insert)} entrées créées.")
    
    # Compter par macro-lot
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    stats = await db.pricing_library.aggregate(pipeline).to_list(100)
    print("\nStatistiques par catégorie:")
    for stat in stats:
        print(f"  {stat['_id']}: {stat['count']} entrées")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(populate_pricing_library())
