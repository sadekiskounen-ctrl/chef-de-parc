import os
from datetime import datetime
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog

from database.db_manager import (
    create_piece, delete_piece, update_piece,
    get_all_engins, get_all_pieces, get_engin_by_code, get_famille_id_by_name,
    get_engin_categories, get_engin_designations_by_category
)
from services.excel_export import export_pieces_xlsx
from ui.theme import COLORS, FAMILLES_PIECES, FONTS, format_money, format_qty, parse_qty
from ui.widgets import (
    make_input, make_primary_button, make_secondary_button, make_danger_button,
    make_combobox, DatePickerWidget, bind_tree_clear_selection, MultiSelectCombobox,
    AutocompleteEntry, show_toast, open_piece_search
)


class PiecesFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color='transparent')
        self.grid_columnconfigure(0, weight=1)
        self.form_fields = []
        self._selected_piece_id = None
        self._filter_critique_only = False
        self._filtered_pieces = []
        self.build()

    def build(self):
        self.header = ctk.CTkFrame(self, fg_color='transparent')
        self.header.grid(row=0, column=0, sticky='ew', padx=18, pady=(18, 8))
        ctk.CTkLabel(self.header, text='Pièces', font=FONTS['title_large'], text_color=COLORS['text_primary']).pack(anchor='w')
        ctk.CTkLabel(self.header, text='Filtres et gestion du stock', font=FONTS['body'], text_color=COLORS['text_secondary']).pack(anchor='w')

        # ── Barre de filtres ─────────────────────────────────────────────────
        filter_bar = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=12, border_width=1, border_color=COLORS['border'])
        filter_bar.grid(row=1, column=0, sticky='ew', padx=18, pady=(0, 12))
        filter_bar.grid_columnconfigure(1, weight=1)

        # Ligne 1 : Barre de recherche + Boutons d'action (toujours visibles et dynamiques)
        ctk.CTkLabel(filter_bar, text='🔍 Recherche :', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=0, padx=(12, 4), pady=(10, 6), sticky='w')
        self.e_search = make_input(filter_bar, 'Réf, désignation, fournisseur, emplacement...', 160)
        self.e_search.grid(row=0, column=1, padx=4, pady=(10, 6), sticky='ew')
        self.e_search.bind('<KeyRelease>', lambda e: self.refresh())
        self.e_search.bind('<Return>', lambda e: self.refresh())

        actions_frame = ctk.CTkFrame(filter_bar, fg_color='transparent')
        actions_frame.grid(row=0, column=2, padx=(4, 12), pady=(10, 6), sticky='e')
        make_primary_button(actions_frame, '🔍 Filtrer', self.refresh, width=85).pack(side='left', padx=3)
        make_danger_button(actions_frame, '⚠️ Critique', self.filter_stock_critique, width=95).pack(side='left', padx=3)
        make_secondary_button(actions_frame, '❌ Reset', self._reset_filters, width=75).pack(side='left', padx=3)
        make_secondary_button(actions_frame, '📊 Exporter Excel', self.export_to_excel, width=130).pack(side='left', padx=(3, 0))

        # Ligne 2 : Filtres Catégorie, Marque, Famille (répartis harmonieusement)
        sub_filters = ctk.CTkFrame(filter_bar, fg_color='transparent')
        sub_filters.grid(row=1, column=0, columnspan=3, padx=12, pady=(0, 10), sticky='ew')
        sub_filters.grid_columnconfigure(1, weight=1)
        sub_filters.grid_columnconfigure(3, weight=1)
        sub_filters.grid_columnconfigure(5, weight=1)

        ctk.CTkLabel(sub_filters, text='🚜 Catégorie :', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=0, padx=(0, 4), sticky='w')
        self.filter_categorie = MultiSelectCombobox(sub_filters, options=get_engin_categories(), width=130, command=self._on_category_changed)
        self.filter_categorie.grid(row=0, column=1, padx=(0, 16), sticky='ew')

        ctk.CTkLabel(sub_filters, text='🏷️ Marque :', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=2, padx=(0, 4), sticky='w')
        marques = ['Toutes'] + get_engin_designations_by_category('Tous')
        self.filter_marque = make_combobox(sub_filters, marques, width=130)
        self.filter_marque.set('Toutes')
        self.filter_marque.grid(row=0, column=3, padx=(0, 16), sticky='ew')

        ctk.CTkLabel(sub_filters, text='📦 Famille :', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=4, padx=(0, 4), sticky='w')
        self.filter_famille = make_combobox(sub_filters, ['Toutes'] + FAMILLES_PIECES, width=130)
        self.filter_famille.set('Toutes')
        self.filter_famille.grid(row=0, column=5, sticky='ew')

        # ── Formulaire ───────────────────────────────────────────────────────
        form = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=16, border_width=1, border_color=COLORS['border'])
        form.grid(row=2, column=0, sticky='ew', padx=18, pady=(0, 12))
        for col in range(4):
            form.grid_columnconfigure(col, weight=1)

        all_p = get_all_pieces()
        p_refs = [p['reference_interne'] for p in all_p if p.get('reference_interne')]
        p_des = [p['designation'] for p in all_p if p.get('designation')]
        p_fours = [p['reference_fournisseur'] for p in all_p if p.get('reference_fournisseur')]

        # Ligne 1 : Références et Catégorie engin
        ctk.CTkLabel(form, text='🔍 Référence interne', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=0, padx=10, pady=(12, 4), sticky='w')
        ref_frame = ctk.CTkFrame(form, fg_color='transparent')
        ref_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky='ew')
        ref_frame.grid_columnconfigure(0, weight=1)
        self.e_ref = AutocompleteEntry(ref_frame, placeholder='PI-001', width=100, completion_list=p_refs, on_select=self._on_ref_autocompleted)
        self.e_ref.grid(row=0, column=0, sticky='ew')
        self.form_fields.append(self.e_ref)
        make_primary_button(ref_frame, '🔎', self._open_piece_search_dialog, width=34, height=36).grid(row=0, column=1, padx=(4, 0))

        ctk.CTkLabel(form, text='Référence fournisseur', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=1, padx=10, pady=(12, 4), sticky='w')
        self.e_ref_f = AutocompleteEntry(form, placeholder='FR-001', width=100, completion_list=p_fours)
        self.e_ref_f.grid(row=1, column=1, padx=10, pady=(0, 10), sticky='ew')
        self.form_fields.append(self.e_ref_f)

        # Désignation
        ctk.CTkLabel(form, text='Désignation', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=2, padx=10, pady=(12, 4), sticky='w')
        self.e_designation = AutocompleteEntry(form, placeholder='Ex: Bougie moteur', width=120, completion_list=p_des)
        self.e_designation.grid(row=1, column=2, padx=10, pady=(0, 10), sticky='ew')
        self.form_fields.append(self.e_designation)

        ctk.CTkLabel(form, text='Catégorie engin', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=3, padx=10, pady=(12, 4), sticky='w')
        self.combo_cat_engin = MultiSelectCombobox(form, options=get_engin_categories(), width=100, command=self._on_form_cat_changed)
        self.combo_cat_engin.grid(row=1, column=3, padx=10, pady=(0, 10), sticky='ew')

        # Ligne 2 : Marque engin, Famille, Date, Quantité
        ctk.CTkLabel(form, text='Marque engin', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=2, column=0, padx=10, pady=(0, 4), sticky='w')
        marques_form = get_engin_designations_by_category('Tous')
        self.combo_marque_engin = make_combobox(form, marques_form if marques_form else ['Aucune marque'], width=100)
        self.combo_marque_engin.grid(row=3, column=0, padx=10, pady=(0, 10), sticky='ew')
        self.form_fields.append(self.combo_marque_engin)

        ctk.CTkLabel(form, text='Famille', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=2, column=1, padx=10, pady=(0, 4), sticky='w')
        self.combo_famille = make_combobox(form, FAMILLES_PIECES, width=100)
        self.combo_famille.grid(row=3, column=1, padx=10, pady=(0, 10), sticky='ew')
        self.form_fields.append(self.combo_famille)

        # Champ Date avec Calendrier Popup
        ctk.CTkLabel(form, text='Date livraison', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=2, column=2, padx=10, pady=(0, 4), sticky='w')
        self.e_date = DatePickerWidget(form, placeholder='2026-01-15', width=100)
        self.e_date.grid(row=3, column=2, padx=10, pady=(0, 10), sticky='ew')

        ctk.CTkLabel(form, text='Quantité', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=2, column=3, padx=10, pady=(0, 4), sticky='w')
        self.e_qte = make_input(form, '8', 80)
        self.e_qte.grid(row=3, column=3, padx=10, pady=(0, 10), sticky='ew')
        self.form_fields.append(self.e_qte)

        # Ligne 3 : Emplacement, Unité, Ancien prix, Nouveau prix
        ctk.CTkLabel(form, text='Emplacement', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=4, column=0, padx=10, pady=(0, 4), sticky='w')
        self.e_emplacement = make_input(form, 'Magasin A', 100)
        self.e_emplacement.grid(row=5, column=0, padx=10, pady=(0, 10), sticky='ew')
        self.form_fields.append(self.e_emplacement)

        ctk.CTkLabel(form, text='Unité', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=4, column=1, padx=10, pady=(0, 4), sticky='w')
        self.combo_unite = make_combobox(form, ['JEUX', 'UNITE', 'LITRE'], width=100)
        self.combo_unite.grid(row=5, column=1, padx=10, pady=(0, 10), sticky='ew')
        self.form_fields.append(self.combo_unite)

        ctk.CTkLabel(form, text='Ancien prix', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=4, column=2, padx=10, pady=(0, 4), sticky='w')
        self.e_ancien = make_input(form, '100', 80)
        self.e_ancien.grid(row=5, column=2, padx=10, pady=(0, 10), sticky='ew')
        self.form_fields.append(self.e_ancien)

        ctk.CTkLabel(form, text='Nouveau prix', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=4, column=3, padx=10, pady=(0, 4), sticky='w')
        self.e_nouveau = make_input(form, '120', 80)
        self.e_nouveau.grid(row=5, column=3, padx=10, pady=(0, 10), sticky='ew')
        self.form_fields.append(self.e_nouveau)

        # Ligne 4 : Stock Alerte
        ctk.CTkLabel(form, text='Stock Alerte (Seuil min)', font=FONTS['body_bold'], text_color='#DC2626').grid(row=6, column=0, padx=10, pady=(0, 4), sticky='w')
        self.e_seuil = make_input(form, '5', 80)
        self.e_seuil.grid(row=7, column=0, padx=10, pady=(0, 10), sticky='ew')
        self.form_fields.append(self.e_seuil)

        # ── Boutons ──────────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(form, fg_color='transparent')
        btn_row.grid(row=8, column=0, columnspan=4, padx=10, pady=(4, 12), sticky='w')

        self.btn_add = make_primary_button(btn_row, '✅ Ajouter', self.add_piece, width=110)
        self.btn_add.pack(side='left', padx=(0, 6))

        self.btn_modif = make_secondary_button(btn_row, '✏️ Modifier', self.update_selected_piece, width=110)
        self.btn_modif.pack(side='left', padx=(0, 6))
        self.btn_modif.configure(state='disabled')

        make_danger_button(btn_row, '🗑️ Supprimer', self.delete_selected_piece, width=120).pack(side='left', padx=(0, 6))
        make_secondary_button(btn_row, 'Vider', self.clear_fields, width=90).pack(side='left', padx=(0, 6))
        make_secondary_button(btn_row, 'Actualiser', self.refresh, width=100).pack(side='left')

        # ── Tableau ──────────────────────────────────────────────────────────
        table_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=16, border_width=1, border_color=COLORS['border'])
        table_frame.grid(row=3, column=0, sticky='nsew', padx=18, pady=(0, 18))
        self.grid_rowconfigure(3, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(table_frame,
            columns=('ref', 'fournisseur', 'designation', 'cat_engin', 'marque_engin', 'famille', 'qte', 'seuil', 'prix'),
            show='headings', height=10)
        self.tree.heading('ref', text='Réf interne')
        self.tree.heading('fournisseur', text='Réf fournisseur')
        self.tree.heading('designation', text='Désignation')
        self.tree.heading('cat_engin', text='Catégorie engin')
        self.tree.heading('marque_engin', text='Marque engin')
        self.tree.heading('famille', text='Famille')
        self.tree.heading('qte', text='Qté Stock')
        self.tree.heading('seuil', text='Seuil Alerte')
        self.tree.heading('prix', text='Nouveau prix')
        for col in ['ref', 'fournisseur', 'designation', 'cat_engin', 'marque_engin', 'famille', 'qte', 'seuil', 'prix']:
            self.tree.column(col, anchor='center', width=100, stretch=True)

        vsb = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew', padx=(10, 0), pady=(10, 0))
        vsb.grid(row=0, column=1, sticky='ns', padx=(0, 10), pady=(10, 0))
        hsb.grid(row=1, column=0, sticky='ew', padx=(10, 0), pady=(0, 10))

        self.tree.bind('<ButtonRelease-1>', self.on_row_select)
        bind_tree_clear_selection(self.tree, clear_callback=self.clear_fields)
        self.refresh()

    def filter_stock_critique(self):
        self._filter_critique_only = True
        self.refresh()

    def _on_category_changed(self, choice=None):
        selected_cats = self.filter_categorie.get_selected()
        is_parc = any(c.strip().upper() == 'PARC' for c in selected_cats)
        if is_parc:
            self.filter_marque.configure(values=['Toutes'], state='disabled')
            self.filter_marque.set('Toutes')
        else:
            marques = ['Toutes'] + get_engin_designations_by_category(selected_cats)
            self.filter_marque.configure(values=marques, state='normal')
            self.filter_marque.set('Toutes')

    def _on_form_cat_changed(self, choice=None):
        selected_cats = self.combo_cat_engin.get_selected()
        is_parc = any(c.strip().upper() == 'PARC' for c in selected_cats)
        if hasattr(self, 'combo_marque_engin'):
            if is_parc:
                self.combo_marque_engin.configure(values=['Aucune marque'], state='disabled')
                self.combo_marque_engin.set('Aucune marque')
            else:
                marques = get_engin_designations_by_category(selected_cats)
                self.combo_marque_engin.configure(values=marques if marques else ['Aucune marque'], state='normal')
                if marques:
                    self.combo_marque_engin.set(marques[0])
                else:
                    self.combo_marque_engin.set('Aucune marque')

    def _get_selected_engin(self):
        selected_cats = [c.lower() for c in self.combo_cat_engin.get_selected()]
        marque = self.combo_marque_engin.get().strip()
        if 'parc' in selected_cats or marque == 'Aucune marque':
            engins = get_all_engins()
            for e in engins:
                if (e['categorie'] or '').lower() == 'parc':
                    return e
            return None
        engins = get_all_engins()
        for e in engins:
            e_cat = (e['categorie'] or '').lower()
            if e_cat == 'leger':
                e_cat = 'vehicule_leger'
            e_des = (e['designation'] or '').strip().lower()
            if e_des == marque.lower():
                if 'tous' in selected_cats or any((sc in e_cat or e_cat in sc) for sc in selected_cats):
                    return e
        for e in engins:
            if (e['designation'] or '').strip().lower() == marque.lower():
                return e
        return None

    def _reset_filters(self):
        self._filter_critique_only = False
        if hasattr(self, 'e_search'):
            self.e_search.delete(0, 'end')
        self.filter_categorie.set_selected('Tous')
        self._on_category_changed('Tous')
        self.filter_famille.set('Toutes')
        self.refresh()

    def clear_fields(self):
        self._selected_piece_id = None
        for f in self.form_fields:
            if isinstance(f, AutocompleteEntry):
                f.set('')
            elif isinstance(f, ctk.CTkEntry):
                f.delete(0, 'end')
            elif isinstance(f, DatePickerWidget):
                f.clear()
            elif isinstance(f, ctk.CTkComboBox):
                vals = f.cget('values')
                if vals:
                    f.set(vals[0])
            elif isinstance(f, MultiSelectCombobox):
                f.clear_selection()
        cats_form = get_engin_categories()
        if hasattr(self, 'combo_cat_engin'):
            self.combo_cat_engin.update_options(cats_form)
            self.combo_cat_engin.set_selected('Tous')
        marques_form = get_engin_designations_by_category('Tous')
        if hasattr(self, 'combo_marque_engin'):
            self.combo_marque_engin.configure(values=marques_form if marques_form else ['Aucune marque'], state='normal')
        self.combo_unite.set('UNITE')
        self.btn_modif.configure(state='disabled')
        self.btn_add.configure(state='normal')

    def add_piece(self):
        ref = self.e_ref.get().strip()
        fournisseur = self.e_ref_f.get().strip()
        designation = self.e_designation.get().strip() or ref
        famille = self.combo_famille.get().strip()
        if not all([ref, famille]):
            show_toast(self, 'Référence interne et famille sont obligatoires.', 'warning')
            return
        engin = self._get_selected_engin()
        data = {
            'reference_interne': ref,
            'reference_fournisseur': fournisseur,
            'designation': designation,
            'engin_id': engin['id'] if engin else None,
            'famille_id': get_famille_id_by_name(famille),
            'date_livraison': self.e_date.get().strip() or None,
            'quantite': parse_qty(self.e_qte.get()),
            'seuil_alerte': parse_qty(self.e_seuil.get().strip() or 5),
            'emplacement': self.e_emplacement.get().strip(),
            'unite': self.combo_unite.get().strip() or 'UNITE',
            'ancien_prix_unitaire': float(self.e_ancien.get().strip().replace(',', '.') or 0),
            'nouveau_prix_unitaire': float(self.e_nouveau.get().strip().replace(',', '.') or 0),
        }
        create_piece(data)
        show_toast(self, f"Pièce '{ref}' enregistrée avec succès.", 'success')
        self.refresh()
        self.clear_fields()

    def update_selected_piece(self):
        if not self._selected_piece_id:
            show_toast(self, 'Sélectionnez une pièce à modifier.', 'warning')
            return
        ref = self.e_ref.get().strip()
        designation = self.e_designation.get().strip() or ref
        famille = self.combo_famille.get().strip()
        if not ref:
            show_toast(self, 'La référence interne est obligatoire.', 'warning')
            return
        engin = self._get_selected_engin()
        if messagebox.askyesno('Confirmation', f'Modifier la pièce "{ref}" ?'):
            kwargs = {
                'reference_interne': ref,
                'reference_fournisseur': self.e_ref_f.get().strip(),
                'designation': designation,
                'date_livraison': self.e_date.get().strip() or None,
                'emplacement': self.e_emplacement.get().strip(),
                'unite': self.combo_unite.get().strip() or 'UNITE',
                'ancien_prix_unitaire': float(self.e_ancien.get().strip().replace(',', '.') or 0),
                'nouveau_prix_unitaire': float(self.e_nouveau.get().strip().replace(',', '.') or 0),
            }
            try:
                kwargs['quantite'] = parse_qty(self.e_qte.get())
            except ValueError:
                pass
            try:
                kwargs['seuil_alerte'] = parse_qty(self.e_seuil.get())
            except ValueError:
                pass
            if engin:
                kwargs['engin_id'] = engin['id']
            if famille:
                fid = get_famille_id_by_name(famille)
                if fid:
                    kwargs['famille_id'] = fid
            update_piece(self._selected_piece_id, **kwargs)
            show_toast(self, f"Pièce '{ref}' mise à jour avec succès.", 'success')
            self.clear_fields()
            self.refresh()

    def delete_selected_piece(self):
        ref = self.e_ref.get().strip()
        if not ref:
            show_toast(self, 'Sélectionnez une pièce dans le tableau.', 'warning')
            return
        if messagebox.askyesno('Confirmation', f'Supprimer définitivement la pièce "{ref}" ?'):
            if self._selected_piece_id:
                delete_piece(self._selected_piece_id)
            else:
                self._delete_piece_by_ref(ref)
            show_toast(self, f"Pièce '{ref}' supprimée.", 'info')
            self.clear_fields()
            self.refresh()

    def _open_piece_search_dialog(self):
        """Ouvre le dialogue de recherche rapide et sélection de pièce."""
        open_piece_search(self, self._on_piece_searched)

    def _on_piece_searched(self, piece):
        """Remplit le formulaire avec la pièce sélectionnée depuis la recherche."""
        if not piece:
            return
        self.clear_fields()
        self._load_piece_into_form(piece)
        ref = piece.get('reference_interne', '')
        for row in self.tree.get_children():
            if self.tree.item(row, 'values')[0] == ref:
                self.tree.selection_set(row)
                self.tree.see(row)
                break

    def _on_ref_autocompleted(self, ref_val):
        if not ref_val:
            return
        for p in get_all_pieces():
            if p.get('reference_interne') == ref_val:
                self.clear_fields()
                self._load_piece_into_form(p)
                break

    def _load_piece_into_form(self, piece):
        """Charge les données d'une pièce dans tous les champs du formulaire."""
        self._selected_piece_id = piece.get('id')
        self.e_ref.set(piece.get('reference_interne', '') or '')
        self.e_ref_f.set(piece.get('reference_fournisseur', '') or '')
        self.e_designation.set(piece.get('designation', '') or '')
        if piece.get('engin_categorie'):
            cat_val = piece['engin_categorie']
            if str(cat_val).lower() == 'leger':
                cat_val = 'VEHICULE_LEGER'
            self.combo_cat_engin.set_selected(cat_val)
            self._on_form_cat_changed(cat_val)
        if piece.get('engin_designation'):
            self.combo_marque_engin.set(piece['engin_designation'])
        if piece.get('famille_nom'):
            self.combo_famille.set(piece['famille_nom'])
        self.e_date.set(str(piece.get('date_livraison', '') or ''))
        self.e_qte.delete(0, 'end')
        self.e_qte.insert(0, format_qty(piece.get('quantite', 0)))
        self.e_seuil.delete(0, 'end')
        self.e_seuil.insert(0, format_qty(piece.get('seuil_alerte', 5)))
        self.e_emplacement.delete(0, 'end')
        self.e_emplacement.insert(0, piece.get('emplacement', '') or '')
        if piece.get('unite'):
            self.combo_unite.set(piece['unite'])
        self.e_ancien.delete(0, 'end')
        self.e_ancien.insert(0, str(piece.get('ancien_prix_unitaire', 0)))
        self.e_nouveau.delete(0, 'end')
        self.e_nouveau.insert(0, str(piece.get('nouveau_prix_unitaire', 0)))
        self.btn_modif.configure(state='normal')
        self.btn_add.configure(state='disabled')

    def on_row_select(self, event):
        item = self.tree.selection()
        if not item:
            return
        values = self.tree.item(item[0], 'values')
        if not values:
            return
        self.clear_fields()
        ref = values[0]
        for piece in get_all_pieces():
            if piece['reference_interne'] == ref:
                self._load_piece_into_form(piece)
                break

    def refresh(self):
        cats_form = get_engin_categories()
        if hasattr(self, 'combo_cat_engin'):
            self.combo_cat_engin.update_options(cats_form)

        for row in self.tree.get_children():
            self.tree.delete(row)

        self.tree.tag_configure('critique', background='#FEE2E2', foreground='#B91C1C')

        filter_q = self.e_search.get().strip().lower() if hasattr(self, 'e_search') else ''
        filter_cats = [c.lower() for c in self.filter_categorie.get_selected()] if hasattr(self, 'filter_categorie') else ['tous']
        filter_m = self.filter_marque.get().strip().lower() if hasattr(self, 'filter_marque') else 'toutes'
        filter_f = self.filter_famille.get().strip().lower() if hasattr(self, 'filter_famille') else 'toutes'
        only_critique = getattr(self, '_filter_critique_only', False)

        all_pieces = get_all_pieces()

        # Mettre à jour les listes d'autocomplétion
        if hasattr(self, 'e_ref') and hasattr(self.e_ref, 'set_completion_list'):
            self.e_ref.set_completion_list([p['reference_interne'] for p in all_pieces if p.get('reference_interne')])
        if hasattr(self, 'e_ref_f') and hasattr(self.e_ref_f, 'set_completion_list'):
            self.e_ref_f.set_completion_list([p['reference_fournisseur'] for p in all_pieces if p.get('reference_fournisseur')])
        if hasattr(self, 'e_designation') and hasattr(self.e_designation, 'set_completion_list'):
            self.e_designation.set_completion_list([p['designation'] for p in all_pieces if p.get('designation')])

        self._filtered_pieces = []

        for piece in all_pieces:
            qte = piece.get('quantite', 0)
            seuil = piece.get('seuil_alerte', 5)
            if seuil is None:
                seuil = 5
            is_critique = float(qte) <= float(seuil)

            if only_critique and not is_critique:
                continue

            # Filtre de recherche textuelle rapide
            if filter_q:
                ref_i = str(piece.get('reference_interne', '') or '').lower()
                ref_f = str(piece.get('reference_fournisseur', '') or '').lower()
                des = str(piece.get('designation', '') or '').lower()
                fam = str(piece.get('famille_nom', '') or '').lower()
                emp = str(piece.get('emplacement', '') or '').lower()
                eng = str(piece.get('engin_designation', '') or '').lower()
                if (filter_q not in ref_i and filter_q not in ref_f and 
                    filter_q not in des and filter_q not in fam and 
                    filter_q not in emp and filter_q not in eng):
                    continue

            # Filtre par catégorie engin (Multi-Sélection)
            if 'tous' not in filter_cats and 'toutes' not in filter_cats:
                engin_cat = str(piece.get('engin_categorie', '') or '').lower()
                if engin_cat == 'leger':
                    engin_cat = 'vehicule_leger'
                if not any((fc in engin_cat or engin_cat in fc) for fc in filter_cats):
                    continue

            # Filtre par marque / désignation engin
            if filter_m not in ('toutes', 'tous', ''):
                engin_des = str(piece.get('engin_designation', '') or '').lower()
                if filter_m not in engin_des and engin_des not in filter_m:
                    continue

            # Filtre par famille
            if filter_f not in ('toutes', 'tous', ''):
                fam_nom = str(piece.get('famille_nom', '') or '').lower()
                if filter_f != fam_nom:
                    continue

            self._filtered_pieces.append(piece)

            tags = ('critique',) if is_critique else ()
            self.tree.insert('', 'end', values=(
                piece['reference_interne'],
                piece.get('reference_fournisseur', ''),
                piece.get('designation', ''),
                piece.get('engin_categorie', '—'),
                piece.get('engin_designation', '—'),
                piece.get('famille_nom', ''),
                format_qty(qte),
                format_qty(seuil),
                format_money(piece.get('nouveau_prix_unitaire', 0)),
            ), tags=tags)

    def export_to_excel(self):
        """Exporte les pièces filtrées actuellement affichées vers un fichier Excel."""
        if not self._filtered_pieces:
            show_toast(self, "Aucune pièce à exporter selon les filtres sélectionnés.", "warning")
            return

        filter_cats = [c for c in self.filter_categorie.get_selected()] if hasattr(self, 'filter_categorie') else ['Tous']
        filter_m = self.filter_marque.get().strip() if hasattr(self, 'filter_marque') else 'Toutes'
        filter_f = self.filter_famille.get().strip() if hasattr(self, 'filter_famille') else 'Toutes'
        only_critique = getattr(self, '_filter_critique_only', False)

        filters_desc = []
        search_q = self.e_search.get().strip() if hasattr(self, 'e_search') else ''
        if search_q:
            filters_desc.append(f"Recherche: '{search_q}'")
        if 'Tous' not in filter_cats:
            filters_desc.append(f"Catégories: {', '.join(filter_cats)}")
        if filter_m not in ('Toutes', 'Tous', ''):
            filters_desc.append(f"Marque: {filter_m}")
        if filter_f not in ('Toutes', 'Tous', ''):
            filters_desc.append(f"Famille: {filter_f}")
        if only_critique:
            filters_desc.append("Stock Critique (< Seuil)")

        summary = ' | '.join(filters_desc) if filters_desc else "Toutes les pièces (sans filtre)"

        default_filename = f"Inventaire_Pieces_AYRIS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        chosen_path = filedialog.asksaveasfilename(
            parent=self,
            title="Exporter l'inventaire des pièces vers Excel",
            defaultextension=".xlsx",
            filetypes=[("Fichiers Excel (*.xlsx)", "*.xlsx"), ("Tous les fichiers", "*.*")],
            initialfile=default_filename
        )

        if not chosen_path:
            return

        try:
            saved_file = export_pieces_xlsx(self._filtered_pieces, output_path=chosen_path, filter_summary=summary)
            show_toast(self, f"✅ Export réussi : {len(self._filtered_pieces)} pièces exportées !", "success")
            if os.path.exists(saved_file):
                try:
                    os.startfile(saved_file)
                except Exception:
                    pass
        except Exception as e:
            messagebox.showerror("Erreur d'exportation", f"Impossible de générer le fichier Excel :\n{e}", parent=self)

    def _delete_piece_by_ref(self, ref):
        for piece in get_all_pieces():
            if piece['reference_interne'] == ref:
                delete_piece(piece['id'])
                return True
        return False
