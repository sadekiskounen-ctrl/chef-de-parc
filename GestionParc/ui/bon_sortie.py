import os
from datetime import datetime
from pathlib import Path
from tkinter import ttk, messagebox

import customtkinter as ctk

from auth.auth_manager import list_users
from database.db_manager import (
    create_bon_sortie_multi, get_bons_sortie_grouped, get_bon_sortie_details,
    delete_bon_sortie_by_num, update_bon_sortie_chemin_pdf,
    get_all_engins, get_all_pieces, get_engin_by_code,
    get_piece_by_reference, get_piece_by_designation, get_piece_by_id,
    get_all_operateurs, save_operateur, get_connection
)
from services.pdf_generator import generate_bon_sortie_pdf
from ui.pdf_viewer import ouvrir_pdf_viewer
from ui.theme import COLORS, FONTS, UNITES, format_qty, parse_qty
from ui.widgets import (
    make_input, make_primary_button, make_secondary_button, make_danger_button,
    make_combobox, DatePickerWidget, bind_tree_clear_selection, AutocompleteEntry,
    show_toast, open_piece_search
)


class BonSortieFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color='transparent')
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._current_articles = []        # Liste des articles du bon en cours de saisie
        self._selected_bon = None           # Bon sélectionné dans l'historique
        self._editing_article_idx = None    # Index de l'article en cours d'édition dans _current_articles
        self._all_pieces = []               # Cache des pièces
        self._syncing = False               # Anti-boucle de synchronisation

        self.build()

    def _generate_auto_bs_num(self) -> str:
        bons = get_bons_sortie_grouped()
        year = datetime.now().year
        num = len(bons) + 1
        return f"BS-{year}-{num:03d}"

    def build(self):
        # ── Header ────────────────────────────────────────────────────────────
        self.header = ctk.CTkFrame(self, fg_color='transparent')
        self.header.grid(row=0, column=0, sticky='ew', padx=18, pady=(14, 6))
        ctk.CTkLabel(self.header, text='Bon de sortie', font=FONTS['title_large'], text_color=COLORS['text_primary']).pack(anchor='w')
        ctk.CTkLabel(self.header, text='Sortie multi-articles par bon et par numéro d’ordre (OR) vers engin — Saisie, Modification & Impression PDF', font=FONTS['body'], text_color=COLORS['text_secondary']).pack(anchor='w')

        # ── Formulaire de Saisie Multi-Articles ────────────────────────────────
        form = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=16, border_width=1, border_color=COLORS['border'])
        form.grid(row=1, column=0, sticky='ew', padx=18, pady=(0, 10))

        self._all_pieces = get_all_pieces()
        pieces_desigs = [p['designation'] for p in self._all_pieces if p.get('designation')]
        pieces_refs = [p['reference_interne'] for p in self._all_pieces if p.get('reference_interne')]
        pieces_fours = [p['reference_fournisseur'] for p in self._all_pieces if p.get('reference_fournisseur')]
        engins = get_all_engins()
        engins_codes = [e['code_engin'] for e in engins if e.get('code_engin')]
        operateurs_list = get_all_operateurs()

        # ── En-tête du Bon : N° BS, Code Engin, Date, N° Ordre (OR), Opérateur, KM ───
        hdr_frame = ctk.CTkFrame(form, fg_color='transparent')
        hdr_frame.pack(fill='x', padx=14, pady=(12, 6))

        # Rangée 1 : N° BS, Code Engin, Date Sortie, N° Ordre (OR)
        ctk.CTkLabel(hdr_frame, text='N° Bon de Sortie :', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=0, padx=(0, 6), sticky='w')
        self.e_num_bs = make_input(hdr_frame, 'ex: BS-2026-001', 150)
        self.e_num_bs.insert(0, self._generate_auto_bs_num())
        self.e_num_bs.grid(row=0, column=1, padx=(0, 14), pady=(0, 4), sticky='w')

        ctk.CTkLabel(hdr_frame, text='Code Engin :', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=2, padx=(0, 6), sticky='w')
        self.e_code_engin = AutocompleteEntry(hdr_frame, placeholder='CL-001', width=140, completion_list=engins_codes)
        if engins_codes:
            self.e_code_engin.set(engins_codes[0])
        self.e_code_engin.grid(row=0, column=3, padx=(0, 14), pady=(0, 4), sticky='w')

        ctk.CTkLabel(hdr_frame, text='Date Sortie :', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=4, padx=(0, 6), sticky='w')
        self.e_date = DatePickerWidget(hdr_frame, placeholder='AAAA-MM-JJ', width=130, default_value=datetime.now().strftime('%Y-%m-%d'))
        self.e_date.grid(row=0, column=5, padx=(0, 14), pady=(0, 4), sticky='w')

        ctk.CTkLabel(hdr_frame, text='N° Ordre (OR) :', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=6, padx=(0, 6), sticky='w')
        self.e_or = make_input(hdr_frame, 'ex: OR-001 / N° Ordre', 150)
        self.e_or.grid(row=0, column=7, pady=(0, 4), sticky='w')

        # Rangée 2 : Opérateur & Kilométrage
        ctk.CTkLabel(hdr_frame, text='👤 Opérateur :', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=1, column=0, padx=(0, 6), pady=(4, 0), sticky='w')
        self.combo_operateur = AutocompleteEntry(hdr_frame, placeholder='Opérateur...', width=240, completion_list=operateurs_list)
        if operateurs_list:
            self.combo_operateur.set(operateurs_list[0])
        self.combo_operateur.grid(row=1, column=1, columnspan=3, padx=(0, 14), pady=(4, 0), sticky='w')

        ctk.CTkLabel(hdr_frame, text='Kilométrage :', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=1, column=4, padx=(0, 6), pady=(4, 0), sticky='w')
        self.e_km = make_input(hdr_frame, 'ex: 125 000 KM', 190)
        self.e_km.grid(row=1, column=5, columnspan=3, pady=(4, 0), sticky='w')

        # Séparateur visuel subtil
        ctk.CTkFrame(form, fg_color=COLORS['border'], height=1).pack(fill='x', padx=14, pady=6)

        # ── Ligne de saisie / modification d'un article ───────────────────────
        art_input_frame = ctk.CTkFrame(form, fg_color='transparent')
        art_input_frame.pack(fill='x', padx=14, pady=(4, 4))

        # Réf Interne avec autocomplétion + bouton recherche
        ctk.CTkLabel(art_input_frame, text='🔍 Réf Interne', font=FONTS['small_bold'], text_color=COLORS['text_secondary']).grid(row=0, column=0, padx=3, sticky='w')
        ref_frame = ctk.CTkFrame(art_input_frame, fg_color='transparent')
        ref_frame.grid(row=1, column=0, padx=3, pady=(2, 0), sticky='w')
        self.e_ref = AutocompleteEntry(
            ref_frame, placeholder='ex: PI-001', width=118,
            completion_list=pieces_refs, on_select=self._on_piece_ref_changed
        )
        self.e_ref.pack(side='left')
        self.e_ref.entry.bind('<KeyRelease>', self._on_ref_typed, add='+')
        import customtkinter as _ctk
        _ctk.CTkButton(
            ref_frame, text='🔎', width=32, height=38,
            fg_color=COLORS['primary'], hover_color=COLORS['primary_dark'],
            text_color='#FFFFFF', font=('Segoe UI Emoji', 14),
            corner_radius=8, command=self._open_piece_search_dialog
        ).pack(side='left', padx=(2, 0))

        # Désignation avec autocomplétion
        ctk.CTkLabel(art_input_frame, text='Désignation Pièce', font=FONTS['small_bold'], text_color=COLORS['text_secondary']).grid(row=0, column=1, padx=3, sticky='w')
        self.e_designation = AutocompleteEntry(
            art_input_frame, placeholder='Désignation', width=220,
            completion_list=pieces_desigs, on_select=self._on_piece_desig_selected
        )
        self.e_designation.grid(row=1, column=1, padx=3, pady=(2, 0), sticky='w')
        self.e_designation.entry.bind('<KeyRelease>', self._on_desig_typed, add='+')

        # Réf Fournisseur
        ctk.CTkLabel(art_input_frame, text='Réf Fournisseur', font=FONTS['small_bold'], text_color=COLORS['text_secondary']).grid(row=0, column=2, padx=3, sticky='w')
        self.e_four = AutocompleteEntry(art_input_frame, placeholder='FR-001', width=130, completion_list=pieces_fours)
        self.e_four.grid(row=1, column=2, padx=3, pady=(2, 0), sticky='w')

        # Unité
        ctk.CTkLabel(art_input_frame, text='Unité', font=FONTS['small_bold'], text_color=COLORS['text_secondary']).grid(row=0, column=3, padx=3, sticky='w')
        self.combo_unite = make_combobox(art_input_frame, UNITES, width=95)
        self.combo_unite.set('UNITE')
        self.combo_unite.grid(row=1, column=3, padx=3, pady=(2, 0), sticky='w')

        # Quantité
        ctk.CTkLabel(art_input_frame, text='Quantité Sortie', font=FONTS['small_bold'], text_color=COLORS['text_secondary']).grid(row=0, column=4, padx=3, sticky='w')
        self.e_qte = make_input(art_input_frame, '1', 95)
        self.e_qte.grid(row=1, column=4, padx=3, pady=(2, 0), sticky='w')

        # Boutons d'action pour l'article (Ajouter / Annuler)
        btn_art_action_box = ctk.CTkFrame(art_input_frame, fg_color='transparent')
        btn_art_action_box.grid(row=1, column=5, padx=(8, 2), pady=(2, 0), sticky='w')

        self.btn_add_art = make_primary_button(btn_art_action_box, '➕ Ajouter', self._add_or_update_article, width=105, height=36)
        self.btn_add_art.pack(side='left', padx=(0, 4))

        self.btn_cancel_art = make_secondary_button(btn_art_action_box, '✖️ Annuler', self._cancel_article_edit, width=80, height=36)
        self.btn_cancel_art.pack(side='left')
        self.btn_cancel_art.configure(state='disabled')

        # Indicateur Stock en temps réel
        self.lbl_stock_info = ctk.CTkLabel(
            form, text='Prêt pour une nouvelle sortie — sélectionnez une pièce pour vérifier son stock disponible.',
            font=FONTS['small'], text_color=COLORS['text_muted']
        )
        self.lbl_stock_info.pack(anchor='w', padx=18, pady=(2, 4))

        # ── Tableau des articles du bon en cours de saisie ────────────────────
        table_art_box = ctk.CTkFrame(form, fg_color=COLORS['bg_hover'], corner_radius=10)
        table_art_box.pack(fill='x', padx=14, pady=(4, 6))

        self.lbl_art_hint = ctk.CTkLabel(
            table_art_box,
            text='💡 Cliquez sur n’importe quel article dans le tableau pour charger et modifier ses champs.',
            font=FONTS['small'], text_color=COLORS['text_muted']
        )
        self.lbl_art_hint.pack(anchor='w', padx=10, pady=(4, 2))

        self.tree_current = ttk.Treeview(
            table_art_box,
            columns=('idx', 'ref', 'four', 'desig', 'unite', 'qte'),
            show='headings', height=4
        )
        self.tree_current.heading('idx', text='N°')
        self.tree_current.heading('ref', text='Réf Interne')
        self.tree_current.heading('four', text='Réf Fournisseur')
        self.tree_current.heading('desig', text='Désignation Pièce')
        self.tree_current.heading('unite', text='Unité')
        self.tree_current.heading('qte', text='Qté Sortie')

        self.tree_current.column('idx', width=35, anchor='center', stretch=False)
        self.tree_current.column('ref', width=130, anchor='center', stretch=True)
        self.tree_current.column('four', width=130, anchor='center', stretch=True)
        self.tree_current.column('desig', width=260, anchor='w', stretch=True)
        self.tree_current.column('unite', width=90, anchor='center', stretch=False)
        self.tree_current.column('qte', width=100, anchor='center', stretch=False)
        self.tree_current.pack(fill='x', padx=8, pady=(2, 6))

        self.tree_current.bind('<ButtonRelease-1>', self._on_current_article_select)
        self.tree_current.bind('<Double-1>', self._on_current_article_select)

        # Barre d'actions sous le tableau d'articles
        sub_art_bar = ctk.CTkFrame(form, fg_color='transparent')
        sub_art_bar.pack(fill='x', padx=14, pady=(2, 8))

        make_danger_button(sub_art_bar, '🗑️ Retirer l\'article sélectionné', self._remove_selected_article, width=220, height=32).pack(side='left', padx=(0, 8))
        make_secondary_button(sub_art_bar, 'Vider la liste', self._clear_current_articles, width=110, height=32).pack(side='left')

        self.lbl_bon_total = ctk.CTkLabel(
            sub_art_bar,
            text='Articles : 0  •  Qté Totale Sortie : 0',
            font=FONTS['subtitle'], text_color=COLORS['primary']
        )
        self.lbl_bon_total.pack(side='right', padx=10)

        # ── Ligne globale de boutons d'action ─────────────────────────────────
        btn_bar = ctk.CTkFrame(form, fg_color='transparent')
        btn_bar.pack(fill='x', padx=14, pady=(0, 12))

        self.btn_save_bon = make_primary_button(btn_bar, '✅ Enregistrer Bon & Générer PDF', self.save_bon_sortie, width=240, height=38)
        self.btn_save_bon.pack(side='left', padx=(0, 8))

        self.btn_view_pdf = make_primary_button(btn_bar, '📄 Consulter PDF', self.open_selected_pdf, width=150, height=38)
        self.btn_view_pdf.pack(side='left', padx=(0, 8))
        self.btn_view_pdf.configure(state='disabled')

        self.btn_load_bon = make_secondary_button(btn_bar, '✏️ Charger / Modifier ce Bon', self.load_selected_bon_into_form, width=200, height=38)
        self.btn_load_bon.pack(side='left', padx=(0, 8))
        self.btn_load_bon.configure(state='disabled')

        self.btn_del_bon = make_danger_button(btn_bar, '🗑️ Supprimer le Bon', self.delete_selected_bon, width=160, height=38)
        self.btn_del_bon.pack(side='left', padx=(0, 8))
        self.btn_del_bon.configure(state='disabled')

        make_secondary_button(btn_bar, 'Tout Réinitialiser', self.reset_entire_form, width=140, height=38).pack(side='left')

        # ── Barre de Filtres par Date & Recherche ─────────────────────────────
        filter_bar = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=12, border_width=1, border_color=COLORS['border'])
        filter_bar.grid(row=2, column=0, sticky='ew', padx=18, pady=(0, 8))

        ctk.CTkLabel(filter_bar, text='📅 Date Début :', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=0, padx=10, pady=8, sticky='w')
        self.filter_start_date = DatePickerWidget(filter_bar, placeholder='AAAA-MM-JJ', width=130)
        self.filter_start_date.grid(row=0, column=1, padx=4, pady=8)

        ctk.CTkLabel(filter_bar, text='📅 Date Fin :', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=2, padx=10, pady=8, sticky='w')
        self.filter_end_date = DatePickerWidget(filter_bar, placeholder='AAAA-MM-JJ', width=130)
        self.filter_end_date.grid(row=0, column=3, padx=4, pady=8)

        ctk.CTkLabel(filter_bar, text='🔍 Recherche :', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=4, padx=10, pady=8, sticky='w')
        self.filter_query = make_input(filter_bar, 'N° BS / Code Engin / Pièce / Opérateur...', 200)
        self.filter_query.grid(row=0, column=5, padx=4, pady=8)

        make_primary_button(filter_bar, '🔍 Filtrer', self.refresh, width=100, height=34).grid(row=0, column=6, padx=6, pady=8)
        make_secondary_button(filter_bar, '❌ Réinitialiser', self._reset_filters, width=110, height=34).grid(row=0, column=7, padx=(0, 10), pady=8)

        # ── Tableau Historique des Bons de Sortie ─────────────────────────────
        table_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=16, border_width=1, border_color=COLORS['border'])
        table_frame.grid(row=3, column=0, sticky='nsew', padx=18, pady=(0, 14))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        self.tree_history = ttk.Treeview(
            table_frame,
            columns=('num_bs', 'engin', 'designation_engin', 'date', 'or', 'operateur', 'nb_art', 'qte_tot', 'km', 'pdf_status'),
            show='headings', height=8
        )
        self.tree_history.heading('num_bs', text='N° Bon Sortie (BS)')
        self.tree_history.heading('engin', text='Code Engin')
        self.tree_history.heading('designation_engin', text='Désignation Engin')
        self.tree_history.heading('date', text='Date Sortie')
        self.tree_history.heading('or', text='N° Ordre (OR)')
        self.tree_history.heading('operateur', text='Opérateur')
        self.tree_history.heading('nb_art', text='Nb Articles')
        self.tree_history.heading('qte_tot', text='Qté Totale')
        self.tree_history.heading('km', text='Kilométrage')
        self.tree_history.heading('pdf_status', text='Document PDF')

        self.tree_history.column('num_bs', anchor='center', width=130, stretch=True)
        self.tree_history.column('engin', anchor='center', width=90, stretch=False)
        self.tree_history.column('designation_engin', anchor='w', width=150, stretch=True)
        self.tree_history.column('date', anchor='center', width=100, stretch=True)
        self.tree_history.column('or', anchor='center', width=100, stretch=False)
        self.tree_history.column('operateur', anchor='center', width=130, stretch=True)
        self.tree_history.column('nb_art', anchor='center', width=80, stretch=False)
        self.tree_history.column('qte_tot', anchor='center', width=80, stretch=False)
        self.tree_history.column('km', anchor='center', width=100, stretch=False)
        self.tree_history.column('pdf_status', anchor='center', width=110, stretch=True)

        self.tree_history.pack(fill='both', expand=True, padx=10, pady=10)

        self.tree_history.bind('<ButtonRelease-1>', self.on_history_select)
        self.tree_history.bind('<Double-1>', lambda e: self.open_selected_pdf())
        bind_tree_clear_selection(self.tree_history, clear_callback=self._on_history_unselect)

        self.refresh()

    def _open_piece_search_dialog(self):
        """Ouvre le dialog de recherche/sélection de pièce."""
        pieces = get_all_pieces()

        def _on_piece_selected(piece: dict):
            self._syncing = True
            self.e_ref.set(piece.get('reference_interne', ''))
            self.e_designation.set(piece.get('designation', ''))
            if piece.get('reference_fournisseur'):
                self.e_four.set(piece['reference_fournisseur'])
            if piece.get('unite'):
                self.combo_unite.set(piece['unite'])
            self._syncing = False
            self._apply_piece_info(piece)

        open_piece_search(self, pieces, on_select=_on_piece_selected)

    def _reset_filters(self):
        self.filter_start_date.delete(0, 'end')
        self.filter_end_date.delete(0, 'end')
        self.filter_query.delete(0, 'end')
        self.refresh()

    def _apply_piece_info(self, piece: dict):
        if not piece:
            return
        if piece.get('id'):
            fresh = get_piece_by_id(piece['id'])
            if fresh:
                piece = fresh
        if piece.get('unite'):
            self.combo_unite.set(piece['unite'])
        if piece.get('reference_fournisseur') and not self.e_four.get().strip():
            self.e_four.set(piece['reference_fournisseur'])

        stock = float(piece.get('quantite', 0) or 0)
        unit = piece.get('unite', 'UNITE')
        empl = f"  •  Emplacement : {piece['emplacement']}" if piece.get('emplacement') else ""
        self.lbl_stock_info.configure(
            text=f"✅ Pièce : {piece.get('designation', '')}  •  Réf : {piece.get('reference_interne', '')}  •  Stock disponible : {format_qty(stock)} {unit}{empl}",
            text_color=COLORS['success'] if stock > 0 else COLORS['danger']
        )

    def _on_piece_ref_changed(self, choice=None):
        if self._syncing:
            return
        ref = self.e_ref.get().strip()
        if ref:
            piece = get_piece_by_reference(ref)
            if piece:
                self._syncing = True
                if piece.get('designation'):
                    self.e_designation.set(piece['designation'])
                if piece.get('reference_fournisseur'):
                    self.e_four.set(piece['reference_fournisseur'])
                self._syncing = False
                self._apply_piece_info(piece)

    def _on_ref_typed(self, event=None):
        if self._syncing:
            return
        ref = self.e_ref.get().strip()
        if ref:
            piece = get_piece_by_reference(ref)
            if piece:
                self._syncing = True
                if piece.get('designation') and not self.e_designation.get().strip():
                    self.e_designation.set(piece['designation'])
                if piece.get('reference_fournisseur') and not self.e_four.get().strip():
                    self.e_four.set(piece['reference_fournisseur'])
                self._syncing = False
                self._apply_piece_info(piece)

    def _on_piece_desig_selected(self, choice=None):
        if self._syncing:
            return
        desig = self.e_designation.get().strip()
        if desig:
            piece = get_piece_by_designation(desig)
            if piece:
                self._syncing = True
                if piece.get('reference_interne'):
                    self.e_ref.set(piece['reference_interne'])
                if piece.get('reference_fournisseur'):
                    self.e_four.set(piece['reference_fournisseur'])
                self._syncing = False
                self._apply_piece_info(piece)

    def _on_desig_typed(self, event=None):
        if self._syncing:
            return
        desig = self.e_designation.get().strip()
        if desig and len(desig) >= 2:
            piece = get_piece_by_designation(desig)
            if piece:
                self._syncing = True
                if piece.get('reference_interne') and not self.e_ref.get().strip():
                    self.e_ref.set(piece['reference_interne'])
                if piece.get('reference_fournisseur') and not self.e_four.get().strip():
                    self.e_four.set(piece['reference_fournisseur'])
                self._syncing = False
                self._apply_piece_info(piece)

    def _on_current_article_select(self, event=None):
        selected = self.tree_current.selection()
        if not selected:
            return
        values = self.tree_current.item(selected[0], 'values')
        if not values:
            return

        try:
            idx = int(values[0]) - 1
            if 0 <= idx < len(self._current_articles):
                art = self._current_articles[idx]
                self._editing_article_idx = idx

                self.e_ref.set(art.get('reference_interne', ''))
                self.e_four.set(art.get('reference_fournisseur', ''))
                self.e_designation.set(art.get('designation', ''))
                self.combo_unite.set(art.get('unite', 'UNITE'))
                self.e_qte.delete(0, 'end')
                self.e_qte.insert(0, format_qty(art.get('quantite', 1)))

                piece = get_piece_by_reference(art.get('reference_interne', ''))
                if piece:
                    self._apply_piece_info(piece)

                self.btn_add_art.configure(text='💾 Mettre à jour')
                self.btn_cancel_art.configure(state='normal')
                self.lbl_art_hint.configure(
                    text=f'✏️ Modification de l’article N° {idx + 1} ({art.get("reference_interne", "")}) — Modifiez les champs ci-dessus puis cliquez sur "💾 Mettre à jour".',
                    text_color=COLORS['primary']
                )
        except Exception:
            pass

    def _cancel_article_edit(self):
        self._editing_article_idx = None
        self.btn_add_art.configure(text='➕ Ajouter')
        self.btn_cancel_art.configure(state='disabled')
        self.lbl_art_hint.configure(text='💡 Cliquez sur n’importe quel article dans le tableau pour charger et modifier ses champs.', text_color=COLORS['text_muted'])

        self.e_ref.set('')
        self.e_designation.set('')
        self.e_four.set('')
        self.e_qte.delete(0, 'end')
        self.e_qte.insert(0, '1')
        self.combo_unite.set('UNITE')
        self.lbl_stock_info.configure(text='Prêt pour une nouvelle sortie — sélectionnez une pièce pour vérifier son stock disponible.', text_color=COLORS['text_muted'])

        for item in self.tree_current.selection():
            self.tree_current.selection_remove(item)

    def _add_or_update_article(self):
        ref_int = self.e_ref.get().strip()
        desig = self.e_designation.get().strip()
        ref_four = self.e_four.get().strip()
        unite = self.combo_unite.get().strip() or 'UNITE'

        if not ref_int and not desig:
            show_toast(self, 'Veuillez saisir ou sélectionner une référence ou désignation de pièce.', 'warning')
            return

        piece = get_piece_by_reference(ref_int) or (get_piece_by_designation(desig) if desig else None)
        if not piece:
            show_toast(self, f"Pièce '{ref_int or desig}' introuvable dans le stock.", 'warning')
            return

        ref_int = piece['reference_interne']
        desig = piece['designation']
        if not ref_four:
            ref_four = piece.get('reference_fournisseur', '')

        try:
            qty = parse_qty(self.e_qte.get())
            if qty <= 0:
                raise ValueError
        except ValueError:
            show_toast(self, 'Veuillez renseigner une quantité valide (> 0).', 'warning')
            return

        stock_dispo = float(piece.get('quantite', 0) or 0)

        # Calculer la quantité déjà saisie dans la liste courante pour cette pièce
        qty_already_in_list = 0.0
        for i, a in enumerate(self._current_articles):
            if i != self._editing_article_idx and a.get('piece_id') == piece['id']:
                qty_already_in_list += float(a.get('quantite', 0))

        if stock_dispo < (qty + qty_already_in_list):
            show_toast(self, f"Stock insuffisant pour '{ref_int}' (Disponible : {format_qty(stock_dispo)} {unite}).", 'danger')
            return

        article_data = {
            'piece_id': piece['id'],
            'reference_interne': ref_int,
            'reference_fournisseur': ref_four,
            'designation': desig,
            'piece_designation': desig,
            'unite': unite,
            'quantite': qty,
        }

        if self._editing_article_idx is not None and 0 <= self._editing_article_idx < len(self._current_articles):
            self._current_articles[self._editing_article_idx] = article_data
            self._editing_article_idx = None
            self.btn_add_art.configure(text='➕ Ajouter')
            self.btn_cancel_art.configure(state='disabled')
            self.lbl_art_hint.configure(text='✅ Article mis à jour dans la liste. Cliquez sur "✅ Enregistrer Bon & Générer PDF" pour valider.', text_color=COLORS['success'])
            show_toast(self, f"Article '{ref_int}' mis à jour.", 'success')
        else:
            # Vérifier si déjà présent dans la liste
            existing_idx = None
            for idx, art in enumerate(self._current_articles):
                if art.get('reference_interne', '').strip().lower() == ref_int.lower():
                    existing_idx = idx
                    break

            if existing_idx is not None:
                old = self._current_articles[existing_idx]
                new_q = old['quantite'] + qty
                if stock_dispo < new_q:
                    show_toast(self, f"Stock insuffisant pour cumuler '{ref_int}' (Disponible : {format_qty(stock_dispo)} {unite}).", 'danger')
                    return
                old['quantite'] = new_q
                if desig:
                    old['designation'] = desig
                if ref_four:
                    old['reference_fournisseur'] = ref_four
                show_toast(self, f"Quantité cumulée pour '{ref_int}' (Total : {format_qty(new_q)})", 'info')
            else:
                self._current_articles.append(article_data)
                show_toast(self, f"Article '{ref_int}' ajouté au bon.", 'success')
                self.lbl_art_hint.configure(text='💡 Cliquez sur n’importe quel article dans le tableau pour charger et modifier ses champs.', text_color=COLORS['text_muted'])

        self._refresh_current_articles_tree()

        # Réinitialiser la ligne de saisie
        self.e_ref.set('')
        self.e_designation.set('')
        self.e_four.set('')
        self.e_qte.delete(0, 'end')
        self.e_qte.insert(0, '1')
        self.lbl_stock_info.configure(text='Prêt pour une nouvelle sortie — sélectionnez une pièce pour vérifier son stock disponible.', text_color=COLORS['text_muted'])

    def _remove_selected_article(self):
        selected = self.tree_current.selection()
        if not selected:
            messagebox.showwarning('Attention', 'Sélectionnez un article à retirer dans le tableau ci-dessus.')
            return
        idx = int(self.tree_current.item(selected[0], 'values')[0]) - 1
        if 0 <= idx < len(self._current_articles):
            self._current_articles.pop(idx)
            if self._editing_article_idx == idx:
                self._cancel_article_edit()
            elif self._editing_article_idx is not None and self._editing_article_idx > idx:
                self._editing_article_idx -= 1
            self._refresh_current_articles_tree()

    def _clear_current_articles(self):
        self._current_articles = []
        self._cancel_article_edit()
        self._refresh_current_articles_tree()

    def _refresh_current_articles_tree(self):
        for row in self.tree_current.get_children():
            self.tree_current.delete(row)

        total_qte = 0.0
        for i, art in enumerate(self._current_articles, start=1):
            q = float(art.get('quantite', 0) or 0)
            total_qte += q
            self.tree_current.insert('', 'end', values=(
                i,
                art.get('reference_interne', ''),
                art.get('reference_fournisseur', '—'),
                art.get('designation', art.get('piece_designation', '')),
                art.get('unite', 'UNITE'),
                format_qty(q),
            ))

        self.lbl_bon_total.configure(
            text=f"Articles : {len(self._current_articles)}  •  Qté Totale Sortie : {format_qty(total_qte)}"
        )

    def load_selected_bon_into_form(self):
        """Charge le bon sélectionné dans l'historique dans le formulaire pour modification."""
        if not self._selected_bon:
            show_toast(self, 'Veuillez sélectionner un bon de sortie dans le tableau.', 'warning')
            return

        b = self._selected_bon
        num_bs = b.get('numero_bon_sortie', '')
        code_engin = b.get('code_engin', '')
        date_s = b.get('date_sortie', '')
        or_val = b.get('ordre_reparation', '')
        op_nom = b.get('nom_operateur', '')
        km_val = b.get('kilometrage', '')

        articles = b.get('articles', [])
        if not articles:
            articles = get_bon_sortie_details(num_bs)

        if not articles:
            show_toast(self, 'Aucun article trouvé pour ce bon de sortie.', 'warning')
            return

        self.e_num_bs.delete(0, 'end')
        self.e_num_bs.insert(0, num_bs)

        if code_engin and hasattr(self, 'e_code_engin'):
            self.e_code_engin.set(code_engin)

        if date_s:
            self.e_date.delete(0, 'end')
            self.e_date.insert(0, str(date_s))

        self.e_or.delete(0, 'end')
        if or_val and or_val != '—':
            self.e_or.insert(0, str(or_val))

        if op_nom:
            self.combo_operateur.set(op_nom)

        self.e_km.delete(0, 'end')
        if km_val and km_val != '—':
            self.e_km.insert(0, str(km_val))

        self._current_articles = []
        for art in articles:
            q = parse_qty(art.get('quantite', 1))
            self._current_articles.append({
                'piece_id': art.get('piece_id'),
                'reference_interne': art.get('reference_interne', ''),
                'reference_fournisseur': art.get('reference_fournisseur', ''),
                'designation': art.get('piece_designation', art.get('designation', '')),
                'piece_designation': art.get('piece_designation', art.get('designation', '')),
                'unite': art.get('unite', 'UNITE') or 'UNITE',
                'quantite': q,
            })

        self.btn_save_bon.configure(text='💾 Enregistrer les Modifications du Bon')
        self._cancel_article_edit()
        self._refresh_current_articles_tree()
        self.lbl_art_hint.configure(
            text=f'✏️ Modification du Bon "{num_bs}" (Engin : {code_engin}). Ajustez les articles puis cliquez sur "💾 Enregistrer les Modifications du Bon".',
            text_color=COLORS['primary']
        )
        show_toast(self, f"Bon '{num_bs}' chargé ({len(self._current_articles)} article(s)).", 'info')

    def save_bon_sortie(self):
        num_bs = self.e_num_bs.get().strip()
        code_engin = self.e_code_engin.get().strip()
        date_s = self.e_date.get().strip()
        or_num = self.e_or.get().strip()
        nom_op = self.combo_operateur.get().strip() or 'Benkerrou Tarek'
        km = self.e_km.get().strip()

        if not num_bs:
            messagebox.showwarning('Attention', 'Veuillez renseigner le numéro de bon de sortie.')
            return

        if not code_engin:
            messagebox.showwarning('Attention', 'Veuillez sélectionner un code engin.')
            return

        engin = get_engin_by_code(code_engin)
        if not engin:
            messagebox.showerror('Erreur', f"Le code engin '{code_engin}' est introuvable.")
            return

        if not self._current_articles:
            # Si l'utilisateur a rempli la ligne mais n'a pas cliqué sur Ajouter
            ref_int = self.e_ref.get().strip()
            desig = self.e_designation.get().strip()
            if ref_int or desig:
                self._add_or_update_article()
            if not self._current_articles:
                messagebox.showwarning('Attention', 'Veuillez ajouter au moins un article à ce bon de sortie.')
                return

        # Si le bon existe déjà dans la base (mode modification), supprimer l'ancienne version
        existing_bons = [b for b in get_bons_sortie_grouped() if str(b['numero_bon_sortie']) == str(num_bs)]
        if existing_bons:
            delete_bon_sortie_by_num(num_bs, restore_stock=True)

        user = list_users()[0] if list_users() else {'id': 1, 'username': 'admin'}
        user_id = user.get('id', 1)

        # Enregistrement en base de données (vérifie le stock et effectue les déductions atomiquement)
        header_data = {
            'numero_bon_sortie': num_bs,
            'engin_id': engin['id'],
            'date_sortie': date_s,
            'nom_operateur': nom_op,
            'ordre_reparation': or_num,
            'kilometrage': km
        }

        try:
            res = create_bon_sortie_multi(header_data, self._current_articles, user_id)
        except ValueError as exc:
            show_toast(self, str(exc), 'danger')
            return

        # Génération du PDF officiel multi-articles
        pdf_data = {
            'numero_bon_sortie': num_bs,
            'date_sortie': date_s,
            'code_engin': engin['code_engin'],
            'matricule': engin.get('matricule', ''),
            'designation_engin': engin['designation'],
            'kilometrage': km,
            'ordre_reparation': or_num,
            'nom_operateur': nom_op,
            'utilisateur': nom_op,
            'articles': self._current_articles
        }
        pdf_path = generate_bon_sortie_pdf(pdf_data)

        # Mettre à jour le chemin PDF dans la base
        update_bon_sortie_chemin_pdf(num_bs, pdf_path)

        show_toast(self, f"Bon de Sortie {num_bs} enregistré avec succès ({len(self._current_articles)} article(s)).", 'success')

        self.reset_entire_form()
        self.refresh()

        if pdf_path and os.path.exists(pdf_path):
            ouvrir_pdf_viewer(self, pdf_path, f"Bon de Sortie {num_bs}")

    def on_history_select(self, event):
        item = self.tree_history.selection()
        if not item:
            return
        values = self.tree_history.item(item[0], 'values')
        if not values:
            return

        num_bs = values[0]
        self._selected_bon = None

        bons = get_bons_sortie_grouped()
        for b in bons:
            if str(b['numero_bon_sortie']) == str(num_bs):
                self._selected_bon = b
                break

        self.btn_view_pdf.configure(state='normal')
        self.btn_load_bon.configure(state='normal')
        self.btn_del_bon.configure(state='normal')

    def _on_history_unselect(self):
        self._selected_bon = None
        self.btn_view_pdf.configure(state='disabled')
        self.btn_load_bon.configure(state='disabled')
        self.btn_del_bon.configure(state='disabled')

    def open_selected_pdf(self):
        if not self._selected_bon:
            messagebox.showwarning('Attention', 'Veuillez sélectionner un bon de sortie dans le tableau.')
            return

        b = self._selected_bon
        pdf_path = b.get('chemin_pdf')

        if not pdf_path or not os.path.exists(pdf_path):
            articles = b.get('articles', [])
            if not articles:
                articles = get_bon_sortie_details(b['numero_bon_sortie'])

            pdf_path = generate_bon_sortie_pdf({
                'numero_bon_sortie': b['numero_bon_sortie'],
                'date_sortie': b.get('date_sortie') or (b.get('date_heure', '')[:10]),
                'code_engin': b.get('code_engin', ''),
                'matricule': b.get('matricule', ''),
                'designation_engin': b.get('engin_designation', ''),
                'kilometrage': b.get('kilometrage', ''),
                'ordre_reparation': b.get('ordre_reparation', ''),
                'nom_operateur': b.get('nom_operateur', 'Benkerrou Tarek'),
                'utilisateur': b.get('nom_operateur', 'Benkerrou Tarek'),
                'articles': articles
            })
            update_bon_sortie_chemin_pdf(b['numero_bon_sortie'], pdf_path)
            b['chemin_pdf'] = pdf_path

        ouvrir_pdf_viewer(self, pdf_path, f"Bon de Sortie {b['numero_bon_sortie']}")

    def delete_selected_bon(self):
        if not self._selected_bon:
            messagebox.showwarning('Attention', 'Veuillez sélectionner un bon de sortie à supprimer.')
            return

        b = self._selected_bon
        num_bs = b['numero_bon_sortie']
        nb_art = len(b.get('articles', []))

        msg = f"Voulez-vous vraiment supprimer le Bon de Sortie '{num_bs}' ({nb_art} article(s)) ?\n\nLes pièces sorties seront réintégrées dans le stock disponible."
        if messagebox.askyesno('Confirmation de suppression', msg):
            delete_bon_sortie_by_num(num_bs, restore_stock=True)
            self._on_history_unselect()
            self.refresh()
            messagebox.showinfo('Supprimé', f"Le Bon de Sortie '{num_bs}' a été supprimé. Stock réintégré.")

    def reset_entire_form(self):
        self.e_num_bs.delete(0, 'end')
        self.e_num_bs.insert(0, self._generate_auto_bs_num())

        engins = get_all_engins()
        engins_codes = [e['code_engin'] for e in engins if e.get('code_engin')]
        if engins_codes and hasattr(self, 'e_code_engin'):
            self.e_code_engin.set(engins_codes[0])

        self.e_ref.set('')
        self.e_four.set('')
        self.e_designation.set('')
        self.combo_unite.set('UNITE')
        self.e_qte.delete(0, 'end')
        self.e_qte.insert(0, '1')
        self.e_km.delete(0, 'end')
        self.e_or.delete(0, 'end')
        self.e_date.delete(0, 'end')
        self.e_date.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.btn_save_bon.configure(text='✅ Enregistrer Bon & Générer PDF')
        self.lbl_art_hint.configure(text='💡 Cliquez sur n’importe quel article dans le tableau pour charger et modifier ses champs.', text_color=COLORS['text_muted'])
        self.lbl_stock_info.configure(text='Prêt pour une nouvelle sortie — sélectionnez une pièce pour vérifier son stock disponible.', text_color=COLORS['text_muted'])
        self._clear_current_articles()
        self._on_history_unselect()

    def refresh(self):
        self._all_pieces = get_all_pieces()
        piece_refs = [p['reference_interne'] for p in self._all_pieces if p.get('reference_interne')]
        piece_desigs = [p['designation'] for p in self._all_pieces if p.get('designation')]
        piece_fours = [p['reference_fournisseur'] for p in self._all_pieces if p.get('reference_fournisseur')]

        if hasattr(self, 'e_ref') and hasattr(self.e_ref, 'set_completion_list'):
            self.e_ref.set_completion_list(piece_refs)
        if hasattr(self, 'e_designation') and hasattr(self.e_designation, 'set_completion_list'):
            self.e_designation.set_completion_list(piece_desigs)
        if hasattr(self, 'e_four') and hasattr(self.e_four, 'set_completion_list'):
            self.e_four.set_completion_list(piece_fours)

        engins = get_all_engins()
        engins_codes = [e['code_engin'] for e in engins if e.get('code_engin')]
        if hasattr(self, 'e_code_engin') and hasattr(self.e_code_engin, 'set_completion_list'):
            self.e_code_engin.set_completion_list(engins_codes)

        operateurs_list = get_all_operateurs()
        if hasattr(self, 'combo_operateur') and hasattr(self.combo_operateur, 'set_completion_list'):
            self.combo_operateur.set_completion_list(operateurs_list)

        for row in self.tree_history.get_children():
            self.tree_history.delete(row)

        start_d = self.filter_start_date.get().strip() if hasattr(self, 'filter_start_date') else ''
        end_d = self.filter_end_date.get().strip() if hasattr(self, 'filter_end_date') else ''
        query = self.filter_query.get().strip().lower() if hasattr(self, 'filter_query') else ''

        for bon in get_bons_sortie_grouped():
            date_s = bon.get('date_sortie', '') or ''

            if start_d and date_s < start_d:
                continue
            if end_d and date_s > end_d:
                continue

            if query:
                num_bs = (bon.get('numero_bon_sortie') or '').lower()
                c_eng = (bon.get('code_engin') or '').lower()
                d_eng = (bon.get('engin_designation') or '').lower()
                op = (bon.get('nom_operateur') or '').lower()
                or_num = (bon.get('ordre_reparation') or '').lower()
                articles_text = ' '.join([(a.get('reference_interne', '') + ' ' + a.get('piece_designation', '') + ' ' + a.get('designation', '')) for a in bon.get('articles', [])]).lower()
                if query not in num_bs and query not in c_eng and query not in d_eng and query not in op and query not in or_num and query not in articles_text:
                    continue

            pdf_indicator = "📄 Disponible" if bon.get('chemin_pdf') and os.path.exists(bon.get('chemin_pdf')) else "📄 À générer"

            self.tree_history.insert('', 'end', values=(
                bon['numero_bon_sortie'],
                bon.get('code_engin', '—'),
                bon.get('engin_designation', '—'),
                date_s or '—',
                bon.get('ordre_reparation') or '—',
                bon.get('nom_operateur') or 'Benkerrou Tarek',
                len(bon.get('articles', [])),
                format_qty(bon.get('quantite_totale', 0)),
                bon.get('kilometrage') or '—',
                pdf_indicator,
            ))
