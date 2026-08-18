"""
SARL AYRIS - Gestionnaire de Parc
Module: ui/options.py
Configuration générale complète : PDF, Excel, Imprimante, BDD, Société, Alertes, À propos.
Même structure et niveau de finition que l'application Magasinier.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import os
import subprocess
from pathlib import Path
from ui.theme import COLORS, FONTS
from ui.widgets import (make_primary_button, make_secondary_button,
                         make_input, make_danger_button)
from services.config_manager import load_config, save_config, get_config
import database.db_manager as db
from datetime import datetime


class OptionsFrame(ctk.CTkFrame):
    """Écran de configuration complète — même style que l'app Magasinier."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS['bg_dark'], **kwargs)
        self._config = load_config()
        try:
            self._build_ui()
        except Exception as e:
            ctk.CTkLabel(
                self, text=f"Erreur lors du chargement de la configuration :\n{e}",
                font=FONTS['body'], text_color=COLORS['danger']
            ).pack(expand=True)

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color='transparent')
        header.pack(fill='x', padx=24, pady=(20, 10))

        ctk.CTkLabel(
            header, text='⚙️  Configuration',
            font=FONTS['title_large'],
            text_color=COLORS['text_primary']
        ).pack(side='left')

        ctk.CTkLabel(
            header,
            text='  — Réglages société, chemins d\'export, alertes et base de données',
            font=FONTS['body'],
            text_color=COLORS['text_secondary']
        ).pack(side='left', pady=(4, 0))

        # Séparateur
        ctk.CTkFrame(self, fg_color=COLORS['border'], height=1, corner_radius=0).pack(
            fill='x', padx=24, pady=(0, 4)
        )

        # ── Scrollable Content ────────────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(
            self, fg_color='transparent',
            scrollbar_button_color=COLORS['border']
        )
        scroll.pack(fill='both', expand=True, padx=24, pady=12)

        # ── Section 1 : Informations Société ──────────────────────────────────
        self._section(scroll, '🏢  Informations Société', COLORS['primary'])
        societe_card = self._card(scroll)

        societe_fields = [
            ('Nom de la société',  'societe_nom',     'SARL NOMADE AYRIS'),
            ('Adresse',            'societe_adresse', 'Adresse complète...'),
            ('Téléphone',          'societe_tel',     '+213 ...'),
            ('Email',              'societe_email',   'contact@ayris.dz'),
            ('Registre Commerce',  'societe_rc',      'RC N°...'),
            ('N° Fiscal',          'societe_nif',     'NIF N°...'),
        ]

        self._soc_vars = {}
        for label, key, placeholder in societe_fields:
            frame = ctk.CTkFrame(societe_card, fg_color='transparent')
            frame.pack(fill='x', padx=16, pady=4)
            ctk.CTkLabel(frame, text=label, font=FONTS['body_bold'],
                         text_color=COLORS['text_secondary'], width=160, anchor='w').pack(side='left')
            var = tk.StringVar(value=self._config.get(key, ''))
            self._soc_vars[key] = var
            make_input(frame, placeholder=placeholder, textvariable=var).pack(side='left', fill='x', expand=True)

        make_primary_button(
            societe_card, '💾 Enregistrer Informations Société',
            command=self._save_societe, width=280
        ).pack(anchor='w', padx=16, pady=(8, 12))

        # ── Section 2 : Dossier PDF ───────────────────────────────────────────
        self._section(scroll, '📁  Dossier d\'Export PDF', COLORS['accent'])
        pdf_card = self._card(scroll)

        ctk.CTkLabel(pdf_card, text='Dossier de destination des Bons PDF générés :',
                     font=FONTS['body'], text_color=COLORS['text_secondary']).pack(
                         anchor='w', padx=16, pady=(12, 4))

        path_row = ctk.CTkFrame(pdf_card, fg_color='transparent')
        path_row.pack(fill='x', padx=16, pady=(0, 12))

        self.var_pdf_dir = tk.StringVar(value=self._config.get('pdf_directory', ''))
        self.e_pdf_dir = make_input(path_row, placeholder='Chemin du dossier PDF...',
                                     textvariable=self.var_pdf_dir)
        self.e_pdf_dir.pack(side='left', fill='x', expand=True, padx=(0, 8))

        make_secondary_button(path_row, '📂 Parcourir', command=self._browse_pdf_dir, width=110).pack(side='left', padx=(0, 6))
        make_primary_button(path_row, 'Ouvrir', command=self._open_pdf_dir, width=80).pack(side='left')

        make_primary_button(pdf_card, '💾 Enregistrer le chemin PDF',
                             command=self._save_pdf_dir, width=240).pack(anchor='w', padx=16, pady=(0, 12))

        # ── Section 3 : Dossier Excel ─────────────────────────────────────────
        self._section(scroll, '📊  Dossier d\'Export Excel', COLORS['success'])
        excel_card = self._card(scroll)

        ctk.CTkLabel(excel_card, text='Dossier de destination des exports Excel :',
                     font=FONTS['body'], text_color=COLORS['text_secondary']).pack(
                         anchor='w', padx=16, pady=(12, 4))

        excel_row = ctk.CTkFrame(excel_card, fg_color='transparent')
        excel_row.pack(fill='x', padx=16, pady=(0, 12))

        self.var_excel_dir = tk.StringVar(value=self._config.get('excel_directory', ''))
        make_input(excel_row, placeholder='Chemin du dossier Excel...',
                   textvariable=self.var_excel_dir).pack(side='left', fill='x', expand=True, padx=(0, 8))
        make_secondary_button(excel_row, '📂 Parcourir',
                              command=self._browse_excel_dir, width=110).pack(side='left', padx=(0, 6))
        make_primary_button(excel_row, 'Ouvrir', command=self._open_excel_dir, width=80).pack(side='left')

        make_primary_button(excel_card, '💾 Enregistrer le chemin Excel',
                             command=self._save_excel_dir, width=250).pack(anchor='w', padx=16, pady=(0, 12))

        # ── Section 4 : Alertes & Seuils ──────────────────────────────────────
        self._section(scroll, '⚠️  Alertes de Stock & Variation Prix', COLORS['warning'])
        alert_card = self._card(scroll)

        alert_row = ctk.CTkFrame(alert_card, fg_color='transparent')
        alert_row.pack(fill='x', padx=16, pady=12)

        ctk.CTkLabel(alert_row, text='Seuil d\'augmentation de prix (% alerte) :',
                     font=FONTS['body'], text_color=COLORS['text_secondary']).pack(side='left', padx=(0, 12))
        self.var_seuil_prix = tk.StringVar(value=str(self._config.get('seuil_augmentation_prix', 15)))
        make_input(alert_row, placeholder='15', textvariable=self.var_seuil_prix, width=80).pack(side='left')
        make_primary_button(alert_row, 'Appliquer', command=self._save_seuil_prix, width=100).pack(side='left', padx=8)

        # ── Section 5 : Imprimante ────────────────────────────────────────────
        self._section(scroll, '🖨️  Imprimante par Défaut', COLORS['text_secondary'])
        print_card = self._card(scroll)

        row_printer = ctk.CTkFrame(print_card, fg_color='transparent')
        row_printer.pack(fill='x', padx=16, pady=12)

        ctk.CTkLabel(row_printer, text='Nom imprimante :', font=FONTS['body_bold'],
                     text_color=COLORS['text_secondary']).pack(side='left', padx=(0, 8))
        self.var_printer = tk.StringVar(value=self._config.get('imprimante', ''))
        make_input(row_printer, placeholder='Ex: HP LaserJet Pro',
                   textvariable=self.var_printer).pack(side='left', fill='x', expand=True, padx=(0, 8))
        make_primary_button(row_printer, '💾 Sauver',
                             command=self._save_printer, width=100).pack(side='left')

        # ── Section 6 : Sécurité & Mot de Passe ──────────────────────────────
        self._section(scroll, '🔒  Sécurité — Mot de Passe de Configuration', COLORS['danger'])
        sec_card = self._card(scroll)

        ctk.CTkLabel(sec_card,
                     text='Changez ici le mot de passe qui protège l\'accès à cette page de configuration.',
                     font=FONTS['body'], text_color=COLORS['text_secondary']).pack(
                         anchor='w', padx=16, pady=(12, 4))

        row_pwd = ctk.CTkFrame(sec_card, fg_color='transparent')
        row_pwd.pack(fill='x', padx=16, pady=(4, 12))

        ctk.CTkLabel(row_pwd, text='Nouveau mot de passe :', font=FONTS['body_bold'],
                     text_color=COLORS['text_secondary']).pack(side='left', padx=(0, 8))
        self.var_config_pwd = tk.StringVar()
        self._e_pwd = ctk.CTkEntry(
            row_pwd, show='*', textvariable=self.var_config_pwd,
            placeholder_text='Nouveau mot de passe...',
            fg_color=COLORS['bg_input'], border_color=COLORS['border'],
            border_width=1, text_color=COLORS['text_primary'],
            font=FONTS['body'], corner_radius=8, height=40, width=260
        )
        self._e_pwd.pack(side='left', padx=(0, 8))
        make_primary_button(row_pwd, '🔒 Enregistrer',
                             command=self._save_config_pwd, width=150).pack(side='left')

        # ── Section 7 : Sauvegarde BDD ────────────────────────────────────────
        self._section(scroll, '💾  Sauvegarde de la Base de Données', COLORS['success'])
        backup_card = self._card(scroll)

        db_path = db.get_db_path()
        info_row = ctk.CTkFrame(backup_card, fg_color=COLORS['bg_hover'], corner_radius=8)
        info_row.pack(fill='x', padx=16, pady=(12, 8))
        ctk.CTkLabel(info_row, text=f'📍 Base de données active :\n{db_path}',
                     font=('Consolas', 9), text_color=COLORS['text_secondary'], justify='left').pack(
                         anchor='w', padx=12, pady=10)

        btn_row = ctk.CTkFrame(backup_card, fg_color='transparent')
        btn_row.pack(fill='x', padx=16, pady=(0, 12))

        make_primary_button(btn_row, '💾 Créer une Sauvegarde (.db)',
                             command=self._backup_db, width=240).pack(side='left', padx=(0, 8))
        make_secondary_button(btn_row, '📂 Ouvrir Dossier BDD',
                              command=lambda: subprocess.run(
                                  ['explorer', os.path.dirname(db_path)], shell=True), width=180).pack(side='left')

        # ── Section 8 : À propos ──────────────────────────────────────────────
        self._section(scroll, 'ℹ️  À Propos du Logiciel', COLORS['text_muted'])
        about_card = self._card(scroll)
        about_data = [
            ('Application',      'SARL NOMADE AYRIS — Gestionnaire de Parc Pro'),
            ('Version',          'v3.5 Enterprise'),
            ('Technologies',     'Python 3.10 / CustomTkinter / SQLite / ReportLab'),
            ('Base de données',  db_path),
            ('Développé pour',   'SARL NOMADE AYRIS — Direction Technique & Parc'),
        ]
        for label, value in about_data:
            row = ctk.CTkFrame(about_card, fg_color=COLORS['bg_hover'], corner_radius=8)
            row.pack(fill='x', padx=16, pady=2)
            ctk.CTkLabel(row, text=label, font=FONTS['small_bold'],
                         text_color=COLORS['text_secondary'], width=140, anchor='w').pack(side='left', padx=10, pady=8)
            ctk.CTkLabel(row, text=value, font=FONTS['small'],
                         text_color=COLORS['text_primary'], wraplength=460, justify='left').pack(side='left', padx=4)

        make_danger_button(about_card, '🔄 Réinitialiser la Base de Données (⚠️ DANGER)',
                              command=self._confirm_reset_db, width=340).pack(anchor='e', padx=16, pady=(8, 12))

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _section(self, parent, title: str, color: str):
        frame = ctk.CTkFrame(parent, fg_color='transparent')
        frame.pack(fill='x', pady=(16, 6))
        bar = ctk.CTkFrame(frame, fg_color=color, corner_radius=3, width=4, height=22)
        bar.pack(side='left', padx=(0, 10))
        bar.pack_propagate(False)
        ctk.CTkLabel(frame, text=title, font=FONTS['subtitle'],
                     text_color=COLORS['text_primary']).pack(side='left')

    def _card(self, parent) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent, fg_color=COLORS['bg_card'],
                            corner_radius=12, border_width=1, border_color=COLORS['border'])
        card.pack(fill='x', pady=(0, 8))
        return card

    # ─── Actions & Sauvegardes ────────────────────────────────────────────────

    def _save_societe(self):
        for key, var in self._soc_vars.items():
            self._config[key] = var.get().strip()
        save_config(self._config)
        messagebox.showinfo('Enregistré', 'Informations société enregistrées avec succès !', parent=self)

    def _browse_pdf_dir(self):
        folder = filedialog.askdirectory(title='Choisir le dossier PDF', parent=self)
        if folder:
            self.var_pdf_dir.set(folder)

    def _save_pdf_dir(self):
        path = self.var_pdf_dir.get().strip()
        if not path:
            messagebox.showwarning('Attention', 'Veuillez choisir un dossier.', parent=self)
            return
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            self._config['pdf_directory'] = path
            save_config(self._config)
            messagebox.showinfo('Enregistré', f'Dossier PDF configuré :\n{path}', parent=self)
        except Exception as e:
            messagebox.showerror('Erreur', f'Impossible de créer le dossier :\n{e}', parent=self)

    def _open_pdf_dir(self):
        p = self.var_pdf_dir.get()
        if p and os.path.exists(p):
            subprocess.run(['explorer', os.path.normpath(p)], shell=True)
        else:
            messagebox.showwarning('Attention', 'Dossier introuvable.', parent=self)

    def _browse_excel_dir(self):
        folder = filedialog.askdirectory(title='Choisir le dossier Excel', parent=self)
        if folder:
            self.var_excel_dir.set(folder)

    def _save_excel_dir(self):
        path = self.var_excel_dir.get().strip()
        if not path:
            messagebox.showwarning('Attention', 'Veuillez choisir un dossier.', parent=self)
            return
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            self._config['excel_directory'] = path
            save_config(self._config)
            messagebox.showinfo('Enregistré', f'Dossier Excel configuré :\n{path}', parent=self)
        except Exception as e:
            messagebox.showerror('Erreur', f'Impossible de créer le dossier :\n{e}', parent=self)

    def _open_excel_dir(self):
        p = self.var_excel_dir.get()
        if p and os.path.exists(p):
            subprocess.run(['explorer', os.path.normpath(p)], shell=True)
        else:
            messagebox.showwarning('Attention', 'Dossier introuvable.', parent=self)

    def _save_seuil_prix(self):
        try:
            val = int(self.var_seuil_prix.get().strip())
            self._config['seuil_augmentation_prix'] = val
            save_config(self._config)
            messagebox.showinfo('Enregistré', f'Seuil d\'augmentation de prix enregistré : {val}%', parent=self)
        except ValueError:
            messagebox.showerror('Erreur', 'Valeur de seuil invalide (entier requis).', parent=self)

    def _save_printer(self):
        printer = self.var_printer.get().strip()
        self._config['imprimante'] = printer
        save_config(self._config)
        messagebox.showinfo('Enregistré', f'Imprimante enregistrée : {printer or "(aucune)"}', parent=self)

    def _save_config_pwd(self):
        new_pwd = self.var_config_pwd.get().strip()
        if not new_pwd:
            messagebox.showwarning('Attention', 'Le mot de passe ne peut pas être vide.', parent=self)
            return
        self._config['config_password'] = new_pwd
        save_config(self._config)
        self.var_config_pwd.set('')
        messagebox.showinfo('Succès', 'Mot de passe de configuration mis à jour avec succès !', parent=self)

    def _backup_db(self):
        now = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f'ayris_parc_backup_{now}.db'
        dest = filedialog.asksaveasfilename(
            title='Sauvegarder la Base de Données',
            defaultextension='.db',
            initialfile=default_name,
            filetypes=[('SQLite DB', '*.db'), ('Tous les fichiers', '*.*')],
            parent=self
        )
        if dest:
            ok = db.backup_database(dest)
            if ok:
                messagebox.showinfo('Sauvegarde réussie', f'Base sauvegardée :\n{dest}', parent=self)
            else:
                messagebox.showerror('Erreur', 'La sauvegarde a échoué.', parent=self)

    def _confirm_reset_db(self):
        confirm = messagebox.askyesno(
            '⚠️ DANGER — Réinitialisation',
            'Voulez-vous vraiment SUPPRIMER toutes les données (engins, pièces, bons) ?\n\n'
            'Cette action est IRRÉVERSIBLE. Assurez-vous d\'avoir une sauvegarde !',
            parent=self
        )
        if confirm:
            confirm2 = messagebox.askyesno(
                '⚠️ Confirmation finale',
                'DERNIÈRE CONFIRMATION : toutes les données seront effacées.',
                parent=self
            )
            if confirm2:
                try:
                    db.reset_database()
                    messagebox.showinfo('Réinitialisé', 'La base de données a été réinitialisée.', parent=self)
                except Exception as e:
                    messagebox.showerror('Erreur', f'Réinitialisation échouée :\n{e}', parent=self)
