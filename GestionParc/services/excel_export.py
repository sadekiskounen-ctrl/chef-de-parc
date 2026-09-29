import os
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


def export_pieces_xlsx(rows: list[dict], output_path: str | None = None, filter_summary: str = '') -> str:
    """
    Exporte la liste des pièces filtrées vers un fichier Excel stylisé et professionnel.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = 'Inventaire Pièces'
    ws.views.sheetView[0].showGridLines = True

    # ── Styles ────────────────────────────────────────────────────────────────
    font_title = Font(name='Segoe UI', size=15, bold=True, color='FFFFFF')
    font_sub = Font(name='Segoe UI', size=10, italic=True, color='E2E8F0')
    font_header = Font(name='Segoe UI', size=11, bold=True, color='FFFFFF')
    font_data = Font(name='Segoe UI', size=10)
    font_data_bold = Font(name='Segoe UI', size=10, bold=True)
    font_alert = Font(name='Segoe UI', size=10, bold=True, color='991B1B')

    fill_title = PatternFill(start_color='003570', end_color='003570', fill_type='solid')
    fill_header = PatternFill(start_color='004899', end_color='004899', fill_type='solid')
    fill_zebra = PatternFill(start_color='F8FAFC', end_color='F8FAFC', fill_type='solid')
    fill_alert = PatternFill(start_color='FEE2E2', end_color='FEE2E2', fill_type='solid')
    fill_total = PatternFill(start_color='E2E8F0', end_color='E2E8F0', fill_type='solid')

    align_center = Alignment(horizontal='center', vertical='center')
    align_left = Alignment(horizontal='left', vertical='center')
    align_right = Alignment(horizontal='right', vertical='center')

    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )
    thick_bottom = Border(
        top=Side(style='thin', color='94A3B8'),
        bottom=Side(style='double', color='0F172A'),
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1')
    )

    # ── En-tête de Document ───────────────────────────────────────────────────
    ws.merge_cells('A1:N1')
    cell_t = ws['A1']
    cell_t.value = "SARL NOMADE AYRIS — CATALOGUE & INVENTAIRE DU PARC"
    cell_t.font = font_title
    cell_t.fill = fill_title
    cell_t.alignment = align_center
    ws.row_dimensions[1].height = 36

    ws.merge_cells('A2:N2')
    cell_sub = ws['A2']
    date_str = datetime.now().strftime('%d/%m/%Y à %H:%M')
    sub_text = f"Exporté le {date_str}  •  Nombre de pièces : {len(rows)}"
    if filter_summary:
        sub_text += f"  •  Filtres : {filter_summary}"
    cell_sub.value = sub_text
    cell_sub.font = font_sub
    cell_sub.fill = fill_title
    cell_sub.alignment = align_center
    ws.row_dimensions[2].height = 20

    # Ligne vide de séparation
    ws.row_dimensions[3].height = 8

    # ── Tableau des Colonnes ─────────────────────────────────────────────────
    headers = [
        'N°',
        'Réf Interne',
        'Réf Fournisseur',
        'Désignation Pièce',
        'Catégorie Engin',
        'Marque / Modèle Engin',
        'Famille',
        'Emplacement',
        'Qté en Stock',
        'Unité',
        'Seuil Alerte',
        'Ancien Prix (DZD)',
        'Nouveau Prix (DZD)',
        'Valeur Stock (DZD)'
    ]

    header_row = 4
    ws.row_dimensions[header_row].height = 28
    for col_idx, h_text in enumerate(headers, start=1):
        c = ws.cell(row=header_row, column=col_idx, value=h_text)
        c.font = font_header
        c.fill = fill_header
        c.alignment = align_center
        c.border = thin_border

    # ── Lignes de Données ────────────────────────────────────────────────────
    current_row = 5
    total_qte = 0.0
    total_valeur = 0.0

    for i, piece in enumerate(rows, start=1):
        qte = float(piece.get('quantite', 0) or 0)
        seuil = float(piece.get('seuil_alerte', 5) or 5)
        ancien_pu = float(piece.get('ancien_prix_unitaire', 0) or 0)
        nouveau_pu = float(piece.get('nouveau_prix_unitaire', 0) or 0)
        val_tot = float(piece.get('prix_total_nouveau', 0) or (qte * nouveau_pu))

        total_qte += qte
        total_valeur += val_tot
        is_critique = (qte <= seuil)

        row_fill = fill_alert if is_critique else (fill_zebra if i % 2 == 0 else PatternFill(fill_type=None))
        current_font = font_alert if is_critique else font_data

        row_data = [
            (i, align_center, '@'),
            (piece.get('reference_interne', ''), align_center, '@'),
            (piece.get('reference_fournisseur', '') or '—', align_center, '@'),
            (piece.get('designation', ''), align_left, '@'),
            (piece.get('engin_categorie', '') or '—', align_center, '@'),
            (piece.get('engin_designation', '') or '—', align_left, '@'),
            (piece.get('famille_nom', '') or '—', align_center, '@'),
            (piece.get('emplacement', '') or '—', align_center, '@'),
            (qte, align_right, '#,##0.##'),
            (piece.get('unite', 'UNITE') or 'UNITE', align_center, '@'),
            (seuil, align_right, '#,##0.##'),
            (ancien_pu, align_right, '#,##0.00'),
            (nouveau_pu, align_right, '#,##0.00'),
            (val_tot, align_right, '#,##0.00'),
        ]

        ws.row_dimensions[current_row].height = 20
        for col_idx, (val, alignment, num_fmt) in enumerate(row_data, start=1):
            c = ws.cell(row=current_row, column=col_idx, value=val)
            c.font = current_font
            if row_fill.fill_type:
                c.fill = row_fill
            c.alignment = alignment
            c.border = thin_border
            if num_fmt != '@':
                c.number_format = num_fmt

        current_row += 1

    # ── Ligne Totale ──────────────────────────────────────────────────────────
    ws.row_dimensions[current_row].height = 24
    ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=8)
    cell_tot_label = ws.cell(row=current_row, column=1, value="TOTAL GÉNÉRAL")
    cell_tot_label.font = font_data_bold
    cell_tot_label.fill = fill_total
    cell_tot_label.alignment = align_right
    cell_tot_label.border = thick_bottom

    for col in range(2, 9):
        ws.cell(row=current_row, column=col).border = thick_bottom
        ws.cell(row=current_row, column=col).fill = fill_total

    # Total Quantité
    cell_tot_qte = ws.cell(row=current_row, column=9, value=total_qte)
    cell_tot_qte.font = font_data_bold
    cell_tot_qte.fill = fill_total
    cell_tot_qte.alignment = align_right
    cell_tot_qte.number_format = '#,##0.##'
    cell_tot_qte.border = thick_bottom

    for col in [10, 11, 12, 13]:
        c = ws.cell(row=current_row, column=col, value='')
        c.fill = fill_total
        c.border = thick_bottom

    # Total Valeur Stock
    cell_tot_val = ws.cell(row=current_row, column=14, value=total_valeur)
    cell_tot_val.font = font_data_bold
    cell_tot_val.fill = fill_total
    cell_tot_val.alignment = align_right
    cell_tot_val.number_format = '#,##0.00'
    cell_tot_val.border = thick_bottom

    # ── Ajustement Automatique de la Largeur des Colonnes ────────────────────
    min_widths = {
        1: 6,   # N°
        2: 16,  # Réf Interne
        3: 16,  # Réf Fournisseur
        4: 26,  # Désignation
        5: 18,  # Catégorie
        6: 22,  # Marque
        7: 18,  # Famille
        8: 14,  # Emplacement
        9: 14,  # Qté Stock
        10: 10, # Unité
        11: 12, # Seuil Alerte
        12: 18, # Ancien Prix
        13: 18, # Nouveau Prix
        14: 20, # Valeur Stock
    }

    for col_idx in range(1, 15):
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = min_widths.get(col_idx, 15)

    # ── Sauvegarde ────────────────────────────────────────────────────────────
    if not output_path:
        default_dir = Path.home() / 'Documents' / 'SARL_Ayris_Parc' / 'Exports_Excel'
        default_dir.mkdir(parents=True, exist_ok=True)
        filename = f"Inventaire_Pieces_AYRIS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        path = default_dir / filename
    else:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

    wb.save(path)
    return str(path)

