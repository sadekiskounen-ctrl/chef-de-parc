import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path


def get_db_path() -> str:
    local_app_data = os.getenv('LOCALAPPDATA', os.path.expanduser('~'))
    app_dir = Path(local_app_data) / 'SARL_Ayris_Parc'
    app_dir.mkdir(parents=True, exist_ok=True)
    return str(app_dir / 'ayris_parc.db')


def get_connection() -> sqlite3.Connection:
    for attempt in range(5):
        try:
            conn = sqlite3.connect(get_db_path(), timeout=30.0)
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA foreign_keys = ON')
            conn.execute('PRAGMA journal_mode = WAL')
            conn.execute('PRAGMA busy_timeout = 30000')
            return conn
        except sqlite3.OperationalError as exc:
            if 'locked' in str(exc).lower() and attempt < 4:
                time.sleep(0.5 * (attempt + 1))
                continue
            raise
    raise sqlite3.OperationalError('Base de données verrouillée, veuillez fermer toute autre instance de l’application.')


def backup_database_auto() -> None:
    try:
        import shutil
        db_file = Path(get_db_path())
        if db_file.exists() and db_file.stat().st_size > 0:
            backup_dir = db_file.parent / 'backups'
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_file = backup_dir / f"ayris_parc_auto_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(db_file, backup_file)
            backups = sorted(backup_dir.glob("ayris_parc_auto_backup_*.db"), key=lambda f: f.stat().st_mtime)
            while len(backups) > 10:
                old = backups.pop(0)
                try:
                    old.unlink()
                except Exception:
                    pass
    except Exception:
        pass


def initialize_database() -> None:
    backup_database_auto()
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS utilisateurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'operateur',
                date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS engins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code_engin TEXT UNIQUE NOT NULL,
                categorie TEXT NOT NULL,
                designation TEXT NOT NULL,
                matricule TEXT,
                date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS familles_pieces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT UNIQUE NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pieces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference_interne TEXT UNIQUE NOT NULL,
                reference_fournisseur TEXT,
                designation TEXT NOT NULL,
                engin_id INTEGER,
                famille_id INTEGER,
                date_livraison DATE,
                quantite INTEGER DEFAULT 0,
                seuil_alerte INTEGER DEFAULT 5,
                emplacement TEXT,
                unite TEXT,
                ancien_prix_unitaire REAL DEFAULT 0,
                nouveau_prix_unitaire REAL DEFAULT 0,
                prix_total_nouveau REAL DEFAULT 0,
                date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (engin_id) REFERENCES engins(id) ON DELETE SET NULL,
                FOREIGN KEY (famille_id) REFERENCES familles_pieces(id) ON DELETE SET NULL
            )
        ''')

        try:
            cursor.execute('ALTER TABLE pieces ADD COLUMN seuil_alerte INTEGER DEFAULT 5')
        except sqlite3.OperationalError:
            pass

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bons_livraison (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_bon_livraison TEXT,
                nom_fournisseur TEXT,
                reference_interne TEXT NOT NULL,
                reference_fournisseur TEXT,
                designation TEXT,
                quantite INTEGER NOT NULL DEFAULT 0,
                prix_unitaire REAL NOT NULL DEFAULT 0,
                prix_total REAL NOT NULL DEFAULT 0,
                date_livraison DATE,
                chemin_pdf TEXT,
                date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        try:
            cursor.execute('ALTER TABLE bons_livraison ADD COLUMN numero_bon_livraison TEXT')
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute('ALTER TABLE bons_livraison ADD COLUMN nom_fournisseur TEXT')
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute('ALTER TABLE bons_livraison ADD COLUMN chemin_pdf TEXT')
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute('ALTER TABLE bons_livraison ADD COLUMN unite TEXT DEFAULT "UNITE"')
        except sqlite3.OperationalError:
            pass

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bons_sortie (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                piece_id INTEGER,
                engin_id INTEGER,
                unite TEXT,
                quantite INTEGER NOT NULL DEFAULT 0,
                kilometrage TEXT DEFAULT '',
                date_heure DATETIME DEFAULT CURRENT_TIMESTAMP,
                chemin_pdf TEXT,
                utilisateur_id INTEGER,
                FOREIGN KEY (piece_id) REFERENCES pieces(id) ON DELETE SET NULL,
                FOREIGN KEY (engin_id) REFERENCES engins(id) ON DELETE SET NULL,
                FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE SET NULL
            )
        ''')

        try:
            cursor.execute('ALTER TABLE bons_sortie ADD COLUMN kilometrage TEXT DEFAULT ""')
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute('ALTER TABLE bons_sortie ADD COLUMN chemin_pdf TEXT')
        except sqlite3.OperationalError:
            pass

        families = ['CARROSSERIE', 'MOTEUR', 'TRANSMISSION', 'FREINAGE', 'ELECTRIQUE', 'SUSPENSION', 'LAVAGE']
        for name in families:
            cursor.execute('INSERT OR IGNORE INTO familles_pieces (nom) VALUES (?)', (name,))

        conn.commit()
    finally:
        conn.close()


