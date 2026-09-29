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
from ui.widgets import make_primary_button, make_secondary_button, StatusBarWidget, show_toast

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
    def __init__(self, user_info: dict = None):
        super().__init__()
        self.title('SARL NOMADE Ayris — Gestionnaire de Parc')
        self.user_info = user_info or {'username': 'Administrateur', 'role': 'admin'}
        
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
        self._setup_shortcuts()
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

    def _setup_shortcuts(self):
        self.bind_all('<Control-n>', self._shortcut_new_bon)
        self.bind_all('<Control-N>', self._shortcut_new_bon)
        self.bind_all('<Control-f>', self._shortcut_search)
        self.bind_all('<Control-F>', self._shortcut_search)

    def _shortcut_new_bon(self, event=None):
        if self._active_key == 'bon_sortie':
            self.navigate_to('bon_livraison')
        else:
            self.navigate_to('bon_sortie' if self._active_key == 'bon_livraison' else 'bon_livraison')
        show_toast(self, "Raccourci [Ctrl+N] : Formulaire de bon", "info")
        return 'break'

    def _shortcut_search(self, event=None):
        target_frame = self._frames.get(self._active_key)
        if target_frame:
            # Chercher récursivement ou attribut direct de recherche
            for attr in ['search_entry', 'e_recherche', 'search_input', 'e_filter', 'e_search']:
                if hasattr(target_frame, attr):
                    w = getattr(target_frame, attr)
                    if hasattr(w, 'focus_set'):
                        w.focus_set()
                        if hasattr(w, 'select_range'):
                            w.select_range(0, 'end')
                        show_toast(self, "Recherche activée [Ctrl+F]", "info")
                        return 'break'
        show_toast(self, "Recherche [Ctrl+F]", "info")
        return 'break'

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self.sidebar = ctk.CTkFrame(self, fg_color=COLORS['bg_sidebar'], corner_radius=0, width=250)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky='nsew')
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
                    size=(160, 160)
                )
                logo_container = ctk.CTkFrame(logo_inner, fg_color='transparent', width=160, height=160)
                logo_container.pack(pady=2, padx=10)
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
                    size=(180, 140)
                )
                lbl_logo = ctk.CTkLabel(logo_inner, image=logo_img, text='')
                lbl_logo.pack(pady=2, padx=10)
                self._logo_images.append(logo_img)
            except Exception:
                pass

        ctk.CTkLabel(self.sidebar, text='SARL NOMADE AYRIS', font=('Segoe UI', 17, 'bold'), text_color='white').pack(pady=(0, 2))

        # Badge de Rôle
        is_admin = (self.user_info.get('role') == 'admin')
        badge_bg = '#1E3A8A' if is_admin else '#065F46'
        badge_text = f"👑 {self.user_info.get('username', 'Admin').upper()} (ADMIN)" if is_admin else f"👤 {self.user_info.get('username', 'Opérateur').upper()} (OPÉRATEUR)"
        badge_color = '#FDE047' if is_admin else '#6EE7B7'

        badge_box = ctk.CTkFrame(self.sidebar, fg_color=badge_bg, corner_radius=8, height=28)
        badge_box.pack(fill='x', padx=18, pady=(4, 10))
        badge_box.pack_propagate(False)
        ctk.CTkLabel(badge_box, text=badge_text, font=FONTS['small_bold'], text_color=badge_color).pack(expand=True)

        ctk.CTkFrame(self.sidebar, fg_color='#1D5197', height=1, corner_radius=0).pack(fill='x', padx=20, pady=(0, 10))

        nav_frame = ctk.CTkFrame(self.sidebar, fg_color='transparent')
        nav_frame.pack(fill='both', expand=True, padx=10, pady=(0, 12))

        for item in SIDEBAR_ITEMS:
            # Si l'utilisateur est opérateur, masquer complètement le menu de configuration/options
            if not is_admin and item['key'] == 'options':
                continue

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

        # Barre de statut inférieure
        self.status_bar = StatusBarWidget(
            self,
            user=self.user_info.get('username', 'Admin'),
            role=self.user_info.get('role', 'admin')
        )
        self.status_bar.grid(row=1, column=1, sticky='ew')

    def navigate_to(self, key):
        # Sécurité : Vérification du mot de passe pour la page de configuration
        if key == 'options':
            if self.user_info.get('role') != 'admin':
                show_toast(self, "Accès réservé aux administrateurs", "error")
                return

            expected_pwd = get_config('config_password', 'admin')
            dlg = PasswordPromptDialog(self)
            if dlg.result != expected_pwd:
                messagebox.showerror('Accès refusé', 'Mot de passe de configuration incorrect.', parent=self)
                return
            # Toujours recréer la frame Options pour éviter une page vide
            if 'options' in self._frames:
                try:
                    self._frames['options'].destroy()
                except Exception:
                    pass
                del self._frames['options']

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
        if hasattr(target_frame, 'refresh') and key != 'options':
            try:
                target_frame.refresh()
            except Exception:
                pass

        if hasattr(self, 'status_bar'):
            module_name = next((item['label'] for item in SIDEBAR_ITEMS if item['key'] == key), key)
            self.status_bar.set_status(f"Module actif : {module_name}")

        # ── Rafraîchissement inter-frames (cohérence du stock) ──────────────────
        STOCK_RELATED_FRAMES = {'bon_livraison', 'bon_sortie', 'pieces', 'dashboard'}
        if key in STOCK_RELATED_FRAMES:
            for other_key, other_frame in self._frames.items():
                if other_key != key and other_key in STOCK_RELATED_FRAMES and other_key != 'options':
                    if hasattr(other_frame, 'refresh'):
                        try:
                            other_frame.refresh()
                        except Exception:
                            pass

