# /app/backend/services/cctp_generator.py
# Service de génération automatique de CCTP avec IA

import sys
import os
import io
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

sys.path.insert(0, '/app/backend')
from utils.database import db
from utils.helpers import generate_uuid, now_iso

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

from dotenv import load_dotenv
load_dotenv()

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# Prompt système pour la génération CCTP
CCTP_AI_PROMPT = """Tu es un expert en rédaction de CCTP (Cahier des Clauses Techniques Particulières) pour les projets de construction en France.

Tu dois générer des prescriptions techniques professionnelles et normatives pour chaque lot, adaptées au projet.

Pour chaque lot, fournis:
1. Prescriptions générales (3-5 points)
2. Prescriptions techniques détaillées (5-10 points avec références normatives)
3. Contrôles et réceptions (3-5 points)

Les prescriptions doivent être:
- Conformes aux DTU et normes françaises/européennes en vigueur
- Adaptées au type de structure, façade et qualité demandés
- Professionnelles et utilisables en consultation d'entreprises

Réponds UNIQUEMENT en JSON valide."""


# Structure des lots CCTP
CCTP_LOTS = {
    "01": {
        "name": "Installation de chantier",
        "description": "Installations provisoires, clôtures, signalisation, branchements"
    },
    "02": {
        "name": "Terrassement - Fondations",
        "description": "Fouilles, remblais, évacuation des terres, fondations"
    },
    "03": {
        "name": "Gros œuvre - Structure",
        "description": "Infrastructure, superstructure, béton armé, maçonnerie"
    },
    "04": {
        "name": "Charpente - Couverture",
        "description": "Structure de toiture, couverture, étanchéité"
    },
    "05": {
        "name": "Façades - Ravalement",
        "description": "Revêtements extérieurs, isolation, enduits"
    },
    "06": {
        "name": "Menuiseries extérieures",
        "description": "Fenêtres, portes, fermetures, stores"
    },
    "07": {
        "name": "Cloisons - Doublages",
        "description": "Cloisonnement, doublages, isolation intérieure"
    },
    "08": {
        "name": "Menuiseries intérieures",
        "description": "Portes intérieures, placards, agencement"
    },
    "09": {
        "name": "Revêtements de sols",
        "description": "Carrelage, parquet, moquette, résine"
    },
    "10": {
        "name": "Peinture - Finitions",
        "description": "Peintures, papiers peints, revêtements muraux"
    },
    "11": {
        "name": "Plomberie - Sanitaires",
        "description": "Distribution eau, évacuations, appareils sanitaires"
    },
    "12": {
        "name": "Chauffage - Ventilation - Climatisation",
        "description": "Production et distribution de chaleur/froid, ventilation"
    },
    "13": {
        "name": "Électricité - Courants forts",
        "description": "Distribution électrique, éclairage, prises"
    },
    "14": {
        "name": "Électricité - Courants faibles",
        "description": "Réseaux informatiques, téléphonie, vidéosurveillance"
    },
    "15": {
        "name": "Ascenseurs",
        "description": "Ascenseurs, monte-charges, élévateurs"
    },
    "16": {
        "name": "VRD - Espaces extérieurs",
        "description": "Voiries, réseaux divers, aménagements paysagers"
    }
}


