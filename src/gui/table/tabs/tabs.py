"""
This module is the tab classes for the main parts table
"""
from tkinter import Frame, Label
from typing import List
from gui.components.table.table import Table


class InputTab(Frame):
    """
    Parent class to all tabs

    Methods:
        + get_info             = gets information for specified part from file
        + set_info             = sets information for specified part from file

    Attributes:
        + items
        - table

    """

    def __init__(self, master: Frame, title: str, items: List[str], debug=False):
        self.debug = debug
        Frame.__init__(self, master)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.items = items

        header = Label(
            self,
            text=title,
            fg="#202020",
            font=("Arial", 16),
            pady=20,
            padx=10,
        )

        self.__table = Table(self, debug=self.debug)

        for i in self.items:
            self.__table.add_item(i)

        self.__table.grid(row=1, column=0, columnspan=2, sticky="nsew")
        header.grid(row=0, column=0, columnspan=2, sticky="nw")

    def get_info(self) -> dict:
        """returns information that is filled in in the table"""
        info = {}
        for i, e in enumerate(self.__table.rows):
            info[self.items[i]] = e.get()
        return info

    def set_info(self, data: List):
        """sets the information into the table when passed a list of shape (('field', 'data'), )"""
        try:
            for i in data:
                try:
                    ind = self.items.index(i[0])
                    self.__table.rows[ind].delete(0, "end")
                    self.__table.rows[ind].insert(0, i[1])
                except ValueError as e:
                    pass  # this fails silently it failes every time intentionally, needs refactor
        except TypeError as e:
            if self.debug:
                print(f"error in Infotab - set_info \n{e}")


class DrawingInfoTab(InputTab):
    """Drawing information"""

    def __init__(self, master: Frame, debug=False):
        InputTab.__init__(
            self,
            master,
            "Drawing Information",
            [
                "Description",
                "CAGE Code",
                "Qty",
                "Flag Notes",
                "Drawing",
                "Sheet No",
                "DWG Rev",
                "EO Numbers",
                "ESDS",
                "HCI",
            ],
            debug,
        )


class MaterialTab(InputTab):
    """Material Information"""

    def __init__(self, master: Frame, debug=False):
        InputTab.__init__(
            self,
            master,
            "Material Information",
            ["Material", "Material Spec", "Type", "Class", "Grade", "Notes"],
            debug,
        )


class PlatingTab(InputTab):
    """Plating Information"""

    def __init__(self, master: Frame, debug=False):
        InputTab.__init__(
            self,
            master,
            "Plating Information",
            ["Plating", "Plating Spec", "Type", "Class", "Grade", "Notes"],
            debug,
        )


class PrimerTab(InputTab):
    """Primer Information"""

    def __init__(self, master: Frame, debug=False):
        InputTab.__init__(
            self,
            master,
            "Primer Information",
            ["Primer", "Primer Spec", "Type", "Class", "Grade", "Notes"],
            debug,
        )


class PaintTab(InputTab):
    """Paint Information"""

    def __init__(self, master: Frame, debug=False):
        InputTab.__init__(
            self,
            master,
            "Paint Information",
            ["Paint Spec", "Color", "Type", "Notes"],
            debug,
        )


class MiscTab(InputTab):
    """Misc Information"""

    def __init__(self, master: Frame, debug=False):
        InputTab.__init__(
            self,
            master,
            "Miscellaneous Information",
            [
                "Welding (Y/N)",
                "Heat Treatment (Y/N)",
                "F-Code",
                "Surface Finish/Roughness",
                "Other Comments",
            ],
            debug,
        )
