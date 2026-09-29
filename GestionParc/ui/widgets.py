import tkinter as tk
import customtkinter as ctk

from ui.theme import COLORS, FONTS


def make_card(parent, title: str = '', width: int = 200, height: int = 120):
    frame = ctk.CTkFrame(
        parent,
        fg_color=COLORS['bg_card'],
        corner_radius=12,
        border_width=1,
        border_color=COLORS['border'],
        width=width,
        height=height,
    )
    if title:
        ctk.CTkLabel(frame, text=title, font=FONTS['subtitle'], text_color=COLORS['text_primary']).pack(anchor='w', padx=16, pady=(12, 6))
    return frame


class DynamicStatCard(ctk.CTkFrame):
    """
    Carte statistique dynamique avec adaptation intelligente de police
    et défilement/marquee fluide pour afficher les grands nombres sans coupure.
    """
    def __init__(self, parent, title: str, value: str, icon: str, color: str, bg_color: str = None, **kwargs):
        super().__init__(
            parent,
            fg_color=COLORS['bg_card'],
            corner_radius=16,
            border_width=1,
            border_color=COLORS['border'],
            **kwargs
        )
        self.original_value = str(value)
        self.color = color
        self.title_text = title
        self._marquee_job = None
        self._offset = 0
        self._is_animating = False

        icon_frame = ctk.CTkFrame(self, fg_color=bg_color or COLORS['bg_hover'], corner_radius=12, width=52, height=52)
        icon_frame.pack(side='left', padx=12, pady=12)
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text=icon, font=('Segoe UI Emoji', 22), text_color=color).place(relx=0.5, rely=0.5, anchor='center')

        self.text_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.text_frame.pack(side='left', padx=(0, 12), pady=10, fill='both', expand=True)

        font_size = self._calc_font_size(self.original_value)
        self.lbl_value = ctk.CTkLabel(
            self.text_frame,
            text=self.original_value,
            font=('Segoe UI', font_size, 'bold'),
            text_color=color,
            anchor='w'
        )
        self.lbl_value.pack(anchor='w', fill='x', expand=True)

        self.lbl_title = ctk.CTkLabel(
            self.text_frame,
            text=title,
            font=FONTS['body_bold'],
            text_color=COLORS['text_secondary'],
            anchor='w'
        )
        self.lbl_title.pack(anchor='w', fill='x', expand=True)

        # Liaison des événements pour défilement au survol ou automatique si très long
        for widget in (self, self.text_frame, self.lbl_value, self.lbl_title, icon_frame):
            widget.bind('<Enter>', self._start_marquee, add='+')
            widget.bind('<Leave>', self._stop_marquee, add='+')

        # Si le texte est très long (>15 caractères), déclencher un léger va-et-vient automatique
        if len(self.original_value) > 15:
            self.after(1500, self._start_marquee)

    def _calc_font_size(self, text: str) -> int:
        n = len(text)
        if n <= 6:
            return 24
        elif n <= 10:
            return 20
        elif n <= 14:
            return 17
        elif n <= 18:
            return 14
        else:
            return 12

    def _start_marquee(self, event=None):
        if not self._is_animating and len(self.original_value) > 12:
            self._is_animating = True
            self._scroll_step()

    def _stop_marquee(self, event=None):
        self._is_animating = False
        if self._marquee_job:
            self.after_cancel(self._marquee_job)
            self._marquee_job = None
        self._offset = 0
        font_size = self._calc_font_size(self.original_value)
        self.lbl_value.configure(text=self.original_value, font=('Segoe UI', font_size, 'bold'))

    def _scroll_step(self):
        if not self._is_animating:
            return
        try:
            full = self.original_value + "    •    "
            max_visible = 15
            if len(self.original_value) > max_visible:
                shifted = full[self._offset:] + full[:self._offset]
                self.lbl_value.configure(text=shifted[:max_visible + 3])
                self._offset = (self._offset + 1) % len(full)
                self._marquee_job = self.after(300, self._scroll_step)
            else:
                self.lbl_value.configure(text=self.original_value)
        except Exception:
            pass

    def update_value(self, value: str):
        self.original_value = str(value)
        font_size = self._calc_font_size(self.original_value)
        self.lbl_value.configure(text=self.original_value, font=('Segoe UI', font_size, 'bold'))


