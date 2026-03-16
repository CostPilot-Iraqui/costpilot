# /app/backend/services/report_generator.py
# Service de génération de rapports professionnels PDF/Excel

import os
import sys
import io
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

sys.path.insert(0, '/app/backend')
from utils.database import db
from utils.helpers import generate_uuid, now_iso, DPGF_LOTS_STRUCTURE

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart


class ProfessionalReportGenerator:
    """Générateur de rapports professionnels pour l'économie de la construction"""
    
    def __init__(self, project_data: Dict):
        self.project = project_data
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Configure les styles personnalisés"""
        # Only add styles that don't already exist
        custom_styles = {
            'ReportTitle': ParagraphStyle(
                name='ReportTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                alignment=TA_CENTER,
                spaceAfter=30,
                textColor=colors.HexColor('#1e3a5f')
            ),
            'SectionTitle': ParagraphStyle(
                name='SectionTitle',
                parent=self.styles['Heading2'],
                fontSize=14,
                spaceBefore=20,
                spaceAfter=10,
                textColor=colors.HexColor('#2563eb'),
                borderPadding=5
            ),
            'SubsectionTitle': ParagraphStyle(
                name='SubsectionTitle',
                parent=self.styles['Heading3'],
                fontSize=12,
                spaceBefore=15,
                spaceAfter=8,
                textColor=colors.HexColor('#334155')
            ),
            'ReportBodyText': ParagraphStyle(
                name='ReportBodyText',
                parent=self.styles['Normal'],
                fontSize=10,
                leading=14,
                spaceBefore=5,
                spaceAfter=5
            ),
            'TableHeader': ParagraphStyle(
                name='TableHeader',
                parent=self.styles['Normal'],
                fontSize=9,
                alignment=TA_CENTER,
                textColor=colors.white
            ),
            'FooterText': ParagraphStyle(
                name='FooterText',
                parent=self.styles['Normal'],
                fontSize=8,
                textColor=colors.gray,
                alignment=TA_CENTER
            ),
            'HighlightBox': ParagraphStyle(
                name='HighlightBox',
                parent=self.styles['Normal'],
                fontSize=11,
                backColor=colors.HexColor('#f0f9ff'),
                borderPadding=10
            )
        }
        
        for name, style in custom_styles.items():
            try:
                self.styles.add(style)
            except KeyError:
                pass  # Style already exists
        
        # Alias for BodyText
        self.body_style = custom_styles.get('ReportBodyText') or self.styles['Normal']
    
    def _get_body_style(self):
        """Returns the body text style"""
        try:
            return self.styles['ReportBodyText']
        except KeyError:
            return self.styles['Normal']
    
    def _format_currency(self, amount: float) -> str:
        """Formate un montant en euros"""
        if amount is None:
            return "N/A"
        return f"{amount:,.2f} €".replace(",", " ").replace(".", ",")
    
    def _format_surface(self, surface: float) -> str:
        """Formate une surface en m²"""
        if surface is None:
            return "N/A"
        return f"{surface:,.2f} m²".replace(",", " ").replace(".", ",")
    
    def _create_cover_page(self, elements: List):
        """Crée la page de couverture"""
        elements.append(Spacer(1, 3*cm))
        
        # Logo placeholder
        elements.append(Paragraph("COSTPILOT SENIOR", self.styles['ReportTitle']))
        elements.append(Spacer(1, 1*cm))
        
        elements.append(Paragraph("RAPPORT D'ÉCONOMIE DE LA CONSTRUCTION", self.styles['SectionTitle']))
        elements.append(Spacer(1, 2*cm))
        
        # Project name
        elements.append(Paragraph(
            f"<b>{self.project.get('project_name', 'Projet')}</b>",
            ParagraphStyle('ProjectName', parent=self.styles['Heading1'], fontSize=28, alignment=TA_CENTER)
        ))
        elements.append(Spacer(1, 1*cm))
        
        # Client
        elements.append(Paragraph(
            f"Client: {self.project.get('client_name', 'N/A')}",
            ParagraphStyle('ClientName', parent=self.styles['Normal'], fontSize=14, alignment=TA_CENTER)
        ))
        elements.append(Spacer(1, 3*cm))
        
        # Date
        elements.append(Paragraph(
            f"Date d'édition: {datetime.now().strftime('%d/%m/%Y')}",
            ParagraphStyle('Date', parent=self.styles['Normal'], fontSize=12, alignment=TA_CENTER, textColor=colors.gray)
        ))
        
        elements.append(PageBreak())
    
    def _create_header(self, elements: List):
        """Crée l'en-tête du rapport"""
        elements.append(Paragraph("SYNTHÈSE DU PROJET", self.styles['ReportTitle']))
        elements.append(Spacer(1, 10))
        
        # Informations projet
        project_info = [
            ["Projet:", self.project.get('project_name', 'N/A')],
            ["Client:", self.project.get('client_name', 'N/A')],
            ["Localisation:", self.project.get('location', 'N/A')],
            ["Typologie:", self.project.get('project_usage', 'N/A').replace('_', ' ').title()],
            ["Surface cible:", self._format_surface(self.project.get('target_surface_m2', 0))],
            ["Niveau de qualité:", self.project.get('quality_level', 'standard').title()],
            ["Date:", datetime.now().strftime("%d/%m/%Y")]
        ]
        
        table = Table(project_info, colWidths=[120, 320])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 30))
    
    def _create_executive_summary(self, elements: List, analyses: Dict):
        """Crée le résumé exécutif"""
        elements.append(Paragraph("1. RÉSUMÉ EXÉCUTIF", self.styles['SectionTitle']))
        
        budget = self.project.get('target_budget', 0) or 0
        surface = self.project.get('target_surface_m2', 1) or 1
        cost_m2 = budget / surface if surface > 0 else 0
        
        # Box de synthèse
        summary_data = [
            ["BUDGET PRÉVISIONNEL", self._format_currency(budget)],
            ["SURFACE TOTALE", self._format_surface(surface)],
            ["COÛT AU M²", f"{self._format_currency(cost_m2)}/m²"],
        ]
        
        t = Table(summary_data, colWidths=[220, 220])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1e3a5f')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('GRID', (0, 0), (-1, -1), 2, colors.HexColor('#3b82f6')),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 20))
        
        # Texte de synthèse
        summary_text = f"""
        Ce rapport présente l'analyse économique complète du projet <b>{self.project.get('project_name', 'N/A')}</b>.
        Le projet prévoit une surface de <b>{self._format_surface(surface)}</b> avec un budget cible de 
        <b>{self._format_currency(budget)}</b>, soit un ratio de <b>{self._format_currency(cost_m2)}/m²</b>.
        """
        elements.append(Paragraph(summary_text, self._get_body_style()))
        elements.append(Spacer(1, 15))
    
    def _create_cost_analysis_section(self, elements: List, cost_data: Optional[Dict]):
        """Crée la section d'analyse des coûts"""
        elements.append(Paragraph("2. ANALYSE DES COÛTS", self.styles['SectionTitle']))
        
        if cost_data:
            elements.append(Paragraph("2.1 Estimation prévisionnelle", self.styles['SubsectionTitle']))
            
            cost_table_data = [
                ["Scénario", "Coût total", "Coût/m²", "Variation"],
                ["Estimation basse", self._format_currency(cost_data.get('predicted_cost_min', 0)), 
                 self._format_currency(cost_data.get('predicted_cost_m2_min', 0)), "-10%"],
                ["Estimation centrale", self._format_currency(cost_data.get('predicted_cost_avg', 0)), 
                 self._format_currency(cost_data.get('predicted_cost_m2_avg', 0)), "Réf."],
                ["Estimation haute", self._format_currency(cost_data.get('predicted_cost_max', 0)), 
                 self._format_currency(cost_data.get('predicted_cost_m2_max', 0)), "+12%"],
            ]
            
            table = Table(cost_table_data, colWidths=[120, 130, 100, 80])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(table)
            
            confidence = cost_data.get('confidence_interval', 0.75) * 100
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(f"<b>Niveau de confiance:</b> {confidence:.0f}%", self._get_body_style()))
        else:
            elements.append(Paragraph("Analyse des coûts non disponible.", self._get_body_style()))
        
        elements.append(Spacer(1, 15))
    
    def _create_macro_budget_section(self, elements: List, categories: List):
        """Crée la section du budget macro"""
        elements.append(Paragraph("3. RÉPARTITION BUDGÉTAIRE MACRO", self.styles['SectionTitle']))
        
        if categories:
            cat_data = [["Catégorie", "Budget cible", "Estimation", "Écart", "%"]]
            total_target = 0
            total_estimated = 0
            
            for cat in categories:
                target = cat.get("target_amount", 0) or 0
                estimated = cat.get("estimated_amount", 0) or 0
                variance = estimated - target
                variance_pct = (variance / target * 100) if target > 0 else 0
                
                total_target += target
                total_estimated += estimated
                
                cat_data.append([
                    cat.get("name", "N/A"),
                    self._format_currency(target),
                    self._format_currency(estimated),
                    self._format_currency(variance),
                    f"{variance_pct:.1f}%"
                ])
            
            # Total row
            total_variance = total_estimated - total_target
            total_variance_pct = (total_variance / total_target * 100) if total_target > 0 else 0
            cat_data.append([
                "TOTAL",
                self._format_currency(total_target),
                self._format_currency(total_estimated),
                self._format_currency(total_variance),
                f"{total_variance_pct:.1f}%"
            ])
            
            cat_table = Table(cat_data, colWidths=[100, 90, 90, 80, 60])
            cat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e2e8f0')),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8fafc')]),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(cat_table)
        else:
            elements.append(Paragraph("Répartition budgétaire non disponible.", self._get_body_style()))
        
        elements.append(Spacer(1, 15))
    
    def _create_dpgf_section(self, elements: List, dpgf_data: Optional[Dict]):
        """Crée la section DPGF"""
        elements.append(Paragraph("4. DÉCOMPOSITION PAR LOTS (DPGF)", self.styles['SectionTitle']))
        
        if dpgf_data and dpgf_data.get('lots'):
            lots = dpgf_data['lots']
            
            dpgf_table_data = [["Code", "Désignation", "Montant HT", "% Total"]]
            total = sum(lot.get('amount', 0) or 0 for lot in lots)
            
            for lot in lots:
                amount = lot.get('amount', 0) or 0
                percentage = (amount / total * 100) if total > 0 else 0
                dpgf_table_data.append([
                    lot.get('code', ''),
                    lot.get('name', ''),
                    self._format_currency(amount),
                    f"{percentage:.1f}%"
                ])
            
            dpgf_table_data.append(["", "TOTAL HT", self._format_currency(total), "100%"])
            
            table = Table(dpgf_table_data, colWidths=[50, 230, 100, 60])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e2e8f0')),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8fafc')]),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("DPGF non disponible.", self._get_body_style()))
        
        elements.append(Spacer(1, 15))
    
    def _create_ai_estimation_section(self, elements: List, ai_data: Optional[Dict]):
        """Crée la section estimation IA"""
        elements.append(Paragraph("5. ESTIMATION INTELLIGENTE (IA)", self.styles['SectionTitle']))
        
        if ai_data:
            ai_table_data = [
                ["Paramètre", "Valeur"],
                ["Coût estimé total", self._format_currency(ai_data.get('estimated_total', 0))],
                ["Coût au m²", self._format_currency(ai_data.get('cost_per_m2', 0))],
                ["Fourchette basse", self._format_currency(ai_data.get('confidence_min', 0))],
                ["Fourchette haute", self._format_currency(ai_data.get('confidence_max', 0))],
                ["Marge de risque", self._format_currency(ai_data.get('risk_margin', 0))],
                ["Niveau de confiance", ai_data.get('confidence_level', 'medium').title()],
            ]
            
            table = Table(ai_table_data, colWidths=[180, 260])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#a78bfa')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#faf5ff'), colors.white]),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(table)
            
            # Recommandations
            recommendations = ai_data.get('recommendations', [])
            if recommendations:
                elements.append(Spacer(1, 10))
                elements.append(Paragraph("<b>Recommandations IA:</b>", self._get_body_style()))
                for rec in recommendations:
                    elements.append(Paragraph(f"• {rec}", self._get_body_style()))
        else:
            elements.append(Paragraph("Estimation IA non disponible.", self._get_body_style()))
        
        elements.append(Spacer(1, 15))
    
    def _create_risk_section(self, elements: List, risk_data: Optional[Dict]):
        """Crée la section d'analyse des risques"""
        elements.append(Paragraph("6. ANALYSE DES RISQUES", self.styles['SectionTitle']))
        
        if risk_data and risk_data.get('risks'):
            risks = risk_data['risks']
            total_contingency = risk_data.get('summary', {}).get('total_contingency', 0)
            
            elements.append(Paragraph(
                f"<b>Provision totale pour risques:</b> {self._format_currency(total_contingency)}",
                self._get_body_style()
            ))
            elements.append(Spacer(1, 10))
            
            risk_table_data = [["Catégorie", "Description", "Impact", "Prob.", "Provision"]]
            
            for risk in risks[:8]:
                risk_table_data.append([
                    risk.get('risk_category', 'N/A').capitalize()[:15],
                    risk.get('description', 'N/A')[:40] + "...",
                    risk.get('impact_level', 'N/A').capitalize(),
                    f"{risk.get('probability', 0)*100:.0f}%",
                    self._format_currency(risk.get('contingency_amount', 0))
                ])
            
            table = Table(risk_table_data, colWidths=[70, 160, 60, 50, 80])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fef2f2')]),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("Analyse des risques non disponible.", self._get_body_style()))
        
        elements.append(Spacer(1, 15))
    
    def _create_scenario_section(self, elements: List, scenario_data: Optional[Dict]):
        """Crée la section de comparaison des scénarios"""
        elements.append(Paragraph("7. COMPARAISON DES SCÉNARIOS", self.styles['SectionTitle']))
        
        if scenario_data and scenario_data.get('scenarios'):
            scenarios = scenario_data['scenarios']
            
            scenario_table_data = [["Scénario", "Coût total", "Coût/m²", "Qualité"]]
            
            for scenario in scenarios:
                scenario_table_data.append([
                    scenario.get('name', 'N/A'),
                    self._format_currency(scenario.get('total_cost', 0)),
                    f"{scenario.get('cost_per_m2', 0):,.0f} €/m²".replace(",", " "),
                    scenario.get('quality_level', 'N/A').capitalize()
                ])
            
            table = Table(scenario_table_data, colWidths=[150, 120, 100, 100])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecfdf5')]),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(table)
            
            recommended = scenario_data.get('recommended_scenario', '')
            if recommended:
                elements.append(Spacer(1, 10))
                elements.append(Paragraph(
                    f"<b>Scénario recommandé:</b> {recommended.capitalize()}",
                    self._get_body_style()
                ))
        else:
            elements.append(Paragraph("Comparaison des scénarios non disponible.", self._get_body_style()))
    
    def _create_footer(self, canvas, doc):
        """Crée le pied de page"""
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.gray)
        canvas.drawCentredString(
            A4[0]/2, 
            15*mm, 
            f"CostPilot Senior - Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} - Page {doc.page}"
        )
        canvas.restoreState()
    
    async def generate_full_report(self, analyses: Dict) -> bytes:
        """Génère le rapport PDF complet"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2.5*cm
        )
        
        elements = []
        
        # Page de couverture
        self._create_cover_page(elements)
        
        # Construire le rapport
        self._create_header(elements)
        self._create_executive_summary(elements, analyses)
        
        elements.append(PageBreak())
        self._create_cost_analysis_section(elements, analyses.get('cost_prediction'))
        self._create_macro_budget_section(elements, analyses.get('categories', []))
        
        elements.append(PageBreak())
        self._create_dpgf_section(elements, analyses.get('dpgf'))
        self._create_ai_estimation_section(elements, analyses.get('ai_estimation'))
        
        elements.append(PageBreak())
        self._create_risk_section(elements, analyses.get('risks'))
        self._create_scenario_section(elements, analyses.get('scenarios'))
        
        # Générer le PDF
        doc.build(elements, onFirstPage=self._create_footer, onLaterPages=self._create_footer)
        
        buffer.seek(0)
        return buffer.getvalue()


async def generate_project_report(project_id: str) -> Dict:
    """Génère un rapport complet pour un projet"""
    from services import senior_economist, cost_prediction, design_optimization, multi_scenario
    
    # Récupérer le projet
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        return {"error": "Projet non trouvé"}
    
    # Récupérer toutes les analyses
    analyses = {}
    
    # Catégories macro
    categories = await db.macro_categories.find({"project_id": project_id}, {"_id": 0}).to_list(100)
    analyses['categories'] = categories
    
    # Prédiction de coûts
    cost_pred = await cost_prediction.get_latest_prediction(project_id)
    analyses['cost_prediction'] = cost_pred
    
    # DPGF
    dpgf = await db.dpgf.find_one({"project_id": project_id}, {"_id": 0})
    analyses['dpgf'] = dpgf
    
    # Optimisation
    opt = await db.design_optimizations.find_one({"project_id": project_id}, {"_id": 0})
    analyses['optimization'] = opt
    
    # Risques
    risks = await senior_economist.get_risk_assessment(project_id)
    total_contingency = sum(r.get("contingency_amount", 0) for r in risks) if risks else 0
    analyses['risks'] = {
        "risks": risks,
        "summary": {"total_contingency": total_contingency}
    }
    
    # Scénarios
    scenario = await db.multi_scenarios.find_one({"project_id": project_id}, {"_id": 0})
    analyses['scenarios'] = scenario
    
    # AI estimation (si disponible)
    ai_est = await db.ai_estimations.find_one({"project_id": project_id}, {"_id": 0})
    analyses['ai_estimation'] = ai_est
    
    # Générer le PDF
    generator = ProfessionalReportGenerator(project)
    pdf_bytes = await generator.generate_full_report(analyses)
    
    # Sauvegarder le rapport
    report_id = generate_uuid()
    now = now_iso()
    
    report_record = {
        "id": report_id,
        "project_id": project_id,
        "type": "full_report",
        "format": "pdf",
        "generated_at": now,
        "file_size_bytes": len(pdf_bytes)
    }
    
    await db.reports.insert_one(report_record)
    
    return {
        "report_id": report_id,
        "pdf_data": pdf_bytes,
        "file_size": len(pdf_bytes),
        "generated_at": now
    }



class PlanAnalysisReportGenerator:
    """Générateur de rapports PDF pour les analyses de plans par IA"""
    
    def __init__(self, analysis_data: Dict, project_data: Dict):
        self.analysis = analysis_data
        self.project = project_data
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configure les styles personnalisés"""
        custom_styles = {
            'PlanTitle': ParagraphStyle(
                name='PlanTitle',
                parent=self.styles['Heading1'],
                fontSize=22,
                alignment=TA_CENTER,
                spaceAfter=20,
                textColor=colors.HexColor('#4f46e5')
            ),
            'PlanSubtitle': ParagraphStyle(
                name='PlanSubtitle',
                parent=self.styles['Normal'],
                fontSize=12,
                alignment=TA_CENTER,
                spaceAfter=30,
                textColor=colors.HexColor('#6b7280')
            ),
            'PlanSection': ParagraphStyle(
                name='PlanSection',
                parent=self.styles['Heading2'],
                fontSize=14,
                spaceBefore=20,
                spaceAfter=10,
                textColor=colors.HexColor('#1e3a5f'),
                borderWidth=0,
                borderColor=colors.HexColor('#e5e7eb'),
                borderPadding=5
            ),
            'PlanKPI': ParagraphStyle(
                name='PlanKPI',
                parent=self.styles['Normal'],
                fontSize=28,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#059669')
            ),
            'PlanKPILabel': ParagraphStyle(
                name='PlanKPILabel',
                parent=self.styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#6b7280')
            ),
            'AINote': ParagraphStyle(
                name='AINote',
                parent=self.styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#9ca3af'),
                leftIndent=10,
                spaceBefore=5
            )
        }
        
        for name, style in custom_styles.items():
            if name not in self.styles:
                self.styles.add(style)
    
    def generate_pdf(self) -> bytes:
        """Génère le rapport PDF d'analyse de plan"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        
        # Page de titre
        story.extend(self._build_title_page())
        story.append(PageBreak())
        
        # Résumé exécutif
        story.extend(self._build_executive_summary())
        
        # Détail des pièces
        story.extend(self._build_rooms_section())
        
        # Murs et ouvertures
        story.extend(self._build_structure_section())
        
        # Notes et recommandations
        story.extend(self._build_notes_section())
        
        # Footer avec métadonnées
        story.extend(self._build_footer())
        
        doc.build(story)
        return buffer.getvalue()
    
    def _build_title_page(self) -> List:
        """Construit la page de titre"""
        elements = []
        
        elements.append(Spacer(1, 3*cm))
        
        # Logo/Header
        elements.append(Paragraph(
            "COSTPILOT SENIOR",
            ParagraphStyle(
                'Logo',
                parent=self.styles['Normal'],
                fontSize=12,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#9ca3af'),
                spaceAfter=10
            )
        ))
        
        elements.append(Paragraph(
            "RAPPORT D'ANALYSE DE PLAN",
            self.styles['PlanTitle']
        ))
        
        elements.append(Paragraph(
            "Extraction automatique par Intelligence Artificielle",
            self.styles['PlanSubtitle']
        ))
        
        elements.append(Spacer(1, 2*cm))
        
        # Informations projet
        project_info = [
            ["PROJET", self.project.get('project_name', 'N/A')],
            ["CLIENT", self.project.get('client_name', 'N/A')],
            ["FICHIER ANALYSÉ", self.analysis.get('filename', 'N/A')],
            ["DATE D'ANALYSE", self._format_date(self.analysis.get('created_at', ''))],
            ["MODÈLE IA", self.analysis.get('ai_model', 'GPT Vision')],
        ]
        
        table = Table(project_info, colWidths=[5*cm, 10*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1f2937')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#e5e7eb')),
        ]))
        
        elements.append(table)
        
        elements.append(Spacer(1, 2*cm))
        
        # Badge de confiance
        confidence = self.analysis.get('overall_confidence_percent', 0)
        confidence_color = '#059669' if confidence >= 80 else '#d97706' if confidence >= 60 else '#dc2626'
        
        elements.append(Paragraph(
            f"CONFIANCE DE L'ANALYSE: {confidence}%",
            ParagraphStyle(
                'Confidence',
                parent=self.styles['Normal'],
                fontSize=14,
                alignment=TA_CENTER,
                textColor=colors.HexColor(confidence_color),
                fontName='Helvetica-Bold'
            )
        ))
        
        return elements
    
    def _build_executive_summary(self) -> List:
        """Construit le résumé exécutif avec KPIs"""
        elements = []
        
        elements.append(Paragraph("RÉSUMÉ EXÉCUTIF", self.styles['PlanSection']))
        
        summary = self.analysis.get('summary', {})
        
        # KPIs principaux
        kpi_data = [
            [
                Paragraph(f"{self.analysis.get('total_surface_m2', 0):.0f}", self.styles['PlanKPI']),
                Paragraph(f"{summary.get('habitable_surface_m2', 0):.0f}", self.styles['PlanKPI']),
                Paragraph(f"{summary.get('room_count', 0)}", self.styles['PlanKPI']),
                Paragraph(f"{summary.get('opening_count', 0)}", self.styles['PlanKPI']),
            ],
            [
                Paragraph("Surface totale (m²)", self.styles['PlanKPILabel']),
                Paragraph("Surface habitable (m²)", self.styles['PlanKPILabel']),
                Paragraph("Pièces détectées", self.styles['PlanKPILabel']),
                Paragraph("Ouvertures", self.styles['PlanKPILabel']),
            ]
        ]
        
        kpi_table = Table(kpi_data, colWidths=[3.75*cm, 3.75*cm, 3.75*cm, 3.75*cm])
        kpi_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0fdf4')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#d1fae5')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1fae5')),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        
        elements.append(kpi_table)
        elements.append(Spacer(1, 1*cm))
        
        # Répartition des surfaces
        circulation = summary.get('circulation_surface_m2', 0)
        habitable = summary.get('habitable_surface_m2', 0)
        total = habitable + circulation if habitable + circulation > 0 else 1
        
        ratio_text = f"Ratio habitable/circulation: {habitable:.0f} m² ({habitable/total*100:.0f}%) / {circulation:.0f} m² ({circulation/total*100:.0f}%)"
        elements.append(Paragraph(ratio_text, self.styles['Normal']))
        
        return elements
    
    def _build_rooms_section(self) -> List:
        """Construit la section des pièces détectées"""
        elements = []
        
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph("PIÈCES DÉTECTÉES", self.styles['PlanSection']))
        
        rooms = self.analysis.get('rooms', [])
        
        if not rooms:
            elements.append(Paragraph("Aucune pièce détectée dans ce plan.", self.styles['Normal']))
            return elements
        
        # Tableau des pièces
        header = ['Pièce', 'Type', 'Surface (m²)', 'Dimensions', 'Confiance']
        data = [header]
        
        for room in rooms:
            dims = f"{room.get('estimated_length_m', '-')}m × {room.get('estimated_width_m', '-')}m"
            data.append([
                room.get('name', 'N/A'),
                room.get('type', 'N/A').capitalize(),
                f"{room.get('surface_m2', 0):.1f}",
                dims,
                f"{room.get('confidence_percent', 0)}%"
            ])
        
        # Total
        total_surface = sum(r.get('surface_m2', 0) for r in rooms)
        data.append(['TOTAL', '', f"{total_surface:.1f}", '', ''])
        
        table = Table(data, colWidths=[4*cm, 3*cm, 3*cm, 3.5*cm, 2.5*cm])
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            # Body
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
            # Alternating rows
            ('BACKGROUND', (0, 1), (-1, -2), colors.white),
            # Total row
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f3f4f6')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            # Grid
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        # Alternating row colors
        for i in range(1, len(data) - 1):
            if i % 2 == 0:
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f9fafb'))
                ]))
        
        elements.append(table)
        
        return elements
    
    def _build_structure_section(self) -> List:
        """Construit la section des murs et ouvertures"""
        elements = []
        
        walls = self.analysis.get('walls', [])
        openings = self.analysis.get('openings', [])
        
        if walls:
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph("STRUCTURE - MURS", self.styles['PlanSection']))
            
            header = ['Type', 'Longueur (m)', 'Épaisseur (cm)', 'Confiance']
            data = [header]
            
            for wall in walls[:10]:  # Limiter à 10 murs
                data.append([
                    wall.get('type', 'N/A').capitalize(),
                    f"{wall.get('estimated_length_m', 0):.2f}",
                    f"{wall.get('estimated_thickness_cm', 0)}",
                    f"{wall.get('confidence_percent', 0)}%"
                ])
            
            if len(walls) > 10:
                data.append([f"... et {len(walls) - 10} autres murs", '', '', ''])
            
            table = Table(data, colWidths=[5*cm, 4*cm, 4*cm, 3*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(table)
        
        if openings:
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph("OUVERTURES", self.styles['PlanSection']))
            
            header = ['Type', 'Largeur (m)', 'Hauteur (m)', 'Pièce associée']
            data = [header]
            
            for opening in openings[:10]:
                data.append([
                    opening.get('type', 'N/A').capitalize(),
                    f"{opening.get('estimated_width_m', 0):.2f}",
                    f"{opening.get('estimated_height_m', 0):.2f}",
                    opening.get('connects_rooms', ['N/A'])[0] if opening.get('connects_rooms') else 'N/A'
                ])
            
            if len(openings) > 10:
                data.append([f"... et {len(openings) - 10} autres ouvertures", '', '', ''])
            
            table = Table(data, colWidths=[4*cm, 3.5*cm, 3.5*cm, 5*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b5cf6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 0), (2, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(table)
        
        return elements
    
    def _build_notes_section(self) -> List:
        """Construit la section des notes IA"""
        elements = []
        
        notes = self.analysis.get('notes', [])
        
        if notes:
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph("OBSERVATIONS DE L'IA", self.styles['PlanSection']))
            
            for note in notes:
                elements.append(Paragraph(f"• {note}", self.styles['AINote']))
        
        return elements
    
    def _build_footer(self) -> List:
        """Construit le footer avec métadonnées"""
        elements = []
        
        elements.append(Spacer(1, 1*cm))
        
        # Ligne de séparation
        elements.append(Paragraph(
            "_" * 80,
            ParagraphStyle('Line', parent=self.styles['Normal'], textColor=colors.HexColor('#e5e7eb'))
        ))
        
        elements.append(Spacer(1, 0.5*cm))
        
        footer_text = f"""
        <font color="#9ca3af" size="8">
        Rapport généré automatiquement par CostPilot Senior<br/>
        Analyse IA: {self.analysis.get('ai_model', 'GPT Vision')} | 
        ID: {self.analysis.get('id', 'N/A')}<br/>
        Date: {self._format_date(self.analysis.get('created_at', ''))} | 
        Confiance: {self.analysis.get('overall_confidence_percent', 0)}%<br/><br/>
        <i>Ce rapport est généré par intelligence artificielle. Les mesures sont des estimations 
        et doivent être vérifiées par un professionnel avant toute utilisation contractuelle.</i>
        </font>
        """
        
        elements.append(Paragraph(footer_text, self.styles['Normal']))
        
        return elements
    
    def _format_date(self, iso_date: str) -> str:
        """Formate une date ISO en français"""
        if not iso_date:
            return 'N/A'
        try:
            dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
            return dt.strftime('%d/%m/%Y à %H:%M')
        except:
            return iso_date[:10] if len(iso_date) >= 10 else iso_date


async def generate_plan_analysis_pdf(project_id: str, analysis_id: str) -> Dict:
    """Génère un rapport PDF pour une analyse de plan"""
    
    # Récupérer les données
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        return {"error": "Projet non trouvé"}
    
    analysis = await db.plan_analyses.find_one({"id": analysis_id}, {"_id": 0})
    if not analysis:
        return {"error": "Analyse non trouvée"}
    
    # Générer le PDF
    generator = PlanAnalysisReportGenerator(analysis, project)
    pdf_bytes = generator.generate_pdf()
    
    return {
        "pdf_data": pdf_bytes,
        "filename": f"analyse_plan_{analysis.get('filename', 'plan').replace('.', '_')}.pdf",
        "file_size": len(pdf_bytes)
    }
