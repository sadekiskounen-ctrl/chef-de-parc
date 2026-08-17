import customtkinter as ctk
from tkinter import ttk, messagebox

from database.db_manager import (
    historique_prix_par_reference, get_piece_by_reference, get_all_pieces
)
from ui.theme import COLORS, FONTS, format_money
from ui.widgets import make_input, make_primary_button, make_secondary_button, make_combobox, bind_tree_clear_selection


class PrixFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color='transparent')
        self.grid_columnconfigure(0, weight=1)
        self.build()

    def build(self):
        # ── Header ────────────────────────────────────────────────────────────
        self.header = ctk.CTkFrame(self, fg_color='transparent')
        self.header.grid(row=0, column=0, sticky='ew', padx=18, pady=(18, 8))
        ctk.CTkLabel(self.header, text='Comparateur & Marge de prix', font=FONTS['title_large'],
                     text_color=COLORS['text_primary']).pack(anchor='w')
        ctk.CTkLabel(self.header, text='Analyse de l\'ancien prix, du nouveau prix et de la marge de variation',
                     font=FONTS['body'], text_color=COLORS['text_secondary']).pack(anchor='w')

        # ── Barre de recherche ────────────────────────────────────────────────
        search = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=16,
                              border_width=1, border_color=COLORS['border'])
        search.grid(row=1, column=0, sticky='ew', padx=18, pady=(0, 12))

        ctk.CTkLabel(search, text='🔍 Référence interne :', font=FONTS['body_bold'],
                     text_color=COLORS['text_primary']).grid(row=0, column=0, padx=12, pady=12, sticky='w')
        piece_refs = [p['reference_interne'] for p in get_all_pieces()]
        self.e_ref = make_combobox(search, piece_refs if piece_refs else ['Aucune pièce'], width=220)
        if piece_refs:
            self.e_ref.set(piece_refs[0])
        self.e_ref.configure(command=lambda choice: self.analyse_prix())
        self.e_ref.grid(row=0, column=1, padx=8, pady=12, sticky='w')

        make_primary_button(search, '🔍 Analyser', self.analyse_prix, width=130).grid(row=0, column=2, padx=8, pady=12, sticky='w')
        make_secondary_button(search, '📋 Tout afficher', self.show_all_pieces, width=160).grid(row=0, column=3, padx=8, pady=12, sticky='w')

        # ── Cartes Synthèse (Ancien Prix | Nouveau Prix | Marge) ─────────────
        cards_frame = ctk.CTkFrame(self, fg_color='transparent')
        cards_frame.grid(row=2, column=0, sticky='ew', padx=18, pady=(0, 12))
        cards_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Card 1 : Ancien Prix
        self.card_ancien = ctk.CTkFrame(cards_frame, fg_color=COLORS['bg_card'], corner_radius=14, border_width=1, border_color=COLORS['border'])
        self.card_ancien.grid(row=0, column=0, padx=(0, 6), sticky='ew')
        ctk.CTkLabel(self.card_ancien, text='🏷️ Ancien Prix', font=FONTS['small_bold'], text_color=COLORS['text_secondary']).pack(anchor='w', padx=14, pady=(10, 2))
        self.lbl_val_ancien = ctk.CTkLabel(self.card_ancien, text='— DZD', font=('Segoe UI', 20, 'bold'), text_color=COLORS['text_primary'])
        self.lbl_val_ancien.pack(anchor='w', padx=14, pady=(0, 10))

        # Card 2 : Nouveau Prix
        self.card_nouveau = ctk.CTkFrame(cards_frame, fg_color=COLORS['bg_card'], corner_radius=14, border_width=1, border_color=COLORS['border'])
        self.card_nouveau.grid(row=0, column=1, padx=6, sticky='ew')
        ctk.CTkLabel(self.card_nouveau, text='💰 Nouveau Prix', font=FONTS['small_bold'], text_color=COLORS['text_secondary']).pack(anchor='w', padx=14, pady=(10, 2))
        self.lbl_val_nouveau = ctk.CTkLabel(self.card_nouveau, text='— DZD', font=('Segoe UI', 20, 'bold'), text_color=COLORS['primary'])
        self.lbl_val_nouveau.pack(anchor='w', padx=14, pady=(0, 10))

        # Card 3 : Marge / Écart
        self.card_marge = ctk.CTkFrame(cards_frame, fg_color=COLORS['bg_card'], corner_radius=14, border_width=1, border_color=COLORS['border'])
        self.card_marge.grid(row=0, column=2, padx=(6, 0), sticky='ew')
        ctk.CTkLabel(self.card_marge, text='📊 Marge & Variation', font=FONTS['small_bold'], text_color=COLORS['text_secondary']).pack(anchor='w', padx=14, pady=(10, 2))
        self.lbl_val_marge = ctk.CTkLabel(self.card_marge, text='—', font=('Segoe UI', 20, 'bold'), text_color=COLORS['text_muted'])
        self.lbl_val_marge.pack(anchor='w', padx=14, pady=(0, 10))

        # ── Tableau comparatif complet ────────────────────────────────────────
        table_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=16, border_width=1, border_color=COLORS['border'])
        table_frame.grid(row=3, column=0, sticky='nsew', padx=18, pady=(0, 18))
        self.grid_rowconfigure(3, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            table_frame,
            columns=('ref', 'fournisseur', 'designation', 'ancien', 'nouveau', 'marge_dzd', 'marge_pct', 'statut'),
            show='headings', height=12
        )
        self.tree.heading('ref', text='Réf Interne')
        self.tree.heading('fournisseur', text='Réf Fournisseur')
        self.tree.heading('designation', text='Désignation')
        self.tree.heading('ancien', text='Ancien Prix')
        self.tree.heading('nouveau', text='Nouveau Prix')
        self.tree.heading('marge_dzd', text='Marge (DZD)')
        self.tree.heading('marge_pct', text='Marge (%)')
        self.tree.heading('statut', text='Statut')

        self.tree.column('ref', width=110, anchor='center')
        self.tree.column('fournisseur', width=110, anchor='center')
        self.tree.column('designation', width=200, anchor='w')
        self.tree.column('ancien', width=120, anchor='center')
        self.tree.column('nouveau', width=120, anchor='center')
        self.tree.column('marge_dzd', width=120, anchor='center')
        self.tree.column('marge_pct', width=100, anchor='center')
        self.tree.column('statut', width=130, anchor='center')

        self.tree.pack(fill='both', expand=True, padx=10, pady=10)
        self.tree.bind('<ButtonRelease-1>', self.on_row_select)

        # Tags de couleur
        self.tree.tag_configure('danger', background='#FEE2E2', foreground='#991B1B')
        self.tree.tag_configure('hausse', background='#FEF3C7', foreground='#92400E')
        self.tree.tag_configure('baisse', background='#D1FAE5', foreground='#065F46')
        self.tree.tag_configure('stable', background='#F1F5F9', foreground='#475569')

        self.tree.bind('<ButtonRelease-1>', self.on_row_select)
        bind_tree_clear_selection(self.tree)
        self.show_all_pieces()

    def on_row_select(self, event):
        item = self.tree.selection()
        if not item:
            return
        values = self.tree.item(item[0], 'values')
        if not values:
            return
        ref = values[0]
        self.e_ref.set(ref)
        self.analyse_prix()

    def analyse_prix(self):
        ref = self.e_ref.get().strip()
        if not ref:
            messagebox.showwarning('Attention', 'Veuillez saisir une référence interne.')
            return

        piece = get_piece_by_reference(ref)
        if not piece:
            messagebox.showerror('Erreur', f'Aucune pièce trouvée pour la référence "{ref}".')
            return

        ancien = float(piece.get('ancien_prix_unitaire', 0) or 0)
        nouveau = float(piece.get('nouveau_prix_unitaire', 0) or 0)
        diff = nouveau - ancien
        pct = (diff / ancien * 100) if ancien > 0 else 0.0

        # Mettre à jour les 3 cartes synthétiques
        self.lbl_val_ancien.configure(text=format_money(ancien))
        self.lbl_val_nouveau.configure(text=format_money(nouveau))

        if diff > 0:
            self.lbl_val_marge.configure(text=f"+{diff:,.2f} DZD (+{pct:.1f}%)", text_color='#DC2626')
        elif diff < 0:
            self.lbl_val_marge.configure(text=f"{diff:,.2f} DZD ({pct:.1f}%)", text_color='#059669')
        else:
            self.lbl_val_marge.configure(text="0.00 DZD (0.0%)", text_color=COLORS['text_secondary'])

        # Filtrer le tableau sur cette pièce
        self._clear_tree()
        self._insert_piece_row(piece)

    def refresh(self):
        self.show_all_pieces()

    def show_all_pieces(self):
        """Affiche l'ensemble des pièces avec Ancien Prix, Nouveau Prix et Marge."""
        pieces = get_all_pieces()
        piece_refs = [p['reference_interne'] for p in pieces]
        if hasattr(self, 'e_ref') and piece_refs:
            self.e_ref.configure(values=piece_refs)

        self._clear_tree()
        if not pieces:
            return

        for p in pieces:
            self._insert_piece_row(p)

    def _insert_piece_row(self, p: dict):
        ancien = float(p.get('ancien_prix_unitaire', 0) or 0)
        nouveau = float(p.get('nouveau_prix_unitaire', 0) or 0)
        diff = nouveau - ancien
        pct = (diff / ancien * 100) if ancien > 0 else 0.0

        if diff > 0:
            tag = 'danger' if pct > 15 else 'hausse'
            statut = f"⚠️ Hausse +{pct:.1f}%" if pct > 15 else f"📈 +{pct:.1f}%"
        elif diff < 0:
            tag = 'baisse'
            statut = f"📉 Baisse {pct:.1f}%"
        else:
            tag = 'stable'
            statut = "＝ Identique"

        marge_dzd_str = f"{'+' if diff > 0 else ''}{diff:,.2f} DZD"
        marge_pct_str = f"{'+' if diff > 0 else ''}{pct:.1f} %"

        self.tree.insert('', 'end', values=(
            p.get('reference_interne', ''),
            p.get('reference_fournisseur', '—'),
            p.get('designation', ''),
            format_money(ancien),
            format_money(nouveau),
            marge_dzd_str,
            marge_pct_str,
            statut
        ), tags=(tag,))

    def _clear_tree(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