def make_stat_card(parent, title: str, value: str, icon: str, color: str, bg_color: str = None):
    return DynamicStatCard(parent, title, value, icon, color, bg_color)


class AutocompleteEntry(ctk.CTkFrame):
    """
    Champ de saisie moderne avec autocomplétion et menu déroulant instantané
    qui s'affiche dès la frappe de la première lettre.
    """
    def __init__(self, parent, placeholder='', width=220, completion_list=None, on_select=None, textvariable=None, height=40):
        super().__init__(parent, fg_color='transparent')
        self._completion_list = [str(x) for x in (completion_list or [])]
        self._on_select = on_select
        self._popup = None
        self._listbox = None
        self._current_matches = []
        self._after_job = None
        self._width = width
        self._height = height

        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            fg_color=COLORS['bg_input'],
            border_color=COLORS['border'],
            border_width=1,
            text_color=COLORS['text_primary'],
            placeholder_text_color=COLORS['text_muted'],
            font=FONTS['body'],
            corner_radius=8,
            height=height,
            width=width,
            textvariable=textvariable,
        )
        self.entry.pack(fill='both', expand=True)

        self.entry.bind('<KeyRelease>', self._on_key_release)
        self.entry.bind('<FocusOut>', self._on_focus_out)
        self.entry.bind('<Down>', self._on_arrow_down)
        self.entry.bind('<Up>', self._on_arrow_up)
        self.entry.bind('<Return>', self._on_return)
        self.entry.bind('<Escape>', lambda e: self._close_popup())
        self.entry.bind('<Tab>', lambda event: _focus_next_widget(event.widget))
        self.entry.bind('<Shift-Tab>', lambda event: _focus_prev_widget(event.widget))

    def set_completion_list(self, new_list: list[str]):
        self._completion_list = [str(x) for x in (new_list or [])]

    def _on_key_release(self, event):
        if event.keysym in ('Up', 'Down', 'Return', 'Escape', 'Tab', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R'):
            return
        
        if self._after_job:
            self.after_cancel(self._after_job)
        self._after_job = self.after(100, self._filter_and_show_popup)

    def _filter_and_show_popup(self):
        query = self.entry.get().strip().lower()
        if not query or len(query) < 1:
            self._close_popup()
            return

        # Priorité aux correspondances au début, puis dans le texte
        starts = [item for item in self._completion_list if item and item.lower().startswith(query)]
        contains = [item for item in self._completion_list if item and query in item.lower() and item not in starts]
        self._current_matches = (starts + contains)[:10]

        if not self._current_matches:
            self._close_popup()
            return

        self._show_popup()

    def _show_popup(self):
        if not self._current_matches:
            return

        top_win = self.winfo_toplevel()

        if self._popup is None or not self._popup.winfo_exists():
            self._popup = tk.Toplevel(top_win)
            self._popup.wm_overrideredirect(True)
            self._popup.attributes('-topmost', True)
            self._popup.configure(bg='#FFFFFF')

            frame = tk.Frame(self._popup, bg='#FFFFFF', highlightthickness=1, highlightbackground='#004899')
            frame.pack(fill='both', expand=True)

            self._listbox = tk.Listbox(
                frame,
                font=('Segoe UI', 11),
                bg='#FFFFFF',
                fg='#0F172A',
                selectbackground='#004899',
                selectforeground='#FFFFFF',
                activestyle='none',
                bd=0,
                highlightthickness=0,
                height=min(8, len(self._current_matches))
            )
            self._listbox.pack(fill='both', expand=True, padx=2, pady=2)
            self._listbox.bind('<ButtonRelease-1>', self._on_listbox_click)
            self._listbox.bind('<Return>', self._on_return)

        self._listbox.delete(0, 'end')
        for item in self._current_matches:
            self._listbox.insert('end', f"  {item}")

        self._listbox.configure(height=min(8, len(self._current_matches)))

        try:
            self.update_idletasks()
            rx = self.entry.winfo_rootx()
            ry = self.entry.winfo_rooty() + self.entry.winfo_height() + 2
            rw = max(self.entry.winfo_width(), self._width)
            rh = min(8, len(self._current_matches)) * 24 + 8
            self._popup.geometry(f"{rw}x{rh}+{rx}+{ry}")
            self._popup.deiconify()
        except Exception:
            pass

    def _close_popup(self):
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
        self._popup = None
        self._listbox = None

    def _on_focus_out(self, event=None):
        # Délai pour permettre le clic sur la listbox
        self.after(200, self._close_popup)

    def _on_arrow_down(self, event):
        if self._popup and self._popup.winfo_exists() and self._listbox:
            curr = self._listbox.curselection()
            next_idx = (curr[0] + 1) if curr else 0
            if next_idx < self._listbox.size():
                self._listbox.selection_clear(0, 'end')
                self._listbox.selection_set(next_idx)
                self._listbox.see(next_idx)
            return 'break'

    def _on_arrow_up(self, event):
        if self._popup and self._popup.winfo_exists() and self._listbox:
            curr = self._listbox.curselection()
            prev_idx = (curr[0] - 1) if curr else (self._listbox.size() - 1)
            if prev_idx >= 0:
                self._listbox.selection_clear(0, 'end')
                self._listbox.selection_set(prev_idx)
                self._listbox.see(prev_idx)
            return 'break'

    def _on_return(self, event=None):
        if self._popup and self._popup.winfo_exists() and self._listbox:
            sel = self._listbox.curselection()
            if sel and 0 <= sel[0] < len(self._current_matches):
                chosen = self._current_matches[sel[0]]
                self._select_item(chosen)
                return 'break'
        self._close_popup()

    def _on_listbox_click(self, event=None):
        if self._listbox:
            sel = self._listbox.curselection()
            if sel and 0 <= sel[0] < len(self._current_matches):
                chosen = self._current_matches[sel[0]]
                self._select_item(chosen)

    def _select_item(self, text: str):
        self.entry.delete(0, 'end')
        self.entry.insert(0, text)
        self._close_popup()
        if self._on_select:
            try:
                self._on_select(text)
            except Exception:
                pass

    def get(self) -> str:
        return self.entry.get().strip()

    def set(self, text: str):
        self.entry.delete(0, 'end')
        if text:
            self.entry.insert(0, str(text))

    def delete(self, first, last=None):
        self.entry.delete(first, last)

    def insert(self, index, string):
        self.entry.insert(index, string)

    def configure(self, **kwargs):
        if 'placeholder_text' in kwargs:
            self.entry.configure(placeholder_text=kwargs.pop('placeholder_text'))
        if 'state' in kwargs:
            self.entry.configure(state=kwargs.pop('state'))
        if 'command' in kwargs:
            self._on_select = kwargs.pop('command')
        super().configure(**kwargs)


def make_autocomplete_entry(parent, values: list[str], placeholder='', width=220, on_select=None):
    return AutocompleteEntry(parent, placeholder=placeholder, width=width, completion_list=values, on_select=on_select)


def show_toast(parent, message: str, toast_type: str = 'success', duration: int = 2600):
    """
    Affiche une notification toast discrète, animée et non bloquante.
    """
    try:
        top = parent.winfo_toplevel()
        toast = ctk.CTkFrame(
            top,
            fg_color='#059669' if toast_type == 'success' else ('#004899' if toast_type == 'info' else ('#D97706' if toast_type == 'warning' else '#DC2626')),
            corner_radius=10,
            border_width=0
        )
        icon = '✅ ' if toast_type == 'success' else ('ℹ️ ' if toast_type == 'info' else ('⚠️ ' if toast_type == 'warning' else '❌ '))
        lbl = ctk.CTkLabel(
            toast,
            text=f"{icon}{message}",
            font=FONTS['body_bold'],
            text_color='white',
            padx=16,
            pady=10
        )
        lbl.pack()

        toast.place(relx=0.98, rely=0.04, anchor='ne')
        toast.tkraise()

        def _dismiss():
            try:
                toast.destroy()
            except Exception:
                pass

        top.after(duration, _dismiss)
    except Exception:
        pass


class StatusBarWidget(ctk.CTkFrame):
    """
    Barre de statut discrète en bas de la fenêtre principale.
    """
    def __init__(self, parent, user: str = 'Admin', role: str = 'admin'):
        super().__init__(parent, fg_color=COLORS['bg_card'], height=28, corner_radius=0, border_width=1, border_color=COLORS['border'])
        self.pack_propagate(False)

        # Gauche : Statut opérationnel
        self.lbl_status = ctk.CTkLabel(
            self,
            text="🟢 Prêt — Système opérationnel",
            font=FONTS['small'],
            text_color=COLORS['text_secondary']
        )
        self.lbl_status.pack(side='left', padx=16)

        # Droite : Utilisateur & Rôle
        self.lbl_user = ctk.CTkLabel(
            self,
            text=f"👤 {user} ({role.upper()})  •  SARL NOMADE AYRIS",
            font=FONTS['small_bold'],
            text_color=COLORS['primary']
        )
        self.lbl_user.pack(side='right', padx=16)

    def set_status(self, text: str, is_success: bool = True):
        icon = "🟢 " if is_success else "🟡 "
        self.lbl_status.configure(text=f"{icon}{text}")
        self.after(5000, lambda: self.lbl_status.configure(text="🟢 Prêt — Système opérationnel"))



def make_input(parent, placeholder='', width=220, textvariable=None):
    entry = ctk.CTkEntry(
        parent,
        placeholder_text=placeholder,
        fg_color=COLORS['bg_input'],
        border_color=COLORS['border'],
        border_width=1,
        text_color=COLORS['text_primary'],
        placeholder_text_color=COLORS['text_muted'],
        font=FONTS['body'],
        corner_radius=8,
        height=40,
        width=width,
        textvariable=textvariable,
    )
    entry.bind('<Tab>', lambda event: _focus_next_widget(event.widget))
    entry.bind('<Shift-Tab>', lambda event: _focus_prev_widget(event.widget))
    return entry


def _focus_next_widget(widget):
    """Navigate to next focusable widget with circular loop support"""
    try:
        root = widget.winfo_toplevel()
        current = widget
        max_iterations = 100
        iterations = 0
        
        while iterations < max_iterations:
            next_widget = current.tk_focusNext()
            if next_widget is None or next_widget == root:
                # Loop back to first widget
                next_widget = root.tk_focusNext()
            
            if next_widget == widget:
                # We've looped back to original widget, stop
                break
                
            # Check if widget is focusable (Entry, Button, Combobox)
            if hasattr(next_widget, 'focus_set'):
                widget_type = type(next_widget).__name__
                if widget_type in ['CTkEntry', 'CTkButton', 'CTkComboBox']:
                    next_widget.focus_set()
                    return 'break'
            
            current = next_widget
            iterations += 1
    except:
        pass
    return 'break'


def _focus_prev_widget(widget):
    """Navigate to previous focusable widget with circular loop support"""
    try:
        root = widget.winfo_toplevel()
        current = widget
        max_iterations = 100
        iterations = 0
        
        while iterations < max_iterations:
            prev_widget = current.tk_focusPrev()
            if prev_widget is None or prev_widget == root:
                # Loop back to last widget
                prev_widget = root.tk_focusPrev()
            
            if prev_widget == widget:
                # We've looped back to original widget, stop
                break
                
            # Check if widget is focusable (Entry, Button, Combobox)
            if hasattr(prev_widget, 'focus_set'):
                widget_type = type(prev_widget).__name__
                if widget_type in ['CTkEntry', 'CTkButton', 'CTkComboBox']:
                    prev_widget.focus_set()
                    return 'break'
            
            current = prev_widget
            iterations += 1
    except:
        pass
    return 'break'


def make_combobox(parent, values, width=220, variable=None):
    combo = ctk.CTkComboBox(
        parent,
        values=values,
        fg_color='#EBF4FF',
        border_color='#90C0F5',
        border_width=1,
        button_color='#1E6CC8',
        button_hover_color='#1557A6',
        dropdown_fg_color='#DEEEFF',
        dropdown_hover_color='#B8D9FA',
        dropdown_text_color='#0D2B5C',
        text_color=COLORS['text_primary'],
        font=FONTS['body'],
        corner_radius=8,
        width=width,
        height=40,
        variable=variable,
    )
    combo.bind('<Tab>', lambda event: _focus_next_widget(event.widget))
    combo.bind('<Shift-Tab>', lambda event: _focus_prev_widget(event.widget))
    return combo


def make_primary_button(parent, text, command=None, width=170, height=42):
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        fg_color=COLORS['primary'],
        hover_color=COLORS['primary_dark'],
        text_color=COLORS['text_white'],
        font=FONTS['body_bold'],
        corner_radius=10,
        width=width,
        height=height,
    )