def get_famille_id_by_name(name: str) -> int | None:
    if not name:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM familles_pieces WHERE nom = ?', (name.upper(),))
    row = cursor.fetchone()
    if not row:
        cursor.execute('INSERT OR IGNORE INTO familles_pieces (nom) VALUES (?)', (name.upper(),))
        conn.commit()
        cursor.execute('SELECT id FROM familles_pieces WHERE nom = ?', (name.upper(),))
        row = cursor.fetchone()
    conn.close()
    return row['id'] if row else None


def get_all_engins() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM engins ORDER BY designation')
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_all_pieces() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.*, e.code_engin, e.categorie AS engin_categorie, e.designation AS engin_designation, f.nom AS famille_nom
        FROM pieces p
        LEFT JOIN engins e ON p.engin_id = e.id
        LEFT JOIN familles_pieces f ON p.famille_id = f.id
        ORDER BY p.date_creation DESC
    ''')
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_piece_by_reference(reference: str) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM pieces WHERE reference_interne = ?', (reference,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_piece_by_id(piece_id: int) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM pieces WHERE id = ?', (piece_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_engin_by_code(code: str) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM engins WHERE code_engin = ?', (code.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def create_engin(code_engin: str, categorie: str, designation: str, matricule: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO engins (code_engin, categorie, designation, matricule) VALUES (?, ?, ?, ?)',
        (code_engin.strip(), categorie, designation.strip(), matricule.strip())
    )
    conn.commit()
    engin_id = cursor.lastrowid
    conn.close()
    return {'id': engin_id, 'code_engin': code_engin.strip(), 'categorie': categorie, 'designation': designation.strip(), 'matricule': matricule.strip()}


def update_engin(engin_id: int, **kwargs) -> None:
    fields = []
    values = []
    for key, value in kwargs.items():
        if value is not None:
            fields.append(f'{key} = ?')
            values.append(value)
    if not fields:
        return
    values.append(engin_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE engins SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    conn.close()


def delete_engin(engin_id: int) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM engins WHERE id = ?', (engin_id,))
    conn.commit()
    conn.close()


def create_piece(data: dict) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    piece = {
        'reference_interne': data.get('reference_interne', '').strip(),
        'reference_fournisseur': data.get('reference_fournisseur', '').strip(),
        'designation': data.get('designation', '').strip(),
        'engin_id': data.get('engin_id'),
        'famille_id': data.get('famille_id'),
        'date_livraison': data.get('date_livraison'),
        'quantite': _clean_qty_num(data.get('quantite', 0)),
        'seuil_alerte': _clean_qty_num(data.get('seuil_alerte', 5)),
        'emplacement': data.get('emplacement', '').strip(),
        'unite': data.get('unite', 'UNITE'),
        'ancien_prix_unitaire': float(data.get('ancien_prix_unitaire', 0) or 0),
        'nouveau_prix_unitaire': float(data.get('nouveau_prix_unitaire', 0) or 0),
    }
    piece['prix_total_nouveau'] = piece['nouveau_prix_unitaire'] * piece['quantite']
    cursor.execute(
        '''
        INSERT INTO pieces (
            reference_interne, reference_fournisseur, designation, engin_id, famille_id,
            date_livraison, quantite, seuil_alerte, emplacement, unite, ancien_prix_unitaire,
            nouveau_prix_unitaire, prix_total_nouveau
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            piece['reference_interne'], piece['reference_fournisseur'], piece['designation'],
            piece['engin_id'], piece['famille_id'], piece['date_livraison'], piece['quantite'],
            piece['seuil_alerte'], piece['emplacement'], piece['unite'], piece['ancien_prix_unitaire'],
            piece['nouveau_prix_unitaire'], piece['prix_total_nouveau']
        )
    )
    conn.commit()
    piece_id = cursor.lastrowid
    conn.close()
    return {'id': piece_id, **piece}



