import customtkinter as ctk
from tkinter import ttk, messagebox

from database.db_manager import (
    create_piece, delete_piece, update_piece,
    get_all_engins, get_all_pieces, get_engin_by_code, get_famille_id_by_name,
    get_engin_categories, get_engin_designations_by_category
)
from ui.theme import COLORS, FAMILLES_PIECES, FONTS, format_money
from ui.widgets import (
    make_input, make_primary_button, make_secondary_button, make_danger_button,
    make_combobox, DatePickerWidget, bind_tree_clear_selection, MultiSelectCombobox
)


class PiecesFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color='transparent')
        self.grid_columnconfigure(0, weight=1)
        self.form_fields = []
        self._selected_piece_id = None
        self._filter_critique_only = False
        self.build()

    def build(self):
        self.header = ctk.CTkFrame(self, fg_color='transparent')
        self.header.grid(row=0, column=0, sticky='ew', padx=18, pady=(18, 8))
        ctk.CTkLabel(self.header, text='Pièces', font=FONTS['title_large'], text_color=COLORS['text_primary']).pack(anchor='w')
        ctk.CTkLabel(self.header, text='Filtres et gestion du stock', font=FONTS['body'], text_color=COLORS['text_secondary']).pack(anchor='w')

        # ── Barre de filtres ─────────────────────────────────────────────────
        filter_bar = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=12, border_width=1, border_color=COLORS['border'])
        filter_bar.grid(row=1, column=0, sticky='ew', padx=18, pady=(0, 12))

        # 1. Filtre Catégorie (Multi-Sélection)
        ctk.CTkLabel(filter_bar, text='🚜 Catégorie :', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=0, padx=(12, 4), pady=12, sticky='w')
        self.filter_categorie = MultiSelectCombobox(filter_bar, options=get_engin_categories(), width=170, command=self._on_category_changed)
        self.filter_categorie.grid(row=0, column=1, padx=4, pady=12)

        # 2. Filtre Marque / Désignation engin (Dynamique)
        ctk.CTkLabel(filter_bar, text='🏷️ Marque :', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=2, padx=(12, 4), pady=12, sticky='w')
        marques = ['Toutes'] + get_engin_designations_by_category('Tous')
        self.filter_marque = make_combobox(filter_bar, marques, width=170)
        self.filter_marque.set('Toutes')
        self.filter_marque.grid(row=0, column=3, padx=4, pady=12)

        # 3. Filtre Famille
        ctk.CTkLabel(filter_bar, text='📦 Famille :', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=4, padx=(12, 4), pady=12, sticky='w')
        self.filter_famille = make_combobox(filter_bar, ['Toutes'] + FAMILLES_PIECES, width=150)
        self.filter_famille.set('Toutes')
        self.filter_famille.grid(row=0, column=5, padx=4, pady=12)

        make_primary_button(filter_bar, '🔍 Filtrer', self.refresh, width=100).grid(row=0, column=6, padx=6, pady=12)
        make_danger_button(filter_bar, '⚠️ Stock Critique', self.filter_stock_critique, width=140).grid(row=0, column=7, padx=4, pady=12)
        make_secondary_button(filter_bar, '❌ Réinitialiser', self._reset_filters, width=120).grid(row=0, column=8, padx=6, pady=12)

        # ── Formulaire ───────────────────────────────────────────────────────
        form = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=16, border_width=1, border_color=COLORS['border'])
        form.grid(row=2, column=0, sticky='ew', padx=18, pady=(0, 12))

        # Ligne 1 : Références et Catégorie engin
        ctk.CTkLabel(form, text='Référence interne', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=0, padx=12, pady=(12, 4), sticky='w')
        self.e_ref = make_input(form, 'PI-001', 180)
        self.e_ref.grid(row=1, column=0, padx=12, pady=(0, 10), sticky='w')
        self.form_fields.append(self.e_ref)

        ctk.CTkLabel(form, text='Référence fournisseur', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=1, padx=12, pady=(12, 4), sticky='w')
        self.e_ref_f = make_input(form, 'FR-001', 180)
        self.e_ref_f.grid(row=1, column=1, padx=12, pady=(0, 10), sticky='w')
        self.form_fields.append(self.e_ref_f)

        # Désignation
        ctk.CTkLabel(form, text='Désignation', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=2, padx=12, pady=(12, 4), sticky='w')
        self.e_designation = make_input(form, 'Ex: Bougie moteur', 220)
        self.e_designation.grid(row=1, column=2, padx=12, pady=(0, 10), sticky='w')
        self.form_fields.append(self.e_designation)

        ctk.CTkLabel(form, text='Catégorie engin', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=3, padx=12, pady=(12, 4), sticky='w')
        self.combo_cat_engin = MultiSelectCombobox(form, options=get_engin_categories(), width=180, command=self._on_form_cat_changed)
        self.combo_cat_engin.grid(row=1, column=3, padx=12, pady=(0, 10), sticky='w')

        # Ligne 2 : Marque engin, Famille, Date, Quantité
        ctk.CTkLabel(form, text='Marque engin', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=2, column=0, padx=12, pady=(0, 4), sticky='w')
        marques_form = get_engin_designations_by_category('Tous')
        self.combo_marque_engin = make_combobox(form, marques_form if marques_form else ['Aucune marque'], width=180)
        self.combo_marque_engin.grid(row=3, column=0, padx=12, pady=(0, 10), sticky='w')
        self.form_fields.append(self.combo_marque_engin)

        ctk.CTkLabel(form, text='Famille', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=2, column=1, padx=12, pady=(0, 4), sticky='w')
        self.combo_famille = make_combobox(form, FAMILLES_PIECES, width=180)
        self.combo_famille.grid(row=3, column=1, padx=12, pady=(0, 10), sticky='w')
        self.form_fields.append(self.combo_famille)

        # Champ Date avec Calendrier Popup
        ctk.CTkLabel(form, text='Date livraison', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=2, column=2, padx=12, pady=(0, 4), sticky='w')
        self.e_date = DatePickerWidget(form, placeholder='2026-01-15', width=180)
        self.e_date.grid(row=3, column=2, padx=12, pady=(0, 10), sticky='w')

        ctk.CTkLabel(form, text='Quantité', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=2, column=3, padx=12, pady=(0, 4), sticky='w')
        self.e_qte = make_input(form, '8', 120)
        self.e_qte.grid(row=3, column=3, padx=12, pady=(0, 10), sticky='w')
        self.form_fields.append(self.e_qte)

        # Ligne 3 : Emplacement, Unité, Ancien prix, Nouveau prix
        ctk.CTkLabel(form, text='Emplacement', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=4, column=0, padx=12, pady=(0, 4), sticky='w')
        self.e_emplacement = make_input(form, 'Magasin A', 180)
        self.e_emplacement.grid(row=5, column=0, padx=12, pady=(0, 10), sticky='w')
        self.form_fields.append(self.e_emplacement)

        ctk.CTkLabel(form, text='Unité', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=4, column=1, padx=12, pady=(0, 4), sticky='w')
        self.combo_unite = make_combobox(form, ['JEUX', 'UNITE', 'LITRE'], width=150)
        self.combo_unite.grid(row=5, column=1, padx=12, pady=(0, 10), sticky='w')
        self.form_fields.append(self.combo_unite)

        ctk.CTkLabel(form, text='Ancien prix', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=4, column=2, padx=12, pady=(0, 4), sticky='w')
        self.e_ancien = make_input(form, '100', 140)
        self.e_ancien.grid(row=5, column=2, padx=12, pady=(0, 10), sticky='w')
        self.form_fields.append(self.e_ancien)

        ctk.CTkLabel(form, text='Nouveau prix', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=4, column=3, padx=12, pady=(0, 4), sticky='w')
        self.e_nouveau = make_input(form, '120', 140)
        self.e_nouveau.grid(row=5, column=3, padx=12, pady=(0, 10), sticky='w')
        self.form_fields.append(self.e_nouveau)

        # Ligne 4 : Stock Alerte
        ctk.CTkLabel(form, text='Stock Alerte (Seuil min)', font=FONTS['body_bold'], text_color='#DC2626').grid(row=6, column=0, padx=12, pady=(0, 4), sticky='w')
        self.e_seuil = make_input(form, '5', 120)
        self.e_seuil.grid(row=7, column=0, padx=12, pady=(0, 10), sticky='w')
        self.form_fields.append(self.e_seuil)

        # ── Boutons ──────────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(form, fg_color='transparent')
        btn_row.grid(row=8, column=0, columnspan=4, padx=12, pady=(4, 12), sticky='w')

        self.btn_add = make_primary_button(btn_row, '✅ Ajouter', self.add_piece, width=120)
        self.btn_add.pack(side='left', padx=(0, 6))

        self.btn_modif = make_secondary_button(btn_row, '✏️ Modifier', self.update_selected_piece, width=120)
        self.btn_modif.pack(side='left', padx=(0, 6))
        self.btn_modif.configure(state='disabled')

        make_danger_button(btn_row, '🗑️ Supprimer', self.delete_selected_piece, width=130).pack(side='left', padx=(0, 6))
        make_secondary_button(btn_row, 'Vider', self.clear_fields, width=100).pack(side='left', padx=(0, 6))
        make_secondary_button(btn_row, 'Actualiser', self.refresh, width=110).pack(side='left')

        # ── Tableau ──────────────────────────────────────────────────────────
        table_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=16, border_width=1, border_color=COLORS['border'])
        table_frame.grid(row=3, column=0, sticky='nsew', padx=18, pady=(0, 18))
        self.grid_rowconfigure(3, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(table_frame,
            columns=('ref', 'fournisseur', 'designation', 'cat_engin', 'marque_engin', 'famille', 'qte', 'seuil', 'prix'),
            show='headings', height=14)
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
            self.tree.column(col, anchor='center', width=110, stretch=True)
        self.tree.pack(fill='both', expand=True, padx=10, pady=10)

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
        self.filter_categorie.set_selected('Tous')
        self._on_category_changed('Tous')
        self.filter_famille.set('Toutes')
        self.refresh()

    def clear_fields(self):
        for w in [self.e_ref, self.e_ref_f, self.e_designation,
                  self.e_qte, self.e_seuil, self.e_emplacement, self.e_ancien, self.e_nouveau]:
            w.delete(0, 'end')
        cats_form = get_engin_categories()
        if hasattr(self, 'combo_cat_engin'):
            self.combo_cat_engin.update_options(cats_form)
            self.combo_cat_engin.set_selected('Tous')
        marques_form = get_engin_designations_by_category('Tous')
        if hasattr(self, 'combo_marque_engin'):
            self.combo_marque_engin.configure(values=marques_form if marques_form else ['Aucune marque'], state='normal')
            if marques_form:
                self.combo_marque_engin.set(marques_form[0])
            else:
                self.combo_marque_engin.set('Aucune marque')
        self.e_date.set('')
        self._selected_piece_id = None
        self.btn_modif.configure(state='disabled')
        self.btn_add.configure(state='normal')

    def add_piece(self):
        ref = self.e_ref.get().strip()
        fournisseur = self.e_ref_f.get().strip()
        designation = self.e_designation.get().strip() or ref
        famille = self.combo_famille.get().strip()
        if not all([ref, famille]):
            messagebox.showwarning('Attention', 'Référence interne et famille sont obligatoires.')
            return
        engin = self._get_selected_engin()
        data = {
            'reference_interne': ref,
            'reference_fournisseur': fournisseur,
            'designation': designation,
            'engin_id': engin['id'] if engin else None,
            'famille_id': get_famille_id_by_name(famille),
            'date_livraison': self.e_date.get().strip() or None,
            'quantite': int(self.e_qte.get().strip() or 0),
            'seuil_alerte': int(self.e_seuil.get().strip() or 5),
            'emplacement': self.e_emplacement.get().strip(),
            'unite': self.combo_unite.get().strip() or 'UNITE',
            'ancien_prix_unitaire': float(self.e_ancien.get().strip() or 0),
            'nouveau_prix_unitaire': float(self.e_nouveau.get().strip() or 0),
        }
        create_piece(data)
        self.refresh()
        self.clear_fields()

    def update_selected_piece(self):
        if not self._selected_piece_id:
            messagebox.showwarning('Attention', 'Sélectionnez une pièce à modifier.')
            return
        ref = self.e_ref.get().strip()
        designation = self.e_designation.get().strip() or ref
        famille = self.combo_famille.get().strip()
        if not ref:
            messagebox.showwarning('Attention', 'La référence interne est obligatoire.')
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
                'ancien_prix_unitaire': float(self.e_ancien.get().strip() or 0),
                'nouveau_prix_unitaire': float(self.e_nouveau.get().strip() or 0),
            }
            try:
                kwargs['quantite'] = int(self.e_qte.get().strip() or 0)
            except ValueError:
                pass
            try:
                kwargs['seuil_alerte'] = int(self.e_seuil.get().strip() or 5)
            except ValueError:
                pass
            if engin:
                kwargs['engin_id'] = engin['id']
            if famille:
                fid = get_famille_id_by_name(famille)
                if fid:
                    kwargs['famille_id'] = fid
            update_piece(self._selected_piece_id, **kwargs)
            self.clear_fields()
            self.refresh()

    def delete_selected_piece(self):
        ref = self.e_ref.get().strip()
        selected = self.tree.selection()
        if not ref and selected:
            values = self.tree.item(selected[0], 'values')
            if values:
                ref = values[0]
        if not ref:
            messagebox.showwarning('Attention', 'Veuillez sélectionner une pièce à supprimer.')
            return

        if messagebox.askyesno('Confirmation', f'Voulez-vous vraiment supprimer la pièce réf "{ref}" ?'):
            if self._delete_piece_by_ref(ref):
                self.clear_fields()
                self.refresh()
            else:
                messagebox.showerror('Erreur', f'Impossible de trouver la pièce réf "{ref}".')

    def on_row_select(self, event):
        item = self.tree.selection()
        if not item:
            return
        values = self.tree.item(item[0], 'values')
        if not values:
            return
        self.clear_fields()
        for piece in get_all_pieces():
            if piece['reference_interne'] == values[0]:
                self._selected_piece_id = piece['id']
                self.e_ref.insert(0, piece.get('reference_interne', ''))
                self.e_ref_f.insert(0, piece.get('reference_fournisseur', ''))
                self.e_designation.insert(0, piece.get('designation', ''))
                if piece.get('engin_categorie'):
                    cat_val = piece['engin_categorie']
                    if cat_val.lower() == 'leger':
                        cat_val = 'VEHICULE_LEGER'
                    self.combo_cat_engin.set_selected(cat_val)
                    self._on_form_cat_changed(cat_val)
                if piece.get('engin_designation'):
                    self.combo_marque_engin.set(piece['engin_designation'])
                if piece.get('famille_nom'):
                    self.combo_famille.set(piece['famille_nom'])
                self.e_date.set(str(piece.get('date_livraison', '') or ''))
                self.e_qte.insert(0, str(piece.get('quantite', 0)))
                self.e_seuil.insert(0, str(piece.get('seuil_alerte', 5)))
                self.e_emplacement.insert(0, piece.get('emplacement', ''))
                if piece.get('unite'):
                    self.combo_unite.set(piece['unite'])
                self.e_ancien.insert(0, str(piece.get('ancien_prix_unitaire', 0)))
                self.e_nouveau.insert(0, str(piece.get('nouveau_prix_unitaire', 0)))
                break
        self.btn_modif.configure(state='normal')
        self.btn_add.configure(state='disabled')

    def refresh(self):
        cats_form = get_engin_categories()
        if hasattr(self, 'combo_cat_engin'):
            self.combo_cat_engin.update_options(cats_form)

        for row in self.tree.get_children():
            self.tree.delete(row)

        self.tree.tag_configure('critique', background='#FEE2E2', foreground='#B91C1C')

        filter_cats = [c.lower() for c in self.filter_categorie.get_selected()] if hasattr(self, 'filter_categorie') else ['tous']
        filter_m = self.filter_marque.get().strip().lower() if hasattr(self, 'filter_marque') else 'toutes'
        filter_f = self.filter_famille.get().strip().lower() if hasattr(self, 'filter_famille') else 'toutes'
        only_critique = getattr(self, '_filter_critique_only', False)

        for piece in get_all_pieces():
            qte = piece.get('quantite', 0)
            seuil = piece.get('seuil_alerte', 5)
            if seuil is None:
                seuil = 5
            is_critique = qte <= seuil

            if only_critique and not is_critique:
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

            tags = ('critique',) if is_critique else ()
            self.tree.insert('', 'end', values=(
                piece['reference_interne'],
                piece.get('reference_fournisseur', ''),
                piece.get('designation', ''),
                piece.get('engin_categorie', '—'),
                piece.get('engin_designation', '—'),
                piece.get('famille_nom', ''),
                qte,
                seuil,
                format_money(piece.get('nouveau_prix_unitaire', 0)),
            ), tags=tags)

    def _delete_piece_by_ref(self, ref):
        for piece in get_all_pieces():
            if piece['reference_interne'] == ref:
                delete_piece(piece['id'])
                return True
        return False
