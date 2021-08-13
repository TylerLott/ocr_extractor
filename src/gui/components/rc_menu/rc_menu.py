"""
This module contains the right click menu for the treeview
"""
from tkinter import Menu


class RightClickMenu(Menu):
    """
    Right Click Menu for the treeview

    ** this should be refactored to either be more general and combined with
       the right click menu for the viewport, or just added to treeview

    Methods:
        + do_popup          = shows the menu at the mouse tip

    Attributes:
        + master
        + selection
        + column

    """

    def __init__(self, master):
        Menu.__init__(self, master, tearoff=0)
        self.master = master
        self.selection, self.column = None, None
        master.bind("<Button-3>", self.do_popup)

    def do_popup(self, event):
        # display the popup menu
        try:
            self.selection = self.master.identify_row(event.y)
            self.master.selection_set(self.selection)
            self.column = self.master.identify_column(event.x)
            self.post(event.x_root, event.y_root)
        finally:
            # make sure to release the grab (Tk 8.0a1 only)
            self.grab_release()
