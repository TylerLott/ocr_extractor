"""
This was adapted from code found on stackoverflow
https://stackoverflow.com/questions/59696557/tkinter-button-different-commands-on-right-and-left-mouse-click
It is pretty heavily modified however
"""

from tkinter import Frame, Menu, Variable
import numpy as np
from data_manager.data_manager import DataWriter, DataReader
from extractor.extractor import TableExtractor
from gui.components.label_frame.label_frame import LabelFrame
from .canvas_image.canvas_image import CanvasImage


class DrawingViewport(Frame):
    """
    Viewport in middle of UI, allows for pan, zoom, and highlight box

    ** should be refactored to not have to load in the whole img array

    Methods:
        + show_imgs            = shows the drawing that is passed to it
        - make_menu            = make right click menu
        - right_click_popup    = create the menu popup
        - rotate_clock         = rotate image clockwise and save new image
        - rotate_counter       = rotate image counterclockwise and save new image
        - next_pg              = switch viewport image to the next in the drawing
        - prev_pg              = switch viewport image to the previous in the drawing

    Attributes:
        + debug
        + images
        + img_names
        + drawing_id
        - data_manager
        - view_frame
        - control_frame
        - canvas
        - drop_menu

    """

    def __init__(
        self,
        master: Frame,
        path,
        data_writer: DataWriter,
        data_reader: DataReader,
        extractor: TableExtractor,
        debug=False,
    ):
        self.debug = debug

        """Initialize the main Frame"""
        Frame.__init__(self, master)

        # Define Variables
        self.__data_writer = data_writer  # fix this from writing
        self.__data_reader = data_reader
        self.image = None
        self.drawing_id = ""
        self.cur_pg = Variable(value=1)
        self.cur_pg.trace_add("write", self.__change_page)
        self.total_pg = Variable(value=1)

        # Define Frames
        self.__view_frame = Frame(self)
        self.__control_frame = LabelFrame(self, "Drawing XXX-XXX", viewport=True)

        # Configure control buttons
        self.__control_frame.next_btn.configure(command=self.__next_pg)
        self.__control_frame.prev_btn.configure(command=self.__prev_pg)

        # Configure Frames
        self.__view_frame.rowconfigure(0, weight=1)
        self.__view_frame.columnconfigure(0, weight=1)
        self.__canvas = CanvasImage(self.__view_frame, path, extractor)  # create widget
        self.__canvas.grid(row=0, column=0)

        # Pack Frames
        self.__view_frame.pack(side="bottom", fill="both", expand=True)
        self.__control_frame.pack(side="top", fill="x")

        self.__make_menu()

    def show_imgs(self, drawing_id: str, drawing_name: str):
        self.drawing_id = drawing_id
        self.__control_frame.label_text.set(value="Drawing " + drawing_name)
        self.cur_pg.set(value=1)

    def __change_page(self, *_):
        self.image, total_imgs = self.__data_reader.get_img(
            self.drawing_id, self.cur_pg.get()
        )
        if total_imgs != self.total_pg.get():
            self.total_pg.set(value=total_imgs)
        self.__canvas.refresh_img(self.image)

    def __make_menu(self):
        self.__drop_menu = Menu(self.__view_frame, tearoff=0)
        self.__drop_menu.add_command(
            label="Rotate Clockwise", command=self.__rotate_clock
        )
        self.__drop_menu.add_command(
            label="Rotate Counter Clockwise", command=self.__rotate_counter
        )
        self.__canvas.canvas.bind("<Button-3>", self.__right_click_popup)

    def __right_click_popup(self, event):
        try:
            self.__drop_menu.post(event.x_root, event.y_root)
        finally:
            self.__drop_menu.grab_release()

    def __rotate_clock(self):
        self.image = np.rot90(self.image, 3)
        self.__canvas.refresh_img(self.image)
        self.__data_writer.insert_image(
            self.drawing_id, self.drawing_id + f"-{self.cur_pg.get()}", self.image
        )

    def __rotate_counter(self):
        self.image = np.rot90(self.image)
        self.__canvas.refresh_img(self.image)
        self.__data_writer.insert_image(
            self.drawing_id, self.drawing_id + f"-{self.cur_pg.get()}", self.image
        )

    def __next_pg(self):
        pg = self.cur_pg.get()
        if pg < self.total_pg.get():
            self.cur_pg.set(pg + 1)
            # self.__canvas.refresh_img(self.images[pg - 1])

    def __prev_pg(self):
        pg = self.cur_pg.get()
        if pg > 1:
            self.cur_pg.set(pg - 1)
            # self.__canvas.refresh_img(self.images[pg - 1])
