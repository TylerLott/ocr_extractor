"""
This is the table that is used in the main part table
"""
from tkinter import Entry, Frame


class Table(Frame):
    """
    Main table structure for the parts information section

    Methods:
        + add_entry          = add an entry with no label
        + remove_entry       = remove entry with no label
        + remove_last        = remove the last row of table
        + add_item           = add an entry with a label
        - unrender           = remove table from view
        - render             = show table

    Attributes:
        + rows
        + row


    """

    def __init__(self, master, debug=False):
        self.debug = debug
        Frame.__init__(self, master)
        self.columnconfigure(1, weight=1)
        self.rows = []
        self.row = 1

    def add_entry(self):
        """add entry with no label"""
        entry = Entry(self)
        self.rows.append(entry)
        self.__unrender()
        self.__render()

    def remove_entry(self, ind):
        """remove specified entry by index"""
        self.__unrender()
        try:
            self.rows.pop(ind)
        except IndexError as e:
            if self.debug:
                print(f"error in Table - remove_entry \n{e}")
        self.__render()

    def remove_last(self):
        """remove last item of table"""
        self.remove_entry(-1)

    def add_item(self, title):
        """add item with label"""
        label = Entry(self, width=23, font=("Arial", 10), justify="center")
        label.insert(0, title)
        label.configure(state="disabled")
        entry = Entry(self)

        label.grid(row=self.row, column=0, padx=(10, 0), sticky="nsew")
        entry.grid(row=self.row, column=1, padx=(0, 10), sticky="nsew")
        self.rows.append(entry)
        self.row += 1

    def __unrender(self):
        for i in self.rows:
            i.grid_forget()

    def __render(self):
        index = 0
        for entry in self.rows:
            entry.grid(row=index, column=0, columnspan=2, padx=10, stick="nsew")
            index += 1
