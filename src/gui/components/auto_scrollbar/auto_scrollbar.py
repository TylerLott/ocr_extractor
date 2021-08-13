"""
This module is a scrollbar that appears only when needed
"""
from tkinter import TclError
from tkinter.ttk import Scrollbar


class AutoScrollbar(Scrollbar):
    """A scrollbar that hides itself if it's not needed. Works only for grid geometry manager"""

    def set(self, first, last):
        if float(first) <= 0.0 and float(last) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
            Scrollbar.set(self, first, last)

    def pack(self, **kw):
        """Dont use pack"""
        raise TclError("Cannot use pack with the widget " + self.__class__.__name__)

    def place(self, **kw):
        """Dont use place"""
        raise TclError("Cannot use place with the widget " + self.__class__.__name__)
