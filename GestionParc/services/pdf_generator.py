"""
SARL NOMADE AYRIS - Gestionnaire de Parc
Module: services/pdf_generator.py
Génère des PDF d'entreprise de standing international (Standard SAP / Oracle / Stripe / Airbus)
pour les Bons de Sortie et Bons de Réception / Livraison.
Design épuré, typographie premium, cartouches d'informations modernes, tableau sans surcharge et traçabilité complète.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable, Image, KeepTogether
)
from reportlab.lib.colors import HexColor

from services.config_manager import get_config

# ─── Palette Entreprise Internationale AYRIS (Design System Moderne) ────────
COLOR_PRIMARY     = HexColor('#0F172A')   # Slate 900 - Noir ardoise luxueux
COLOR_NAVY        = HexColor('#1E3A8A')   # Bleu marine officiel AYRIS
COLOR_ROYAL       = HexColor('#2563EB')   # Bleu royal moderne
COLOR_CYAN        = HexColor('#0284C7')   # Sky / Cyan eau de source
COLOR_LIGHT_BG    = HexColor('#F8FAFC')   # Slate 50 - Fond doux
COLOR_ROW_ALT     = HexColor('#F1F5F9')   # Slate 100 - Ligne alternée
COLOR_BORDER      = HexColor('#E2E8F0')   # Slate 200 - Bordure fine moderne
COLOR_BORDER_DARK = HexColor('#CBD5E1')   # Slate 300 - Délimitation franche
COLOR_TEXT_DARK   = HexColor('#0F172A')   # Slate 900 - Texte principal
COLOR_TEXT_MUTED  = HexColor('#64748B')   # Slate 500 - Texte secondaire / Labels
COLOR_SUCCESS     = HexColor('#059669')   # Emerald 600 - Validation officielle
COLOR_WHITE       = colors.white

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
    """Retourne l'image du logo officielle avec proportions parfaites."""
    if os.path.exists(LOGO_PATH):
        try:
            return Image(LOGO_PATH, width=3.8*cm, height=2.8*cm)
        except Exception:
            pass
    return None