# Clauses types par lot et système
CCTP_CLAUSES = {
    "structure": {
        "concrete": [
            "Les bétons seront conformes à la norme NF EN 206-1.",
            "Classe d'exposition XC1 pour les parties intérieures, XC3/XC4 pour les parties extérieures.",
            "Résistance minimale C25/30 pour les voiles et poteaux, C30/37 pour les poutres.",
            "Enrobage des armatures conforme à l'Eurocode 2.",
            "Cure du béton obligatoire par produit de cure ou bâche polyane.",
            "Tolérance dimensionnelle conforme au DTU 21."
        ],
        "steel": [
            "Acier de construction conforme à la norme NF EN 10025.",
            "Nuance S275JR minimum, S355JR pour éléments fortement sollicités.",
            "Assemblages boulonnés classe 8.8 minimum.",
            "Protection anticorrosion classe C3 minimum selon NF EN ISO 12944.",
            "Soudures conformes à la norme NF EN 1090-2.",
            "Contrôle visuel et ressuage sur soudures principales."
        ],
        "timber": [
            "Bois de structure conforme à la norme NF EN 14081.",
            "Classe de résistance C24 minimum pour éléments porteurs.",
            "Traitement classe 2 minimum, classe 3 pour éléments extérieurs.",
            "Assemblages métalliques en acier inoxydable ou galvanisé.",
            "Humidité du bois inférieure à 18% à la pose.",
            "CLT conforme à la norme NF EN 16351."
        ]
    },
    "facade": {
        "brick": [
            "Briques de parement conformes à la norme NF EN 771-1.",
            "Absorption d'eau inférieure à 6%.",
            "Joints au mortier bâtard M5, épaisseur 10-12mm.",
            "Mise en œuvre conforme au DTU 20.1.",
            "Chanfreins et appuis conformes aux règles de l'art."
        ],
        "render": [
            "Enduit monocouche conforme à la norme NF EN 998-1.",
            "Application sur support conforme au DTU 26.1.",
            "Épaisseur minimale 15mm.",
            "Finition talochée ou grattée selon prescriptions.",
            "Traitement des points singuliers avec profils adaptés."
        ],
        "curtain_wall": [
            "Mur rideau conforme à la norme NF EN 13830.",
            "Classement AEV selon le site et l'exposition.",
            "Vitrage isolant double 6/16/6 minimum, Ug ≤ 1.1 W/m²K.",
            "Profilés aluminium à rupture de pont thermique.",
            "Coefficient Ucw ≤ 1.8 W/m²K.",
            "Garde-corps intégrés conformes à la NF P01-012."
        ]
    },
    "cvc": {
        "standard": [
            "Installation conforme au DTU 68.3 et au code de la construction.",
            "Dimensionnement selon RT 2012/RE 2020.",
            "VMC double flux avec échangeur haut rendement (>85%).",
            "Régulation centralisée avec programmation hebdomadaire.",
            "Équilibrage des réseaux avec procès-verbal.",
            "Calorifugeage des réseaux selon classe 3."
        ]
    },
    "electricite": {
        "standard": [
            "Installation conforme à la norme NF C 15-100.",
            "Tableau électrique avec protection différentielle 30mA.",
            "Éclairage LED, efficacité lumineuse >100 lm/W.",
            "Détection de présence dans circulations.",
            "GTL conforme aux prescriptions.",
            "Parafoudre selon le niveau kéraunique."
        ]
    }
}


def get_cctp_clauses(lot_code: str, system_type: str) -> List[str]:
    """Récupère les clauses CCTP pour un lot et un système"""
    
    lot_clauses = {
        "03": CCTP_CLAUSES.get("structure", {}),
        "05": CCTP_CLAUSES.get("facade", {}),
        "12": CCTP_CLAUSES.get("cvc", {}),
        "13": CCTP_CLAUSES.get("electricite", {})
    }
    
    if lot_code in lot_clauses:
        category = lot_clauses[lot_code]
        return category.get(system_type, category.get("standard", []))
    
    return []


async def generate_ai_prescriptions(
    lot_code: str,
    lot_name: str,
    structure_type: str,
    facade_type: str,
    quality_level: str,
    project_type: str
) -> Dict:
    """Génère des prescriptions CCTP avec l'IA"""
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"cctp_{generate_uuid()[:8]}",
            system_message=CCTP_AI_PROMPT
        ).with_model("openai", "gpt-4o")
        
        prompt = f"""Génère les prescriptions CCTP pour le lot {lot_code} - {lot_name}.

Contexte du projet:
- Type de bâtiment: {project_type}
- Structure: {structure_type}
- Façade: {facade_type}
- Niveau de qualité: {quality_level}

Réponds en JSON:
{{
  "prescriptions_generales": ["...", "..."],
  "prescriptions_techniques": ["...", "..."],
  "controles_receptions": ["...", "..."],
  "references_normatives": ["DTU X.X", "NF EN XXXX"]
}}"""
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        # Nettoyer la réponse
        json_str = response
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]
        
        return json.loads(json_str.strip())
        
    except Exception as e:
        # Fallback vers les clauses prédéfinies
        return None