def make_secondary_button(parent, text, command=None, width=170, height=42):
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        fg_color=COLORS['bg_hover'],
        hover_color=COLORS['border'],
        text_color=COLORS['text_primary'],
        border_color=COLORS['border'],
        border_width=1,
        font=FONTS['body_bold'],
        corner_radius=10,
        width=width,
        height=height,
    )


def make_danger_button(parent, text, command=None, width=170, height=42):
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        fg_color=COLORS['danger_bg'],
        hover_color=COLORS['danger'],
        text_color=COLORS['danger'],
        border_color=COLORS['danger'],
        border_width=1,
        font=FONTS['body_bold'],
        corner_radius=10,
        width=width,
        height=height,
    )


def bind_tree_clear_selection(tree, clear_callback=None):
    """
    Désélectionne la ligne active du Treeview lors d'un clic dans une zone vide du tableau.
    """
    def _on_click(event):
        row_id = tree.identify_row(event.y)
        if not row_id:
            tree.selection_remove(tree.selection())
            if clear_callback:
                clear_callback()
    tree.bind('<Button-1>', _on_click, add='+')


class DatePickerWidget(ctk.CTkFrame):
    """
    Champ de date interactif avec calendrier pop-up (tkcalendar).
    """

    def __init__(self, parent, placeholder='YYYY-MM-DD', width=180, default_value=''):
        super().__init__(parent, fg_color='transparent')
        self.grid_columnconfigure(0, weight=1)

        self.entry = make_input(self, placeholder=placeholder, width=width - 44)
        self.entry.grid(row=0, column=0, sticky='ew', padx=(0, 4))
        if default_value:
            self.entry.insert(0, default_value)

        self.btn_cal = ctk.CTkButton(
            self,
            text='📅',
            width=36,
            height=40,
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_dark'],
            text_color='white',
            font=('Segoe UI Emoji', 15),
            corner_radius=8,
            command=self._open_calendar
        )
        self.btn_cal.grid(row=0, column=1, sticky='e')

    def _open_calendar(self):
        try:
            import tkcalendar
            from datetime import datetime

            top = ctk.CTkToplevel(self)
            top.title("Sélectionner une date")
            top.geometry("320x300")
            top.resizable(False, False)
            top.transient(self.winfo_toplevel())
            top.grab_set()

            # Date initiale
            val = self.entry.get().strip()
            try:
                dt = datetime.strptime(val, '%Y-%m-%d')
                year, month, day = dt.year, dt.month, dt.day
            except Exception:
                now = datetime.now()
                year, month, day = now.year, now.month, now.day

            cal = tkcalendar.Calendar(
                top,
                selectmode='day',
                year=year,
                month=month,
                day=day,
                date_pattern='yyyy-mm-dd',
                background='#0B2E6B',
                foreground='white',
                headersbackground='#004899',
                headersforeground='white',
                selectbackground='#0096D6',
                selectforeground='white',
                normalbackground='white',
                normalforeground='#0F172A',
                weekendbackground='#F1F5F9',
                weekendforeground='#0F172A'
            )
            cal.pack(padx=16, pady=16, fill='both', expand=True)

            def _confirm():
                selected = cal.get_date()
                self.entry.delete(0, 'end')
                self.entry.insert(0, selected)
                top.destroy()

            btn_ok = ctk.CTkButton(
                top, text='Valider la date', command=_confirm,
                fg_color=COLORS['primary'], hover_color=COLORS['primary_dark'],
                font=FONTS['body_bold'], height=36, corner_radius=8
            )
            btn_ok.pack(pady=(0, 12))

        except Exception as e:
            pass

    def get(self) -> str:
        return self.entry.get().strip()

    def set(self, value: str):
        self.entry.delete(0, 'end')
        if value:
            self.entry.insert(0, str(value))

    def delete(self, first, last=None):
        self.entry.delete(first, last)

    def insert(self, index, string):
        self.entry.insert(index, string)


