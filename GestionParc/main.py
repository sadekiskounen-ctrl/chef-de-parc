import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.db_manager import initialize_database, ensure_demo_data, repair_stock_from_bons_reception
from ui.login_window import LoginWindow
from ui.main_window import MainWindow


def main():
    # Initialisation de la base + réparation des données historiques
    initialize_database()
    ensure_demo_data()
    repair_stock_from_bons_reception()  # Crée les pièces manquantes depuis les bons de réception

    login = LoginWindow()
    login.mainloop()
    if not getattr(login, 'authenticated', False):
        return
    app = MainWindow()
    app.mainloop()


if __name__ == '__main__':
    main()