def _build_corporate_header(doc_type: str, num_doc: str, date_str: str,
                            beneficiaire: str = "", fournisseur: str = "",
                            code_engin: str = "", matricule: str = "",
                            kilometrage: str = "", utilisateur: str = "",
                            ordre_reparation: str = "") -> list:
    """
    En-tête PDF de standard international :
    - Bloc Identité Entreprise à gauche avec logo haute définition
    - Cartouche Document moderne à droite avec Badge de Référence et Statut
    - 3 Cartouches d'Informations (Émetteur, Destinataire/Fournisseur, Statut & Traçabilité)
    """
    elements = []

    # 1. En-tête supérieur (Logo + Marque à gauche | Badge Document à droite)
    logo_img = _get_header_logo()
    
    company_text = (
        '<b><font color="#0F172A" size="13">SARL NOMADE AYRIS</font></b><br/>'
        '<font color="#1E3A8A" size="8"><b>CHEF DE PARC LOGISTIQUE</b></font><br/>'
        '<font color="#64748B" size="7.5">Eau Minérale Naturelle • Logistique & Exploitation</font>'
    )
    
    left_header_data = []
    if logo_img:
        left_header_data.append([logo_img, Paragraph(company_text, ParagraphStyle('comp_hdr', leading=11))])
        left_header_table = Table(left_header_data, colWidths=[3.9*cm, 5.0*cm])
        left_header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        left_cell = left_header_table
    else:
        left_cell = Paragraph(
            '<b><font color="#0F172A" size="16">SARL NOMADE AYRIS</font></b><br/>'
            '<font color="#1E3A8A" size="9"><b>CHEF DE PARC LOGISTIQUE</b></font><br/>'
            '<font color="#64748B" size="8">Eau Minérale Naturelle & Exploitation</font>',
            ParagraphStyle('logo_text_only', fontName='Helvetica-Bold', leading=13)
        )

    # Cartouche de droite (Badge moderne international)
    right_box_data = [
        [Paragraph(f'<b><font color="#0F172A" size="12">{doc_type.upper()}</font></b>',
                   ParagraphStyle('r_title', fontName='Helvetica-Bold', alignment=TA_RIGHT, leading=14))],
        [Paragraph(f'<font color="#64748B" size="8">RÉFÉRENCE : </font><b><font color="#1E3A8A" size="11">{num_doc}</font></b>',
                   ParagraphStyle('r_ref', fontName='Helvetica', alignment=TA_RIGHT, leading=13))],
        [Paragraph(f'<font color="#64748B" size="8">Émission : </font><b><font color="#0F172A" size="8">{date_str}</font></b>',
                   ParagraphStyle('r_dt', fontName='Helvetica', alignment=TA_RIGHT, leading=11))],
        [Paragraph('<b><font color="#059669" size="7.5">● DOCUMENT OFFICIEL VALIDÉ</font></b>',
                   ParagraphStyle('r_st', fontName='Helvetica-Bold', alignment=TA_RIGHT, leading=10))]
    ]
    right_table = Table(right_box_data, colWidths=[9.0*cm])
    right_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    header_master = Table([[left_cell, right_table]], colWidths=[9.3*cm, 9.3*cm])
    header_master.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(header_master)
    elements.append(Spacer(1, 0.15*cm))

    # Ligne de séparation élégante à double ton
    elements.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_NAVY, spaceAfter=8, spaceBefore=2))

    # 2. Cartouches d'Informations (Layout 3 colonnes moderne)
    card_hdr_style = ParagraphStyle('chdr', fontName='Helvetica-Bold', fontSize=8, textColor=COLOR_WHITE, leading=10)
    card_body_style = ParagraphStyle('cbod', fontName='Helvetica', fontSize=8, textColor=COLOR_TEXT_DARK, leading=11)

    # Données Carte 1 : Émetteur & Responsable
    nom_operateur = utilisateur if (utilisateur and utilisateur not in ('admin', 'Chef de Parc', '')) else 'Benkerrou Tarek'
    card1_hdr = Paragraph("ÉMETTEUR & RESPONSABLE", card_hdr_style)
    card1_content = (
        f"<b>SARL NOMADE AYRIS</b><br/>"
        f"<font color='#64748B'>Service : </font><b>Chef de Parc Logistique</b><br/>"
        f"<font color='#64748B'>Opérateur : </font><b>{nom_operateur}</b>"
    )

    # Données Carte 2 : Destinataire (Engin ou Fournisseur)
    if 'SORTIE' in doc_type:
        card2_hdr = Paragraph("AFFECTATION ENGIN", card_hdr_style)
        card2_content = (
            f"<font color='#64748B'>Code Engin : </font><b><font color='#1E3A8A'>{code_engin or '—'}</font></b><br/>"
            f"<font color='#64748B'>Désignation : </font><b>{beneficiaire or '—'}</b><br/>"
            f"<font color='#64748B'>Matricule : </font><b>{matricule or '—'}</b>"
        )
        if ordre_reparation:
            card2_content += f"<br/><font color='#64748B'>N° Ordre Rép. : </font><b><font color='#1E3A8A'>{ordre_reparation}</font></b>"
        if kilometrage:
            card2_content += f"<br/><font color='#64748B'>Compteur : </font><b>{kilometrage}</b>"
    else:
        card2_hdr = Paragraph("FOURNISSEUR & TIERS", card_hdr_style)
        card2_content = (
            f"<font color='#64748B'>Fournisseur : </font><b><font color='#1E3A8A'>{fournisseur or beneficiaire or 'Non spécifié'}</font></b><br/>"
            f"<font color='#64748B'>N° BL Fournisseur : </font><b>{num_doc}</b><br/>"
            f"<font color='#64748B'>Date Livraison : </font><b>{date_str}</b>"
        )

    # Données Carte 3 : Statut & Contrôle Qualité
    card3_hdr = Paragraph("TRAÇABILITÉ & STATUT", card_hdr_style)
    type_mvt_label = "Sortie Magasin / Pièce" if 'SORTIE' in doc_type else "Réception / Entrée Stock"
    card3_content = (
        f"<font color='#64748B'>Type Mouvement : </font><b>{type_mvt_label}</b><br/>"
        f"<font color='#64748B'>Contrôle : </font><b>Conforme & Validé</b><br/>"
        f"<font color='#64748B'>Registre : </font><b>Système Central Ayris</b>"
    )

    cards_data = [
        [card1_hdr, card2_hdr, card3_hdr],
        [Paragraph(card1_content, card_body_style),
         Paragraph(card2_content, card_body_style),
         Paragraph(card3_content, card_body_style)]
    ]

    cards_table = Table(cards_data, colWidths=[6.0*cm, 6.6*cm, 6.0*cm])
    cards_table.setStyle(TableStyle([
        # Entêtes des cartes
        ('BACKGROUND',    (0, 0), (-1, 0),  COLOR_NAVY),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  COLOR_WHITE),
        ('TOPPADDING',    (0, 0), (-1, 0),  4),
        ('BOTTOMPADDING', (0, 0), (-1, 0),  4),
        ('LEFTPADDING',   (0, 0), (-1, 0),  7),
        ('RIGHTPADDING',  (0, 0), (-1, 0),  7),
        # Corps des cartes
        ('BACKGROUND',    (0, 1), (-1, 1),  COLOR_LIGHT_BG),
        ('TOPPADDING',    (0, 1), (-1, 1),  6),
        ('BOTTOMPADDING', (0, 1), (-1, 1),  6),
        ('LEFTPADDING',   (0, 1), (-1, 1),  7),
        ('RIGHTPADDING',  (0, 1), (-1, 1),  7),
        ('GRID',          (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(cards_table)
    elements.append(Spacer(1, 0.35*cm))

    return elements


def _build_signatures_block(type_mvt: str, utilisateur: str = "") -> list:
    """
    Bloc de signatures moderne et aéré (Standard Audit & Certification ISO).
    """
    elements = []
    elements.append(Spacer(1, 0.4*cm))

    sig_hdr_style = ParagraphStyle('sighdr', fontName='Helvetica-Bold', fontSize=8, textColor=COLOR_WHITE, alignment=TA_CENTER)
    sig_sub_style = ParagraphStyle('sigsub', fontName='Helvetica-Oblique', fontSize=7, textColor=COLOR_TEXT_MUTED, alignment=TA_CENTER)

    nom_operateur = utilisateur if (utilisateur and utilisateur not in ('admin', 'Chef de Parc', '')) else 'Benkerrou Tarek'

    if type_mvt == 'SORTIE':
        left_title = "ÉMETTEUR (CHEF DE PARC LOGISTIQUE)"
        left_person = f"Opérateur : {nom_operateur}"
        right_title = "RÉCEPTIONNAIRE (CHAUFFEUR / MÉCANICIEN)"
        right_person = "Nom & Prénom du Bénéficiaire"
    else:
        left_title = "RÉCEPTIONNAIRE (MAGASIN AYRIS)"
        left_person = f"Réceptionné par : {nom_operateur}"
        right_title = "FOURNISSEUR / TRANSPORTEUR"
        right_person = "Nom du Livreur / Représentant"

    sig_data = [
        [Paragraph(f"<b>{left_title}</b>", sig_hdr_style), Paragraph(f"<b>{right_title}</b>", sig_hdr_style)],
        [
            Paragraph(f"<b>{left_person}</b><br/><br/><br/><br/><br/>", ParagraphStyle('p1', fontName='Helvetica', fontSize=7.5, alignment=TA_CENTER, leading=10)),
            Paragraph(f"<b>{right_person}</b><br/><br/><br/><br/><br/>", ParagraphStyle('p2', fontName='Helvetica', fontSize=7.5, alignment=TA_CENTER, leading=10))
        ],
        [
            Paragraph("Signature & Cachet officiel précédés de la mention <i>\"Lu et approuvé\"</i>", sig_sub_style),
            Paragraph("Signature & Cachet officiel du Tiers / Livreur", sig_sub_style)
        ]
    ]

    sig_table = Table(sig_data, colWidths=[9.3*cm, 9.3*cm])
    sig_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  COLOR_NAVY),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  COLOR_WHITE),
        ('TOPPADDING',    (0, 0), (-1, 0),  5),
        ('BOTTOMPADDING', (0, 0), (-1, 0),  5),
        ('BACKGROUND',    (0, 1), (-1, 1),  COLOR_WHITE),
        ('BACKGROUND',    (0, 2), (-1, 2),  COLOR_LIGHT_BG),
        ('TOPPADDING',    (0, 1), (-1, 1),  8),
        ('BOTTOMPADDING', (0, 1), (-1, 1),  4),
        ('TOPPADDING',    (0, 2), (-1, 2),  3),
        ('BOTTOMPADDING', (0, 2), (-1, 2),  4),
        ('GRID',          (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))

    elements.append(KeepTogether([sig_table]))
    return elements


def _draw_page_decorations(canvas, doc, num_doc: str):
    """
    Dessine la charte graphique internationale sur canvas :
    - Bandeau supérieur de marque bicolore (Navy + Cyan)
    - Filet de pied de page et métadonnées d'audit
    """
    canvas.saveState()

    # 1. Bandeau supérieur corporate à fleur de page
    canvas.setFillColor(COLOR_NAVY)
    canvas.rect(0, 29.3*cm, 16.5*cm, 0.4*cm, stroke=0, fill=1)
    canvas.setFillColor(COLOR_CYAN)
    canvas.rect(16.5*cm, 29.3*cm, 4.5*cm, 0.4*cm, stroke=0, fill=1)

    # 2. Pied de page ancré
    canvas.setStrokeColor(COLOR_BORDER_DARK)
    canvas.setLineWidth(0.75)
    canvas.line(1.2 * cm, 1.3 * cm, 19.8 * cm, 1.3 * cm)

    now_str = datetime.now().strftime('%d/%m/%Y à %H:%M')
    
    # Texte gauche
    canvas.setFont('Helvetica', 7.5)
    canvas.setFillColor(COLOR_TEXT_MUTED)
    canvas.drawString(1.2 * cm, 0.9 * cm, "SARL NOMADE AYRIS • Service Chef de Parc Logistique • Système de Traçabilité Intégré")

    # Texte droite
    footer_right = f"Réf. {num_doc} • Édité le {now_str} • Page {doc.page}"
    canvas.setFont('Helvetica-Bold', 7.5)
   # ─────────────────── GÉNÉRATEUR BON DE SORTIE PDF ────────────────────────────

def generate_bon_sortie_pdf(data: dict, output_path: str | None = None) -> str:
    """Génère un Bon de Sortie PDF officiel avec design d'entreprise de classe internationale (Support Multi-Articles)."""
    now_str = datetime.now().strftime('%d/%m/%Y à %H:%M')
    date_doc = str(data.get('date_sortie') or now_str)
    directory = Path(output_path) if output_path else Path(get_default_pdf_dir())
    directory.mkdir(parents=True, exist_ok=True)

    bon_id = str(data.get('numero_bon_sortie') or data.get('bon_id', '0001')).strip()
    num_doc = f"BS-{bon_id}" if not str(bon_id).startswith('BS-') else str(bon_id)
    clean_num = bon_id.replace('/', '_').replace('\\', '_')
    filename = directory / f"BS_{clean_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    doc = SimpleDocTemplate(
        str(filename), pagesize=A4,
        rightMargin=1.2*cm, leftMargin=1.2*cm,
        topMargin=1.2*cm, bottomMargin=1.8*cm,
        title=f"SARL NOMADE AYRIS — BON DE SORTIE {num_doc}",
        author="SARL NOMADE AYRIS Parc Management System",
    )

    story = []
    nom_op = data.get('nom_operateur') or data.get('utilisateur', '')
    story.extend(_build_corporate_header(
        "BON DE SORTIE DE MATÉRIEL",
        num_doc,
        date_doc,
        beneficiaire=data.get('designation_engin', ''),
        code_engin=data.get('code_engin', ''),
        matricule=data.get('matricule', ''),
        kilometrage=data.get('kilometrage', ''),
        utilisateur=nom_op,
        ordre_reparation=data.get('ordre_reparation', '')
    ))

    # Tableau des détails de la sortie (Style Moderne sans surcharge de lignes verticales)
    col_hdr_style = ParagraphStyle('ch_s', fontName='Helvetica-Bold', fontSize=8, textColor=COLOR_WHITE, alignment=TA_CENTER)
    cell_style    = ParagraphStyle('c_s',  fontName='Helvetica', fontSize=8, textColor=COLOR_TEXT_DARK, leading=10)
    cell_bold_txt = ParagraphStyle('cb_s', fontName='Helvetica-Bold', fontSize=8, textColor=COLOR_TEXT_DARK, leading=10)
    cell_center   = ParagraphStyle('cc_s', fontName='Helvetica', fontSize=8, textColor=COLOR_TEXT_DARK, alignment=TA_CENTER)
    cell_qty      = ParagraphStyle('cq_s', fontName='Helvetica-Bold', fontSize=8.5, textColor=COLOR_ROYAL, alignment=TA_CENTER)
    cell_badge    = ParagraphStyle('cbdg', fontName='Helvetica-Bold', fontSize=7.5, textColor=COLOR_NAVY, alignment=TA_CENTER)

    table_data = [
        [
            Paragraph('N°', col_hdr_style),
            Paragraph('Réf. Interne', col_hdr_style),
            Paragraph('Réf. Fournisseur', col_hdr_style),
            Paragraph('Désignation Pièce & Article', col_hdr_style),
            Paragraph('Code Engin', col_hdr_style),
            Paragraph('Désignation Engin', col_hdr_style),
            Paragraph('Qté Sortie', col_hdr_style),
            Paragraph('Unité', col_hdr_style),
        ]
    ]

    raw_articles = data.get('articles')
    if not raw_articles:
        raw_articles = [{
            'reference_interne': data.get('reference_interne', '—'),
            'reference_fournisseur': data.get('reference_fournisseur', '—'),
            'designation_piece': data.get('designation_piece', data.get('designation', '—')),
            'code_engin': data.get('code_engin', '—'),
            'designation_engin': data.get('designation_engin', '—'),
            'quantite': data.get('quantite', 1),
            'unite': data.get('unite', 'UNITE'),
        }]

    total_qte = 0.0
    for idx, art in enumerate(raw_articles, 1):
        q_val = art.get('quantite', 1)
        try:
            q_num = float(q_val)
            total_qte += q_num
            q_str = str(int(q_num)) if q_num.is_integer() else f"{q_num:.2f}".rstrip('0').rstrip('.')
        except Exception:
            q_str = str(q_val)

        c_eng = str(art.get('code_engin') or data.get('code_engin', '—'))
        d_eng = str(art.get('designation_engin') or art.get('engin_designation') or data.get('designation_engin', '—'))
        r_int = str(art.get('reference_interne') or '—')
        r_four = str(art.get('reference_fournisseur') or '—')
        desig_p = str(art.get('piece_designation') or art.get('designation_piece') or art.get('designation') or '—')
        unit_str = str(art.get('unite') or 'UNITE').upper()

        table_data.append([
            Paragraph(str(idx), cell_center),
            Paragraph(f"<b>{r_int}</b>", cell_bold_txt),
            Paragraph(r_four, cell_style),
            Paragraph(f"<b>{desig_p}</b>", cell_bold_txt),
            Paragraph(f"<b>{c_eng}</b>", cell_badge),
            Paragraph(d_eng, cell_style),
            Paragraph(q_str, cell_qty),
            Paragraph(f"<b>{unit_str}</b>", cell_center),
        ])

    tot_q_str = str(int(total_qte)) if total_qte.is_integer() else f"{total_qte:.2f}".rstrip('0').rstrip('.')
    table_data.append([
        Paragraph(f'<b>TOTAL PIÈCES : {len(raw_articles)} article(s)</b>', ParagraphStyle('t_tot_lbl', fontName='Helvetica-Bold', fontSize=8, textColor=COLOR_NAVY, alignment=TA_RIGHT)),
        Paragraph('', cell_style),
        Paragraph('', cell_style),
        Paragraph('', cell_style),
        Paragraph('', cell_style),
        Paragraph('', cell_style),
        Paragraph(f'<b>{tot_q_str}</b>', ParagraphStyle('t_tot_q', fontName='Helvetica-Bold', fontSize=9, textColor=COLOR_ROYAL, alignment=TA_CENTER)),
        Paragraph('', cell_style),
    ])

    col_widths = [0.9*cm, 2.3*cm, 2.3*cm, 4.2*cm, 2.0*cm, 3.5*cm, 1.8*cm, 1.6*cm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    t_style = [
        ('BACKGROUND',    (0, 0), (-1, 0),  COLOR_PRIMARY),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  COLOR_WHITE),
        ('ALIGN',         (0, 0), (-1, 0),  'CENTER'),
        ('TOPPADDING',    (0, 0), (-1, 0),  6),
        ('BOTTOMPADDING', (0, 0), (-1, 0),  6),
        ('GRID',          (0, 0), (-1, -2), 0.5, COLOR_BORDER),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',   (0, 0), (-1, 0), 4),
        ('RIGHTPADDING',  (0, 0), (-1, 0), 4),
    ]
    for r in range(1, len(raw_articles) + 1):
        bg = COLOR_WHITE if r % 2 == 1 else COLOR_ROW_ALT
        t_style.append(('BACKGROUND', (0, r), (-1, r), bg))
        t_style.append(('TOPPADDING', (0, r), (-1, r), 5))
        t_style.append(('BOTTOMPADDING', (0, r), (-1, r), 5))

    tot_row_idx = len(raw_articles) + 1
    t_style.extend([
        ('SPAN',          (0, tot_row_idx), (5, tot_row_idx)),
        ('BACKGROUND',    (0, tot_row_idx), (-1, tot_row_idx), COLOR_LIGHT_BG),
        ('TOPPADDING',    (0, tot_row_idx), (-1, tot_row_idx), 7),
        ('BOTTOMPADDING', (0, tot_row_idx), (-1, tot_row_idx), 7),
        ('LINEABOVE',     (0, tot_row_idx), (-1, tot_row_idx), 1.2, COLOR_NAVY),
        ('LINEBELOW',     (0, tot_row_idx), (-1, tot_row_idx), 1.2, COLOR_NAVY),
    ])

    table.setStyle(TableStyle(t_style))
    story.append(table)

    story.extend(_build_signatures_block('SORTIE', utilisateur=nom_op))

    doc.build(
        story,
        onFirstPage=lambda c, d: _draw_page_decorations(c, d, num_doc),
        onLaterPages=lambda c, d: _draw_page_decorations(c, d, num_doc)
    )
    return str(filename)


# ─────────────────── GÉNÉRATEUR BON DE RÉCEPTION / LIVRAISON PDF ─────────────

def generate_bon_reception_pdf(data: dict, output_path: str | None = None) -> str:
    """
    Génère un Bon de Réception / Livraison multi-articles officiel (Format A4 SAP / Entreprise)
    avec colonne Emplacement.
    """
    date_str = str(data.get('date_livraison') or datetime.now().strftime('%d/%m/%Y'))
    directory = Path(output_path) if output_path else Path(get_default_pdf_dir())
    directory.mkdir(parents=True, exist_ok=True)

    num_bl = str(data.get('numero_bon_livraison') or '0001').strip()
    num_doc = num_bl if num_bl.startswith(('BL-', 'BR-')) else f"BR-{num_bl}"
    clean_num = num_bl.replace('/', '_').replace('\\', '_')
    filename = directory / f"BR_{clean_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    doc = SimpleDocTemplate(
        str(filename), pagesize=A4,
        rightMargin=1.2*cm, leftMargin=1.2*cm,
        topMargin=1.2*cm, bottomMargin=1.8*cm,
        title=f"SARL NOMADE AYRIS — BON DE RÉCEPTION {num_doc}",
        author="SARL NOMADE AYRIS Parc Management System",
    )

    story = []
    story.extend(_build_corporate_header(
        "BON DE RÉCEPTION & LIVRAISON",
        num_doc,
        date_str,
        fournisseur=data.get('nom_fournisseur', ''),
        utilisateur=data.get('utilisateur', '')
    ))

    # Tableau Multi-Articles avec Emplacement
    col_hdr_style = ParagraphStyle('ch_br', fontName='Helvetica-Bold', fontSize=8, textColor=COLOR_WHITE, alignment=TA_CENTER)
    cell_style    = ParagraphStyle('c_br',  fontName='Helvetica', fontSize=8, textColor=COLOR_TEXT_DARK, leading=10)
    cell_bold_txt = ParagraphStyle('cb_br', fontName='Helvetica-Bold', fontSize=8, textColor=COLOR_TEXT_DARK, leading=10)
    cell_center   = ParagraphStyle('cc_br', fontName='Helvetica', fontSize=8, textColor=COLOR_TEXT_DARK, alignment=TA_CENTER)
    cell_right    = ParagraphStyle('cr_br', fontName='Helvetica', fontSize=8, textColor=COLOR_TEXT_DARK, alignment=TA_RIGHT)
    cell_qty      = ParagraphStyle('cq_br', fontName='Helvetica-Bold', fontSize=8.5, textColor=COLOR_ROYAL, alignment=TA_CENTER)
    cell_tot_val  = ParagraphStyle('ct_br', fontName='Helvetica-Bold', fontSize=8.5, textColor=COLOR_NAVY, alignment=TA_RIGHT)

    table_data = [
        [
            Paragraph('N°', col_hdr_style),
            Paragraph('Réf. Interne', col_hdr_style),
            Paragraph('Réf. Fournisseur', col_hdr_style),
            Paragraph('Désignation Pièce / Article', col_hdr_style),
            Paragraph('Emplacement', col_hdr_style),
            Paragraph('Unité', col_hdr_style),
            Paragraph('Qté', col_hdr_style),
            Paragraph('Prix Unit. (DZD)', col_hdr_style),
            Paragraph('Total (DZD)', col_hdr_style),
        ]
    ]

    articles = data.get('articles', [])
    total_general = 0.0
    total_qte = 0.0

    if not articles:
        # Fallback si article unique passé à la racine de data
        articles = [{
            'reference_interne': data.get('reference_interne', '—'),
            'reference_fournisseur': data.get('reference_fournisseur', '—'),
            'designation': data.get('designation', '—'),
            'emplacement': data.get('emplacement', '—'),
            'unite': data.get('unite', 'UNITE'),
            'quantite': data.get('quantite', 0),
            'prix_unitaire': data.get('prix_unitaire', 0),
            'prix_total': data.get('prix_total', 0),
        }]

    for idx, art in enumerate(articles, start=1):
        try:
            from ui.theme import parse_qty
            qte = parse_qty(art.get('quantite', 0))
        except Exception:
            qte = float(art.get('quantite', 0) or 0)
        pu = float(art.get('prix_unitaire', 0) or 0)
        tot = float(art.get('prix_total', 0) or (qte * pu))
        unite = str(art.get('unite', 'UNITE') or 'UNITE')
        empl = str(art.get('emplacement') or '—')
        total_general += tot
        total_qte += qte

        qte_display = str(int(qte)) if qte.is_integer() else f"{qte:.2f}".rstrip('0').rstrip('.')
        table_data.append([
            Paragraph(str(idx), cell_center),
            Paragraph(f"<b>{str(art.get('reference_interne', ''))}</b>", cell_bold_txt),
            Paragraph(str(art.get('reference_fournisseur', '—')), cell_style),
            Paragraph(f"<b>{str(art.get('designation', ''))}</b>", cell_bold_txt),
            Paragraph(empl, cell_center),
            Paragraph(f"<b>{unite.upper()}</b>", cell_center),
            Paragraph(qte_display, cell_qty),
            Paragraph(f"{pu:,.2f}", cell_right),
            Paragraph(f"{tot:,.2f}", cell_tot_val),
        ])

    col_widths = [0.8*cm, 2.2*cm, 2.0*cm, 4.2*cm, 2.0*cm, 1.4*cm, 1.5*cm, 2.2*cm, 2.3*cm]

    # Ligne Récapitulative Totale
    tot_label_style = ParagraphStyle('tot_lbl', fontName='Helvetica-Bold', fontSize=8.5, textColor=COLOR_NAVY, alignment=TA_RIGHT)
    tot_val_style = ParagraphStyle('tot_val', fontName='Helvetica-Bold', fontSize=9.5, textColor=COLOR_ROYAL, alignment=TA_RIGHT)
    tot_ttc_style = ParagraphStyle('tot_ttc', fontName='Helvetica-Bold', fontSize=10, textColor=COLOR_PRIMARY, alignment=TA_RIGHT)

    total_qte_display = str(int(total_qte)) if total_qte.is_integer() else f"{total_qte:.2f}".rstrip('0').rstrip('.')

    appliquer_tva = bool(data.get('appliquer_tva') or data.get('tva_applicable') or (data.get('taux_tva', 0) > 0))
    taux_tva = float(data.get('taux_tva', 19.0) if appliquer_tva else 0.0)
    if taux_tva <= 0 and appliquer_tva:
        taux_tva = 19.0

    if not appliquer_tva:
        table_data.append([
            Paragraph('<b>TOTAL GÉNÉRAL :</b>', tot_label_style),
            Paragraph('', cell_style),
            Paragraph('', cell_style),
            Paragraph(f'<b>{len(articles)} article(s)</b>', cell_style),
            Paragraph('', cell_style),
            Paragraph('', cell_style),
            Paragraph(f'<b>{total_qte_display}</b>', cell_qty),
            Paragraph('', cell_style),
            Paragraph(f'<b>{total_general:,.2f} DZD</b>', tot_val_style),
        ])
    else:
        total_ht = total_general
        montant_tva = total_ht * (taux_tva / 100.0)
        total_ttc = total_ht + montant_tva

        # Ligne 1 : Total HT
        table_data.append([
            Paragraph('<b>TOTAL HORS TAXES (HT) :</b>', tot_label_style),
            Paragraph('', cell_style),
            Paragraph('', cell_style),
            Paragraph(f'<b>{len(articles)} article(s)</b>', cell_style),
            Paragraph('', cell_style),
            Paragraph('', cell_style),
            Paragraph(f'<b>{total_qte_display}</b>', cell_qty),
            Paragraph('', cell_style),
            Paragraph(f'<b>{total_ht:,.2f} DZD</b>', tot_val_style),
        ])

        # Ligne 2 : TVA (19%)
        tva_pct_str = f"{int(taux_tva)} %" if taux_tva.is_integer() else f"{taux_tva:.1f} %"
        table_data.append([
            Paragraph(f'<b>TVA ({tva_pct_str}) :</b>', tot_label_style),
            Paragraph('', cell_style),
            Paragraph('', cell_style),
            Paragraph('', cell_style),
            Paragraph('', cell_style),
            Paragraph('', cell_style),
            Paragraph('', cell_style),
            Paragraph('', cell_style),
            Paragraph(f'<b>{montant_tva:,.2f} DZD</b>', tot_val_style),
        ])

        # Ligne 3 : Total TTC / Total avec TVA
        table_data.append([
            Paragraph('<b>TOTAL GÉNÉRAL (AVEC TVA / TTC) :</b>', tot_label_style),
            Paragraph('', cell_style),
            Paragraph('', cell_style),
            Paragraph('', cell_style),
            Paragraph('', cell_style),
            Paragraph('', cell_style),
            Paragraph('', cell_style),
            Paragraph('', cell_style),
            Paragraph(f'<b>{total_ttc:,.2f} DZD</b>', tot_ttc_style),
        ])

    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    t_style = [
        ('BACKGROUND',    (0, 0), (-1, 0),  COLOR_PRIMARY),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  COLOR_WHITE),
        ('ALIGN',         (0, 0), (-1, 0),  'CENTER'),
        ('TOPPADDING',    (0, 0), (-1, 0),  7),
        ('BOTTOMPADDING', (0, 0), (-1, 0),  7),
        ('GRID',          (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
    ]

    # Alternance des couleurs de lignes pour les articles
    for i in range(1, len(articles) + 1):
        bg = COLOR_WHITE if i % 2 == 1 else COLOR_LIGHT_BG
        t_style.append(('BACKGROUND', (0, i), (-1, i), bg))
        t_style.append(('TOPPADDING', (0, i), (-1, i), 6))
        t_style.append(('BOTTOMPADDING', (0, i), (-1, i), 6))

    if not appliquer_tva:
        t_style.extend([
            ('SPAN',          (0, -1), (2, -1)),
            ('BACKGROUND',    (0, -1), (-1, -1), COLOR_ROW_ALT),
            ('TOPPADDING',    (0, -1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
        ])
    else:
        # Ligne Total HT
        t_style.extend([
            ('SPAN',          (0, -3), (2, -3)),
            ('BACKGROUND',    (0, -3), (-1, -3), COLOR_ROW_ALT),
            ('TOPPADDING',    (0, -3), (-1, -3), 6),
            ('BOTTOMPADDING', (0, -3), (-1, -3), 6),
        ])
        # Ligne TVA 19%
        t_style.extend([
            ('SPAN',          (0, -2), (7, -2)),
            ('BACKGROUND',    (0, -2), (-1, -2), COLOR_LIGHT_BG),
            ('TOPPADDING',    (0, -2), (-1, -2), 6),
            ('BOTTOMPADDING', (0, -2), (-1, -2), 6),
        ])
        # Ligne Total TTC
        t_style.extend([
            ('SPAN',          (0, -1), (7, -1)),
            ('BACKGROUND',    (0, -1), (-1, -1), COLOR_ROW_ALT),
            ('TOPPADDING',    (0, -1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 7),
        ])

    table.setStyle(TableStyle(t_style))
    story.append(table)

    story.extend(_build_signatures_block('LIVRAISON', utilisateur=data.get('utilisateur', '')))

    doc.build(
        story,
        onFirstPage=lambda c, d: _draw_page_decorations(c, d, num_doc),
        onLaterPages=lambda c, d: _draw_page_decorations(c, d, num_doc)
    )
    return str(filename)
