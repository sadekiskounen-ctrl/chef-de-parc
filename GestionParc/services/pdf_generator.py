"""
SARL NOMADE AYRIS - Gestionnaire de Parc
Module: services/pdf_generator.py
Génère des PDF d'entreprise de classe internationale (style SAP / Oracle / IBM) pour les Bons de Sortie et Bons de Livraison.
Footer ancré à la fin de la page A4.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable, Image)
from reportlab.lib.colors import HexColor

from services.config_manager import get_config

# ─── Palette Entreprise Internationale AYRIS ──────────────────────────────────
COLOR_NAVY     = HexColor('#0B2E6B')   # Bleu marine officiel AYRIS
COLOR_ROYAL    = HexColor('#004899')   # Bleu royal
COLOR_CYAN     = HexColor('#0096D6')   # Cyan source
COLOR_LIGHT_BG = HexColor('#F8FAFC')   # Ardoise claire
COLOR_BORDER   = HexColor('#CBD5E1')   # Bordure fine
COLOR_TEXT_DARK= HexColor('#0F172A')   # Noir ardoise
COLOR_ROW_ALT  = HexColor('#F1F5F9')   # Ligne alternée
COLOR_WHITE    = colors.white

ROOT_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = Path(getattr(sys, '_MEIPASS', ROOT_DIR))
LOGO_PATH = str((BASE_DIR / 'assets' / 'logo_nomade_ayris.png'))


def get_default_pdf_dir() -> str:
    pdf_dir = get_config('pdf_directory', '')
    if pdf_dir and os.path.isdir(pdf_dir):
        return pdf_dir
    docs = Path.home() / 'Documents' / 'SARL_Ayris_Parc'
    docs.mkdir(parents=True, exist_ok=True)
    return str(docs)


def _get_header_logo() -> Image | None:
    """Retourne l'image du logo officielle sans déformation."""
    if os.path.exists(LOGO_PATH):
        try:
            return Image(LOGO_PATH, width=4.2*cm, height=3.28*cm)
        except Exception:
            pass
    return None