def update_piece(piece_id: int, **kwargs) -> None:
    fields = []
    values = []
    for key, value in kwargs.items():
        if value is not None:
            fields.append(f'{key} = ?')
            values.append(value)
    if not fields:
        return
    values.append(piece_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE pieces SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    conn.close()


def delete_piece(piece_id: int) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM pieces WHERE id = ?', (piece_id,))
    conn.commit()
    conn.close()


def create_bon_livraison(data: dict) -> dict:
    qty = int(data.get('quantite', 0) or 0)
    unit = float(data.get('prix_unitaire', 0) or 0)
    total = qty * unit
    num_bl = data.get('numero_bon_livraison', '').strip()
    nom_four = data.get('nom_fournisseur', '').strip()
    chemin_pdf = data.get('chemin_pdf', '').strip()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''
        INSERT INTO bons_livraison (numero_bon_livraison, nom_fournisseur, reference_interne, reference_fournisseur, designation, quantite, prix_unitaire, prix_total, date_livraison, chemin_pdf)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            num_bl,
            nom_four,
            data.get('reference_interne', '').strip(),
            data.get('reference_fournisseur', '').strip(),
            data.get('designation', '').strip(),
            qty,
            unit,
            total,
            data.get('date_livraison'),
            chemin_pdf,
        )
    )
    bon_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": bon_id, "numero_bon_livraison": num_bl, "nom_fournisseur": nom_four, "reference_interne": data.get('reference_interne', '').strip(), "quantite": qty, "prix_unitaire": unit, "prix_total": total, "chemin_pdf": chemin_pdf}


def _clean_qty_num(val) -> int | float:
    try:
        if isinstance(val, (int, float)):
            f = float(val)
        else:
            s = str(val).strip().replace(',', '.')
            f = float(s) if s else 0.0
        return int(f) if f.is_integer() else round(f, 3)
    except Exception:
        return 0


