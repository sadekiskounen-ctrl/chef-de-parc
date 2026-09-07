import os
from pathlib import Path
from tkinter import ttk, messagebox
from datetime import datetime

import customtkinter as ctk

from database.db_manager import (
    create_bon_reception_multi, get_bons_reception_grouped,
    get_bon_reception_details, delete_bon_reception_by_num,
    update_bon_reception_chemin_pdf, get_piece_by_reference,
    get_all_pieces
)
from services.pdf_generator import generate_bon_reception_pdf
from ui.pdf_viewer import ouvrir_pdf_viewer
from ui.theme import COLORS, FONTS, UNITES, format_money, format_qty, parse_qty
from ui.widgets import (
    make_input, make_primary_button, make_secondary_button, make_danger_button,
    make_combobox, DatePickerWidget, bind_tree_clear_selection
)


class BonLivraisonFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color='transparent')
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._current_articles = []       # Liste des articles du bon en cours de saisie
        self._selected_bon = None          # Bon sélectionné dans l'historique
        self._editing_article_idx = None   # Index de l'article en cours d'édition dans _current_articles

        self.build()

    def build(self):
        # ── Header ────────────────────────────────────────────────────────────
        self.header = ctk.CTkFrame(self, fg_color='transparent')
        self.header.grid(row=0, column=0, sticky='ew', padx=18, pady=(14, 6))
        ctk.CTkLabel(self.header, text='Bon de réception', font=FONTS['title_large'], text_color=COLORS['text_primary']).pack(anchor='w')
        ctk.CTkLabel(self.header, text='Réception de livraisons multi-articles — Consultation, Modification & Impression PDF', font=FONTS['body'], text_color=COLORS['text_secondary']).pack(anchor='w')

        # ── Formulaire de Saisie Multi-Articles ────────────────────────────────
        form = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=16, border_width=1, border_color=COLORS['border'])
        form.grid(row=1, column=0, sticky='ew', padx=18, pady=(0, 10))

        # En-tête du Bon : N° BL, Fournisseur, Date
        hdr_frame = ctk.CTkFrame(form, fg_color='transparent')
        hdr_frame.pack(fill='x', padx=14, pady=(12, 6))

        ctk.CTkLabel(hdr_frame, text='N° Bon de Livraison / Réception :', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=0, padx=(0, 6), sticky='w')
        self.e_num_bl = make_input(hdr_frame, 'ex: BL-2025-001', 170)
        self.e_num_bl.grid(row=0, column=1, padx=(0, 14), sticky='w')

        ctk.CTkLabel(hdr_frame, text='Nom Fournisseur :', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=2, padx=(0, 6), sticky='w')
        self.e_nom_four = make_input(hdr_frame, 'SARL Fournisseur', 190)
        self.e_nom_four.grid(row=0, column=3, padx=(0, 14), sticky='w')

        ctk.CTkLabel(hdr_frame, text='Date Réception :', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=4, padx=(0, 6), sticky='w')
        self.e_date = DatePickerWidget(hdr_frame, placeholder='AAAA-MM-JJ', width=140, default_value=datetime.now().strftime('%Y-%m-%d'))
        self.e_date.grid(row=0, column=5, sticky='w')

        # Séparateur visuel subtil
        ctk.CTkFrame(form, fg_color=COLORS['border'], height=1).pack(fill='x', padx=14, pady=4)

        # Ligne de saisie / modification d'un article
        art_input_frame = ctk.CTkFrame(form, fg_color='transparent')
        art_input_frame.pack(fill='x', padx=14, pady=(6, 6))

        # Réf Interne
        ctk.CTkLabel(art_input_frame, text='Réf Interne', font=FONTS['small_bold'], text_color=COLORS['text_secondary']).grid(row=0, column=0, padx=3, sticky='w')
        piece_refs = [p['reference_interne'] for p in get_all_pieces()]
        self.e_ref = make_combobox(art_input_frame, piece_refs if piece_refs else ['PI-001'], width=140)
        self.e_ref.grid(row=1, column=0, padx=3, pady=(2, 0), sticky='w')
        self.e_ref.configure(command=self._on_piece_ref_changed)

        # Réf Fournisseur
        ctk.CTkLabel(art_input_frame, text='Réf Fournisseur', font=FONTS['small_bold'], text_color=COLORS['text_secondary']).grid(row=0, column=1, padx=3, sticky='w')
        self.e_four = make_input(art_input_frame, 'FR-001', 130)
        self.e_four.grid(row=1, column=1, padx=3, pady=(2, 0), sticky='w')

        # Désignation
        ctk.CTkLabel(art_input_frame, text='Désignation Pièce', font=FONTS['small_bold'], text_color=COLORS['text_secondary']).grid(row=0, column=2, padx=3, sticky='w')
        self.e_designation = make_input(art_input_frame, 'Désignation', 190)
        self.e_designation.grid(row=1, column=2, padx=3, pady=(2, 0), sticky='w')

        # Unité
        ctk.CTkLabel(art_input_frame, text='Unité', font=FONTS['small_bold'], text_color=COLORS['text_secondary']).grid(row=0, column=3, padx=3, sticky='w')
        self.combo_unite = make_combobox(art_input_frame, UNITES, width=105)
        self.combo_unite.set('UNITE')
        self.combo_unite.grid(row=1, column=3, padx=3, pady=(2, 0), sticky='w')

        # Quantité (dynamique float / int)
        ctk.CTkLabel(art_input_frame, text='Quantité', font=FONTS['small_bold'], text_color=COLORS['text_secondary']).grid(row=0, column=4, padx=3, sticky='w')
        self.e_qte = make_input(art_input_frame, '1', 80)
        self.e_qte.grid(row=1, column=4, padx=3, pady=(2, 0), sticky='w')

        # Prix Unitaire
        ctk.CTkLabel(art_input_frame, text='Prix Unit. (DZD)', font=FONTS['small_bold'], text_color=COLORS['text_secondary']).grid(row=0, column=5, padx=3, sticky='w')
        self.e_prix = make_input(art_input_frame, '0.00', 105)
        self.e_prix.grid(row=1, column=5, padx=3, pady=(2, 0), sticky='w')

        # Boutons d'action pour l'article (Ajouter / Modifier / Annuler)
        btn_art_action_box = ctk.CTkFrame(art_input_frame, fg_color='transparent')
        btn_art_action_box.grid(row=1, column=6, padx=(8, 2), pady=(2, 0), sticky='w')

        self.btn_add_art = make_primary_button(btn_art_action_box, '➕ Ajouter', self._add_or_update_article, width=110, height=36)
        self.btn_add_art.pack(side='left', padx=(0, 4))

        self.btn_cancel_art = make_secondary_button(btn_art_action_box, '✖️ Annuler', self._cancel_article_edit, width=85, height=36)
        self.btn_cancel_art.pack(side='left')
        self.btn_cancel_art.configure(state='disabled')

        # Tableau des articles du bon en cours de saisie
        table_art_box = ctk.CTkFrame(form, fg_color=COLORS['bg_hover'], corner_radius=10)
        table_art_box.pack(fill='x', padx=14, pady=(8, 6))

        # Instructions / indication d'édition
        self.lbl_art_hint = ctk.CTkLabel(
            table_art_box,
            text='💡 Cliquez sur n’importe quel article dans le tableau pour charger et modifier ses champs.',
            font=FONTS['small'], text_color=COLORS['text_muted']
        )
        self.lbl_art_hint.pack(anchor='w', padx=10, pady=(6, 2))

        self.tree_current = ttk.Treeview(
            table_art_box,
            columns=('idx', 'ref', 'four', 'desig', 'unite', 'qte', 'prix', 'total'),
            show='headings', height=4
        )
        self.tree_current.heading('idx', text='N°')
        self.tree_current.heading('ref', text='Réf Interne')
        self.tree_current.heading('four', text='Réf Fournisseur')
        self.tree_current.heading('desig', text='Désignation')
        self.tree_current.heading('unite', text='Unité')
        self.tree_current.heading('qte', text='Qté')
        self.tree_current.heading('prix', text='Prix Unit.')
        self.tree_current.heading('total', text='Total Ligne')

        self.tree_current.column('idx', width=35, anchor='center', stretch=False)
        self.tree_current.column('ref', width=110, anchor='center', stretch=True)
        self.tree_current.column('four', width=110, anchor='center', stretch=True)
        self.tree_current.column('desig', width=180, anchor='w', stretch=True)
        self.tree_current.column('unite', width=75, anchor='center', stretch=False)
        self.tree_current.column('qte', width=75, anchor='center', stretch=False)
        self.tree_current.column('prix', width=110, anchor='center', stretch=True)
        self.tree_current.column('total', width=120, anchor='center', stretch=True)
        self.tree_current.pack(fill='x', padx=8, pady=(2, 6))

        self.tree_current.bind('<ButtonRelease-1>', self._on_current_article_select)
        self.tree_current.bind('<Double-1>', self._on_current_article_select)

        # Barre d'actions sous le tableau d'articles
        sub_art_bar = ctk.CTkFrame(form, fg_color='transparent')
        sub_art_bar.pack(fill='x', padx=14, pady=(2, 10))

        make_danger_button(sub_art_bar, '🗑️ Retirer l\'article sélectionné', self._remove_selected_article, width=220, height=32).pack(side='left', padx=(0, 8))
        make_secondary_button(sub_art_bar, 'Vider la liste', self._clear_current_articles, width=110, height=32).pack(side='left')

        self.lbl_bon_total = ctk.CTkLabel(
            sub_art_bar,
            text='Articles : 0  •  Montant Total Bon : 0,00 DZD',
            font=FONTS['subtitle'], text_color=COLORS['primary']
        )
        self.lbl_bon_total.pack(side='right', padx=10)

        # Ligne globale de boutons d'action
        btn_bar = ctk.CTkFrame(form, fg_color='transparent')
        btn_bar.pack(fill='x', padx=14, pady=(0, 12))

        self.btn_save_bon = make_primary_button(btn_bar, '✅ Enregistrer Bon & Générer PDF', self.save_bon_reception, width=240, height=38)
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
        self.filter_query = make_input(filter_bar, 'N° BL / Fournisseur / Réf...', 180)
        self.filter_query.grid(row=0, column=5, padx=4, pady=8)

        make_primary_button(filter_bar, '🔍 Filtrer', self.refresh, width=100, height=34).grid(row=0, column=6, padx=6, pady=8)
        make_secondary_button(filter_bar, '❌ Réinitialiser', self._reset_filters, width=110, height=34).grid(row=0, column=7, padx=(0, 10), pady=8)

        # ── Tableau Historique des Bons de Réception ─────────────────────────
        table_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=16, border_width=1, border_color=COLORS['border'])
        table_frame.grid(row=3, column=0, sticky='nsew', padx=18, pady=(0, 14))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        self.tree_history = ttk.Treeview(
            table_frame,
            columns=('num_bl', 'fournisseur', 'date', 'nb_art', 'qte_tot', 'montant_tot', 'pdf_status'),
            show='headings', height=8
        )
        self.tree_history.heading('num_bl', text='N° Bon de Réception (BL)')
        self.tree_history.heading('fournisseur', text='Fournisseur')
        self.tree_history.heading('date', text='Date Réception')
        self.tree_history.heading('nb_art', text='Nb Articles')
        self.tree_history.heading('qte_tot', text='Qté Totale')
        self.tree_history.heading('montant_tot', text='Montant Total (DZD)')
        self.tree_history.heading('pdf_status', text='Document PDF')

        self.tree_history.column('num_bl', anchor='center', width=150, stretch=True)
        self.tree_history.column('fournisseur', anchor='w', width=180, stretch=True)
        self.tree_history.column('date', anchor='center', width=110, stretch=True)
        self.tree_history.column('nb_art', anchor='center', width=90, stretch=False)
        self.tree_history.column('qte_tot', anchor='center', width=90, stretch=False)
        self.tree_history.column('montant_tot', anchor='center', width=140, stretch=True)
        self.tree_history.column('pdf_status', anchor='center', width=120, stretch=True)

        self.tree_history.pack(fill='both', expand=True, padx=10, pady=10)

        self.tree_history.bind('<ButtonRelease-1>', self.on_history_select)
        self.tree_history.bind('<Double-1>', lambda e: self.open_selected_pdf())
        bind_tree_clear_selection(self.tree_history, clear_callback=self._on_history_unselect)

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
                if piece.get('unite'):
                    self.combo_unite.set(piece['unite'])
                pu = piece.get('nouveau_prix_unitaire') or piece.get('ancien_prix_unitaire') or 0
                if pu > 0:
                    self.e_prix.delete(0, 'end')
                    self.e_prix.insert(0, f"{pu:.2f}")

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

                # Charger les données dans les champs de saisie
                self.e_ref.set(art.get('reference_interne', ''))
                self.e_four.delete(0, 'end')
                self.e_four.insert(0, art.get('reference_fournisseur', ''))

                self.e_designation.delete(0, 'end')
                self.e_designation.insert(0, art.get('designation', ''))

                self.combo_unite.set(art.get('unite', 'UNITE'))

                self.e_qte.delete(0, 'end')
                self.e_qte.insert(0, format_qty(art.get('quantite', 1)))

                self.e_prix.delete(0, 'end')
                self.e_prix.insert(0, f"{float(art.get('prix_unitaire', 0)):.2f}")

                # Basculer le bouton en mode mise à jour
                self.btn_add_art.configure(text='💾 Mettre à jour')
                self.btn_cancel_art.configure(state='normal')
                self.lbl_art_hint.configure(text=f'✏️ Modification de l’article N° {idx + 1} ({art.get("reference_interne", "")}) — Modifiez les champs ci-dessus puis cliquez sur "💾 Mettre à jour".', text_color=COLORS['primary'])
        except Exception:
            pass

    def _cancel_article_edit(self):
        self._editing_article_idx = None
        self.btn_add_art.configure(text='➕ Ajouter')
        self.btn_cancel_art.configure(state='disabled')
        self.lbl_art_hint.configure(text='💡 Cliquez sur n’importe quel article dans le tableau pour charger et modifier ses champs.', text_color=COLORS['text_muted'])
        
        # Réinitialiser la ligne de saisie
        self.e_designation.delete(0, 'end')
        self.e_four.delete(0, 'end')
        self.e_qte.delete(0, 'end')
        self.e_qte.insert(0, '1')
        self.e_prix.delete(0, 'end')
        self.combo_unite.set('UNITE')
        
        # Désélectionner dans l'arbre
        for item in self.tree_current.selection():
            self.tree_current.selection_remove(item)

    def _add_or_update_article(self):
        ref_int = self.e_ref.get().strip()
        if not ref_int or (ref_int == 'PI-001' and not get_piece_by_reference(ref_int)):
            if not ref_int:
                messagebox.showwarning('Attention', 'Veuillez saisir ou sélectionner une référence interne.')
                return

        ref_four = self.e_four.get().strip()
        designation = self.e_designation.get().strip()
        unite = self.combo_unite.get().strip() or 'UNITE'

        try:
            qty = parse_qty(self.e_qte.get())
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning('Attention', 'Veuillez renseigner une quantité valide (> 0).')
            return

        try:
            pu = float(self.e_prix.get().strip().replace(',', '.') or 0)
            if pu < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning('Attention', 'Veuillez renseigner un prix unitaire valide.')
            return

        tot = qty * pu
        article_data = {
            'reference_interne': ref_int,
            'reference_fournisseur': ref_four,
            'designation': designation,
            'unite': unite,
            'quantite': qty,
            'prix_unitaire': pu,
            'prix_total': tot
        }

        if self._editing_article_idx is not None and 0 <= self._editing_article_idx < len(self._current_articles):
            # Mise à jour d'un article existant
            self._current_articles[self._editing_article_idx] = article_data
            self._editing_article_idx = None
            self.btn_add_art.configure(text='➕ Ajouter')
            self.btn_cancel_art.configure(state='disabled')
            self.lbl_art_hint.configure(text='✅ Article mis à jour avec succès.', text_color=COLORS['success'])
        else:
            # Ajout d'un nouvel article
            self._current_articles.append(article_data)
            self.lbl_art_hint.configure(text='💡 Cliquez sur n’importe quel article dans le tableau pour charger et modifier ses champs.', text_color=COLORS['text_muted'])

        self._refresh_current_articles_tree()

        # Vider la ligne d'article pour le suivant
        self.e_designation.delete(0, 'end')
        self.e_four.delete(0, 'end')
        self.e_qte.delete(0, 'end')
        self.e_qte.insert(0, '1')
        self.e_prix.delete(0, 'end')

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

        total_bon = 0.0
        total_qte = 0.0
        for i, art in enumerate(self._current_articles, start=1):
            tot = float(art.get('prix_total', 0) or 0)
            q = float(art.get('quantite', 0) or 0)
            total_bon += tot
            total_qte += q
            self.tree_current.insert('', 'end', values=(
                i,
                art.get('reference_interne', ''),
                art.get('reference_fournisseur', '—'),
                art.get('designation', ''),
                art.get('unite', 'UNITE'),
                format_qty(q),
                format_money(art.get('prix_unitaire', 0)),
                format_money(tot)
            ))

        self.lbl_bon_total.configure(
            text=f"Articles : {len(self._current_articles)}  •  Qté Totale : {format_qty(total_qte)}  •  Montant Total Bon : {format_money(total_bon)}"
        )

    def load_selected_bon_into_form(self):
        """Charge le bon sélectionné dans l'historique dans le formulaire pour modification."""
        if not self._selected_bon:
            messagebox.showwarning('Attention', 'Veuillez sélectionner un bon de réception dans le tableau.')
            return

        b = self._selected_bon
        num_bl = b.get('numero_bon_livraison', '')
        nom_four = b.get('nom_fournisseur', '')
        date_liv = b.get('date_livraison', '')

        articles = b.get('articles', [])
        if not articles:
            articles = get_bon_reception_details(num_bl)

        if not articles:
            messagebox.showwarning('Attention', 'Aucun article trouvé pour ce bon de réception.')
            return

        # Remplir le formulaire
        self.e_num_bl.delete(0, 'end')
        self.e_num_bl.insert(0, num_bl)

        self.e_nom_four.delete(0, 'end')
        self.e_nom_four.insert(0, nom_four if nom_four != '—' else '')

        if date_liv:
            self.e_date.delete(0, 'end')
            self.e_date.insert(0, date_liv)

        self._current_articles = []
        for art in articles:
            q = parse_qty(art.get('quantite', 0))
            pu = float(art.get('prix_unitaire', 0) or 0)
            tot = float(art.get('prix_total', 0) or (q * pu))
            self._current_articles.append({
                'reference_interne': art.get('reference_interne', ''),
                'reference_fournisseur': art.get('reference_fournisseur', ''),
                'designation': art.get('designation', ''),
                'unite': art.get('unite', 'UNITE') or 'UNITE',
                'quantite': q,
                'prix_unitaire': pu,
                'prix_total': tot
            })

        self._cancel_article_edit()
        self._refresh_current_articles_tree()
        messagebox.showinfo('Bon Chargé', f"Le Bon '{num_bl}' ({len(self._current_articles)} articles) a été chargé dans le formulaire.\nVous pouvez modifier les articles au clic, puis réenregistrer.")

    def save_bon_reception(self):
        num_bl = self.e_num_bl.get().strip()
        nom_four = self.e_nom_four.get().strip()
        date_liv = self.e_date.get().strip()

        if not num_bl:
            messagebox.showwarning('Attention', 'Veuillez saisir le numéro de bon de livraison (N° BL).')
            return

        if not self._current_articles:
            # Si aucun article dans la liste mais qu'une ligne est tapée dans les champs
            ref_int = self.e_ref.get().strip()
            if ref_int:
                self._add_or_update_article()
            if not self._current_articles:
                messagebox.showwarning('Attention', 'Veuillez ajouter au moins un article à ce bon de réception.')
                return

        # Si le bon existe déjà dans la base, on supprime l'ancienne version avant de réenregistrer
        existing_bons = [b for b in get_bons_reception_grouped() if str(b['numero_bon_livraison']) == str(num_bl)]
        if existing_bons:
            delete_bon_reception_by_num(num_bl, revert_stock=True)

        # Génération du PDF
        pdf_data = {
            'numero_bon_livraison': num_bl,
            'nom_fournisseur': nom_four,
            'date_livraison': date_liv,
            'articles': self._current_articles,
            'utilisateur': 'Benkerrou Tarek'
        }
        pdf_path = generate_bon_reception_pdf(pdf_data)

        # Enregistrement en base de données avec mise à jour automatique des stocks
        header_data = {
            'numero_bon_livraison': num_bl,
            'nom_fournisseur': nom_four,
            'date_livraison': date_liv
        }
        create_bon_reception_multi(header_data, self._current_articles, chemin_pdf=pdf_path)

        messagebox.showinfo('Succès', f'Bon de Réception {num_bl} enregistré avec succès ({len(self._current_articles)} article(s)).')

        # Vider le formulaire et actualiser
        self.reset_entire_form()
        self.refresh()

        # Ouvrir directement le visualiseur PDF avec bouton d'impression
        if pdf_path and os.path.exists(pdf_path):
            ouvrir_pdf_viewer(self, pdf_path, f"Bon de Réception {num_bl}")

    def on_history_select(self, event):
        item = self.tree_history.selection()
        if not item:
            return
        values = self.tree_history.item(item[0], 'values')
        if not values:
            return

        num_bl = values[0]
        self._selected_bon = None

        bons = get_bons_reception_grouped()
        for b in bons:
            if str(b['numero_bon_livraison']) == str(num_bl):
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
            messagebox.showwarning('Attention', 'Veuillez sélectionner un bon de réception dans le tableau.')
            return

        b = self._selected_bon
        pdf_path = b.get('chemin_pdf')

        if not pdf_path or not os.path.exists(pdf_path):
            # Régénérer le PDF
            articles = b.get('articles', [])
            if not articles:
                articles = get_bon_reception_details(b['numero_bon_livraison'])

            pdf_path = generate_bon_reception_pdf({
                'numero_bon_livraison': b['numero_bon_livraison'],
                'nom_fournisseur': b.get('nom_fournisseur', ''),
                'date_livraison': b.get('date_livraison', ''),
                'articles': articles,
                'utilisateur': 'Benkerrou Tarek'
            })
            update_bon_reception_chemin_pdf(b['numero_bon_livraison'], pdf_path)
            b['chemin_pdf'] = pdf_path

        ouvrir_pdf_viewer(self, pdf_path, f"Bon de Réception {b['numero_bon_livraison']}")

    def delete_selected_bon(self):
        if not self._selected_bon:
            messagebox.showwarning('Attention', 'Veuillez sélectionner un bon de réception à supprimer.')
            return

        b = self._selected_bon
        num_bl = b['numero_bon_livraison']
        nb_art = len(b.get('articles', []))

        msg = f"Voulez-vous vraiment supprimer le Bon de Réception '{num_bl}' ({nb_art} article(s)) ?\n\nLes quantités correspondantes seront déduites du stock."
        if messagebox.askyesno('Confirmation de suppression', msg):
            delete_bon_reception_by_num(num_bl, revert_stock=True)
            self._on_history_unselect()
            self.refresh()
            messagebox.showinfo('Supprimé', f"Le Bon de Réception '{num_bl}' a été supprimé.")

    def reset_entire_form(self):
        self.e_num_bl.delete(0, 'end')
        self.e_nom_four.delete(0, 'end')
        self.e_four.delete(0, 'end')
        self.e_designation.delete(0, 'end')
        self.combo_unite.set('UNITE')
        self.e_qte.delete(0, 'end')
        self.e_qte.insert(0, '1')
        self.e_prix.delete(0, 'end')
        self.e_date.delete(0, 'end')
        self.e_date.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self._clear_current_articles()
        self._on_history_unselect()

    def refresh(self):
        # Mettre à jour la liste des pièces dans le combobox
        piece_refs = [p['reference_interne'] for p in get_all_pieces()]
        if hasattr(self, 'e_ref') and piece_refs:
            self.e_ref.configure(values=piece_refs)

        for row in self.tree_history.get_children():
            self.tree_history.delete(row)

        start_d = self.filter_start_date.get().strip() if hasattr(self, 'filter_start_date') else ''
        end_d = self.filter_end_date.get().strip() if hasattr(self, 'filter_end_date') else ''
        query = self.filter_query.get().strip().lower() if hasattr(self, 'filter_query') else ''

        for bon in get_bons_reception_grouped():
            date_liv = bon.get('date_livraison', '') or ''

            # Filtres dates
            if start_d and date_liv < start_d:
                continue
            if end_d and date_liv > end_d:
                continue

            # Filtre texte
            if query:
                num_bl = (bon.get('numero_bon_livraison') or '').lower()
                nom_four = (bon.get('nom_fournisseur') or '').lower()
                articles_text = ' '.join([(a.get('reference_interne', '') + ' ' + a.get('designation', '') + ' ' + a.get('reference_fournisseur', '')) for a in bon.get('articles', [])]).lower()
                if query not in num_bl and query not in nom_four and query not in articles_text:
                    continue

            pdf_indicator = "📄 Disponible" if bon.get('chemin_pdf') and os.path.exists(bon.get('chemin_pdf')) else "📄 À générer"

            self.tree_history.insert('', 'end', values=(
                bon['numero_bon_livraison'],
                bon.get('nom_fournisseur', '—'),
                date_liv or '—',
                len(bon.get('articles', [])),
                format_qty(bon.get('quantite_totale', 0)),
                format_money(bon.get('montant_total', 0)),
                pdf_indicator,
            ))

