import customtkinter as ctk
from pathlib import Path
from tkinter import ttk, messagebox
from datetime import datetime

from database.db_manager import (
    create_bon_livraison, delete_bon_livraison, update_bon_livraison,
    get_all_bons_livraison, get_piece_by_reference, update_piece, get_all_pieces
)
from ui.theme import COLORS, FONTS, format_money
from ui.widgets import (
    make_input, make_primary_button, make_secondary_button, make_danger_button, make_combobox,
    DatePickerWidget, bind_tree_clear_selection
)


class BonLivraisonFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color='transparent')
        self.grid_columnconfigure(0, weight=1)
        self.form_fields = []
        self._selected_bon_id = None
        self.build()

    def build(self):
        self.header = ctk.CTkFrame(self, fg_color='transparent')
        self.header.grid(row=0, column=0, sticky='ew', padx=18, pady=(18, 8))
        ctk.CTkLabel(self.header, text='Bon de livraison', font=FONTS['title_large'], text_color=COLORS['text_primary']).pack(anchor='w')
        ctk.CTkLabel(self.header, text='Historique et ajouts de livraisons — Filtres par date et recherche', font=FONTS['body'], text_color=COLORS['text_secondary']).pack(anchor='w')

        # ── Formulaire de Saisie ──────────────────────────────────────────────
        form = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=16, border_width=1, border_color=COLORS['border'])
        form.grid(row=1, column=0, sticky='ew', padx=18, pady=(0, 12))

        # Ligne 1 : Références
        ctk.CTkLabel(form, text='Référence interne', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=0, padx=12, pady=(12, 4), sticky='w')
        piece_refs = [p['reference_interne'] for p in get_all_pieces()]
        self.e_ref = make_combobox(form, piece_refs if piece_refs else ['PI-001'], width=180)
        self.e_ref.grid(row=1, column=0, padx=12, pady=(0, 10), sticky='w')
        self.e_ref.configure(command=self._on_piece_ref_changed)
        self.form_fields.append(self.e_ref)

        ctk.CTkLabel(form, text='Référence fournisseur', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=1, padx=12, pady=(12, 4), sticky='w')
        self.e_four = make_input(form, 'FR-001', 180)
        self.e_four.grid(row=1, column=1, padx=12, pady=(0, 10), sticky='w')
        self.form_fields.append(self.e_four)

        ctk.CTkLabel(form, text='Désignation', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=2, padx=12, pady=(12, 4), sticky='w')
        self.e_designation = make_input(form, 'Désignation', 220)
        self.e_designation.grid(row=1, column=2, padx=12, pady=(0, 10), sticky='w')
        self.form_fields.append(self.e_designation)

        # Ligne 2 : Quantité, Prix, Date
        ctk.CTkLabel(form, text='Quantité', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=2, column=0, padx=12, pady=(8, 4), sticky='w')
        self.e_qte = make_input(form, '12', 120)
        self.e_qte.grid(row=3, column=0, padx=12, pady=(0, 10), sticky='w')
        self.form_fields.append(self.e_qte)

        ctk.CTkLabel(form, text='Prix unitaire', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=2, column=1, padx=12, pady=(8, 4), sticky='w')
        self.e_prix = make_input(form, '150', 140)
        self.e_prix.grid(row=3, column=1, padx=12, pady=(0, 10), sticky='w')
        self.form_fields.append(self.e_prix)

        ctk.CTkLabel(form, text='Date livraison', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=2, column=2, padx=12, pady=(8, 4), sticky='w')
        self.e_date = DatePickerWidget(form, placeholder='AAAA-MM-JJ', width=180, default_value=datetime.now().strftime('%Y-%m-%d'))
        self.e_date.grid(row=3, column=2, padx=12, pady=(0, 10), sticky='w')

        # Boutons
        btn_row = ctk.CTkFrame(form, fg_color='transparent')
        btn_row.grid(row=4, column=0, columnspan=4, padx=12, pady=(4, 12), sticky='w')

        self.btn_save = make_primary_button(btn_row, '✅ Enregistrer', self.add_bon, width=150)
        self.btn_save.pack(side='left', padx=(0, 6))

        self.btn_modif = make_secondary_button(btn_row, '✏️ Modifier', self.update_selected_bon, width=130)
        self.btn_modif.pack(side='left', padx=(0, 6))
        self.btn_modif.configure(state='disabled')

        btn_del = make_danger_button(btn_row, '🗑️ Supprimer', self.delete_selected_bon, width=130)
        btn_del.pack(side='left', padx=(0, 6))

        btn_clear = make_secondary_button(btn_row, 'Vider', self.clear_fields, width=100)
        btn_clear.pack(side='left')

        # ── Barre de Filtres par Date & Recherche ─────────────────────────────
        filter_bar = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=12, border_width=1, border_color=COLORS['border'])
        filter_bar.grid(row=2, column=0, sticky='ew', padx=18, pady=(0, 12))

        ctk.CTkLabel(filter_bar, text='📅 Date Début :', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.filter_start_date = DatePickerWidget(filter_bar, placeholder='AAAA-MM-JJ', width=150)
        self.filter_start_date.grid(row=0, column=1, padx=6, pady=10)

        ctk.CTkLabel(filter_bar, text='📅 Date Fin :', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=2, padx=10, pady=10, sticky='w')
        self.filter_end_date = DatePickerWidget(filter_bar, placeholder='AAAA-MM-JJ', width=150)
        self.filter_end_date.grid(row=0, column=3, padx=6, pady=10)


        ctk.CTkLabel(filter_bar, text='🔍 Recherche :', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=4, padx=10, pady=10, sticky='w')
        self.filter_query = make_input(filter_bar, 'Réf / Désignation...', 160)
        self.filter_query.grid(row=0, column=5, padx=6, pady=10)

        make_primary_button(filter_bar, '🔍 Filtrer', self.refresh, width=110).grid(row=0, column=6, padx=8, pady=10)
        make_secondary_button(filter_bar, '❌ Réinitialiser', self._reset_filters, width=120).grid(row=0, column=7, padx=(0, 10), pady=10)

        # ── Tableau Historique ────────────────────────────────────────────────
        table_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=16, border_width=1, border_color=COLORS['border'])
        table_frame.grid(row=3, column=0, sticky='nsew', padx=18, pady=(0, 18))
        self.grid_rowconfigure(3, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(table_frame, columns=('id', 'ref', 'fournisseur', 'designation', 'qte', 'prix', 'total', 'date'), show='headings', height=13)
        self.tree.heading('id', text='ID')
        self.tree.heading('ref', text='Réf Interne')
        self.tree.heading('fournisseur', text='Réf Fournisseur')
        self.tree.heading('designation', text='Désignation')
        self.tree.heading('qte', text='Qté')
        self.tree.heading('prix', text='Prix Unitaire')
        self.tree.heading('total', text='Total')
        self.tree.heading('date', text='Date Livraison')
        self.tree.column('id', width=50, anchor='center')
        for col in ['ref', 'fournisseur', 'designation', 'qte', 'prix', 'total', 'date']:
            self.tree.column(col, anchor='center', width=120)
        self.tree.pack(fill='both', expand=True, padx=10, pady=10)

        self.tree.bind('<ButtonRelease-1>', self.on_row_select)
        bind_tree_clear_selection(self.tree, clear_callback=self.clear_fields)
        self.refresh()

    def _reset_filters(self):
        self.filter_start_date.delete(0, 'end')
        self.filter_end_date.delete(0, 'end')
        self.filter_query.delete(0, 'end')
        self.refresh()

    def _on_piece_ref_changed(self, choice=None):
        ref = self.e_ref.get().strip()
        if ref:
            piece = get_piece_by_reference(ref)
            if piece:
                if piece.get('reference_fournisseur'):
                    self.e_four.delete(0, 'end')
                    self.e_four.insert(0, piece['reference_fournisseur'])
                if piece.get('designation'):
                    self.e_designation.delete(0, 'end')
                    self.e_designation.insert(0, piece['designation'])

    def clear_fields(self):
        piece_refs = [p['reference_interne'] for p in get_all_pieces()]
        if hasattr(self, 'e_ref') and piece_refs:
            self.e_ref.configure(values=piece_refs)

        self.e_four.delete(0, 'end')
        self.e_designation.delete(0, 'end')
        self.e_qte.delete(0, 'end')
        self.e_prix.delete(0, 'end')
        self.e_date.delete(0, 'end')
        self.e_date.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self._selected_bon_id = None
        self.btn_modif.configure(state='disabled')
        self.btn_save.configure(state='normal')

    def on_row_select(self, event):
        item = self.tree.selection()
        if not item:
            return
        values = self.tree.item(item[0], 'values')
        if not values:
            return
        self.clear_fields()
        self._selected_bon_id = int(values[0])
        self.e_ref.set(values[1])
        self.e_four.insert(0, values[2])
        self.e_designation.insert(0, values[3])
        self.e_qte.insert(0, str(values[4]))
        self.e_date.delete(0, 'end')
        self.e_date.insert(0, values[7])
        self.btn_modif.configure(state='normal')
        self.btn_save.configure(state='disabled')

    def update_selected_bon(self):
        if not self._selected_bon_id:
            messagebox.showwarning('Attention', 'Sélectionnez un bon de livraison à modifier.')
            return
        data = {
            'reference_interne': self.e_ref.get().strip(),
            'reference_fournisseur': self.e_four.get().strip(),
            'designation': self.e_designation.get().strip(),
            'quantite': int(self.e_qte.get().strip() or 0),
            'prix_unitaire': float(self.e_prix.get().strip() or 0),
            'date_livraison': self.e_date.get().strip(),
        }
        if not data['reference_interne']:
            messagebox.showwarning('Attention', 'La référence interne est obligatoire.')
            return
        if messagebox.askyesno('Confirmation', f'Modifier le bon de livraison ID {self._selected_bon_id} ?'):
            update_bon_livraison(self._selected_bon_id, data)
            piece = get_piece_by_reference(data['reference_interne'])
            if piece:
                update_piece(piece['id'],
                             ancien_prix_unitaire=piece.get('nouveau_prix_unitaire', 0),
                             nouveau_prix_unitaire=data['prix_unitaire'])
            self.clear_fields()
            self.refresh()

    def delete_selected_bon(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning('Attention', 'Veuillez sélectionner un bon de livraison à supprimer dans le tableau.')
            return

        values = self.tree.item(selected[0], 'values')
        if not values:
            return

        bon_id = values[0]
        ref = values[1]
        if messagebox.askyesno('Confirmation', f'Voulez-vous vraiment supprimer le bon de livraison ID {bon_id} (Réf: {ref}) ?'):
            delete_bon_livraison(int(bon_id))
            self.clear_fields()
            self.refresh()

    def add_bon(self):
        data = {
            'reference_interne': self.e_ref.get().strip(),
            'reference_fournisseur': self.e_four.get().strip(),
            'designation': self.e_designation.get().strip(),
            'quantite': int(self.e_qte.get().strip() or 0),
            'prix_unitaire': float(self.e_prix.get().strip() or 0),
            'date_livraison': self.e_date.get().strip(),
        }
        if not data['reference_interne']:
            messagebox.showwarning('Attention', 'La référence interne est obligatoire.')
            return
        create_bon_livraison(data)
        piece = get_piece_by_reference(data['reference_interne'])
        if piece:
            update_piece(piece['id'],
                         ancien_prix_unitaire=piece.get('nouveau_prix_unitaire', 0),
                         nouveau_prix_unitaire=data['prix_unitaire'])
        self.clear_fields()
        self.refresh()

    def refresh(self):
        piece_refs = [p['reference_interne'] for p in get_all_pieces()]
        if hasattr(self, 'e_ref') and piece_refs:
            self.e_ref.configure(values=piece_refs)

        for row in self.tree.get_children():
            self.tree.delete(row)

        start_d = self.filter_start_date.get().strip() if hasattr(self, 'filter_start_date') else ''
        end_d = self.filter_end_date.get().strip() if hasattr(self, 'filter_end_date') else ''
        query = self.filter_query.get().strip().lower() if hasattr(self, 'filter_query') else ''

        for bon in get_all_bons_livraison():
            date_liv = bon.get('date_livraison', '') or ''

            # Filtre date début
            if start_d and date_liv < start_d:
                continue
            # Filtre date fin
            if end_d and date_liv > end_d:
                continue
            # Filtre texte (référence, fournisseur, désignation)
            if query:
                ref = (bon.get('reference_interne') or '').lower()
                four = (bon.get('reference_fournisseur') or '').lower()
                desig = (bon.get('designation') or '').lower()
                if query not in ref and query not in four and query not in desig:
                    continue

            self.tree.insert('', 'end', values=(
                bon['id'],
                bon['reference_interne'],
                bon.get('reference_fournisseur', ''),
                bon.get('designation', ''),
                bon.get('quantite', 0),
                format_money(bon.get('prix_unitaire', 0)),
                format_money(bon.get('prix_total', 0)),
                date_liv,
            ))
