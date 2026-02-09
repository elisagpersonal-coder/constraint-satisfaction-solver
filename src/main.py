import os.path

from PySide6.QtWidgets import QApplication
from argparse import ArgumentParser
from gui import SolverWindow
from pathlib import Path
import sys


def _main() -> int:
    """
    Parses the CLI arguments and runs the GUI.

    :return: The exit status of the GUI
    """

    parser = ArgumentParser()
    parser.add_argument("--file", "-f",
                        help="CSV-formatted file containing the system to input into the "
                             "application",
                        type=Path,
                        required=False)

    args = parser.parse_args()
    table_path = args.file if args.file and args.file.exists() else None
    icon_file = "matrix.ico"

    if getattr(sys, "frozen", False):
        icon_path = os.path.join(sys._MEIPASS, icon_file)
    else:
        this_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(this_dir, "resources", icon_file)

    app = QApplication()
    window = SolverWindow(table_path=table_path, icon_path=icon_path)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(_main())