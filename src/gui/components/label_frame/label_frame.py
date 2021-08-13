"""
This module contains the upper labels for the different sections
"""
from tkinter import Frame, Label, PhotoImage, Button, StringVar


class LabelFrame(Frame):
    """
    Two types of labels - viewport (with buttons and page number) and label
    which is just the section label

    ** this should probably be refactored into two subclasses of a main
       LabelFrame class

    Methods:
        + make_label          = creates label for label type
        + make_viewport       = creates all components for viewport type
        - refresh_pg          = refreshes the viewport page
        - refresh_label       = refreshed the label text

    Attributes:
        + label_text
        - label_bg
        - label_fg
        - is_viewport



    """

    def __init__(self, master, text, viewport=False):
        self.__label_bg = "black"
        self.__label_fg = "white"
        self.__is_viewport = viewport
        self.master = master

        Frame.__init__(self, master, bg=self.__label_bg)

        self.label_text = StringVar(value=text)
        self.label_text.trace_add("write", self.__refresh_label)

        if viewport:
            self.master.cur_pg.trace_add("write", self.__refresh_pg)
            self.master.total_pg.trace_add("write", self.__refresh_pg)
            self.make_viewport_label()
        else:
            self.make_label()

    def make_label(self):
        self.label = Label(
            self,
            text=self.label_text.get(),
            bg=self.__label_bg,
            fg=self.__label_fg,
            font=("Arial", 20, "bold"),
            pady=22,
        )
        self.label.pack()

    def make_viewport_label(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.label = Label(
            self,
            text=self.label_text.get(),
            bg=self.__label_bg,
            fg=self.__label_fg,
            font=("Arial", 20, "bold"),
        )
        self.pg = Label(
            self,
            text=f"Pg. {self.master.cur_pg.get()} of {self.master.total_pg.get()}",
            bg=self.__label_bg,
            fg=self.__label_fg,
        )
        next_img = PhotoImage(file="data/images/next.png")
        self.next_btn = Button(
            self,
            image=next_img,
            bg=self.__label_bg,
            fg=self.__label_bg,
            borderwidth=0,
        )
        self.next_btn.image = next_img
        prev_img = PhotoImage(file="data/images/prev.png")
        self.prev_btn = Button(
            self,
            image=prev_img,
            bg=self.__label_bg,
            fg=self.__label_bg,
            borderwidth=0,
        )
        self.prev_btn.image = prev_img

        self.label.grid(row=0, column=0, columnspan=3, pady=(10, 0))
        self.next_btn.grid(row=0, column=2, rowspan=2)
        self.pg.grid(row=1, column=1, pady=(0, 10))
        self.prev_btn.grid(row=0, column=0, rowspan=2)

    def __refresh_pg(self, *_):
        self.pg.grid_forget()
        self.pg.configure(
            text=f"Pg. {self.master.cur_pg.get()} of {self.master.total_pg.get()}"
        )
        self.pg.grid(row=1, column=1, pady=(0, 10))

    def __refresh_label(self, *_):
        if self.__is_viewport:
            self.label.grid_forget()
            self.label.configure(text=self.label_text.get())
            self.label.grid(row=0, column=0, columnspan=3, pady=(10, 0))
        else:
            self.label.pack_forget()
            self.label.configure(text=self.label_text.get())
            self.label.pack()
