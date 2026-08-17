from pathlib import Path

from openpyxl import Workbook


def export_pieces_xlsx(rows: list[dict], output_path: str | None = None) -> str:
    wb = Workbook()
    ws = wb.active
    ws.title = 'Pieces'
    headers = ['ID', 'Référence interne', 'Référence fournisseur', 'Désignation', 'Engin', 'Famille', 'Quantité', 'Unité', 'Ancien prix', 'Nouveau prix', 'Prix total']
    ws.append(headers)
    for row in rows:
        ws.append([
            row.get('id', ''),
            row.get('reference_interne', ''),
            row.get('reference_fournisseur', ''),
            row.get('designation', ''),
            row.get('engin_designation', row.get('code_engin', '')),
            row.get('famille_nom', row.get('famille_id', '')),
            row.get('quantite', ''),
            row.get('unite', ''),
            row.get('ancien_prix_unitaire', ''),
            row.get('nouveau_prix_unitaire', ''),
            row.get('prix_total_nouveau', ''),
        ])
    path = Path(output_path or Path.home() / 'Documents' / 'SARL_Ayris_Parc' / 'catalogue_pieces.xlsx')
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return str(path)