def create_bon_reception_multi(header: dict, articles: list[dict], chemin_pdf: str = '') -> dict:
    """
    Enregistre un bon de réception multi-articles :
    1. Insère chaque article dans bons_livraison
    2. Met à jour le stock, l'unité et les prix (ancien / nouveau) de chaque pièce
    """
    num_bl = header.get('numero_bon_livraison', '').strip()
    nom_four = header.get('nom_fournisseur', '').strip()
    date_liv = header.get('date_livraison', datetime.now().strftime('%Y-%m-%d')).strip()

    conn = get_connection()
    try:
        cursor = conn.cursor()
        inserted_ids = []
        for art in articles:
            ref_int = art.get('reference_interne', '').strip()
            ref_four = art.get('reference_fournisseur', '').strip()
            designation = art.get('designation', '').strip()
            unite = art.get('unite', 'UNITE').strip() or 'UNITE'
            qty = _clean_qty_num(art.get('quantite', 0))
            pu = float(art.get('prix_unitaire', 0) or 0)
            total = float(art.get('prix_total', 0) or (qty * pu))

            cursor.execute(
                '''
                INSERT INTO bons_livraison (
                    numero_bon_livraison, nom_fournisseur, reference_interne,
                    reference_fournisseur, designation, unite, quantite, prix_unitaire,
                    prix_total, date_livraison, chemin_pdf
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (num_bl, nom_four, ref_int, ref_four, designation, unite, qty, pu, total, date_liv, chemin_pdf)
            )
            inserted_ids.append(cursor.lastrowid)

            # Mise à jour ou création de la pièce dans le stock
            if ref_int:
                cursor.execute('SELECT id, quantite, nouveau_prix_unitaire FROM pieces WHERE reference_interne = ?', (ref_int,))
                p_row = cursor.fetchone()
                if p_row:
                    # ── Pièce existante : incrémenter le stock ────────────────
                    old_qty = _clean_qty_num(p_row['quantite'] or 0)
                    old_pu = float(p_row['nouveau_prix_unitaire'] or 0)
                    new_qty = _clean_qty_num(old_qty + qty)
                    new_tot = new_qty * pu
                    cursor.execute(
                        '''
                        UPDATE pieces SET
                            quantite = ?,
                            unite = ?,
                            reference_fournisseur = COALESCE(NULLIF(reference_fournisseur,''), ?),
                            designation = CASE WHEN TRIM(COALESCE(designation,''))='' THEN ? ELSE designation END,
                            ancien_prix_unitaire = ?,
                            nouveau_prix_unitaire = ?,
                            prix_total_nouveau = ?,
                            date_livraison = ?
                        WHERE id = ?
                        ''',
                        (new_qty, unite, ref_four, designation or ref_int, old_pu, pu, new_tot, date_liv, p_row['id'])
                    )
                else:
                    # ── Pièce inconnue : la créer automatiquement dans le stock ─
                    new_tot = qty * pu
                    cursor.execute(
                        '''
                        INSERT INTO pieces (
                            reference_interne, reference_fournisseur, designation,
                            quantite, unite, nouveau_prix_unitaire, ancien_prix_unitaire,
                            prix_total_nouveau, date_livraison
                        ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
                        ''',
                        (ref_int, ref_four, designation or ref_int, qty, unite, pu, new_tot, date_liv)
                    )

        conn.commit()
        return {
            'numero_bon_livraison': num_bl,
            'nom_fournisseur': nom_four,
            'date_livraison': date_liv,
            'nb_articles': len(articles),
            'inserted_ids': inserted_ids,
            'chemin_pdf': chemin_pdf
        }
    finally:
        conn.close()



def get_bons_reception_grouped() -> list[dict]:
    """
    Retourne la liste des bons de réception groupés par N° de bon,
    avec le total cumulé et la liste des articles.
    Garantit une rétrocompatibilité totale avec les anciens enregistrements.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            id,
            COALESCE(NULLIF(TRIM(numero_bon_livraison), ''), 'BL-' || id) AS num_bl_grouped,
            numero_bon_livraison,
            nom_fournisseur,
            reference_interne,
            reference_fournisseur,
            designation,
            COALESCE(unite, 'UNITE') AS unite,
            quantite,
            prix_unitaire,
            prix_total,
            date_livraison,
            COALESCE(chemin_pdf, '') AS chemin_pdf,
            date_creation
        FROM bons_livraison
        ORDER BY date_livraison DESC, id DESC
    ''')
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    # Grouper par num_bl_grouped
    grouped_map = {}
    for r in rows:
        key = r['num_bl_grouped']
        if key not in grouped_map:
            grouped_map[key] = {
                'id': r['id'],
                'numero_bon_livraison': r.get('numero_bon_livraison') or r['num_bl_grouped'],
                'nom_fournisseur': r.get('nom_fournisseur') or '—',
                'date_livraison': r.get('date_livraison') or '',
                'chemin_pdf': r.get('chemin_pdf') or '',
                'date_creation': r.get('date_creation') or '',
                'articles': [],
                'montant_total': 0.0,
                'quantite_totale': 0,
            }
        grouped_map[key]['articles'].append(r)
        grouped_map[key]['montant_total'] += float(r.get('prix_total', 0) or 0)
        grouped_map[key]['quantite_totale'] = _clean_qty_num(grouped_map[key]['quantite_totale'] + _clean_qty_num(r.get('quantite', 0) or 0))
        if r.get('chemin_pdf') and not grouped_map[key]['chemin_pdf']:
            grouped_map[key]['chemin_pdf'] = r['chemin_pdf']

    # Convertir en liste ordonnée
    result = list(grouped_map.values())
    result.sort(key=lambda x: (x.get('date_livraison') or '', x.get('id') or 0), reverse=True)
    return result


def get_bon_reception_details(numero_bon_livraison: str) -> list[dict]:
    """Retourne toutes les lignes d'articles d'un bon de livraison donné."""
    conn = get_connection()
    cursor = conn.cursor()
    num = (numero_bon_livraison or '').strip()
    cursor.execute(
        '''
        SELECT * FROM bons_livraison
        WHERE numero_bon_livraison = ? OR ('BL-' || id) = ?
        ORDER BY id ASC
        ''',
        (num, num)
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def update_bon_reception_chemin_pdf(numero_bon_livraison: str, chemin_pdf: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    num = (numero_bon_livraison or '').strip()
    cursor.execute(
        '''
        UPDATE bons_livraison SET chemin_pdf = ?
        WHERE numero_bon_livraison = ? OR ('BL-' || id) = ?
        ''',
        (chemin_pdf, num, num)
    )
    conn.commit()
    conn.close()


def delete_bon_reception_by_num(numero_bon_livraison: str, revert_stock: bool = True) -> None:
    """Supprime un bon de réception complet (toutes ses lignes) et réajuste éventuellement le stock."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        num = (numero_bon_livraison or '').strip()
        cursor.execute(
            '''
            SELECT reference_interne, quantite FROM bons_livraison
            WHERE numero_bon_livraison = ? OR ('BL-' || id) = ?
            ''',
            (num, num)
        )
        lines = cursor.fetchall()

        if revert_stock:
            for row in lines:
                ref = row['reference_interne']
                qty = _clean_qty_num(row['quantite'] or 0)
                if ref and qty > 0:
                    cursor.execute('UPDATE pieces SET quantite = MAX(0, quantite - ?) WHERE reference_interne = ?', (qty, ref))

        cursor.execute(
            '''
            DELETE FROM bons_livraison
            WHERE numero_bon_livraison = ? OR ('BL-' || id) = ?
            ''',
            (num, num)
        )
        conn.commit()
    finally:
        conn.close()


def get_all_bons_livraison() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bons_livraison ORDER BY date_livraison DESC, id DESC')
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def delete_bon_livraison(bon_id: int) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM bons_livraison WHERE id = ?', (bon_id,))
    conn.commit()
    conn.close()


def historique_prix_par_reference(reference: str) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM bons_livraison WHERE reference_interne = ? ORDER BY date_livraison ASC, id ASC',
        (reference.strip(),)
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def create_bon_sortie(piece_id: int, engin_id: int, unite: str, quantite: int | float, utilisateur_id: int, kilometrage: str = '') -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    km = (kilometrage or '').strip()
    qty = _clean_qty_num(quantite)
    cursor.execute(
        'INSERT INTO bons_sortie (piece_id, engin_id, unite, quantite, utilisateur_id, kilometrage) VALUES (?, ?, ?, ?, ?, ?)',
        (piece_id, engin_id, unite, qty, utilisateur_id, km)
    )
    bon_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {'id': bon_id, 'piece_id': piece_id, 'engin_id': engin_id, 'unite': unite, 'quantite': qty, 'kilometrage': km}


def get_all_bons_sortie() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT bs.*, p.reference_interne, p.designation AS piece_designation, e.code_engin, e.designation AS engin_designation, e.matricule, u.username
        FROM bons_sortie bs
        LEFT JOIN pieces p ON bs.piece_id = p.id
        LEFT JOIN engins e ON bs.engin_id = e.id
        LEFT JOIN utilisateurs u ON bs.utilisateur_id = u.id
        ORDER BY bs.date_heure DESC, bs.id DESC
    ''')
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def delete_bon_sortie(bon_id: int, restore_stock: bool = True) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    if restore_stock:
        cursor.execute('SELECT piece_id, quantite FROM bons_sortie WHERE id = ?', (bon_id,))
        row = cursor.fetchone()
        if row and row['piece_id']:
            qty = _clean_qty_num(row['quantite'])
            cursor.execute('UPDATE pieces SET quantite = quantite + ? WHERE id = ?', (qty, row['piece_id']))
    cursor.execute('DELETE FROM bons_sortie WHERE id = ?', (bon_id,))
    conn.commit()
    conn.close()


def update_bon_sortie(bon_id: int, piece_id: int, engin_id: int, unite: str, quantite: int | float, kilometrage: str = '') -> None:
    conn = get_connection()
    cursor = conn.cursor()
    km = (kilometrage or '').strip()
    qty = _clean_qty_num(quantite)
    cursor.execute(
        'UPDATE bons_sortie SET piece_id = ?, engin_id = ?, unite = ?, quantite = ?, kilometrage = ? WHERE id = ?',
        (piece_id, engin_id, unite, qty, km, bon_id)
    )
    conn.commit()
    conn.close()


def update_bon_livraison(bon_id: int, data: dict) -> None:
    qty = _clean_qty_num(data.get('quantite', 0) or 0)
    unit = float(data.get('prix_unitaire', 0) or 0)
    total = qty * unit
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''UPDATE bons_livraison SET
            numero_bon_livraison = ?, nom_fournisseur = ?, reference_interne = ?, reference_fournisseur = ?, designation = ?,
            quantite = ?, prix_unitaire = ?, prix_total = ?, date_livraison = ?
           WHERE id = ?''',
        (
            data.get('numero_bon_livraison', '').strip(),
            data.get('nom_fournisseur', '').strip(),
            data.get('reference_interne', '').strip(),
            data.get('reference_fournisseur', '').strip(),
            data.get('designation', '').strip(),
            qty, unit, total,
            data.get('date_livraison'),
            bon_id
        )
    )
    conn.commit()
    conn.close()


def update_piece_stock_after_sortie(piece_id: int, quantite_sortie: int | float) -> None:
    piece = get_piece_by_id(piece_id)
    if not piece:
        return
    old_qty = _clean_qty_num(piece.get('quantite', 0))
    sortie_qty = _clean_qty_num(quantite_sortie)
    new_qty = _clean_qty_num(max(0.0, float(old_qty) - float(sortie_qty)))
    update_piece(piece_id, quantite=new_qty)


def repair_stock_from_bons_reception() -> int:
    """
    Parcourt tous les bons de réception et crée dans 'pieces' les articles
    qui n'y sont pas encore enregistrés. Retourne le nombre de pièces créées.
    Appelé au démarrage pour garantir la cohérence des données historiques.
    """
    conn = get_connection()
    created = 0
    try:
        cursor = conn.cursor()
        # Récupérer toutes les lignes de bons_livraison
        cursor.execute('''
            SELECT reference_interne, reference_fournisseur, designation,
                   unite, quantite, prix_unitaire, date_livraison
            FROM bons_livraison
            WHERE TRIM(COALESCE(reference_interne,'')) != ''
            ORDER BY id ASC
        ''')
        rows = cursor.fetchall()

        # Agréger les quantités par référence (somme de toutes les réceptions)
        agg = {}
        for r in rows:
            ref = (r['reference_interne'] or '').strip()
            if not ref:
                continue
            if ref not in agg:
                agg[ref] = {
                    'reference_fournisseur': (r['reference_fournisseur'] or '').strip(),
                    'designation': (r['designation'] or ref).strip(),
                    'unite': (r['unite'] or 'UNITE').strip() or 'UNITE',
                    'quantite': 0.0,
                    'prix_unitaire': float(r['prix_unitaire'] or 0),
                    'date_livraison': r['date_livraison'],
                }
            agg[ref]['quantite'] += float(r['quantite'] or 0)
            # Garder le prix le plus récent et la date la plus récente
            if r['prix_unitaire']:
                agg[ref]['prix_unitaire'] = float(r['prix_unitaire'])
            if r['date_livraison']:
                agg[ref]['date_livraison'] = r['date_livraison']

        for ref, data in agg.items():
            cursor.execute('SELECT id, quantite FROM pieces WHERE reference_interne = ?', (ref,))
            existing = cursor.fetchone()
            if not existing:
                # Créer la pièce manquante
                qty = _clean_qty_num(data['quantite'])
                pu = data['prix_unitaire']
                cursor.execute(
                    '''
                    INSERT INTO pieces (
                        reference_interne, reference_fournisseur, designation,
                        quantite, unite, nouveau_prix_unitaire, ancien_prix_unitaire,
                        prix_total_nouveau, date_livraison
                    ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
                    ''',
                    (
                        ref, data['reference_fournisseur'], data['designation'],
                        qty, data['unite'], pu, qty * pu, data['date_livraison']
                    )
                )
                created += 1
        conn.commit()
    finally:
        conn.close()
    return created



def get_engin_categories() -> list[str]:
    default_cats = ['CAMION', 'CLARCK', 'VEHICULE_LEGER', 'REMORQUE', 'PARC']
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT categorie FROM engins WHERE categorie IS NOT NULL AND TRIM(categorie) != ""')
    db_cats = [r['categorie'].strip() for r in cursor.fetchall() if r['categorie']]
    conn.close()
    
    combined = list(default_cats)
    for c in db_cats:
        c_norm = 'VEHICULE_LEGER' if c.lower() == 'leger' else c.upper()
        if not any(x.upper() == c_norm for x in combined):
            combined.append(c_norm)
    return combined


def get_engin_designations_by_category(categorie: str | list[str] | tuple = 'Tous') -> list[str]:
    if isinstance(categorie, str):
        if not categorie or categorie.lower() in ('tous', 'toutes'):
            cats = []
        else:
            cats = [c.strip() for c in categorie.split(',') if c.strip()]
    elif isinstance(categorie, (list, tuple)):
        cats = list(categorie)
    else:
        cats = []

    cats_normalized = []
    for c in cats:
        if not c or c.lower() in ('tous', 'toutes'):
            continue
        if c.lower() == 'leger':
            cats_normalized.append('VEHICULE_LEGER')
        else:
            cats_normalized.append(c.upper())

    conn = get_connection()
    cursor = conn.cursor()
    if not cats_normalized:
        cursor.execute('SELECT DISTINCT designation FROM engins WHERE designation IS NOT NULL ORDER BY designation')
    else:
        conditions = []
        params = []
        for c in cats_normalized:
            conditions.append('LOWER(categorie) LIKE ?')
            params.append(f'%{c.lower()}%')
            if 'VEHICULE_LEGER' in c:
                conditions.append('LOWER(categorie) LIKE ?')
                params.append('%leger%')
        where_clause = ' OR '.join(conditions)
        cursor.execute(
            f'SELECT DISTINCT designation FROM engins WHERE designation IS NOT NULL AND ({where_clause}) ORDER BY designation',
            params
        )
    designations = [r['designation'].strip() for r in cursor.fetchall() if r['designation']]
    conn.close()
    return designations


def get_dashboard_stats() -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) AS total FROM engins')
    total_engins = cursor.fetchone()['total']
    
    cursor.execute('SELECT COUNT(*) AS total FROM pieces')
    total_pieces = cursor.fetchone()['total']
    
    cursor.execute('SELECT COALESCE(SUM(nouveau_prix_unitaire * quantite), 0) AS total FROM pieces')
    total_valeur = float(cursor.fetchone()['total'] or 0)
    
    cursor.execute('SELECT COUNT(*) AS total FROM bons_sortie WHERE date_heure >= date("now", "start of month")')
    sorties_mois = cursor.fetchone()['total']

    cursor.execute('SELECT COUNT(*) AS total FROM bons_livraison WHERE date_creation >= date("now", "start of month")')
    livraisons_mois = cursor.fetchone()['total']

    # Stock critique / faible (quantite <= seuil_alerte)
    cursor.execute('SELECT COUNT(*) AS total FROM pieces WHERE quantite <= COALESCE(seuil_alerte, 5)')
    stock_faible = cursor.fetchone()['total']

    # Répartition par catégorie d'engin
    cursor.execute('''
        SELECT 
            SUM(CASE WHEN LOWER(e.categorie) LIKE '%camion%' THEN 1 ELSE 0 END) as count_camion,
            SUM(CASE WHEN LOWER(e.categorie) LIKE '%clarck%' THEN 1 ELSE 0 END) as count_clarck,
            SUM(CASE WHEN LOWER(e.categorie) LIKE '%leger%' OR LOWER(e.categorie) LIKE '%véhicule%' THEN 1 ELSE 0 END) as count_leger,
            SUM(CASE WHEN LOWER(e.categorie) LIKE '%remorque%' THEN 1 ELSE 0 END) as count_remorque
        FROM engins e
    ''')
    row = cursor.fetchone()
    c_camion = int(row['count_camion'] or 0)
    c_clarck = int(row['count_clarck'] or 0)
    c_leger = int(row['count_leger'] or 0)
    c_remorque = int(row['count_remorque'] or 0)
    c_autres = max(0, total_engins - (c_camion + c_clarck + c_leger + c_remorque))

    conn.close()

    # Calcul pourcentage de disponibilité/santé du stock
    stock_health = 100 if total_pieces == 0 else max(0, int(round((total_pieces - stock_faible) / total_pieces * 100)))

    return {
        'total_engins': total_engins,
        'total_pieces': total_pieces,
        'total_valeur_stock': total_valeur,
        'sorties_mois': sorties_mois,
        'livraisons_mois': livraisons_mois,
        'stock_faible': stock_faible,
        'stock_health': stock_health,
        'cat_camion': c_camion,
        'cat_clarck': c_clarck,
        'cat_leger': c_leger,
        'cat_remorque': c_remorque,
        'cat_autres': c_autres,
    }



def ensure_demo_data() -> None:
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute('SELECT id, code_engin FROM engins ORDER BY id')
        engins = cursor.fetchall()
        engin_map = {row['code_engin']: row['id'] for row in engins}
        if not engin_map:
            engins = [
                ('CL-001', 'CLARCK', 'Clarck 10T', 'AB-123-CD'),
                ('TR-012', 'CAMION', 'Camion 4x4', 'XY-456-ZA'),
                ('VL-005', 'VEHICULE_LEGER', 'Véhicule léger service', 'TT-998-PP'),
            ]
            cursor.executemany('INSERT INTO engins (code_engin, categorie, designation, matricule) VALUES (?, ?, ?, ?)', engins)
            conn.commit()
            cursor.execute('SELECT id, code_engin FROM engins ORDER BY id')
            engin_map = {row['code_engin']: row['id'] for row in cursor.fetchall()}

        cursor.execute('SELECT id, nom FROM familles_pieces ORDER BY id')
        famille_ids = {row['nom'].upper(): row['id'] for row in cursor.fetchall()}
        for family_name in ['CARROSSERIE', 'MOTEUR', 'TRANSMISSION', 'FREINAGE', 'ELECTRIQUE', 'SUSPENSION', 'LAVAGE']:
            if family_name not in famille_ids:
                cursor.execute('INSERT INTO familles_pieces (nom) VALUES (?)', (family_name,))
        conn.commit()

        cursor.execute('SELECT id, nom FROM familles_pieces ORDER BY id')
        famille_ids = {row['nom'].upper(): row['id'] for row in cursor.fetchall()}

        cursor.execute('SELECT COUNT(*) FROM pieces')
        if cursor.fetchone()[0] == 0:
            samples = [
                ('PI-001', 'FR-001', 'Bougie moteur', 'CL-001', 'MOTEUR', '2025-01-15', 12, 'Atelier', 'UNITE', 150, 180),
                ('PI-002', 'FR-002', 'Plaque carrosserie', 'TR-012', 'CARROSSERIE', '2025-02-12', 4, 'Magasin A', 'JEUX', 420, 460),
                ('PI-003', 'FR-003', 'Disque frein', 'VL-005', 'FREINAGE', '2025-03-01', 8, 'Magasin B', 'UNITE', 80, 95),
            ]
            for ref, fournisseur, designation, code_engin, famille_name, date, qty, emplacement, unite, ancien, nouveau in samples:
                engin_id = engin_map.get(code_engin)
                famille_id = famille_ids.get(famille_name.upper())
                if not engin_id or not famille_id:
                    continue
                cursor.execute(
                    'INSERT INTO pieces (reference_interne, reference_fournisseur, designation, engin_id, famille_id, date_livraison, quantite, emplacement, unite, ancien_prix_unitaire, nouveau_prix_unitaire, prix_total_nouveau) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (ref, fournisseur, designation, engin_id, famille_id, date, qty, emplacement, unite, ancien, nouveau, nouveau * qty)
                )

        conn.commit()
    finally:
        conn.close()


def backup_database(dest_path: str) -> bool:
    try:
        import shutil
        db_path = get_db_path()
        shutil.copy2(db_path, dest_path)
        return True
    except Exception:
        return False


def reset_database() -> None:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM bons_sortie')
        cursor.execute('DELETE FROM bons_livraison')
        cursor.execute('DELETE FROM pieces')
        cursor.execute('DELETE FROM engins')
        conn.commit()
    finally:
        conn.close()


if __name__ == '__main__':
    initialize_database()
    ensure_demo_data()
    print('DB ok')

