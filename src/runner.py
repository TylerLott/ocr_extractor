"""
This module is the main application entry point
"""
import sys
import os
path = sys.argv[0].split("\\")[:-1]
os.chdir("\\".join(path))
from gui.gui import GUI


def run_app(argv):
    """RUN!!!"""
    app = GUI(debug=True)
    if len(argv) > 1 and ".bci" in argv[1]:
        app.run_file(argv[1])
    else:
        app.run()


run_app(sys.argv)
