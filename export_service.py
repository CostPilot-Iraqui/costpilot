# /app/backend/services/export_service.py
# Services d'export: Excel, Word, PDF, Rapports clients

import sys
import io
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


async def export_project_to_excel(project_id: str) -> Dict:
    """Exporte les données du projet au format Excel (CSV compatible)"""
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        return {"error": "Projet non trouvé"}
    
    # Générer un CSV
    lines = []
    
    # En-tête projet
    lines.append("RAPPORT PROJET - COSTPILOT SENIOR")
    lines.append("")
    lines.append(f"Nom du projet;{project.get('project_name', 'N/A')}")
    lines.append(f"Client;{project.get('client_name', 'N/A')}")
    lines.append(f"Surface (m²);{project.get('target_surface_m2', 0)}")
    lines.append(f"Budget (€);{project.get('target_budget', 0)}")
    lines.append(f"Type;{project.get('project_usage', 'N/A')}")
    lines.append(f"Qualité;{project.get('quality_level', 'N/A')}")
    lines.append("")
    
    # Métré si disponible
    takeoff = await db.quantity_takeoffs.find_one(
        {"project_id": project_id},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    
    if takeoff:
        lines.append("MÉTRÉ")
        lines.append("Lot;Désignation;Unité;Quantité;Prix unitaire;Total")
        for lot in takeoff.get("lots", []):
            lines.append(f"{lot['code']};{lot['name']};{lot['unit']};{lot['quantity']};{lot['unit_price']};{lot['total_cost']}")
        lines.append(f";;;;;;{takeoff.get('total_cost', 0)}")
        lines.append("")
    
    csv_content = "\n".join(lines)
    
    return {
        "filename": f"projet_{project_id[:8]}.csv",
        "content": csv_content,
        "mime_type": "text/csv"
    }


async def export_dpgf_to_excel(project_id: str) -> Dict:
    """Exporte le DPGF au format Excel (CSV compatible)"""
    
    # Récupérer le métré
    takeoff = await db.quantity_takeoffs.find_one(
        {"project_id": project_id},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    
    if not takeoff:
        return {"error": "Aucun métré disponible"}
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    
    lines = []
    lines.append("DÉCOMPOSITION DU PRIX GLOBAL ET FORFAITAIRE (DPGF)")
    lines.append(f"Projet: {project.get('project_name', 'N/A') if project else 'N/A'}")
    lines.append("")
    lines.append("N° Lot;Désignation;Unité;Quantité;Prix unitaire HT;Total HT")
    
    for lot in takeoff.get("lots", []):
        lines.append(f"{lot['code']};{lot['name']};{lot['unit']};{lot['quantity']};{lot['unit_price']};{lot['total_cost']}")
    
    lines.append("")
    lines.append(f"TOTAL HT;;;;{takeoff.get('total_cost', 0)}")
    lines.append(f"TVA 20%;;;;{takeoff.get('total_cost', 0) * 0.20}")
    lines.append(f"TOTAL TTC;;;;{takeoff.get('total_cost', 0) * 1.20}")
    
    csv_content = "\n".join(lines)
    
    return {
        "filename": f"dpgf_{project_id[:8]}.csv",
        "content": csv_content,
        "mime_type": "text/csv"
    }


async def generate_client_report_pdf(project_id: str) -> Dict:
    """Génère un rapport client professionnel en PDF"""
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        return {"error": "Projet non trouvé"}
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        alignment=TA_CENTER,
        spaceAfter=30,
        textColor=colors.HexColor('#1e3a5f')
    )
    story.append(Paragraph("RAPPORT DE SYNTHÈSE", title_style))
    story.append(Paragraph(project.get('project_name', 'Projet'), styles['Heading2']))
    story.append(Spacer(1, 1*cm))
    
    # Informations projet
    story.append(Paragraph("1. INFORMATIONS GÉNÉRALES", styles['Heading2']))
    
    info_data = [
        ["Client", project.get('client_name', 'N/A')],
        ["Surface programmée", f"{project.get('target_surface_m2', 0):,.0f} m²"],
        ["Budget objectif", f"{project.get('target_budget', 0):,.0f} €"],
        ["Type de bâtiment", project.get('project_usage', 'N/A')],
        ["Niveau de qualité", project.get('quality_level', 'N/A')],
    ]
    
    table = Table(info_data, colWidths=[6*cm, 10*cm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
    ]))
    story.append(table)
    story.append(Spacer(1, 1*cm))
    
    # Estimation
    takeoff = await db.quantity_takeoffs.find_one(
        {"project_id": project_id},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    
    if takeoff:
        story.append(Paragraph("2. SYNTHÈSE BUDGÉTAIRE", styles['Heading2']))
        
        budget_data = [
            ["Poste", "Montant HT", "%"],
        ]
        
        macro = takeoff.get("macro_lots", {})
        total = takeoff.get("total_cost", 1)
        
        budget_data.append(["Structure / Clos-couvert", f"{macro.get('structure', 0):,.0f} €", f"{macro.get('structure', 0)/total*100:.1f}%"])
        budget_data.append(["Second œuvre", f"{macro.get('second_oeuvre', 0):,.0f} €", f"{macro.get('second_oeuvre', 0)/total*100:.1f}%"])
        budget_data.append(["Lots techniques", f"{macro.get('lots_techniques', 0):,.0f} €", f"{macro.get('lots_techniques', 0)/total*100:.1f}%"])
        budget_data.append(["TOTAL HT", f"{total:,.0f} €", "100%"])
        
        budget_table = Table(budget_data, colWidths=[8*cm, 5*cm, 3*cm])
        budget_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f3f4f6')),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ]))
        story.append(budget_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Ratio
        surface = project.get("target_surface_m2", 1)
        ratio = total / surface if surface > 0 else 0
        story.append(Paragraph(f"<b>Ratio moyen: {ratio:,.0f} €/m² HT</b>", styles['Normal']))
    
    story.append(Spacer(1, 1*cm))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#9ca3af'),
        alignment=TA_CENTER
    )
    story.append(Paragraph("_" * 80, footer_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        f"Rapport généré par CostPilot Senior - {datetime.now().strftime('%d/%m/%Y')}",
        footer_style
    ))
    story.append(Paragraph(
        "Document de travail - Les montants sont donnés à titre indicatif",
        footer_style
    ))
    
    doc.build(story)
    
    return {
        "pdf_data": buffer.getvalue(),
        "filename": f"rapport_client_{project_id[:8]}.pdf",
        "file_size": buffer.tell()
    }


async def generate_technical_report_pdf(project_id: str) -> Dict:
    """Génère un rapport technique détaillé en PDF"""
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        return {"error": "Projet non trouvé"}
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=colors.HexColor('#1e3a5f')
    )
    story.append(Paragraph("RAPPORT TECHNIQUE DÉTAILLÉ", title_style))
    story.append(Paragraph(project.get('project_name', 'Projet'), styles['Heading2']))
    story.append(Spacer(1, 0.5*cm))
    
    # Métré détaillé
    takeoff = await db.quantity_takeoffs.find_one(
        {"project_id": project_id},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    
    if takeoff:
        story.append(Paragraph("DÉTAIL PAR LOT", styles['Heading2']))
        
        lot_data = [["N°", "Désignation", "U", "Qté", "PU (€)", "Total (€)"]]
        
        for lot in takeoff.get("lots", []):
            lot_data.append([
                lot['code'],
                lot['name'],
                lot['unit'],
                f"{lot['quantity']:,.1f}",
                f"{lot['unit_price']:,.0f}",
                f"{lot['total_cost']:,.0f}"
            ])
        
        lot_data.append(["", "TOTAL HT", "", "", "", f"{takeoff.get('total_cost', 0):,.0f}"])
        
        lot_table = Table(lot_data, colWidths=[1.5*cm, 6*cm, 1.5*cm, 2.5*cm, 2.5*cm, 3*cm])
        lot_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f3f4f6')),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ]))
        
        story.append(lot_table)
    
    doc.build(story)
    
    return {
        "pdf_data": buffer.getvalue(),
        "filename": f"rapport_technique_{project_id[:8]}.pdf",
        "file_size": buffer.tell()
    }


async def get_available_exports(project_id: str) -> List[Dict]:
    """Liste les exports disponibles pour un projet"""
    
    exports = [
        {
            "id": "project_csv",
            "name": "Données projet (CSV)",
            "description": "Export des données générales du projet",
            "format": "csv",
            "available": True
        },
        {
            "id": "dpgf_csv",
            "name": "DPGF (CSV)",
            "description": "Décomposition du Prix Global et Forfaitaire",
            "format": "csv",
            "available": True
        },
        {
            "id": "client_report",
            "name": "Rapport client (PDF)",
            "description": "Synthèse professionnelle pour le client",
            "format": "pdf",
            "available": True
        },
        {
            "id": "technical_report",
            "name": "Rapport technique (PDF)",
            "description": "Détail technique par lot",
            "format": "pdf",
            "available": True
        },
        {
            "id": "plan_analysis",
            "name": "Analyse de plan (PDF)",
            "description": "Rapport d'analyse IA des plans",
            "format": "pdf",
            "available": True
        }
    ]
    
    return exports