async def generate_cctp(
    project_data: Dict,
    structure_type: str = "concrete",
    facade_type: str = "render",
    selected_lots: Optional[List[str]] = None,
    use_ai: bool = True
) -> Dict:
    """Génère un CCTP complet avec option IA"""
    
    cctp_id = generate_uuid()
    now = now_iso()
    
    # Lots à inclure
    lots_to_generate = selected_lots if selected_lots else list(CCTP_LOTS.keys())
    
    project_type = project_data.get("project_usage", "housing")
    quality_level = project_data.get("quality_level", "standard")
    
    # Construire le CCTP
    cctp_content = {
        "id": cctp_id,
        "project": {
            "name": project_data.get("project_name", "Projet"),
            "client": project_data.get("client_name", "Maître d'ouvrage"),
            "location": project_data.get("location", ""),
            "surface_m2": project_data.get("target_surface_m2", 0)
        },
        "general_clauses": {
            "object": f"Le présent CCTP définit les prescriptions techniques pour la réalisation du projet {project_data.get('project_name', '')}.",
            "normative_references": [
                "DTU applicables selon la nature des travaux",
                "Normes NF EN en vigueur",
                "Règles professionnelles RAGE",
                "RT 2012 / RE 2020 selon date de permis",
                "Code de la construction et de l'habitation"
            ],
            "quality_requirements": [
                "Tous les matériaux seront neufs et de première qualité",
                "Les ouvrages seront réalisés selon les règles de l'art",
                "L'entrepreneur est réputé connaître les lieux et les contraintes du site",
                "Tout matériau ou procédé non conforme sera refusé"
            ]
        },
        "lots": [],
        "ai_generated": use_ai,
        "generated_at": now
    }
    
    # Lots prioritaires pour génération IA (les plus techniques)
    priority_lots = {"03", "05", "06", "11", "12", "13"}
    
    # Générer chaque lot
    for lot_code in lots_to_generate:
        if lot_code not in CCTP_LOTS:
            continue
            
        lot_info = CCTP_LOTS[lot_code]
        
        # Utiliser l'IA seulement pour les lots prioritaires (éviter timeout)
        should_use_ai = use_ai and lot_code in priority_lots
        
        ai_prescriptions = None
        if should_use_ai:
            ai_prescriptions = await generate_ai_prescriptions(
                lot_code, lot_info["name"],
                structure_type, facade_type,
                quality_level, project_type
            )
        
        if ai_prescriptions:
            lot_content = {
                "code": lot_code,
                "name": lot_info["name"],
                "description": lot_info["description"],
                "prescriptions_generales": ai_prescriptions.get("prescriptions_generales", []),
                "prescriptions_techniques": ai_prescriptions.get("prescriptions_techniques", []),
                "controles_receptions": ai_prescriptions.get("controles_receptions", []),
                "references_normatives": ai_prescriptions.get("references_normatives", []),
                "ai_generated": True
            }
        else:
            # Fallback vers les clauses prédéfinies
            specific_clauses = []
            if lot_code == "03":
                specific_clauses = get_cctp_clauses("03", structure_type)
            elif lot_code == "05":
                specific_clauses = get_cctp_clauses("05", facade_type)
            elif lot_code in ["12", "13"]:
                specific_clauses = get_cctp_clauses(lot_code, "standard")
            
            lot_content = {
                "code": lot_code,
                "name": lot_info["name"],
                "description": lot_info["description"],
                "prescriptions_generales": [
                    f"Les travaux du lot {lot_code} - {lot_info['name']} comprennent l'ensemble des fournitures et mises en œuvre.",
                    "L'entrepreneur devra la coordination avec les autres lots.",
                    "Tous les travaux seront réalisés conformément aux DTU en vigueur."
                ],
                "prescriptions_techniques": specific_clauses if specific_clauses else [
                    "Matériaux conformes aux normes en vigueur",
                    "Mise en œuvre selon les règles de l'art",
                    "Essais et contrôles à la charge de l'entrepreneur"
                ],
                "controles_receptions": [
                    "Auto-contrôle par l'entreprise",
                    "Contrôle externe si requis par le CCAP",
                    "Réception avec procès-verbal contradictoire"
                ],
                "ai_generated": False
            }
        
        cctp_content["lots"].append(lot_content)
    
    return cctp_content


