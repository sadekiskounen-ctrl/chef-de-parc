import customtkinter as ctk
from datetime import datetime

from database.db_manager import get_dashboard_stats
from ui.theme import COLORS, FONTS, format_money
from ui.widgets import make_stat_card, CircularProgressWidget, make_primary_button, make_secondary_button


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color='transparent')
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.build()

    def build(self):
        # ── Header ────────────────────────────────────────────────────────────
        self.header = ctk.CTkFrame(self, fg_color='transparent')
        self.header.grid(row=0, column=0, sticky='ew', padx=18, pady=(18, 8))

        header_left = ctk.CTkFrame(self.header, fg_color='transparent')
        header_left.pack(side='left', anchor='w')
        ctk.CTkLabel(
            header_left, text='SARL NOMADE Ayris — Tableau de bord',
            font=FONTS['title_large'], text_color=COLORS['text_primary']
        ).pack(anchor='w')
        ctk.CTkLabel(
            header_left, text='Vue d’ensemble opérationnelle & santé globale du parc',
            font=FONTS['body'], text_color=COLORS['text_secondary']
        ).pack(anchor='w')

        header_right = ctk.CTkFrame(self.header, fg_color='transparent')
        header_right.pack(side='right', anchor='e')
        now = datetime.now()
        MOIS_FR = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
        today_str = f"{now.day} {MOIS_FR[now.month]} {now.year}"
        ctk.CTkLabel(
            header_right, text=f'🗓️ {today_str}',
            font=FONTS['body_bold'], text_color=COLORS['text_secondary']
        ).pack(side='left', padx=(0, 10))

        make_secondary_button(header_right, '🔄 Actualiser', self.refresh, width=120, height=36).pack(side='left')

        # ── Grille KPI ────────────────────────────────────────────────────────
        self.kpi_grid = ctk.CTkFrame(self, fg_color='transparent')
        self.kpi_grid.grid(row=1, column=0, sticky='ew', padx=18, pady=(0, 12))

        # ── Zone centrale (Cercle relatif & Panneaux d'analyse) ───────────────
        self.main_panel = ctk.CTkFrame(self, fg_color='transparent')
        self.main_panel.grid(row=2, column=0, sticky='nsew', padx=18, pady=(0, 18))
        self.main_panel.grid_columnconfigure(0, weight=1)
        self.main_panel.grid_columnconfigure(1, weight=1)
        self.main_panel.grid_rowconfigure(0, weight=1)

        self.refresh()

    def _go_to_stock_critique(self, event=None):
        try:
            top = self.winfo_toplevel()
            if hasattr(top, 'navigate_to'):
                top.navigate_to('pieces')
                pieces_frame = top._frames.get('pieces')
                if pieces_frame and hasattr(pieces_frame, 'filter_stock_critique'):
                    pieces_frame.filter_stock_critique()
        except Exception:
            pass

    def refresh(self):
        # 1. Mise à jour des cartes KPI
        for child in self.kpi_grid.winfo_children():
            child.destroy()
        for child in self.main_panel.winfo_children():
            child.destroy()

        stats = get_dashboard_stats()

        # 4 Cartes KPI
        cards = [
            make_stat_card(self.kpi_grid, 'Engins au parc', str(stats['total_engins']), '🚜', '#004899', '#EAF2FF'),
            make_stat_card(self.kpi_grid, 'Pièces en stock', str(stats['total_pieces']), '🔧', '#059669', '#D1FAE5'),
            make_stat_card(self.kpi_grid, 'Valeur globale', format_money(stats['total_valeur_stock']), '💰', '#D97706', '#FEF3C7'),
            make_stat_card(self.kpi_grid, 'Mouvements ce mois', f"{stats['sorties_mois']} Sorties / {stats['livraisons_mois']} Entrées", '📊', '#0EA5E9', '#E0F2FE'),
        ]
        for i, card in enumerate(cards):
            card.grid(row=0, column=i, sticky='nsew', padx=6, pady=4)
            self.kpi_grid.grid_columnconfigure(i, weight=1)

        # 2. Carte Gauche : Cercle Relatif Dynamique (Donut Chart)
        left_card = ctk.CTkFrame(
            self.main_panel, fg_color=COLORS['bg_card'],
            corner_radius=16, border_width=1, border_color=COLORS['border']
        )
        left_card.grid(row=0, column=0, sticky='nsew', padx=(0, 8), pady=0)

        ctk.CTkLabel(
            left_card, text='📊 Répartition & Cercle Relatif du Parc',
            font=FONTS['subtitle'], text_color=COLORS['text_primary']
        ).pack(anchor='w', padx=18, pady=(16, 4))

        ctk.CTkLabel(
            left_card, text='Répartition relative des engins & état de santé du stock',
            font=FONTS['small'], text_color=COLORS['text_muted']
        ).pack(anchor='w', padx=18, pady=(0, 12))

        # Intégration du Widget Donut
        c_camion = stats.get('cat_camion', 0)
        c_clarck = stats.get('cat_clarck', 0)
        c_leger = stats.get('cat_leger', 0)
        c_autres = stats.get('cat_autres', 0)

        segments = [
            (c_camion or 1, '#0096D6', 'Camions'),
            (c_clarck or 1, '#0B2E6B', 'Clarcks'),
            (c_leger or 1, '#059669', 'Légers'),
            (c_autres or 0.1, '#D97706', 'Autres'),
        ]

        donut_container = ctk.CTkFrame(left_card, fg_color='transparent')
        donut_container.pack(expand=True, fill='both', padx=18, pady=4)

        donut = CircularProgressWidget(donut_container, size=210, bg_color='#FFFFFF')
        donut.pack(side='left', padx=(10, 20), pady=10)
        health_pct = f"{stats.get('stock_health', 100)}%"
        donut.set_data(segments, health_pct, "Santé Stock")

        # Légende du Cercle Relatif
        legend_frame = ctk.CTkFrame(donut_container, fg_color='transparent')
        legend_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

        leg_items = [
            ('🚛 Camions', f"{c_camion} engins", '#0096D6'),
            ('🏗️ Clarcks', f"{c_clarck} engins", '#0B2E6B'),
            ('🚗 Véhicules Légers', f"{c_leger} engins", '#059669'),
            ('📦 Stock Critique (<5)', f"{stats.get('stock_faible', 0)} pièces", '#DC2626'),
        ]

        for title, subtitle, color in leg_items:
            row = ctk.CTkFrame(legend_frame, fg_color=COLORS['bg_hover'], corner_radius=10)
            row.pack(fill='x', pady=4)

            if 'Critique' in title:
                row.configure(cursor='hand2')
                row.bind('<Button-1>', self._go_to_stock_critique)

            badge = ctk.CTkFrame(row, fg_color=color, corner_radius=6, width=12, height=12)
            badge.pack(side='left', padx=10, pady=10)

            t_frame = ctk.CTkFrame(row, fg_color='transparent')
            t_frame.pack(side='left', fill='x', expand=True)
            lbl1 = ctk.CTkLabel(t_frame, text=title, font=FONTS['body_bold'], text_color=COLORS['text_primary'])
            lbl1.pack(anchor='w')
            lbl2 = ctk.CTkLabel(t_frame, text=subtitle, font=FONTS['small'], text_color=COLORS['text_secondary'])
            lbl2.pack(anchor='w')

            if 'Critique' in title:
                lbl1.bind('<Button-1>', self._go_to_stock_critique)
                lbl2.bind('<Button-1>', self._go_to_stock_critique)

        # 3. Carte Droite : Statistiques Opérationnelles & Accès Rapides
        right_card = ctk.CTkFrame(
            self.main_panel, fg_color=COLORS['bg_card'],
            corner_radius=16, border_width=1, border_color=COLORS['border']
        )
        right_card.grid(row=0, column=1, sticky='nsew', padx=(8, 0), pady=0)

        ctk.CTkLabel(
            right_card, text='⚡ Indicateurs Rapides & Alertes Stock',
            font=FONTS['subtitle'], text_color=COLORS['text_primary']
        ).pack(anchor='w', padx=18, pady=(16, 4))

        ctk.CTkLabel(
            right_card, text='Statut du stock et accès rapide aux modules',
            font=FONTS['small'], text_color=COLORS['text_muted']
        ).pack(anchor='w', padx=18, pady=(0, 16))

        # Alertes & métriques (Cliquables pour amener directement à l'alerte en ROUGE VIF)
        has_alert = stats['stock_faible'] > 0
        alert_box = ctk.CTkFrame(
            right_card,
            fg_color='#DC2626' if has_alert else '#F0FDF4',
            corner_radius=12, border_width=2,
            border_color='#991B1B' if has_alert else '#86EFAC',
            cursor='hand2'
        )
        alert_box.pack(fill='x', padx=18, pady=(0, 16))
        alert_box.bind('<Button-1>', self._go_to_stock_critique)

        alert_inner = ctk.CTkFrame(alert_box, fg_color='transparent')
        alert_inner.pack(fill='x', padx=14, pady=12)

        alert_text = f"🚨 ALERTE STOCK : {stats['stock_faible']} référence(s) en quantité critique (< 5) !" if has_alert else "✅ Stock optimal : Aucune pièce en seuil critique."
        lbl_alert = ctk.CTkLabel(
            alert_inner, text=alert_text,
            font=('Segoe UI', 13, 'bold'),
            text_color='white' if has_alert else '#166534'
        )
        lbl_alert.pack(side='left', anchor='w')
        lbl_alert.bind('<Button-1>', self._go_to_stock_critique)

        btn_go = ctk.CTkButton(
            alert_inner, text="🔍 Voir l'alerte",
            command=self._go_to_stock_critique,
            fg_color='white' if has_alert else '#16A34A',
            hover_color='#F1F5F9' if has_alert else '#15803D',
            text_color='#DC2626' if has_alert else 'white',
            font=FONTS['body_bold'],
            height=34, width=120, corner_radius=8
        )
        btn_go.pack(side='right', padx=(10, 0))

        metrics_grid = ctk.CTkFrame(right_card, fg_color='transparent')
        metrics_grid.pack(fill='x', padx=18, pady=(0, 16))

        m_items = [
            ("Sorties de stock ce mois", f"{stats['sorties_mois']} Bons BS"),
            ("Livraisons reçues ce mois", f"{stats['livraisons_mois']} Bons BL"),
            ("Taux d'engins actifs", "100% Fonctionnel"),
        ]
        for label, val in m_items:
            row = ctk.CTkFrame(metrics_grid, fg_color=COLORS['bg_hover'], corner_radius=8)
            row.pack(fill='x', pady=3)
            ctk.CTkLabel(row, text=label, font=FONTS['body'], text_color=COLORS['text_secondary']).pack(side='left', padx=12, pady=8)
            ctk.CTkLabel(row, text=val, font=FONTS['body_bold'], text_color=COLORS['primary_dark']).pack(side='right', padx=12, pady=8)

