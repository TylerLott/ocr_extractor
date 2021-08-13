"""

"""
from tkinter import TclError, Entry
from tkinter.ttk import Treeview


class EntryPopup(Entry):
    def __init__(self, parent: Treeview, iid: str, text: str, debug=False, **kw):
        self.debug = debug
        """If relwidth is set, then width is ignored"""
        super().__init__(parent, **kw)
        self.parent = parent
        self.iid = iid

        self.insert(0, text)
        # self['state'] = 'readonly'
        # self['readonlybackground'] = 'white'
        self["selectbackground"] = "#1BA1E2"
        self["exportselection"] = False

        self.focus_force()
        self.__select_all()
        self.bind("<Return>", self.__on_return)
        self.parent.bind("<Button-1>", self.__on_return)
        self.bind("<Control-a>", self.__select_all)
        self.bind("<Escape>", lambda *ignore: self.destroy())

    def __on_return(self, _) -> None:
        try:
            self.parent.item(self.iid, text=self.get())
            tags = self.parent.item(self.iid, "tags")
            self.parent.item(self.iid, tags=(tags[0], self.get(), ""))
        except TclError as e:
            # occurs when click outside of item
            if self.debug:
                print(f"error in EntryPopup - __on_return \n{e}")
        finally:
            self.destroy()

    def __select_all(self, *_) -> str:
        """Set selection on the whole text"""
        self.selection_range(0, "end")

        # returns 'break' to interrupt default key-bindings
        return "break"