async def generate_cctp_pdf(cctp_content: Dict) -> bytes:
    """Génère le PDF du CCTP"""
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm, leftMargin=2*cm, rightMargin=2*cm)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CCTPTitle', parent=styles['Heading1'], fontSize=20, alignment=TA_CENTER, spaceAfter=30))
    styles.add(ParagraphStyle(name='LotTitle', parent=styles['Heading2'], fontSize=14, spaceBefore=20, spaceAfter=10, textColor=colors.HexColor('#1e3a5f')))
    styles.add(ParagraphStyle(name='SubTitle', parent=styles['Heading3'], fontSize=11, spaceBefore=10, spaceAfter=5))
    styles.add(ParagraphStyle(name='CCTPBody', parent=styles['Normal'], fontSize=10, alignment=TA_JUSTIFY, leading=14))
    
    elements = []
    
    # Page de titre
    elements.append(Spacer(1, 3*cm))
    elements.append(Paragraph("CAHIER DES CLAUSES TECHNIQUES PARTICULIÈRES", styles['CCTPTitle']))
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph(f"<b>{cctp_content['project']['name']}</b>", ParagraphStyle('ProjectName', parent=styles['Heading1'], fontSize=18, alignment=TA_CENTER)))
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph(f"Maître d'ouvrage: {cctp_content['project']['client']}", ParagraphStyle('Client', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER)))
    elements.append(Paragraph(f"Surface: {cctp_content['project']['surface_m2']:,.0f} m²".replace(",", " "), ParagraphStyle('Surface', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER)))
    elements.append(Spacer(1, 2*cm))
    elements.append(Paragraph(f"Date: {datetime.now().strftime('%d/%m/%Y')}", ParagraphStyle('Date', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, textColor=colors.gray)))
    elements.append(PageBreak())
    
    # Clauses générales
    elements.append(Paragraph("PRESCRIPTIONS GÉNÉRALES", styles['CCTPTitle']))
    elements.append(Paragraph("<b>Objet du marché</b>", styles['SubTitle']))
    elements.append(Paragraph(cctp_content['general_clauses']['object'], styles['CCTPBody']))
    elements.append(Spacer(1, 10))
    
    elements.append(Paragraph("<b>Références normatives</b>", styles['SubTitle']))
    for ref in cctp_content['general_clauses']['normative_references']:
        elements.append(Paragraph(f"• {ref}", styles['CCTPBody']))
    elements.append(Spacer(1, 10))
    
    elements.append(Paragraph("<b>Exigences de qualité</b>", styles['SubTitle']))
    for req in cctp_content['general_clauses']['quality_requirements']:
        elements.append(Paragraph(f"• {req}", styles['CCTPBody']))
    
    elements.append(PageBreak())
    
    # Lots
    for lot in cctp_content['lots']:
        elements.append(Paragraph(f"LOT {lot['code']} - {lot['name'].upper()}", styles['LotTitle']))
        elements.append(Paragraph(lot['description'], styles['CCTPBody']))
        elements.append(Spacer(1, 10))
        
        elements.append(Paragraph("<b>Prescriptions générales</b>", styles['SubTitle']))
        for clause in lot['prescriptions_generales']:
            elements.append(Paragraph(f"• {clause}", styles['CCTPBody']))
        elements.append(Spacer(1, 8))
        
        elements.append(Paragraph("<b>Prescriptions techniques</b>", styles['SubTitle']))
        for clause in lot['prescriptions_techniques']:
            elements.append(Paragraph(f"• {clause}", styles['CCTPBody']))
        elements.append(Spacer(1, 8))
        
        elements.append(Paragraph("<b>Contrôles et réceptions</b>", styles['SubTitle']))
        for ctrl in lot['controles_receptions']:
            elements.append(Paragraph(f"• {ctrl}", styles['CCTPBody']))
        
        elements.append(Spacer(1, 20))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


async def save_cctp(project_id: str, cctp_content: Dict) -> Dict:
    """Sauvegarde un CCTP"""
    
    record = {
        "id": cctp_content["id"],
        "project_id": project_id,
        **cctp_content,
        "saved_at": now_iso()
    }
    
    await db.cctp_documents.insert_one(record)
    record.pop("_id", None)
    
    return record
