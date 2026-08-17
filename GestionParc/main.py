import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.login_window import LoginWindow
from ui.main_window import MainWindow


def main():
    login = LoginWindow()
    login.mainloop()
    if not getattr(login, 'authenticated', False):
        return
    app = MainWindow()
    app.mainloop()


if __name__ == '__main__':
    main()
