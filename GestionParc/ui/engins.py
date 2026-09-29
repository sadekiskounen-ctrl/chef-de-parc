import customtkinter as ctk
from tkinter import ttk, messagebox

from database.db_manager import (
    create_engin, delete_engin, get_all_engins, update_engin,
    get_all_bons_sortie, get_engin_by_code
)
from ui.theme import CATEGORIES_ENGINS, COLORS, FONTS, format_qty
from ui.widgets import (
    make_input, make_primary_button, make_secondary_button, make_danger_button,
    make_combobox, bind_tree_clear_selection, AutocompleteEntry, show_toast
)


class EnginDetailsDialog(ctk.CTkToplevel):
    """
    Fiche détaillée d'un engin : Spécifications + Historique des pièces consommées.
    """
    def __init__(self, parent, code_engin: str):
        super().__init__(parent)
        self.title(f"Fiche Engin — {code_engin}")
        self.geometry("780x520")
        self.minsize(700, 450)
        self.transient(parent.winfo_toplevel())
        self.configure(fg_color=COLORS['bg_card'])

        try:
            self.update_idletasks()
            pw = parent.winfo_toplevel().winfo_width()
            ph = parent.winfo_toplevel().winfo_height()
            px = parent.winfo_toplevel().winfo_x()
            py = parent.winfo_toplevel().winfo_y()
            x = max(0, px + (pw - 780) // 2)
            y = max(0, py + (ph - 520) // 2)
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

        engin = get_engin_by_code(code_engin) or {}

        # ── En-tête ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=COLORS['bg_hover'], corner_radius=12)
        header.pack(fill='x', padx=18, pady=(16, 12))

        ctk.CTkLabel(header, text=f"🚜 {engin.get('code_engin', code_engin)} — {engin.get('designation', '')}",
                     font=FONTS['title_large'], text_color=COLORS['primary']).pack(anchor='w', padx=16, pady=(12, 4))

        meta_frame = ctk.CTkFrame(header, fg_color='transparent')
        meta_frame.pack(fill='x', padx=16, pady=(0, 12))

        ctk.CTkLabel(meta_frame, text=f"Catégorie : {engin.get('categorie', '—')}", font=FONTS['body_bold'], text_color=COLORS['text_primary']).pack(side='left', padx=(0, 20))
        ctk.CTkLabel(meta_frame, text=f"Matricule : {engin.get('matricule', '—')}", font=FONTS['body_bold'], text_color=COLORS['text_primary']).pack(side='left', padx=(0, 20))
        ctk.CTkLabel(meta_frame, text="Statut : 🟢 En service", font=FONTS['body_bold'], text_color=COLORS['success']).pack(side='left')

        # ── Tableau Historique des Pièces Consommées ──────────────────────────
        ctk.CTkLabel(self, text="📦 Historique des Pièces Consommées & Entretiens :", font=FONTS['subtitle'], text_color=COLORS['text_primary']).pack(anchor='w', padx=18, pady=(4, 6))

        table_box = ctk.CTkFrame(self, fg_color='transparent')
        table_box.pack(fill='both', expand=True, padx=18, pady=(0, 14))

        tree = ttk.Treeview(
            table_box,
            columns=('date', 'or', 'ref', 'desig', 'qte', 'km', 'operateur'),
            show='headings', height=10
        )
        tree.heading('date', text='Date Sortie')
        tree.heading('or', text='N° OR')
        tree.heading('ref', text='Réf Pièce')
        tree.heading('desig', text='Désignation Pièce')
        tree.heading('qte', text='Qté')
        tree.heading('km', text='Kilométrage')
        tree.heading('operateur', text='Opérateur')

        tree.column('date', width=90, anchor='center')
        tree.column('or', width=90, anchor='center')
        tree.column('ref', width=100, anchor='center')
        tree.column('desig', width=180, anchor='w')
        tree.column('qte', width=60, anchor='center')
        tree.column('km', width=110, anchor='center')
        tree.column('operateur', width=120, anchor='center')
        tree.pack(fill='both', expand=True)

        # Charger les données des sorties pour cet engin
        bons = get_all_bons_sortie()
        total_pieces = 0
        for b in bons:
            if str(b.get('code_engin', '')).strip().lower() == str(code_engin).strip().lower():
                q = b.get('quantite', 0)
                total_pieces += float(q or 0)
                date_s = b.get('date_sortie') or (b.get('date_heure', '')[:10]) or '—'
                tree.insert('', 'end', values=(
                    date_s,
                    b.get('ordre_reparation') or '—',
                    b.get('reference_interne', '—'),
                    b.get('piece_designation', '—'),
                    format_qty(q, b.get('unite', '')),
                    b.get('kilometrage') or '—',
                    b.get('nom_operateur') or b.get('username') or 'Benkerrou Tarek'
                ))

        btn_box = ctk.CTkFrame(self, fg_color='transparent')
        btn_box.pack(fill='x', padx=18, pady=(0, 14))

        ctk.CTkLabel(btn_box, text=f"Total pièces consommées : {format_qty(total_pieces)} article(s)",
                     font=FONTS['body_bold'], text_color=COLORS['primary']).pack(side='left')

        make_secondary_button(btn_box, "Fermer", self.destroy, width=110, height=34).pack(side='right')


class EnginsFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color='transparent')
        self.grid_columnconfigure(0, weight=1)
        self.form_fields = []
        self._selected_engin_id = None
        self.build()

    def build(self):
        self.header = ctk.CTkFrame(self, fg_color='transparent')
        self.header.grid(row=0, column=0, sticky='ew', padx=18, pady=(18, 8))
        ctk.CTkLabel(self.header, text='Engins', font=FONTS['title_large'], text_color=COLORS['text_primary']).pack(anchor='w')
        ctk.CTkLabel(self.header, text='Gestion du parc et historique des pièces consommées par engin', font=FONTS['body'], text_color=COLORS['text_secondary']).pack(anchor='w')

        form = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=16, border_width=1, border_color=COLORS['border'])
        form.grid(row=1, column=0, sticky='ew', padx=18, pady=(0, 12))

        all_engins = get_all_engins()
        codes = [e['code_engin'] for e in all_engins if e.get('code_engin')]
        desigs = list(set([e['designation'] for e in all_engins if e.get('designation')]))

        # ── Champs ─────────────────────────────────────────────────────────
        ctk.CTkLabel(form, text='🔍 Code engin', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=0, padx=12, pady=(12, 4), sticky='w')
        self.e_code = AutocompleteEntry(form, placeholder='CL-001', width=180, completion_list=codes)
        self.e_code.grid(row=1, column=0, padx=12, pady=(0, 10), sticky='w')
        self.form_fields.append(self.e_code)

        ctk.CTkLabel(form, text='Catégorie', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=1, padx=12, pady=(12, 4), sticky='w')
        self.combo_cat = make_combobox(form, CATEGORIES_ENGINS, width=180)
        self.combo_cat.grid(row=1, column=1, padx=12, pady=(0, 10), sticky='w')
        self.form_fields.append(self.combo_cat)

        ctk.CTkLabel(form, text='Désignation / Marque', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=2, padx=12, pady=(12, 4), sticky='w')
        self.e_designation = AutocompleteEntry(form, placeholder='Désignation...', width=220, completion_list=desigs)
        self.e_designation.grid(row=1, column=2, padx=12, pady=(0, 10), sticky='w')
        self.form_fields.append(self.e_designation)

        ctk.CTkLabel(form, text='Matricule', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=3, padx=12, pady=(12, 4), sticky='w')
        self.e_matricule = make_input(form, 'AB-123-CD', 180)
        self.e_matricule.grid(row=1, column=3, padx=12, pady=(0, 10), sticky='w')
        self.form_fields.append(self.e_matricule)

        # ── Boutons ─────────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(form, fg_color='transparent')
        btn_row.grid(row=2, column=0, columnspan=4, padx=12, pady=(4, 12), sticky='w')

        self.btn_add = make_primary_button(btn_row, '✅ Ajouter', self.add_engin, width=120)
        self.btn_add.pack(side='left', padx=(0, 6))

        self.btn_modif = make_secondary_button(btn_row, '✏️ Modifier', self.update_selected_engin, width=120)
        self.btn_modif.pack(side='left', padx=(0, 6))
        self.btn_modif.configure(state='disabled')

        self.btn_details = make_primary_button(btn_row, '📋 Fiche & Historique', self.view_selected_engin_details, width=170)
        self.btn_details.pack(side='left', padx=(0, 6))
        self.btn_details.configure(state='disabled')

        btn_del = make_danger_button(btn_row, '🗑️ Supprimer', self.delete_selected_engin, width=120)
        btn_del.pack(side='left', padx=(0, 6))

        btn_clear = make_secondary_button(btn_row, 'Vider', self.clear_fields, width=100)
        btn_clear.pack(side='left', padx=(0, 6))

        self.btn_refresh = make_secondary_button(btn_row, 'Actualiser', self.refresh, width=110)
        self.btn_refresh.pack(side='left')

        # ── Tableau ─────────────────────────────────────────────────────────
        table_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=16, border_width=1, border_color=COLORS['border'])
        table_frame.grid(row=2, column=0, sticky='nsew', padx=18, pady=(0, 18))
        self.grid_rowconfigure(2, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(table_frame, columns=('code', 'categorie', 'designation', 'matricule', 'statut'), show='headings', height=15)
        self.tree.heading('code', text='Code')
        self.tree.heading('categorie', text='Catégorie')
        self.tree.heading('designation', text='Désignation')
        self.tree.heading('matricule', text='Matricule')
        self.tree.heading('statut', text='Statut Opérationnel')

        self.tree.column('code', width=120, anchor='center', stretch=True)
        self.tree.column('categorie', width=150, anchor='center', stretch=True)
        self.tree.column('designation', width=260, stretch=True)
        self.tree.column('matricule', width=150, anchor='center', stretch=True)
        self.tree.column('statut', width=150, anchor='center', stretch=True)
        self.tree.pack(fill='both', expand=True, padx=10, pady=10)

        self.tree.bind('<ButtonRelease-1>', self.on_row_select)
        self.tree.bind('<Double-1>', lambda e: self.view_selected_engin_details())
        bind_tree_clear_selection(self.tree, clear_callback=self.clear_fields)
        self.refresh()

    def clear_fields(self):
        self.e_code.set('')
        self.e_designation.set('')
        self.e_matricule.delete(0, 'end')
        self._selected_engin_id = None
        self.btn_modif.configure(state='disabled')
        self.btn_details.configure(state='disabled')
        self.btn_add.configure(state='normal')

    def add_engin(self):
        code = self.e_code.get().strip()
        cat = self.combo_cat.get().strip()
        designation = self.e_designation.get().strip()
        matricule = self.e_matricule.get().strip()
        if not all([code, cat, designation, matricule]):
            show_toast(self, 'Tous les champs sont obligatoires.', 'warning')
            return
        create_engin(code, cat, designation, matricule)
        show_toast(self, f"Engin '{code}' ajouté avec succès.", 'success')
        self.refresh()
        self.clear_fields()

    def update_selected_engin(self):
        if not self._selected_engin_id:
            show_toast(self, 'Sélectionnez un engin à modifier.', 'warning')
            return
        code = self.e_code.get().strip()
        cat = self.combo_cat.get().strip()
        designation = self.e_designation.get().strip()
        matricule = self.e_matricule.get().strip()
        if not all([code, cat, designation]):
            show_toast(self, 'Code, catégorie et désignation sont obligatoires.', 'warning')
            return
        if messagebox.askyesno('Confirmation', f'Modifier l\'engin sélectionné (ID {self._selected_engin_id}) ?'):
            update_engin(self._selected_engin_id,
                         code_engin=code, categorie=cat,
                         designation=designation, matricule=matricule)
            show_toast(self, f"Engin '{code}' mis à jour.", 'success')
            self.clear_fields()
            self.refresh()

    def view_selected_engin_details(self):
        code = self.e_code.get().strip()
        if not code:
            selected_item = self.tree.selection()
            if selected_item:
                values = self.tree.item(selected_item[0], 'values')
                if values:
                    code = values[0]
        if not code:
            show_toast(self, 'Sélectionnez un engin pour voir sa fiche.', 'warning')
            return
        EnginDetailsDialog(self, code)

    def delete_selected_engin(self):
        code = self.e_code.get().strip()
        selected_item = self.tree.selection()
        if not code and selected_item:
            values = self.tree.item(selected_item[0], 'values')
            if values:
                code = values[0]
        if not code:
            show_toast(self, 'Veuillez sélectionner un engin à supprimer.', 'warning')
            return

        if messagebox.askyesno('Confirmation', f'Voulez-vous vraiment supprimer l\'engin code "{code}" ?'):
            if self.remove_by_code(code):
                show_toast(self, f"Engin '{code}' supprimé.", 'info')
                self.clear_fields()
                self.refresh()
            else:
                show_toast(self, f'Impossible de trouver l\'engin code "{code}".', 'danger')

    def on_row_select(self, event):
        item = self.tree.selection()
        if not item:
            return
        values = self.tree.item(item[0], 'values')
        if not values:
            return
        self.clear_fields()
        for engin in get_all_engins():
            if engin['code_engin'] == values[0]:
                self._selected_engin_id = engin['id']
                break
        self.e_code.set(values[0])
        self.combo_cat.set(values[1])
        self.e_designation.set(values[2])
        self.e_matricule.delete(0, 'end')
        self.e_matricule.insert(0, values[3])
        self.btn_modif.configure(state='normal')
        self.btn_details.configure(state='normal')
        self.btn_add.configure(state='disabled')

    def refresh(self):
        all_engins = get_all_engins()
        codes = [e['code_engin'] for e in all_engins if e.get('code_engin')]
        desigs = list(set([e['designation'] for e in all_engins if e.get('designation')]))

        if hasattr(self, 'e_code') and hasattr(self.e_code, 'set_completion_list'):
            self.e_code.set_completion_list(codes)
        if hasattr(self, 'e_designation') and hasattr(self.e_designation, 'set_completion_list'):
            self.e_designation.set_completion_list(desigs)

        for row in self.tree.get_children():
            self.tree.delete(row)
        for engin in all_engins:
            self.tree.insert('', 'end', values=(
                engin['code_engin'],
                engin['categorie'],
                engin['designation'],
                engin['matricule'],
                "🟢 En service"
            ))

    @staticmethod
    def remove_by_code(code):
        engins = get_all_engins()
        for engin in engins:
            if engin['code_engin'] == code:
                delete_engin(engin['id'])
                return True
        return False