class CircularProgressWidget(ctk.CTkFrame):
    """
    Cercle relatif dynamique (Donut chart premium) sur Canvas Tkinter.
    """

    def __init__(self, parent, size=220, bg_color='#FFFFFF', **kwargs):
        super().__init__(parent, fg_color=bg_color, corner_radius=16, **kwargs)
        self.size = size
        self.bg_color = bg_color

        import tkinter as tk
        self.canvas = tk.Canvas(
            self, width=size, height=size,
            bg=bg_color, highlightthickness=0, bd=0
        )
        self.canvas.pack(expand=True, pady=10)

    def set_data(self, segments: list[tuple[float, str, str]], center_value: str, center_label: str):
        """
        segments: [(pourcentage, couleur, nom_segment), ...]
        center_value: Texte central (ex: '87%')
        center_label: Sous-titre central (ex: 'Santé Stock')
        """
        self.canvas.delete('all')

        cx, cy = self.size / 2, self.size / 2
        r_outer = (self.size / 2) - 16
        r_inner = r_outer - 28

        # Fond de cercle neutre
        self.canvas.create_oval(
            cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer,
            fill='#E2E8F0', outline=''
        )

        total_pct = sum(s[0] for s in segments)
        if total_pct <= 0:
            total_pct = 1.0

        start_angle = 90.0
        for pct, color, label in segments:
            extent = - (pct / total_pct) * 360.0
            if abs(extent) > 0.1:
                self.canvas.create_arc(
                    cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer,
                    start=start_angle, extent=extent,
                    fill=color, outline='', style='pieslice'
                )
                start_angle += extent

        # Trou central (Donut)
        self.canvas.create_oval(
            cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner,
            fill=self.bg_color, outline=''
        )

        # Texte central
        self.canvas.create_text(
            cx, cy - 8,
            text=center_value,
            font=('Segoe UI', 24, 'bold'),
            fill='#0B2E6B'
        )
        self.canvas.create_text(
            cx, cy + 18,
            text=center_label,
            font=('Segoe UI', 10, 'bold'),
            fill='#64748B'
        )


