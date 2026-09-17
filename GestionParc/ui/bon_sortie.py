import os
from datetime import datetime
from pathlib import Path
from tkinter import ttk, messagebox

import customtkinter as ctk

from auth.auth_manager import list_users
from database.db_manager import (
    create_bon_sortie, delete_bon_sortie, get_all_bons_sortie,
    get_all_engins, get_all_pieces, get_engin_by_code,
    get_piece_by_reference, get_piece_by_designation, update_bon_sortie,
    get_piece_by_id, get_connection, get_all_operateurs, save_operateur
)
from services.pdf_generator import generate_bon_sortie_pdf
from ui.pdf_viewer import ouvrir_pdf_viewer
from ui.theme import COLORS, FONTS, UNITES, format_qty, parse_qty
from ui.widgets import (
    make_input, make_primary_button, make_secondary_button, make_danger_button,
    make_combobox, DatePickerWidget, bind_tree_clear_selection
)


class BonSortieFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color='transparent')
        self.grid_columnconfigure(0, weight=1)
        self.form_fields = []
        self._selected_bon_id = None
        self._selected_bon_data = None
        self._all_pieces = []          # cache des pièces pour la recherche dynamique
        self._syncing = False           # verrou anti-boucle de synchronisation
        self.build()

    def build(self):
        self.header = ctk.CTkFrame(self, fg_color='transparent')
        self.header.grid(row=0, column=0, sticky='ew', padx=18, pady=(16, 6))
        ctk.CTkLabel(self.header, text='Bon de sortie', font=FONTS['title_large'], text_color=COLORS['text_primary']).pack(anchor='w')
        ctk.CTkLabel(self.header, text='Sortie de pièces vers engin — Date, N° OR, Opérateur, Kilométrage & Impression PDF', font=FONTS['body'], text_color=COLORS['text_secondary']).pack(anchor='w')

        form = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=16, border_width=1, border_color=COLORS['border'])
        form.grid(row=1, column=0, sticky='ew', padx=18, pady=(0, 10))

        self._all_pieces = get_all_pieces()
        pieces_designations = [p['designation'] for p in self._all_pieces]
        pieces_refs        = [p['reference_interne'] for p in self._all_pieces]
        engins_codes       = [e['code_engin'] for e in get_all_engins()]
        operateurs_list    = get_all_operateurs()

        # ── Rangée 1 : Pièce & Engin ──────────────────────────────────────────
        ctk.CTkLabel(form, text='🔍 Désignation pièce', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 2), sticky='w')
        self.e_designation = make_combobox(form, pieces_designations if pieces_designations else ['Aucune pièce'], width=270)
        self.e_designation.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 8), sticky='w')
        if pieces_designations:
            self.e_designation.set(pieces_designations[0])
        self.e_designation.configure(command=self._on_designation_selected)
        self.e_designation._entry.bind('<KeyRelease>', self._on_designation_typed)
        self.form_fields.append(self.e_designation)

        ctk.CTkLabel(form, text='Référence pièce', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=2, padx=8, pady=(10, 2), sticky='w')
        self.e_ref = make_combobox(form, pieces_refs if pieces_refs else ['Aucune pièce'], width=150)
        if pieces_refs:
            self.e_ref.set(pieces_refs[0])
        self.e_ref.grid(row=1, column=2, padx=8, pady=(0, 8), sticky='w')
        self.e_ref.configure(command=self._on_piece_selected)
        self.e_ref._entry.bind('<KeyRelease>', self._on_ref_typed)
        self.form_fields.append(self.e_ref)

        ctk.CTkLabel(form, text='Code engin', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=3, padx=8, pady=(10, 2), sticky='w')
        self.e_code_engin = make_combobox(form, engins_codes if engins_codes else ['Aucun engin'], width=140)
        if engins_codes:
            self.e_code_engin.set(engins_codes[0])
        self.e_code_engin.grid(row=1, column=3, padx=8, pady=(0, 8), sticky='w')
        self.form_fields.append(self.e_code_engin)

        ctk.CTkLabel(form, text='Unité', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=4, padx=8, pady=(10, 2), sticky='w')
        self.combo_unite = make_combobox(form, UNITES, width=105)
        self.combo_unite.grid(row=1, column=4, padx=8, pady=(0, 8), sticky='w')
        self.form_fields.append(self.combo_unite)

        ctk.CTkLabel(form, text='Quantité', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=5, padx=8, pady=(10, 2), sticky='w')
        self.e_qte = make_input(form, '1', 80)
        self.e_qte.grid(row=1, column=5, padx=8, pady=(0, 8), sticky='w')
        self.form_fields.append(self.e_qte)

        # ── Rangée 2 : Date Sortie, N° OR, Opérateur, Kilométrage ─────────────
        ctk.CTkLabel(form, text='📅 Date Sortie', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=2, column=0, padx=10, pady=(4, 2), sticky='w')
        self.e_date = DatePickerWidget(form, placeholder='AAAA-MM-JJ', width=130, default_value=datetime.now().strftime('%Y-%m-%d'))
        self.e_date.grid(row=3, column=0, padx=10, pady=(0, 10), sticky='w')
        self.form_fields.append(self.e_date)

        ctk.CTkLabel(form, text='N° Ordre Rép. (OR)', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=2, column=1, padx=8, pady=(4, 2), sticky='w')
        self.e_or = make_input(form, 'ex: OR-2025-001', 130)
        self.e_or.grid(row=3, column=1, padx=8, pady=(0, 10), sticky='w')
        self.form_fields.append(self.e_or)

        ctk.CTkLabel(form, text='👤 Opérateur', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=2, column=2, columnspan=2, padx=8, pady=(4, 2), sticky='w')
        self.combo_operateur = make_combobox(form, operateurs_list if operateurs_list else ['Benkerrou Tarek'], width=290)
        if operateurs_list:
            self.combo_operateur.set(operateurs_list[0])
        self.combo_operateur.grid(row=3, column=2, columnspan=2, padx=8, pady=(0, 10), sticky='w')
        self.form_fields.append(self.combo_operateur)

        ctk.CTkLabel(form, text='Kilométrage', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=2, column=4, columnspan=2, padx=8, pady=(4, 2), sticky='w')
        self.e_km = make_input(form, 'ex: 125 000 KM', 190)
        self.e_km.grid(row=3, column=4, columnspan=2, padx=8, pady=(0, 10), sticky='w')
        self.form_fields.append(self.e_km)

        # ── Rangée 3 : Boutons d'action ───────────────────────────────────────
        btn_row = ctk.CTkFrame(form, fg_color='transparent')
        btn_row.grid(row=4, column=0, columnspan=6, padx=10, pady=(2, 12), sticky='w')

        self.btn_val = make_primary_button(btn_row, '✅ Valider & PDF', self.validate_and_save, width=170)
        self.btn_val.pack(side='left', padx=(0, 6))

        self.btn_view_pdf = make_primary_button(btn_row, '📄 Voir PDF', self.open_selected_pdf, width=130)
        self.btn_view_pdf.pack(side='left', padx=(0, 6))
        self.btn_view_pdf.configure(state='disabled')

        self.btn_modif = make_secondary_button(btn_row, '✏️ Modifier', self.update_selected, width=120)
        self.btn_modif.pack(side='left', padx=(0, 6))
        self.btn_modif.configure(state='disabled')

        btn_del = make_danger_button(btn_row, '🗑️ Supprimer', self.delete_selected_sortie, width=130)
        btn_del.pack(side='left', padx=(0, 6))

        btn_clear = make_secondary_button(btn_row, 'Vider', self.clear_fields, width=100)
        btn_clear.pack(side='left')

        # ── Zone info ────────────────────────────────────────────────────────
        self.info = ctk.CTkLabel(self, text='Sélectionnez un bon pour afficher son PDF, ou effectuez une nouvelle sortie.',
                                 font=FONTS['body'], text_color=COLORS['text_secondary'], justify='left')
        self.info.grid(row=2, column=0, sticky='ew', padx=18, pady=(0, 6))

        # ── Tableau ──────────────────────────────────────────────────────────
        table_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=16, border_width=1, border_color=COLORS['border'])
        table_frame.grid(row=3, column=0, sticky='nsew', padx=18, pady=(0, 16))
        self.grid_rowconfigure(3, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            table_frame,
            columns=('id', 'date_sortie', 'or', 'ref', 'piece', 'engin', 'unite', 'qte', 'km', 'operateur'),
            show='headings', height=12
        )
        self.tree.heading('id', text='ID')
        self.tree.heading('date_sortie', text='Date Sortie')
        self.tree.heading('or', text='N° OR')
        self.tree.heading('ref', text='Réf Pièce')
        self.tree.heading('piece', text='Désignation Pièce')
        self.tree.heading('engin', text='Code Engin')
        self.tree.heading('unite', text='Unité')
        self.tree.heading('qte', text='Qté')
        self.tree.heading('km', text='Kilométrage')
        self.tree.heading('operateur', text='Opérateur')

        self.tree.column('id', width=45, anchor='center', stretch=False)
        self.tree.column('date_sortie', width=95, anchor='center', stretch=False)
        self.tree.column('or', width=95, anchor='center', stretch=False)
        self.tree.column('ref', width=100, anchor='center', stretch=False)
        self.tree.column('piece', width=170, anchor='w', stretch=True)
        self.tree.column('engin', width=90, anchor='center', stretch=False)
        self.tree.column('unite', width=75, anchor='center', stretch=False)
        self.tree.column('qte', width=65, anchor='center', stretch=False)
        self.tree.column('km', width=105, anchor='center', stretch=False)
        self.tree.column('operateur', width=130, anchor='center', stretch=True)

        self.tree.pack(fill='both', expand=True, padx=10, pady=10)

        self.tree.bind('<ButtonRelease-1>', self.on_row_select)
        self.tree.bind('<Double-1>', lambda e: self.open_selected_pdf())
        bind_tree_clear_selection(self.tree, clear_callback=self.clear_fields)
        self.refresh()

    def _find_piece_by_designation(self, designation: str):
        """Recherche une pièce par désignation exacte ou partielle (insensible à la casse)."""
        desig_lower = designation.strip().lower()
        if not desig_lower:
            return None
        for p in self._all_pieces:
            if (p.get('designation') or '').strip().lower() == desig_lower:
                return p
        for p in self._all_pieces:
            if (p.get('designation') or '').strip().lower().startswith(desig_lower):
                return p
        for p in self._all_pieces:
            if desig_lower in (p.get('designation') or '').strip().lower():
                return p
        return None

    def _on_designation_selected(self, choice=None):
        """Appelé quand l'utilisateur choisit une désignation dans le dropdown."""
        if self._syncing:
            return
        desig = self.e_designation.get().strip()
        piece = self._find_piece_by_designation(desig)
        if piece:
            self._syncing = True
            self.e_ref.set(piece['reference_interne'])
            self._syncing = False
            self._apply_piece_info(piece)

    def _on_designation_typed(self, event=None):
        """Filtre la liste de désignations en live pendant la saisie."""
        if self._syncing:
            return
        typed = self.e_designation.get().strip().lower()
        if not typed:
            all_desig = [p['designation'] for p in self._all_pieces]
            self.e_designation.configure(values=all_desig)
            return
        filtered = [p['designation'] for p in self._all_pieces
                    if typed in (p.get('designation') or '').lower()]
        self.e_designation.configure(values=filtered if filtered else [self.e_designation.get()])
        if len(filtered) == 1:
            piece = self._find_piece_by_designation(filtered[0])
            if piece:
                self._syncing = True
                self.e_ref.set(piece['reference_interne'])
                self._syncing = False
                self._apply_piece_info(piece)
        elif len(filtered) == 0:
            piece = self._find_piece_by_designation(typed)
            if piece:
                self._syncing = True
                self.e_ref.set(piece['reference_interne'])
                self.e_designation.set(piece['designation'])
                self._syncing = False
                self._apply_piece_info(piece)

    def _apply_piece_info(self, piece: dict):
        """Met à jour Unité et affiche le stock en temps réel après identification d'une pièce."""
        if piece.get('id'):
            fresh_p = get_piece_by_id(piece['id'])
            if fresh_p:
                piece = fresh_p
        if piece.get('unite'):
            self.combo_unite.set(piece['unite'])
        stock = piece.get('quantite', 0)
        unit = piece.get('unite', 'UNITE')
        empl = f"  •  Emplacement : {piece['emplacement']}" if piece.get('emplacement') else ""
        self.info.configure(
            text=f"✅ Pièce : {piece.get('designation', '')}  •  Réf : {piece.get('reference_interne', '')}  •  Stock disponible : {format_qty(stock)} {unit}{empl}",
            text_color=COLORS['success'] if float(stock or 0) > 0 else COLORS['danger']
        )

    def _on_ref_typed(self, event=None):
        """Filtre la liste de références en live pendant la saisie et synchronise la désignation."""
        if self._syncing:
            return
        typed = self.e_ref.get().strip().lower()
        if not typed:
            all_refs = [p['reference_interne'] for p in self._all_pieces]
            self.e_ref.configure(values=all_refs)
            return
        filtered = [p['reference_interne'] for p in self._all_pieces
                    if typed in (p.get('reference_interne') or '').lower()]
        self.e_ref.configure(values=filtered if filtered else [self.e_ref.get()])
        if len(filtered) == 1:
            piece = get_piece_by_reference(filtered[0])
            if piece:
                self._syncing = True
                self.e_designation.set(piece.get('designation', ''))
                self._syncing = False
                self._apply_piece_info(piece)
        elif len(filtered) == 0:
            piece = get_piece_by_reference(typed)
            if piece:
                self._syncing = True
                self.e_designation.set(piece.get('designation', ''))
                self.e_ref.set(piece['reference_interne'])
                self._syncing = False
                self._apply_piece_info(piece)

    def _on_piece_selected(self, choice=None):
        """Appelé quand l'utilisateur choisit une référence dans le dropdown."""
        if self._syncing:
            return
        ref = self.e_ref.get().strip()
        if ref:
            piece = get_piece_by_reference(ref)
            if piece:
                self._syncing = True
                self.e_designation.set(piece.get('designation', ''))
                self._syncing = False
                self._apply_piece_info(piece)

    def clear_fields(self):
        self._all_pieces = get_all_pieces()
        pieces_refs  = [p['reference_interne'] for p in self._all_pieces]
        pieces_desig = [p['designation'] for p in self._all_pieces]

        if hasattr(self, 'e_ref'):
            self.e_ref.configure(values=pieces_refs if pieces_refs else ['Aucune pièce'])
            if pieces_refs:
                self.e_ref.set(pieces_refs[0])

        if hasattr(self, 'e_designation'):
            self.e_designation.configure(values=pieces_desig if pieces_desig else ['Aucune pièce'])
            if pieces_desig:
                self.e_designation.set(pieces_desig[0])

        if self._all_pieces:
            self._apply_piece_info(self._all_pieces[0])

        engins = get_all_engins()
        engins_codes = [e['code_engin'] for e in engins]
        if hasattr(self, 'e_code_engin') and engins_codes:
            self.e_code_engin.configure(values=engins_codes)
            self.e_code_engin.set(engins_codes[0])

        operateurs_list = get_all_operateurs()
        if hasattr(self, 'combo_operateur') and operateurs_list:
            self.combo_operateur.configure(values=operateurs_list)
            self.combo_operateur.set(operateurs_list[0])

        self.e_qte.delete(0, 'end')
        self.e_km.delete(0, 'end')
        self.e_or.delete(0, 'end')
        self.e_date.delete(0, 'end')
        self.e_date.insert(0, datetime.now().strftime('%Y-%m-%d'))

        self._selected_bon_id = None
        self._selected_bon_data = None
        self.btn_modif.configure(state='disabled')
        self.btn_view_pdf.configure(state='disabled')
        self.btn_val.configure(state='normal')
        self.info.configure(text='Prêt pour une nouvelle sortie — saisissez la désignation ou la référence.', text_color=COLORS['text_secondary'])

    def on_row_select(self, event):
        item = self.tree.selection()
        if not item:
            return
        values = self.tree.item(item[0], 'values')
        if not values:
            return
        self.clear_fields()
        self._selected_bon_id = int(values[0])

        # Retrouver les détails du bon depuis la liste
        bons = get_all_bons_sortie()
        for b in bons:
            if b['id'] == self._selected_bon_id:
                self._selected_bon_data = b
                break

        b = self._selected_bon_data or {}
        ref_val = b.get('reference_interne', '')
        desig_val = b.get('piece_designation', b.get('designation', ''))
        self.e_ref.set(ref_val)
        if hasattr(self, 'e_designation'):
            self.e_designation.set(desig_val)
        self.e_code_engin.set(b.get('code_engin', ''))
        self.combo_unite.set(b.get('unite', 'UNITE'))
        self.e_qte.delete(0, 'end')
        self.e_qte.insert(0, format_qty(b.get('quantite', 1)))

        self.e_km.delete(0, 'end')
        km_val = b.get('kilometrage', '')
        if km_val and km_val != '—':
            self.e_km.insert(0, str(km_val))

        self.e_or.delete(0, 'end')
        or_val = b.get('ordre_reparation', '')
        if or_val and or_val != '—':
            self.e_or.insert(0, str(or_val))

        self.e_date.delete(0, 'end')
        date_s = b.get('date_sortie') or (b.get('date_heure', '')[:10]) or datetime.now().strftime('%Y-%m-%d')
        self.e_date.insert(0, str(date_s))

        op_nom = b.get('nom_operateur') or b.get('username') or 'Benkerrou Tarek'
        self.combo_operateur.set(op_nom)

        self.btn_modif.configure(state='normal')
        self.btn_view_pdf.configure(state='normal')
        self.btn_val.configure(state='disabled')
        self.info.configure(
            text=f'Bon ID {self._selected_bon_id} sélectionné — "{desig_val}" ({ref_val}) — double-clic pour PDF.',
            text_color=COLORS['text_secondary']
        )

    def open_selected_pdf(self):
        """Ouvre le visualiseur PDF pour le bon sélectionné."""
        if not self._selected_bon_id or not self._selected_bon_data:
            messagebox.showwarning('Attention', 'Veuillez sélectionner un bon de sortie dans le tableau.')
            return

        b = self._selected_bon_data
        pdf_path = b.get('chemin_pdf')

        if not pdf_path or not os.path.exists(pdf_path):
            op_nom = b.get('nom_operateur') or b.get('username') or 'Benkerrou Tarek'
            pdf_path = generate_bon_sortie_pdf({
                'bon_id': b['id'],
                'reference_interne': b.get('reference_interne', ''),
                'reference_fournisseur': b.get('reference_fournisseur', ''),
                'designation_piece': b.get('piece_designation', b.get('designation', '')),
                'code_engin': b.get('code_engin', ''),
                'matricule': b.get('matricule', ''),
                'designation_engin': b.get('engin_designation', ''),
                'unite': b.get('unite', 'UNITE'),
                'quantite': b.get('quantite', 0),
                'kilometrage': b.get('kilometrage', ''),
                'ordre_reparation': b.get('ordre_reparation', ''),
                'nom_operateur': op_nom,
                'date_sortie': b.get('date_sortie') or (b.get('date_heure', '')[:10]),
                'utilisateur': op_nom
            })

        ouvrir_pdf_viewer(self, pdf_path, f"Bon de Sortie BS-{b['id']}")

    def update_selected(self):
        if not self._selected_bon_id:
            messagebox.showwarning('Attention', 'Sélectionnez un bon de sortie dans le tableau.')
            return
        ref = self.e_ref.get().strip()
        code_engin = self.e_code_engin.get().strip()
        unit = self.combo_unite.get().strip() or 'UNITE'
        km = self.e_km.get().strip()
        or_num = self.e_or.get().strip()
        nom_op = self.combo_operateur.get().strip() or 'Benkerrou Tarek'
        date_s = self.e_date.get().strip() or datetime.now().strftime('%Y-%m-%d')

        try:
            qte = parse_qty(self.e_qte.get())
            if qte <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror('Erreur', 'Quantité invalide.')
            return
        desig = self.e_designation.get().strip() if hasattr(self, 'e_designation') else ''
        piece = get_piece_by_reference(ref) or (get_piece_by_designation(desig) if desig else None)
        engin = get_engin_by_code(code_engin)
        if not piece or not engin:
            messagebox.showerror('Erreur', 'Référence pièce ou code engin introuvable.')
            return
        if messagebox.askyesno('Confirmation', f'Modifier le bon de sortie ID {self._selected_bon_id} ?'):
            save_operateur(nom_op)
            update_bon_sortie(
                self._selected_bon_id, piece['id'], engin['id'], unit, qte,
                kilometrage=km, ordre_reparation=or_num, nom_operateur=nom_op, date_sortie=date_s
            )

            # Régénérer le PDF avec les nouvelles données
            pdf_path = generate_bon_sortie_pdf({
                'bon_id': self._selected_bon_id,
                'reference_interne': piece['reference_interne'],
                'reference_fournisseur': piece.get('reference_fournisseur', ''),
                'designation_piece': piece.get('designation', ''),
                'code_engin': engin['code_engin'],
                'matricule': engin.get('matricule', ''),
                'designation_engin': engin['designation'],
                'unite': unit,
                'quantite': qte,
                'kilometrage': km,
                'ordre_reparation': or_num,
                'nom_operateur': nom_op,
                'date_sortie': date_s,
                'utilisateur': nom_op
            })
            conn = get_connection()
            conn.execute('UPDATE bons_sortie SET chemin_pdf = ? WHERE id = ?', (pdf_path, self._selected_bon_id))
            conn.commit()
            conn.close()

            self.clear_fields()
            self.refresh()
            self.info.configure(text=f'Bon ID {self._selected_bon_id} modifié avec succès.')

    def delete_selected_sortie(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning('Attention', 'Veuillez sélectionner un bon de sortie à supprimer dans le tableau.')
            return
        values = self.tree.item(selected[0], 'values')
        if not values:
            return

        bon_id = values[0]
        if messagebox.askyesno('Confirmation', f'Voulez-vous vraiment supprimer le bon de sortie ID {bon_id} et réintégrer les pièces au stock ?'):
            delete_bon_sortie(int(bon_id), restore_stock=True)
            self.clear_fields()
            self.refresh()
            self.info.configure(text=f'Bon de sortie ID {bon_id} supprimé. Stock réintégré.')

    def refresh(self):
        self._all_pieces = get_all_pieces()
        pieces_refs  = [p['reference_interne'] for p in self._all_pieces]
        pieces_desig = [p['designation'] for p in self._all_pieces]

        if hasattr(self, 'e_ref'):
            if pieces_refs:
                self.e_ref.configure(values=pieces_refs)
                if not self.e_ref.get().strip() or self.e_ref.get() == 'Aucune pièce':
                    self.e_ref.set(pieces_refs[0])
            else:
                self.e_ref.configure(values=['Aucune pièce'])
                self.e_ref.set('Aucune pièce')

        if hasattr(self, 'e_designation'):
            if pieces_desig:
                self.e_designation.configure(values=pieces_desig)
                cur = self.e_designation.get().strip()
                if not cur or cur == 'Aucune pièce':
                    self.e_designation.set(pieces_desig[0])
            else:
                self.e_designation.configure(values=['Aucune pièce'])
                self.e_designation.set('Aucune pièce')

        engins = get_all_engins()
        engins_codes = [e['code_engin'] for e in engins]
        if hasattr(self, 'e_code_engin'):
            if engins_codes:
                self.e_code_engin.configure(values=engins_codes)
                if not self.e_code_engin.get().strip() or self.e_code_engin.get() == 'Aucun engin':
                    self.e_code_engin.set(engins_codes[0])
            else:
                self.e_code_engin.configure(values=['Aucun engin'])
                self.e_code_engin.set('Aucun engin')

        operateurs_list = get_all_operateurs()
        if hasattr(self, 'combo_operateur') and operateurs_list:
            self.combo_operateur.configure(values=operateurs_list)

        for row in self.tree.get_children():
            self.tree.delete(row)
        for bon in get_all_bons_sortie():
            date_s_val = bon.get('date_sortie') or (bon.get('date_heure', '')[:10]) or '—'
            self.tree.insert('', 'end', values=(
                bon['id'],
                date_s_val,
                bon.get('ordre_reparation') or '—',
                bon.get('reference_interne', ''),
                bon.get('piece_designation', ''),
                bon.get('code_engin', ''),
                bon.get('unite', ''),
                format_qty(bon.get('quantite', 0)),
                bon.get('kilometrage') or '—',
                bon.get('nom_operateur') or bon.get('username') or 'Benkerrou Tarek',
            ))

    def validate_and_save(self):
        ref = self.e_ref.get().strip()
        code_engin = self.e_code_engin.get().strip()
        unit = self.combo_unite.get().strip() or 'UNITE'
        km = self.e_km.get().strip()
        or_num = self.e_or.get().strip()
        nom_op = self.combo_operateur.get().strip() or 'Benkerrou Tarek'
        date_s = self.e_date.get().strip() or datetime.now().strftime('%Y-%m-%d')

        try:
            qte = parse_qty(self.e_qte.get())
            if qte <= 0:
                raise ValueError
        except ValueError:
            self.info.configure(text='Quantité invalide.', text_color=COLORS['danger'])
            return
        desig = self.e_designation.get().strip() if hasattr(self, 'e_designation') else ''
        piece = get_piece_by_reference(ref) or (get_piece_by_designation(desig) if desig else None)
        engin = get_engin_by_code(code_engin)
        if not piece or not engin:
            self.info.configure(text='Référence pièce ou code engin introuvable.', text_color=COLORS['danger'])
            return
        if float(piece.get('quantite', 0)) < qte:
            dispo = format_qty(piece.get('quantite', 0))
            u = piece.get('unite', 'UNITE')
            self.info.configure(text=f'Stock insuffisant pour cette sortie (Stock disponible : {dispo} {u}).', text_color=COLORS['danger'])
            return

        save_operateur(nom_op)
        user = list_users()[0] if list_users() else {'username': 'admin'}
        try:
            bon = create_bon_sortie(
                piece['id'], engin['id'], unit, qte, user.get('id', 1),
                kilometrage=km, ordre_reparation=or_num, nom_operateur=nom_op, date_sortie=date_s
            )
        except ValueError as exc:
            self.info.configure(text=str(exc), text_color=COLORS['danger'])
            return

        pdf_path = generate_bon_sortie_pdf({
            'bon_id': bon['id'],
            'reference_interne': piece['reference_interne'],
            'reference_fournisseur': piece.get('reference_fournisseur', ''),
            'designation_piece': piece.get('designation', ''),
            'code_engin': engin['code_engin'],
            'matricule': engin.get('matricule', ''),
            'designation_engin': engin['designation'],
            'unite': unit,
            'quantite': qte,
            'kilometrage': km,
            'ordre_reparation': or_num,
            'nom_operateur': nom_op,
            'date_sortie': date_s,
            'utilisateur': nom_op
        })

        # Mettre à jour chemin_pdf dans la BDD
        conn = get_connection()
        conn.execute('UPDATE bons_sortie SET chemin_pdf = ? WHERE id = ?', (pdf_path, bon['id']))
        conn.commit()
        conn.close()

        self.clear_fields()
        self.refresh()
        self.info.configure(text=f'Sortie enregistrée. PDF : {pdf_path}', text_color=COLORS['success'])

        # Ouvrir la visionneuse PDF modale
        ouvrir_pdf_viewer(self, pdf_path, f"Bon de Sortie BS-{bon['id']}")