def _build_corporate_header(doc_type: str, num_doc: str, date_str: str,
                            beneficiaire: str = "", fournisseur: str = "",
                            code_engin: str = "", matricule: str = "") -> list:
    """En-tête PDF Entreprise Internationale (Layout 2 colonnes avec logo et cartouche)."""
    elements = []

    logo_img = _get_header_logo()
    if logo_img:
        logo_cell = logo_img
    else:
        logo_cell = Paragraph(
            '<b><font color="#0B2E6B" size="18">SARL NOMADE AYRIS</font></b><br/>'
            '<font color="#0096D6" size="9">EAU DE SOURCE NATURELLE</font>',
            ParagraphStyle('logo_fall', fontName='Helvetica-Bold', leading=18)
        )

    # Cartouche de droite (Titre + N° Document)
    doc_title_style = ParagraphStyle(
        'doctitle', fontName='Helvetica-Bold', fontSize=14,
        textColor=COLOR_WHITE, alignment=TA_CENTER
    )

    right_cartouche_data = [
        [Paragraph(f"<b>{doc_type}</b>", doc_title_style)],
        [Paragraph(f'N° Document : <b><font color="#004899">{num_doc}</font></b>',
                   ParagraphStyle('numd', fontName='Helvetica-Bold', fontSize=11, alignment=TA_CENTER))],
        [Paragraph(f'<b>Date : {date_str}</b>',
                   ParagraphStyle('dtd', fontName='Helvetica-Bold', fontSize=9, alignment=TA_CENTER, textColor=COLOR_TEXT_DARK))]
    ]
    cartouche_table = Table(right_cartouche_data, colWidths=[9*cm])
    cartouche_table.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, 0),  COLOR_NAVY),
        ('BACKGROUND',   (0, 1), (-1, -1), COLOR_LIGHT_BG),
        ('GRID',         (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('ALIGN',        (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',   (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 6),
    ]))

    header_table = Table([[logo_cell, cartouche_table]], colWidths=[9*cm, 9*cm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',  (0, 0), (0, 0),   'LEFT'),
        ('ALIGN',  (1, 0), (1, 0),   'RIGHT'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.3*cm))

    # Ligne de séparation corporate
    elements.append(HRFlowable(width="100%", thickness=2, color=COLOR_ROYAL, spaceAfter=8))

    # Bloc informations complémentaires (Bénéficiaire / Engin / Statut)
    if 'SORTIE' in doc_type:
        col2_label = 'Engin Destinataire'
        col2_val = f'<b>Code Engin : {code_engin or "—"}</b>'
        if matricule:
            col2_val += f'<br/><b>Matricule : {matricule}</b>'
        if beneficiaire:
            col2_val += f'<br/><b>Engin : {beneficiaire}</b>'
    else:
        col2_label = 'Fournisseur / Livreur'
        col2_val = f'<b>{fournisseur or beneficiaire or "Non spécifié"}</b>'

    info_data = [
        [
            Paragraph('<b>Société Émettrice</b>', ParagraphStyle('l1', fontName='Helvetica-Bold', fontSize=8, textColor=COLOR_TEXT_DARK)),
            Paragraph(f'<b>{col2_label}</b>', ParagraphStyle('l2', fontName='Helvetica-Bold', fontSize=8, textColor=COLOR_TEXT_DARK)),
            Paragraph('<b>Statut Document</b>', ParagraphStyle('l3', fontName='Helvetica-Bold', fontSize=8, textColor=COLOR_TEXT_DARK)),
        ],
        [
            Paragraph('<b>SARL NOMADE AYRIS</b><br/><b>Eau de Source Naturelle</b>',
                      ParagraphStyle('v1', fontName='Helvetica-Bold', fontSize=9, textColor=COLOR_TEXT_DARK)),
            Paragraph(col2_val,
                      ParagraphStyle('v2', fontName='Helvetica-Bold', fontSize=10, textColor=COLOR_ROYAL)),
            Paragraph('<b>DOCUMENT OFFICIEL</b><br/><b>Validé & Enregistré</b>',
                      ParagraphStyle('v3', fontName='Helvetica-Bold', fontSize=9, textColor=COLOR_TEXT_DARK)),
        ]
    ]
    info_table = Table(info_data, colWidths=[6*cm, 6.5*cm, 5.5*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, -1), COLOR_LIGHT_BG),
        ('GRID',         (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',   (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 8),
        ('LEFTPADDING',  (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.4*cm))
    return elements


def _build_signatures_block(type_mvt: str, utilisateur: str = "") -> list:
    """Bloc de signatures officiel (Responsable Parc / Demandeur / Magasinier)."""
    elements = []
    elements.append(Spacer(1, 0.4*cm))

    sig_label = ParagraphStyle('sigl', fontName='Helvetica-Bold', fontSize=9, textColor=COLOR_WHITE, alignment=TA_CENTER)

    if type_mvt == 'SORTIE':
        left_title = f"Émis par : {utilisateur or 'Chef de Parc'}"
        right_title = "Le Responsable Maintenance / Engin"
    else:
        left_title = f"Réceptionné par : {utilisateur or 'Chef de Parc'}"
        right_title = "Le Livreur / Fournisseur"

    sig_data = [
        [Paragraph(left_title, sig_label), Paragraph(right_title, sig_label)],
        [
            Paragraph('\n\n\n\n<b>Signature & Cachet Officiel</b>',
                      ParagraphStyle('s1', fontName='Helvetica-Bold', fontSize=8, alignment=TA_CENTER, textColor=COLOR_TEXT_DARK)),
            Paragraph('\n\n\n\n<b>Signature & Cachet Officiel</b>',
                      ParagraphStyle('s2', fontName='Helvetica-Bold', fontSize=8, alignment=TA_CENTER, textColor=COLOR_TEXT_DARK)),
        ]
    ]
    sig_table = Table(sig_data, colWidths=[8.8*cm, 8.8*cm])
    sig_table.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, 0),  COLOR_ROYAL),
        ('TEXTCOLOR',    (0, 0), (-1, 0),  COLOR_WHITE),
        ('GRID',         (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('ALIGN',        (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',   (0, 0), (-1, 0),  6),
        ('BOTTOMPADDING',(0, 0), (-1, 0),  6),
        ('TOPPADDING',   (0, 1), (-1, 1),  30),
        ('BOTTOMPADDING',(0, 1), (-1, 1),  10),
    ]))
    elements.append(sig_table)
    return elements


def _draw_footer(canvas, doc, num_doc: str):
    """Dessine le pied de page ancré à la toute fin de la page A4."""
    canvas.saveState()

    canvas.setStrokeColor(COLOR_BORDER)
    canvas.setLineWidth(1)
    canvas.line(1.5 * cm, 1.5 * cm, 19.5 * cm, 1.5 * cm)

    now_str = datetime.now().strftime('%d/%m/%Y à %H:%M')
    footer_text = f'SARL NOMADE AYRIS — Direction Technique & Parc — Réf. {num_doc} — Édité le {now_str} — Page {doc.page}'

    canvas.setFont('Helvetica-Bold', 8)
    canvas.setFillColor(COLOR_TEXT_DARK)
    canvas.drawCentredString(10.5 * cm, 1.0 * cm, footer_text)

    canvas.restoreState()


# ─────────────────── GÉNÉRATEUR BON DE SORTIE PDF ────────────────────────────

def generate_bon_sortie_pdf(data: dict, output_path: str | None = None) -> str:
    """Génère un Bon de Sortie PDF officiel avec en-tête corporate et footer ancré."""
    now_str = datetime.now().strftime('%d/%m/%Y %H:%M')
    directory = Path(output_path) if output_path else Path(get_default_pdf_dir())
    directory.mkdir(parents=True, exist_ok=True)

    bon_id = str(data.get('bon_id', '0001'))
    num_doc = f"BS-{bon_id}"
    filename = directory / f"BS_{bon_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    doc = SimpleDocTemplate(
        str(filename), pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=1.2*cm, bottomMargin=2.2*cm,
        title=f"SARL NOMADE AYRIS — BON DE SORTIE {num_doc}",
        author="SARL NOMADE AYRIS Parc Management System",
    )

    story = []
    story.extend(_build_corporate_header(
        "BON DE SORTIE ENGIN",
        num_doc,
        now_str,
        beneficiaire=data.get('designation_engin', ''),
        code_engin=data.get('code_engin', ''),
        matricule=data.get('matricule', '')
    ))

    # Tableau des détails de la sortie
    col_header_style = ParagraphStyle('ch', fontName='Helvetica-Bold', fontSize=9, textColor=COLOR_WHITE, alignment=TA_CENTER)
    cell_style  = ParagraphStyle('cell',  fontName='Helvetica', fontSize=9, textColor=COLOR_TEXT_DARK)
    cell_center = ParagraphStyle('cellc', fontName='Helvetica', fontSize=9, textColor=COLOR_TEXT_DARK, alignment=TA_CENTER)
    cell_bold   = ParagraphStyle('cellb', fontName='Helvetica-Bold', fontSize=10, textColor=COLOR_ROYAL, alignment=TA_CENTER)

    table_data = [
        [
            Paragraph('N°', col_header_style),
            Paragraph('Réf. Interne', col_header_style),
            Paragraph('Réf. Fournisseur', col_header_style),
            Paragraph('Code Engin', col_header_style),
            Paragraph('Désignation Engin', col_header_style),
            Paragraph('Qté Sortie', col_header_style),
            Paragraph('Unité', col_header_style),
        ],
        [
            Paragraph('1', cell_center),
            Paragraph(str(data.get('reference_interne', '')), cell_style),
            Paragraph(str(data.get('reference_fournisseur', '—')), cell_style),
            Paragraph(str(data.get('code_engin', '')), cell_center),
            Paragraph(str(data.get('designation_engin', '')), cell_style),
            Paragraph(str(data.get('quantite', 1)), cell_bold),
            Paragraph(str(data.get('unite', 'UNITE')), cell_center),
        ]
    ]

    table = Table(table_data, colWidths=[1*cm, 3.5*cm, 3.5*cm, 2.5*cm, 4.5*cm, 1.5*cm, 1.5*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  COLOR_NAVY),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  COLOR_WHITE),
        ('ALIGN',         (0, 0), (-1, 0),  'CENTER'),
        ('TOPPADDING',    (0, 0), (-1, 0),  8),
        ('BOTTOMPADDING', (0, 0), (-1, 0),  8),
        ('GRID',          (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
        ('TOPPADDING',    (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
        ('BACKGROUND',    (0, 1), (-1, 1),  COLOR_LIGHT_BG),
    ]))
    story.append(table)

    story.extend(_build_signatures_block('SORTIE', utilisateur=data.get('utilisateur', '')))

    doc.build(
        story,
        onFirstPage=lambda c, d: _draw_footer(c, d, num_doc),
        onLaterPages=lambda c, d: _draw_footer(c, d, num_doc)
    )
    return str(filename)
