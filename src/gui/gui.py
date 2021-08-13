"""
This module in the main entry point for the drawing tree application
"""
from tkinter import Button, PhotoImage, Tk, Frame, Label
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.ttk import PanedWindow, Style
from random import randint
from PIL import ImageTk
from h5py import File
import cv2

from data_manager.data_manager import DataWriter, DataReader
from gui.components.loading_popup.loading_popup import LoadingPopup
from extractor.extractor import TableExtractor
from .treeview.treeview import DrawingTreeview
from .viewport.viewport import DrawingViewport
from .table.table import DrawingTable
from .app_menu.app_menu import AppMenu


class GUI:
    """
    Main user interface
        Facilitates information passing through the three main sections
            - Drawing Tree
            - Drawing Viewport
            - Drawing Table

    ** This needs to be refactored to simplify - has too many instance attributes

    Methods:
        + run                       = runs application with no starter file given
        + run_file                  = runs application with file given from command line
        + save_file                 = saves the current tree and table
        - on_closing                = makes sure the application exits correctly
        - initialize_dashboard      = creates the main application dashboard and all widgets
        - render_dashboard          = pulls data from treeview and updates the table and viewport
                                      as needed
        - render_entry              = renders the application entry if no file given,
                                      asks user to open or create a file
        - set_style                 = sets the application style and styles the paned window view

    Attributes:
        + debug
        + root
        + drawing_img
        + part_info
        + filename
        - loading
        - entry_frame
        - data_reader
        - data_writer
        - main_pw
        - tree_pane
        - drawing_pane
        - table_pane
        - drawing_browser
        - drawing_viewport
        - drawing_table

    """

    def __init__(self, debug=False):
        self.debug = debug
        self.root = Tk()
        self.root.geometry("400x200+500+300")

        # Loading Label
        self.__loading = Label(
            self.root,
            text="Loading...",
            font=("Arial", 20, "bold"),
            fg="white",
            bg="black",
            pady=20,
            padx=20,
        )
        self.__loading.pack(fill="both", expand=True)

        # Title
        self.root.title("BCI Drawing Tree Tool")

        # Styling
        self.__set_style()

        # App entry frame
        self.__entry_frame = Frame(self.root, bg="black")

        # Define Variables
        self.__extractor = TableExtractor(self.root)
        self.__extractor.data.trace_add("write", self.__add_ocr_items)
        self.__data_writer = None
        self.__data_reader = None
        self.__main_pw = None
        self.__tree_pane = None
        self.__drawing_pane = None
        self.__table_pane = None
        self.__drawing_browser = None
        self.__drawing_viewport = None
        self.__drawing_table = None
        self.drawing_img = cv2.imread(r"data\images\new_img.png", 0)
        self.part_info = None
        self.filename = None

    def run(self):
        """Run the application with no file given in command line"""
        self.__render_entry()
        self.root.mainloop()

    def run_file(self, file: str):
        """Run file directly from command line file entry"""
        self.filename = file
        self.__loading.pack(fill="both", expand=True)
        self.__initialize_dashboard()
        self.__loading.pack_forget()
        self.root.mainloop()

    def save_file(self):
        """save the current data from treeview and table"""
        loading = LoadingPopup(self.root, title="testing", desc="this is for testing")
        tree_data, tree_deleted = self.__drawing_browser.get_parts()
        loading.change_progress(randint(10, 40))
        self.__data_writer.save_drawings(tree_data, tree_deleted)
        loading.change_progress(randint(50, 90))
        self.__drawing_table.save_data()
        loading.change_progress(100)

    def open_file(self):
        """open file when there is already one open"""
        self.save_file()
        self.__set_open_file()

    def new_file(self):
        """create new file when other file is already open"""
        self.save_file()
        self.__set_new_file()

    def __unrender_all(self):
        self.__main_pw.pack_forget()
        self.__main_pw.remove(self.__tree_pane)
        self.__main_pw.remove(self.__drawing_pane)
        self.__main_pw.remove(self.__table_pane)
        self.__tree_pane.remove(self.__drawing_browser)
        self.__drawing_pane.remove(self.__drawing_viewport)
        self.__table_pane.remove(self.__drawing_table)
        self.__drawing_browser.pack_forget()
        self.__drawing_viewport.pack_forget()
        self.__drawing_table.pack_forget()

    def __on_closing(self):
        """exit app cleanly"""
        self.root.destroy()

    def __initialize_dashboard(self):
        self.root.title(f"BCI Drawing Tree Tool    -    {self.filename.split('/')[-1]}")
        # Define adjustable window areas
        self.__data_writer = DataWriter(self.filename, debug=self.debug)
        self.__data_reader = DataReader(self.filename, debug=self.debug)
        self.__main_pw = PanedWindow(orient="horizontal")
        self.__tree_pane = PanedWindow(self.__main_pw, orient="horizontal", width=300)
        self.__drawing_pane = PanedWindow(
            self.__main_pw, orient="horizontal", width=850
        )
        self.__table_pane = PanedWindow(self.__main_pw, orient="horizontal", width=400)

        # Define Elements
        self.__drawing_browser = DrawingTreeview(
            self.__tree_pane, self.__data_reader, debug=self.debug
        )
        self.__drawing_viewport = DrawingViewport(
            self.__drawing_pane,
            self.drawing_img,
            self.__data_writer,
            self.__data_reader,
            self.__extractor,
            debug=self.debug,
        )
        self.__drawing_table = DrawingTable(
            self.__table_pane, self.__data_writer, debug=self.debug
        )

        self.__main_pw.add(self.__tree_pane)
        self.__main_pw.add(self.__drawing_pane)
        self.__main_pw.add(self.__table_pane)
        self.__tree_pane.add(self.__drawing_browser)
        self.__drawing_pane.add(self.__drawing_viewport)
        self.__table_pane.add(self.__drawing_table)

        self.root.state("zoomed")
        self.root["menu"] = AppMenu(self.root, self)

        self.__main_pw.pack(fill="both", expand=True)

        # Define traced variables
        self.__drawing_browser.cur_item.trace_add("write", self.__refresh_table)
        self.__drawing_browser.cur_drawing.trace_add("write", self.__refresh_viewport)
        self.__drawing_browser.added_drawing.trace_add("write", self.__write_drawings)

        self.root.protocol("WM_DELETE_WINDOW", self.__on_closing)

    def __write_drawings(self, *_):
        part_id, pdf_path = self.__drawing_browser.added_drawing.get()
        self.__data_writer.insert_images(part_id, pdf_path, self.root)

    def __refresh_table(self, *_):
        try:
            # Change variables
            part_id = self.__drawing_browser.cur_item.get()[0]
            part_name = self.__drawing_browser.cur_item.get()[1]
            # Update Table
            table_data = self.__data_reader.get_user_data(part_id)
            self.__drawing_table.change_part(part_id, part_name, table_data)
        except IndexError as e:
            # happens if the user clicks on somewhere that is not a tree item
            if self.debug:
                print(f"error in gui - __refresh_table \n{e}")

    def __refresh_viewport(self, *_):
        # Change variables
        try:
            drawing_id = self.__drawing_browser.cur_drawing.get()[0]
            drawing_name = self.__drawing_browser.cur_drawing.get()[1]

            # Update Viewport
            try:
                self.__drawing_viewport.show_imgs(drawing_id, drawing_name)
            except TypeError as e:
                if self.debug:
                    print(f"error in gui - __refresh_viewport \n{e}")
        except IndexError as e:
            # happens if the user clicks on somewhere that is not a tree item
            if self.debug:
                print(f"error in gui - __refresh_viewport \n{e}")

    def __render_entry(self):
        def set_new_file():
            self.filename = asksaveasfilename(
                title="New Drawing Tree File",
                defaultextension=".bci",
                filetypes=[("BCI file", ".bci")],
                initialfile="new_drawing_tree",
            )

            if self.filename == "":
                self.__entry_frame.pack_forget()
                new_file.pack_forget()
                open_file.pack_forget()
                self.__render_entry()
            else:
                f = File(self.filename, "w")
                f.close()
                self.__entry_frame.pack_forget()
                self.run_file(self.filename)

        def set_open_file():
            self.filename = askopenfilename(
                title="Open Drawing Tree File",
                defaultextension=".bci",
                filetypes=[("BCI file", ".bci")],
                initialfile="new_drawing_tree",
            )
            if self.filename == "":
                self.__entry_frame.pack_forget()
                open_file.pack_forget()
                new_file.pack_forget()
                self.__render_entry()
            else:
                self.__entry_frame.pack_forget()
                self.run_file(self.filename)

        new_img = PhotoImage(file="data/images/new_file.png")
        new_file = Button(
            self.__entry_frame,
            command=set_new_file,
            image=new_img,
            text="New File...",
            compound="top",
            font=("Arial", 16, "bold"),
        )
        new_file.image = new_img
        open_img = PhotoImage(file="data/images/open_file.png")
        open_file = Button(
            self.__entry_frame,
            command=set_open_file,
            image=open_img,
            text="Open File...",
            compound="top",
            font=("Arial", 16, "bold"),
        )
        open_file.image = open_img
        self.__loading.pack_forget()
        new_file.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        open_file.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        self.__entry_frame.pack(fill="both", expand=True)

    def __set_style(self):
        style = Style()
        style.theme_use("clam")
        style.configure("TPanedwindow", background="#606060")
        style.configure(
            "Sash",
            background="white",
            gripcount=10,
            handlesize=500,
            handlepad=10,
            lightcolor="#606060",
            sashthickness=10,
        )

    def __set_new_file(self):
        self.filename = asksaveasfilename(
            title="New Drawing Tree File",
            defaultextension=".bci",
            filetypes=[("BCI file", ".bci")],
            initialfile="new_drawing_tree",
        )

        if self.filename == "":
            pass
        else:
            f = File(self.filename, "w")
            f.close()
            self.__unrender_all()
            self.run_file(self.filename)

    def __set_open_file(self):
        self.filename = askopenfilename(
            title="Open Drawing Tree File",
            defaultextension=".bci",
            filetypes=[("BCI file", ".bci")],
            initialfile="new_drawing_tree",
        )
        if self.filename == "":
            pass
        else:
            self.__unrender_all()
            self.run_file(self.filename)

    def __add_ocr_items(self, *_):
        data = self.__extractor.data.get()
        for row in data:
            for col in row:
                if "PART" in col[0]:
                    part_ind = row.index(col)
                    print(f"part index is {row.index(col)}")
                    for i in data:
                        if (
                            i[part_ind][0].strip() != ""
                            and "PART" not in i[part_ind][0]
                        ):
                            self.__drawing_browser.add_extracted_part(i[part_ind])
                # if "DESCRIPTION" in col[0]:
                #     desc_ind = row.index(col)
                #     print(f"description index is {row.index(col)}")
                #     descs = []
                #     for i in data:
                #         descs.append(i[desc_ind])
                #     if (
                #         i[desc_ind][0].strip() != ""
                #         and "DESCRIPTION" not in i[desc_ind][0]
                #     ):
                #         print(
                #             f"Item = {i[desc_ind][0].strip()} conf = {i[desc_ind][1]}"
                #         )
