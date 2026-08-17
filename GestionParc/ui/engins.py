import customtkinter as ctk
from tkinter import ttk, messagebox

from database.db_manager import create_engin, delete_engin, get_all_engins, update_engin
from ui.theme import CATEGORIES_ENGINS, COLORS, FONTS
from ui.widgets import make_input, make_primary_button, make_secondary_button, make_danger_button, make_combobox, bind_tree_clear_selection


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
        ctk.CTkLabel(self.header, text='Gestion du parc et des engins', font=FONTS['body'], text_color=COLORS['text_secondary']).pack(anchor='w')

        form = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=16, border_width=1, border_color=COLORS['border'])
        form.grid(row=1, column=0, sticky='ew', padx=18, pady=(0, 12))

        # ── Champs ─────────────────────────────────────────────────────────
        ctk.CTkLabel(form, text='Code engin', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=0, padx=12, pady=(12, 4), sticky='w')
        self.e_code = make_input(form, 'CL-001', 180)
        self.e_code.grid(row=1, column=0, padx=12, pady=(0, 10), sticky='w')
        self.form_fields.append(self.e_code)

        ctk.CTkLabel(form, text='Catégorie', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=1, padx=12, pady=(12, 4), sticky='w')
        self.combo_cat = make_combobox(form, CATEGORIES_ENGINS, width=180)
        self.combo_cat.grid(row=1, column=1, padx=12, pady=(0, 10), sticky='w')
        self.form_fields.append(self.combo_cat)

        ctk.CTkLabel(form, text='Désignation', font=FONTS['body_bold'], text_color=COLORS['text_primary']).grid(row=0, column=2, padx=12, pady=(12, 4), sticky='w')
        self.e_designation = make_input(form, 'Désignation...', 220)
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

        self.tree = ttk.Treeview(table_frame, columns=('code', 'categorie', 'designation', 'matricule'), show='headings', height=15)
        self.tree.heading('code', text='Code')
        self.tree.heading('categorie', text='Catégorie')
        self.tree.heading('designation', text='Désignation')
        self.tree.heading('matricule', text='Matricule')
        self.tree.column('code', width=120, anchor='center', stretch=True)
        self.tree.column('categorie', width=150, anchor='center', stretch=True)
        self.tree.column('designation', width=300, stretch=True)
        self.tree.column('matricule', width=160, anchor='center', stretch=True)
        self.tree.pack(fill='both', expand=True, padx=10, pady=10)

        self.tree.bind('<ButtonRelease-1>', self.on_row_select)
        bind_tree_clear_selection(self.tree, clear_callback=self.clear_fields)
        self.refresh()

    def clear_fields(self):
        self.e_code.delete(0, 'end')
        self.e_designation.delete(0, 'end')
        self.e_matricule.delete(0, 'end')
        self._selected_engin_id = None
        self.btn_modif.configure(state='disabled')
        self.btn_add.configure(state='normal')

    def add_engin(self):
        code = self.e_code.get().strip()
        cat = self.combo_cat.get().strip()
        designation = self.e_designation.get().strip()
        matricule = self.e_matricule.get().strip()
        if not all([code, cat, designation, matricule]):
            messagebox.showwarning('Attention', 'Tous les champs sont obligatoires.')
            return
        create_engin(code, cat, designation, matricule)
        self.refresh()
        self.clear_fields()

    def update_selected_engin(self):
        if not self._selected_engin_id:
            messagebox.showwarning('Attention', 'Sélectionnez un engin à modifier.')
            return
        code = self.e_code.get().strip()
        cat = self.combo_cat.get().strip()
        designation = self.e_designation.get().strip()
        matricule = self.e_matricule.get().strip()
        if not all([code, cat, designation]):
            messagebox.showwarning('Attention', 'Code, catégorie et désignation sont obligatoires.')
            return
        if messagebox.askyesno('Confirmation', f'Modifier l\'engin sélectionné (ID {self._selected_engin_id}) ?'):
            update_engin(self._selected_engin_id,
                         code_engin=code, categorie=cat,
                         designation=designation, matricule=matricule)
            self.clear_fields()
            self.refresh()

    def delete_selected_engin(self):
        code = self.e_code.get().strip()
        selected_item = self.tree.selection()
        if not code and selected_item:
            values = self.tree.item(selected_item[0], 'values')
            if values:
                code = values[0]
        if not code:
            messagebox.showwarning('Attention', 'Veuillez sélectionner un engin à supprimer.')
            return

        if messagebox.askyesno('Confirmation', f'Voulez-vous vraiment supprimer l\'engin code "{code}" ?'):
            if self.remove_by_code(code):
                self.clear_fields()
                self.refresh()
            else:
                messagebox.showerror('Erreur', f'Impossible de trouver l\'engin code "{code}".')

    def on_row_select(self, event):
        item = self.tree.selection()
        if not item:
            return
        values = self.tree.item(item[0], 'values')
        if not values:
            return
        self.clear_fields()
        # Trouver l'ID depuis la base
        for engin in get_all_engins():
            if engin['code_engin'] == values[0]:
                self._selected_engin_id = engin['id']
                break
        self.e_code.insert(0, values[0])
        self.combo_cat.set(values[1])
        self.e_designation.insert(0, values[2])
        self.e_matricule.insert(0, values[3])
        self.btn_modif.configure(state='normal')
        self.btn_add.configure(state='disabled')

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for engin in get_all_engins():
            self.tree.insert('', 'end', values=(engin['code_engin'], engin['categorie'], engin['designation'], engin['matricule']))

    @staticmethod
    def remove_by_code(code):
        engins = get_all_engins()
        for engin in engins:
            if engin['code_engin'] == code:
                delete_engin(engin['id'])
                return True
        return False
