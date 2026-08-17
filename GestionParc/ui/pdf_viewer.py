"""
SARL NOMADE AYRIS - Gestionnaire de Parc
Module: ui/pdf_viewer.py
Visionneuse PDF intégrée — affiche le PDF dans une fenêtre modale avec barres de défilement
verticale et horizontale dynamiques, contrôles de zoom et impression/téléchargement.
"""

import os
import subprocess
import sys
import shutil
import io
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from PIL import Image, ImageTk

from ui.theme import COLORS, FONTS


class PDFViewerModal(ctk.CTkToplevel):
    """
    Fenêtre modale pour visionner un PDF généré.
    Affiche les pages rendues du document avec défilement vertical et horizontal.
    """

    def __init__(self, parent, pdf_path: str, title: str = "Visualisation PDF"):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.doc_title = title
        self._tk_images = []
        self._zoom_level = 1.3

        self.title(f"📄  {title}")
        self.geometry("980x780")
        self.minsize(750, 550)
        self.configure(fg_color=COLORS['bg_dark'])
        self.transient(parent)
        self.grab_set()
        self.lift()
        self.focus_force()

        self._build_ui()
        self._load_pdf()

    def _build_ui(self):
        # ── Barre supérieure ──────────────────────────────────────────────────
        top_bar = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=0)
        top_bar.pack(fill='x', padx=0, pady=0)

        ctk.CTkLabel(
            top_bar, text=f"📄  {self.doc_title}",
            font=FONTS['title'], text_color=COLORS['text_primary']
        ).pack(side='left', padx=16, pady=12)

        # Contrôles de zoom au centre/droite
        zoom_frame = ctk.CTkFrame(top_bar, fg_color='transparent')
        zoom_frame.pack(side='left', padx=10, pady=8)

        ctk.CTkButton(
            zoom_frame, text='🔍 +',
            command=self._zoom_in,
            fg_color=COLORS['bg_hover'], hover_color=COLORS['border'],
            text_color=COLORS['text_primary'], font=FONTS['body_bold'],
            corner_radius=6, height=32, width=42
        ).pack(side='left', padx=2)

        self.lbl_zoom = ctk.CTkLabel(
            zoom_frame, text="130%",
            font=FONTS['small_bold'], text_color=COLORS['text_secondary'], width=46
        )
        self.lbl_zoom.pack(side='left', padx=2)

        ctk.CTkButton(
            zoom_frame, text='🔍 -',
            command=self._zoom_out,
            fg_color=COLORS['bg_hover'], hover_color=COLORS['border'],
            text_color=COLORS['text_primary'], font=FONTS['body_bold'],
            corner_radius=6, height=32, width=42
        ).pack(side='left', padx=2)

        ctk.CTkButton(
            zoom_frame, text='📐 Ajuster',
            command=self._fit_width,
            fg_color=COLORS['bg_hover'], hover_color=COLORS['border'],
            text_color=COLORS['text_primary'], font=FONTS['small_bold'],
            corner_radius=6, height=32, width=75
        ).pack(side='left', padx=6)

        # Boutons à droite
        btn_frame = ctk.CTkFrame(top_bar, fg_color='transparent')
        btn_frame.pack(side='right', padx=16, pady=8)

        ctk.CTkButton(
            btn_frame, text='🖨️  Imprimer',
            command=self._imprimer,
            fg_color=COLORS['bg_hover'],
            hover_color=COLORS['border'],
            text_color=COLORS['text_primary'],
            font=FONTS['body_bold'],
            corner_radius=8, height=38, width=120
        ).pack(side='left', padx=4)

        ctk.CTkButton(
            btn_frame, text='💾  Télécharger',
            command=self._telecharger,
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_dark'],
            text_color='white',
            font=FONTS['body_bold'],
            corner_radius=8, height=38, width=135
        ).pack(side='left', padx=4)

        ctk.CTkButton(
            btn_frame, text='✕',
            command=self.destroy,
            fg_color=COLORS['danger'],
            hover_color='#DC2626',
            text_color='white',
            font=FONTS['body_bold'],
            corner_radius=8, height=38, width=40
        ).pack(side='left', padx=(4, 0))

        # ── Zone principale : Canvas bidirectionnel avec défilement V + H ──────
        container = ctk.CTkFrame(self, fg_color='#1E293B', corner_radius=0)
        container.pack(fill='both', expand=True, padx=0, pady=0)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            container, bg='#1E293B', highlightthickness=0, bd=0
        )
        self.canvas.grid(row=0, column=0, sticky='nsew')

        # Barre de défilement verticale
        self.v_scrollbar = ttk.Scrollbar(container, orient='vertical', command=self.canvas.yview)
        self.v_scrollbar.grid(row=0, column=1, sticky='ns')

        # Barre de défilement horizontale (menu déroulant horizontal)
        self.h_scrollbar = ttk.Scrollbar(container, orient='horizontal', command=self.canvas.xview)
        self.h_scrollbar.grid(row=1, column=0, sticky='ew')

        self.canvas.configure(
            xscrollcommand=self.h_scrollbar.set,
            yscrollcommand=self.v_scrollbar.set
        )

        # Frame interne hébergé dans le Canvas
        self.inner_frame = ctk.CTkFrame(self.canvas, fg_color='#1E293B', corner_radius=0)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor='nw')

        self.inner_frame.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind('<MouseWheel>', self._on_mousewheel)
        self.canvas.bind('<Shift-MouseWheel>', self._on_shift_mousewheel)

        # Navigation / footer
        self.nav_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=0)
        self.nav_frame.pack(fill='x', side='bottom')
        self.lbl_page = ctk.CTkLabel(
            self.nav_frame, text='',
            font=FONTS['body_bold'],
            text_color=COLORS['text_secondary']
        )
        self.lbl_page.pack(side='left', padx=20, pady=8)

        ctk.CTkLabel(
            self.nav_frame,
            text=f"📁  {self.pdf_path}",
            font=FONTS['small'],
            text_color=COLORS['text_muted']
        ).pack(side='right', padx=16, pady=8)

    def _on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_shift_mousewheel(self, event):
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def _zoom_in(self):
        if self._zoom_level < 2.5:
            self._zoom_level += 0.2
            self.lbl_zoom.configure(text=f"{int(self._zoom_level * 100)}%")
            self._load_pdf()

    def _zoom_out(self):
        if self._zoom_level > 0.6:
            self._zoom_level -= 0.2
            self.lbl_zoom.configure(text=f"{int(self._zoom_level * 100)}%")
            self._load_pdf()

    def _fit_width(self):
        self._zoom_level = 1.0
        self.lbl_zoom.configure(text="100%")
        self._load_pdf()

    def _load_pdf(self):
        """Charge et affiche le PDF (PyMuPDF / fitz)."""
        if not os.path.exists(self.pdf_path):
            self._show_error("Fichier PDF introuvable :\n" + self.pdf_path)
            return

        try:
            import pymupdf as fitz
            self._render_with_fitz(fitz)
        except ImportError:
            self._show_fallback_info()

    def _render_with_fitz(self, fitz):
        """Rendu des pages PDF en images avec PyMuPDF et PIL."""
        try:
            doc = fitz.open(self.pdf_path)
            nb_pages = len(doc)

            for w in self.inner_frame.winfo_children():
                w.destroy()

            self._tk_images = []

            for page_num in range(nb_pages):
                page = doc.load_page(page_num)
                mat = fitz.Matrix(self._zoom_level, self._zoom_level)
                pix = page.get_pixmap(matrix=mat, alpha=False)

                img_data = pix.tobytes("png")
                pil_img = Image.open(io.BytesIO(img_data))
                tk_img = ImageTk.PhotoImage(pil_img)
                self._tk_images.append(tk_img)

                if page_num > 0:
                    ctk.CTkLabel(
                        self.inner_frame,
                        text=f"─── Page {page_num + 1} ───",
                        font=FONTS['body_bold'],
                        text_color='#94A3B8'
                    ).pack(pady=8)

                lbl = tk.Label(
                    self.inner_frame,
                    image=tk_img,
                    bg='#1E293B',
                    relief='flat',
                    borderwidth=0
                )
                lbl.pack(pady=12, padx=16)

            doc.close()
            self.lbl_page.configure(text=f"📄  {nb_pages} page(s) affichée(s)  •  Défilement V+H activé")
            self.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))

        except Exception as e:
            self._show_error(f"Erreur lors du rendu PDF :\n{e}")

    def _show_fallback_info(self):
        """Fallback si PyMuPDF n'est pas disponible."""
        for w in self.inner_frame.winfo_children():
            w.destroy()

        info_card = ctk.CTkFrame(
            self.inner_frame, fg_color=COLORS['bg_card'],
            corner_radius=16, border_width=1,
            border_color=COLORS['border']
        )
        info_card.pack(expand=True, padx=40, pady=40, fill='both')

        ctk.CTkLabel(
            info_card, text='📄',
            font=('Segoe UI Emoji', 64),
            text_color=COLORS['primary']
        ).pack(pady=(32, 8))

        ctk.CTkLabel(
            info_card, text='Bon PDF Généré',
            font=FONTS['title_large'],
            text_color=COLORS['text_primary']
        ).pack()

        ctk.CTkLabel(
            info_card, text='Le document a été créé avec succès.',
            font=FONTS['body'],
            text_color=COLORS['text_secondary']
        ).pack(pady=(4, 16))

        try:
            size_kb = os.path.getsize(self.pdf_path) / 1024
            size_str = f"{size_kb:.1f} Ko"
        except Exception:
            size_str = "N/A"

        details_frame = ctk.CTkFrame(info_card, fg_color=COLORS['bg_hover'], corner_radius=10)
        details_frame.pack(fill='x', padx=32, pady=(0, 16))

        for label, value in [
            ('📁 Fichier', os.path.basename(self.pdf_path)),
            ('📂 Dossier', os.path.dirname(self.pdf_path)),
            ('📏 Taille', size_str),
        ]:
            row = ctk.CTkFrame(details_frame, fg_color='transparent')
            row.pack(fill='x', padx=16, pady=4)
            ctk.CTkLabel(row, text=label, font=FONTS['body_bold'],
                         text_color=COLORS['text_secondary'], width=100, anchor='w').pack(side='left')
            ctk.CTkLabel(row, text=value, font=FONTS['body'],
                         text_color=COLORS['text_primary'], wraplength=500, anchor='w').pack(side='left')

        self.lbl_page.configure(text="📄  PDF généré avec succès")

    def _show_error(self, msg: str):
        for w in self.inner_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.inner_frame,
            text=f"⚠️  {msg}",
            font=FONTS['body'],
            text_color=COLORS['danger'],
            wraplength=600
        ).pack(expand=True, pady=40)

    def _telecharger(self):
        dest = filedialog.asksaveasfilename(
            title='Enregistrer le PDF sous…',
            defaultextension='.pdf',
            initialfile=os.path.basename(self.pdf_path),
            filetypes=[('PDF', '*.pdf'), ('Tous les fichiers', '*.*')],
            parent=self
        )
        if not dest:
            return
        try:
            shutil.copy2(self.pdf_path, dest)
            messagebox.showinfo('✅  Téléchargement réussi', f'Fichier enregistré :\n{dest}', parent=self)
        except Exception as e:
            messagebox.showerror('Erreur', f'Impossible d\'enregistrer :\n{e}', parent=self)

    def _imprimer(self):
        if not os.path.exists(self.pdf_path):
            messagebox.showerror('Erreur', 'Fichier PDF introuvable.', parent=self)
            return
        try:
            if sys.platform == 'win32':
                os.startfile(self.pdf_path, 'print')
            elif sys.platform == 'darwin':
                subprocess.Popen(['lpr', self.pdf_path])
            else:
                subprocess.Popen(['lp', self.pdf_path])
        except Exception as e:
            try:
                os.startfile(self.pdf_path)
            except Exception:
                messagebox.showerror('Erreur Impression', f'Impossible d\'imprimer :\n{e}', parent=self)


def ouvrir_pdf_viewer(parent, pdf_path: str, title: str = "Bon PDF"):
    """Ouvre la visionneuse PDF."""
    if not pdf_path or not os.path.exists(pdf_path):
        messagebox.showwarning('PDF introuvable', f'Fichier PDF introuvable :\n{pdf_path}', parent=parent)
        return None
    return PDFViewerModal(parent, pdf_path, title)