class MultiSelectCombobox(ctk.CTkFrame):
    """
    Combobox à sélection multiple avec cases à cocher.
    """
    def __init__(self, parent, options: list[str], width=200, command=None, default_all=True):
        super().__init__(parent, fg_color='transparent')
        import tkinter as tk
        self.options = [opt for opt in options if opt.lower() != 'tous']
        self.command = command
        self._selected_map = {opt: True if default_all else False for opt in self.options}

        self.btn = ctk.CTkButton(
            self,
            text=self._format_display_text(),
            width=width,
            height=40,
            fg_color='#EBF4FF',
            hover_color='#D0E4FF',
            border_color='#90C0F5',
            border_width=1,
            text_color=COLORS['text_primary'],
            font=FONTS['body'],
            corner_radius=8,
            anchor='w',
            command=self._open_popup
        )
        self.btn.pack(fill='x', expand=True)

    def _format_display_text(self) -> str:
        selected = [opt for opt, is_sel in self._selected_map.items() if is_sel]
        if not selected or len(selected) == len(self.options):
            return "Tous"
        return ", ".join(selected)

    def update_options(self, options: list[str]):
        new_opts = [opt for opt in options if opt.lower() != 'tous']
        curr_selected = set(self.get_selected())
        self.options = new_opts
        self._selected_map = {opt: (opt in curr_selected if curr_selected else True) for opt in self.options}
        self.btn.configure(text=self._format_display_text())

    def _open_popup(self):
        import tkinter as tk
        top = ctk.CTkToplevel(self)
        top.title("Sélectionner")
        top.geometry("260x280")
        top.resizable(False, False)
        top.transient(self.winfo_toplevel())
        top.grab_set()
        # Fond blanc, texte noir
        top.configure(fg_color='#FFFFFF')

        try:
            top.update_idletasks()
            bx = self.winfo_rootx()
            by = self.winfo_rooty() + self.winfo_height() + 4
            top.geometry(f"+{bx}+{by}")
        except Exception:
            pass

        scroll = ctk.CTkScrollableFrame(top, fg_color='#FFFFFF', scrollbar_button_color='#CBD5E1', scrollbar_button_hover_color='#94A3B8')
        scroll.pack(fill='both', expand=True, padx=8, pady=(8, 4))

        var_all = tk.BooleanVar(value=all(self._selected_map.values()))
        chk_vars = {}

        def _toggle_all():
            val = var_all.get()
            for opt, v in chk_vars.items():
                v.set(val)
                self._selected_map[opt] = val
            self._update_display()

        cb_all = ctk.CTkCheckBox(
            scroll, text="Tout sélectionner / Vider", variable=var_all,
            command=_toggle_all, font=FONTS['body_bold'],
            text_color=COLORS['primary'],
            fg_color=COLORS['primary'], hover_color=COLORS['primary_dark'],
            checkmark_color='#FFFFFF'
        )
        cb_all.pack(anchor='w', pady=4, padx=4)
        ctk.CTkFrame(scroll, fg_color='#CBD5E1', height=1).pack(fill='x', pady=4)

        def _on_item_toggle(opt):
            self._selected_map[opt] = chk_vars[opt].get()
            var_all.set(all(self._selected_map.values()))
            self._update_display()

        for opt in self.options:
            v = tk.BooleanVar(value=self._selected_map.get(opt, True))
            chk_vars[opt] = v
            cb = ctk.CTkCheckBox(
                scroll, text=opt, variable=v,
                command=lambda o=opt: _on_item_toggle(o),
                font=FONTS['body'],
                text_color='#0F172A',
                fg_color=COLORS['primary'], hover_color=COLORS['primary_dark'],
                checkmark_color='#FFFFFF'
            )
            cb.pack(anchor='w', pady=4, padx=4)

        btn_ok = ctk.CTkButton(
            top, text="Valider", command=top.destroy,
            fg_color=COLORS['primary'], hover_color=COLORS['primary_dark'],
            text_color='#FFFFFF', height=32, corner_radius=6
        )
        btn_ok.pack(pady=(4, 8))

    def _update_display(self):
        text = self._format_display_text()
        self.btn.configure(text=text)
        if self.command:
            try:
                self.command(text)
            except Exception:
                pass

    def get_selected(self) -> list[str]:
        selected = [opt for opt, is_sel in self._selected_map.items() if is_sel]
        if not selected or len(selected) == len(self.options):
            return ['Tous']
        return selected

    def get(self) -> str:
        sel = self.get_selected()
        return "Tous" if sel == ['Tous'] else ", ".join(sel)

    def set_selected(self, values: list[str] | str):
        if isinstance(values, str):
            if values.lower() in ('tous', 'toutes', ''):
                values = list(self.options)
            else:
                values = [v.strip() for v in values.split(',')]
        val_set = set(v.lower() for v in values)
        for opt in self.options:
            self._selected_map[opt] = (opt.lower() in val_set or 'tous' in val_set)
        self.btn.configure(text=self._format_display_text())

