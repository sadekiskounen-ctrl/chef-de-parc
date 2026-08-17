import os
import sys
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageTk

from tkinter import messagebox

from services.config_manager import get_config
from ui.dashboard import DashboardFrame
from ui.engins import EnginsFrame
from ui.pieces import PiecesFrame
from ui.prix import PrixFrame
from ui.bon_livraison import BonLivraisonFrame
from ui.bon_sortie import BonSortieFrame
from ui.options import OptionsFrame
from ui.theme import COLORS, FONTS, SIDEBAR_ITEMS
from ui.widgets import make_primary_button, make_secondary_button

ROOT_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = Path(getattr(sys, '_MEIPASS', ROOT_DIR))
ASSET_DIR = BASE_DIR / 'assets'
LOGO_PATH = ASSET_DIR / 'logo_nomade_ayris.png'
ICO_PATH = ASSET_DIR / 'ayris.ico'
WATERMARK_PATH = ASSET_DIR / 'watermark.png'


class PasswordPromptDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="Zone Sécurisée", prompt="Saisissez le mot de passe de configuration :"):
        super().__init__(parent)
        self.title(title)
        self.geometry("420x220")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.result = None
        self.configure(fg_color=COLORS['bg_card'])

        try:
            parent.update_idletasks()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            px = parent.winfo_x()
            py = parent.winfo_y()
            x = max(0, px + (pw - 420) // 2)
            y = max(0, py + (ph - 220) // 2)
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

        ctk.CTkLabel(self, text="🔒 Accès Sécurisé", font=FONTS['subtitle'], text_color=COLORS['primary']).pack(pady=(16, 4))
        ctk.CTkLabel(self, text=prompt, font=FONTS['body'], text_color=COLORS['text_secondary']).pack(pady=(0, 12))

        self.e_pwd = ctk.CTkEntry(self, show='*', width=280, font=FONTS['body'], height=38)
        self.e_pwd.pack(pady=(0, 16))
        self.e_pwd.focus()
        self.e_pwd.bind('<Return>', lambda e: self._on_ok())

        btn_box = ctk.CTkFrame(self, fg_color='transparent')
        btn_box.pack()
        make_primary_button(btn_box, "Déverrouiller", self._on_ok, width=130).pack(side='left', padx=6)
        make_secondary_button(btn_box, "Annuler", self._on_cancel, width=110).pack(side='left', padx=6)

        self.wait_window()

    def _on_ok(self):
        self.result = self.e_pwd.get()
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('SARL NOMADE Ayris — Gestionnaire de Parc')
        
        # Adaptabilité dynamique selon l'écran et la résolution
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        win_w = max(1100, min(1600, int(screen_w * 0.88)))
        win_h = max(680, min(950, int(screen_h * 0.84)))
        pos_x = max(0, (screen_w - win_w) // 2)
        pos_y = max(0, (screen_h - win_h) // 2)
        self.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
        self.minsize(1000, 640)
        self.resizable(True, True)

        self.configure(fg_color=COLORS['bg_dark'])
        self._logo_images = []
        self._setup_icon()

        self._active_key = None
        self._frames = {}
        self._nav_buttons = {}
        self._build_ui()
        self.navigate_to('dashboard')

    def _setup_icon(self):
        if ICO_PATH.exists():
            try:
                self.iconbitmap(str(ICO_PATH))
                self.wm_iconbitmap(str(ICO_PATH))
            except Exception:
                pass

        circle_path = BASE_DIR / 'assets' / 'logo_circle.png'
        if circle_path.exists():
            try:
                img = Image.open(circle_path).convert('RGBA')
                self._app_icon_photo = ImageTk.PhotoImage(img)
                self.iconphoto(True, self._app_icon_photo)
                self._logo_images.append(self._app_icon_photo)
            except Exception:
                pass

        if LOGO_PATH.exists():
            try:
                icon_img = ImageTk.PhotoImage(Image.open(LOGO_PATH))
                self.iconphoto(True, icon_img)
                self._logo_images.append(icon_img)
            except Exception:
                pass

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, fg_color=COLORS['bg_sidebar'], corner_radius=0, width=250)
        self.sidebar.grid(row=0, column=0, sticky='nsew')
        self.sidebar.grid_propagate(False)

        logo_frame = ctk.CTkFrame(self.sidebar, fg_color='transparent')
        logo_frame.pack(fill='x', padx=0, pady=0)

        logo_inner = ctk.CTkFrame(logo_frame, fg_color='transparent')
        logo_inner.pack(fill='x', pady=(16, 6))

        circle_path = ASSET_DIR / 'logo_circle.png'
        if circle_path.exists():
            try:
                pil_img = Image.open(circle_path).convert('RGBA')
                logo_img = ctk.CTkImage(
                    light_image=pil_img,
                    dark_image=pil_img,
                    size=(170, 170)
                )
                logo_container = ctk.CTkFrame(logo_inner, fg_color='transparent', width=170, height=170)
                logo_container.pack(pady=4, padx=10)
                logo_container.pack_propagate(False)
                lbl_logo = ctk.CTkLabel(logo_container, image=logo_img, text='')
                lbl_logo.pack(expand=True)
                self._logo_images.append(logo_img)
            except Exception:
                pass
        elif LOGO_PATH.exists():
            try:
                pil_img = Image.open(LOGO_PATH).convert('RGBA')
                logo_img = ctk.CTkImage(
                    light_image=pil_img,
                    dark_image=pil_img,
                    size=(192, 150)
                )
                lbl_logo = ctk.CTkLabel(logo_inner, image=logo_img, text='')
                lbl_logo.pack(pady=4, padx=10)
                self._logo_images.append(logo_img)
            except Exception:
                pass

        ctk.CTkLabel(self.sidebar, text='SARL NOMADE AYRIS', font=('Segoe UI', 18, 'bold'), text_color='white').pack(pady=(0, 4))
        ctk.CTkFrame(self.sidebar, fg_color='#1D5197', height=1, corner_radius=0).pack(fill='x', padx=20, pady=(4, 12))

        nav_frame = ctk.CTkFrame(self.sidebar, fg_color='transparent')
        nav_frame.pack(fill='both', expand=True, padx=10, pady=(0, 12))

        for item in SIDEBAR_ITEMS:
            btn = ctk.CTkButton(
                nav_frame,
                text=f"  {item['icon']}   {item['label']}",
                command=lambda key=item['key']: self.navigate_to(key),
                fg_color='transparent',
                hover_color='#1D5197',
                text_color=COLORS['sidebar_text'],
                font=FONTS['subtitle'],
                corner_radius=10,
                height=44,
                anchor='w',
            )
            btn.pack(fill='x', pady=3)
            self._nav_buttons[item['key']] = btn

        self.content_area = ctk.CTkFrame(self, fg_color=COLORS['bg_dark'], corner_radius=0)
        self.content_area.grid(row=0, column=1, sticky='nsew')
        self.content_area.grid_propagate(False)
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)
        self.content_area.configure(fg_color='#F8FAFC')

        if WATERMARK_PATH.exists():
            try:
                wm_pil = Image.open(WATERMARK_PATH).convert('RGBA')
                wm_img = ctk.CTkImage(light_image=wm_pil, dark_image=wm_pil, size=(560, 438))
                self.bg_watermark_lbl = ctk.CTkLabel(self.content_area, image=wm_img, text='', fg_color='transparent')
                self.bg_watermark_lbl.place(relx=0.5, rely=0.5, anchor='center')
            except Exception:
                pass

    def navigate_to(self, key):
        # Sécurité : Vérification du mot de passe pour la page de configuration
        if key == 'options':
            expected_pwd = get_config('config_password', 'admin')
            dlg = PasswordPromptDialog(self)
            if dlg.result != expected_pwd:
                messagebox.showerror('Accès refusé', 'Mot de passe de configuration incorrect.', parent=self)
                return

        if self._active_key and self._active_key in self._nav_buttons:
            self._nav_buttons[self._active_key].configure(fg_color='transparent', text_color=COLORS['sidebar_text'])

        self._active_key = key
        if key in self._nav_buttons:
            self._nav_buttons[key].configure(fg_color=COLORS['sidebar_active_bg'], text_color=COLORS['sidebar_text_active'])

        for f in self._frames.values():
            f.grid_forget()

        if key not in self._frames:
            if key == 'dashboard':
                frame = DashboardFrame(self.content_area)
            elif key == 'engins':
                frame = EnginsFrame(self.content_area)
            elif key == 'pieces':
                frame = PiecesFrame(self.content_area)
            elif key == 'prix':
                frame = PrixFrame(self.content_area)
            elif key == 'bon_livraison':
                frame = BonLivraisonFrame(self.content_area)
            elif key == 'bon_sortie':
                frame = BonSortieFrame(self.content_area)
            elif key == 'options':
                frame = OptionsFrame(self.content_area)
            else:
                frame = DashboardFrame(self.content_area)
            self._frames[key] = frame

        target_frame = self._frames[key]
        target_frame.grid(row=0, column=0, sticky='nsew')
        target_frame.tkraise()
        if hasattr(target_frame, 'refresh'):
            try:
                target_frame.refresh()
            except Exception:
                pass

