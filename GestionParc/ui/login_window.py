import os
import sqlite3
import sys
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageTk

from auth.auth_manager import authenticate, ensure_default_users
from database.db_manager import initialize_database, ensure_demo_data

ROOT_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = Path(getattr(sys, '_MEIPASS', ROOT_DIR))
ASSET_DIR = BASE_DIR / 'assets'
LOGO = ASSET_DIR / 'logo_nomade_ayris.png'
ICO = ASSET_DIR / 'ayris.ico'


class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.authenticated = False
        self.title('SARL NOMADE Ayris — Gestionnaire de Parc')
        self.geometry('520x620')
        self.minsize(500, 560)
        self.resizable(True, True)
        self.configure(fg_color='#0B2E6B')
        self._logo_images = []
        self._setup_icon()

        self._build_ui()
        self.bind('<Return>', lambda e: self._login())
        self.after(100, self._focus_input)

    def _setup_icon(self):
        if ICO.exists():
            try:
                self.wm_iconbitmap(str(ICO))
            except Exception:
                pass

        circle_path = ASSET_DIR / 'logo_circle.png'
        if circle_path.exists():
            try:
                img = ImageTk.PhotoImage(Image.open(circle_path))
                self.iconphoto(True, img)
                self._logo_images.append(img)
            except Exception:
                pass

        if LOGO.exists():
            try:
                img = ImageTk.PhotoImage(Image.open(LOGO))
                self.iconphoto(True, img)
                self._logo_images.append(img)
            except Exception:
                pass

    def _focus_input(self):
        self.e_user.focus_set()

    def _bind_focus_navigation(self):
        self.e_user.bind('<Tab>', lambda event: self.e_pass.focus_set() or 'break')
        self.e_pass.bind('<Tab>', lambda event: self.btn_login.focus_set() or 'break')
        self.e_pass.bind('<Shift-Tab>', lambda event: self.e_user.focus_set() or 'break')

    def _build_ui(self):
        logo_frame = ctk.CTkFrame(self, fg_color='transparent')
        logo_frame.pack(pady=(22, 10))

        circle_path = ASSET_DIR / 'logo_circle.png'
        if circle_path.exists():
            try:
                img = ctk.CTkImage(light_image=Image.open(circle_path), dark_image=Image.open(circle_path), size=(150, 150))
                ctk.CTkLabel(logo_frame, image=img, text='').pack()
                self._logo_images.append(img)
            except Exception:
                pass
        elif LOGO.exists():
            try:
                img = ctk.CTkImage(light_image=Image.open(LOGO), dark_image=Image.open(LOGO), size=(120, 90))
                ctk.CTkLabel(logo_frame, image=img, text='').pack()
                self._logo_images.append(img)
            except Exception:
                pass

        ctk.CTkLabel(logo_frame, text='SARL NOMADE AYRIS', font=('Segoe UI', 24, 'bold'), text_color='white').pack(pady=(8, 0))
        ctk.CTkLabel(logo_frame, text='Gestionnaire de Parc', font=('Segoe UI', 12), text_color='#93C5FD').pack()

        card = ctk.CTkFrame(self, fg_color='white', corner_radius=20)
        card.pack(fill='both', expand=True, padx=28, pady=(8, 18))

        ctk.CTkLabel(card, text='🔐 Connexion', font=('Segoe UI', 22, 'bold'), text_color='#0B2E6B').pack(pady=(18, 4))
        ctk.CTkLabel(card, text='Accédez au système de gestion de parc', font=('Segoe UI', 11), text_color='#64748B').pack(pady=(0, 12))

        ctk.CTkLabel(card, text='👤 Nom d’utilisateur', font=('Segoe UI', 13, 'bold'), text_color='#374151', anchor='w').pack(fill='x', padx=24)
        self.e_user = ctk.CTkEntry(card, placeholder_text='Nom d’utilisateur...', font=('Segoe UI', 14), fg_color='#F8FAFC', border_color='#004899', border_width=2, text_color='#0F172A', corner_radius=10, height=44)
        self.e_user.pack(fill='x', padx=24, pady=(4, 10))

        ctk.CTkLabel(card, text='🔒 Mot de passe', font=('Segoe UI', 13, 'bold'), text_color='#374151', anchor='w').pack(fill='x', padx=24)
        self.e_pass = ctk.CTkEntry(card, placeholder_text='Mot de passe...', show='●', font=('Segoe UI', 14), fg_color='#F8FAFC', border_color='#004899', border_width=2, text_color='#0F172A', corner_radius=10, height=44)
        self.e_pass.pack(fill='x', padx=24, pady=(4, 6))

        self.lbl_error = ctk.CTkLabel(card, text='', font=('Segoe UI', 12, 'bold'), text_color='#DC2626')
        self.lbl_error.pack(pady=(4, 0))

        self.btn_login = ctk.CTkButton(card, text='🔑 Se connecter', command=self._login, fg_color='#004899', hover_color='#0B2E6B', text_color='white', font=('Segoe UI', 15, 'bold'), corner_radius=12, height=48)
        self.btn_login.pack(fill='x', padx=24, pady=(10, 12))
        self._bind_focus_navigation()

        ctk.CTkLabel(card, text='Système de gestion de parc — SARL NOMADE AYRIS\nCompte de démonstration : admin / admin', font=('Segoe UI', 10), text_color='#111827', justify='center').pack(pady=(0, 12))

    def _login(self):
        username = self.e_user.get().strip()
        password = self.e_pass.get().strip()
        if not username or not password:
            self.lbl_error.configure(text='Veuillez remplir tous les champs.')
            return
        try:
            initialize_database()
            ensure_default_users()
            ensure_demo_data()
        except sqlite3.OperationalError as exc:
            if 'locked' in str(exc).lower():
                self.lbl_error.configure(text='La base de données est déjà utilisée. Fermez l’autre instance puis réessayez.')
            else:
                self.lbl_error.configure(text=f'Erreur de base de données : {exc}')
            return

        user = authenticate(username, password)
        if user:
            self.authenticated = True
            self.destroy()
        else:
            self.lbl_error.configure(text='❌ Identifiants incorrects.')
            self.e_pass.delete(0, 'end')
            self.e_pass.focus_set()

    def _show_error(self, msg):
        self.lbl_error.configure(text=msg)
