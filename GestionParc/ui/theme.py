COLORS = {
    'bg_darkest': '#F1F5F9',
    'bg_dark': '#F8FAFC',
    'bg_card': '#FFFFFF',
    'bg_sidebar': '#0B2E6B',
    'bg_hover': '#F1F5F9',
    'bg_input': '#FFFFFF',
    'bg_selected': '#004899',
    'primary': '#004899',
    'primary_dark': '#003366',
    'primary_light': '#0074D9',
    'accent': '#0096D6',
    'accent_light': '#00B5EC',
    'success': '#059669',
    'success_bg': '#D1FAE5',
    'warning': '#D97706',
    'warning_bg': '#FEF3C7',
    'danger': '#DC2626',
    'danger_bg': '#FEE2E2',
    'info': '#0096D6',
    'text_primary': '#0F172A',
    'text_secondary': '#475569',
    'text_muted': '#94A3B8',
    'text_white': '#FFFFFF',
    'border': '#CBD5E1',
    'border_light': '#E2E8F0',
    'sidebar_text': '#CBD5E1',
    'sidebar_text_active': '#FFFFFF',
    'sidebar_active_bg': '#004899',
    'sidebar_icon': '#00B5EC',
}

FONTS = {
    'title_large': ('Segoe UI', 22, 'bold'),
    'title': ('Segoe UI', 18, 'bold'),
    'subtitle': ('Segoe UI', 15, 'bold'),
    'body': ('Segoe UI', 13),
    'body_bold': ('Segoe UI', 13, 'bold'),
    'small': ('Segoe UI', 11),
    'small_bold': ('Segoe UI', 11, 'bold'),
    'mono': ('Consolas', 12, 'bold'),
    'icon': ('Segoe UI Emoji', 16),
}

SIDEBAR_ITEMS = [
    {'key': 'dashboard', 'icon': '📊', 'label': 'Dashboard'},
    {'key': 'engins', 'icon': '🚜', 'label': 'Engins'},
    {'key': 'pieces', 'icon': '🔧', 'label': 'Pièces'},
    {'key': 'prix', 'icon': '💰', 'label': 'Prix'},
    {'key': 'bon_livraison', 'icon': '📥', 'label': 'Bon de livraison'},
    {'key': 'bon_sortie', 'icon': '📤', 'label': 'Bon de sortie'},
    {'key': 'options', 'icon': '⚙️', 'label': 'Configuration'},
]

FAMILLES_PIECES = ['CARROSSERIE', 'MOTEUR', 'TRANSMISSION', 'FREINAGE', 'ELECTRIQUE', 'SUSPENSION']
UNITES = ['JEUX', 'UNITE', 'LITRE']
CATEGORIES_ENGINS = ['CLARCK', 'CAMION', 'VEHICULE_LEGER']


def format_money(value, currency='DZD'):
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return f'0 {currency}'
    return f'{amount:,.2f} {currency}'
