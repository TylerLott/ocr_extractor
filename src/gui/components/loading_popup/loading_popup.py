"""
This module is a popup window which displays a loading bar
"""
from tkinter import Label, Toplevel
from tkinter.ttk import Progressbar
from PIL import ImageTk


class LoadingPopup(Toplevel):
    """
    This is the loading bar popup

    Methods:
        + change_progress       = set the amount loaded in the progress bar

    Attributes:
        - progress

    """

    def __init__(
        self,
        master,
        title="Uploading",
        desc="Uploading...",
        background="black",
        text_color="white",
    ):
        Toplevel.__init__(self, master)
        self.grab_set()
        self.__master = master
        self.title(title)
        x = int(master.winfo_screenwidth() / 2 - 125)
        y = int(master.winfo_screenheight() / 2 - 50)
        self.geometry(f"250x100+{x}+{y}")
        icon = ImageTk.PhotoImage(file="data/images/NG.jpg")
        self.iconphoto(False, icon)
        self.config(bg=background)
        self.__progress = Progressbar(self, orient="horizontal", length=200)
        label = Label(self, text=desc, fg=text_color, bg=background)
        self.__progress.pack(side="bottom", pady=(0, 20))
        label.pack(side="top", pady=(20, 0))
        self.__master.update_idletasks()

    def change_progress(self, percent):
        """give the progress bar a percentage complete to show"""
        self.__progress["value"] = percent
        self.__master.update_idletasks()
        if percent == 100:
            self.grab_release()
            self.destroy()
