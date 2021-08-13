"""
This module is the main part tree for the application
"""

from tkinter import Frame, TclError, Variable, Event, filedialog
from tkinter.ttk import Treeview, Style
from typing import List
import numpy as np


from data_manager.data_manager import DataReader
from gui.components.auto_scrollbar.auto_scrollbar import AutoScrollbar
from gui.components.label_frame.label_frame import LabelFrame
from gui.components.rc_menu.rc_menu import RightClickMenu
from gui.treeview.entry_popup.entry_popup import EntryPopup


class DrawingTreeview(Frame):
    """
    Part Tree for the application, also creates the ids for each part,

    ** this should probably be refactored to be less of a manager and more of
       an accepter object

    Methods:
        + read_data          = read data in from the main datafile and recreate tree
        + save_data          = save the tree data to the main datafile as a linked list
        - make_menu          = create the right click dropdown menu
        - user_add_item      = allows the user to add an item to the tree the has edit box
        - user_add_child     = allows the user to add an item child to the tree then has edit box
        - remove_item        = removes an item and shifts it's children to the deleted items parent
        - edit_item          = brings up an edit box that allows the user to change the part name
        - add_file           = user selects pdf, treeview changes a variable for added_drawing
        - no_drawing         = marks the item as no drawing
        - double_click       = brings up edit box on double click
        - single_click       = shifts focus to the selected tree item
        - edit_popup         = edit item helper - creates the popup to edit the item text
        - id_creator         = creates a new item id that hasn't been used before
        - app_add_item       = applications way of adding items on file load
        - read_data_helper   = recursive helper
        - save_data_helper   = recursive helper

    Attributes:
        + debug
        + item_id
        + cur_item
        + added_drawing
        - deleted
        - data_reader
        - drawing_tree
        - drop_menu
    """

    def __init__(
        self,
        master: Frame,
        data_reader: DataReader,
        debug=False,
    ):
        self.debug = debug
        self.master = master
        Frame.__init__(self, master)

        style = Style()
        style.configure(
            "Treeview",
            indent=15,
            background="#DCDCDC",
            foreground="black",
            fieldbackground="#DCDCDC",
            rowheight=25,
        )
        style.map("Treeview", background=[("selected", "#004F98")])

        self.item_id = 0
        self.cur_item = Variable(value=("", ""))
        self.cur_drawing = Variable(value=("", ""))
        self.added_drawing = Variable(value=("", ""))
        self.__deleted = []
        self.__data_reader = data_reader

        # Define Frames
        label_frame = LabelFrame(self, "Drawing Tree")
        tree_frame = Frame(self)

        # Configure Treeframe
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # Define Elements
        self.__drawing_tree = Treeview(tree_frame, show="tree")
        scrolly = AutoScrollbar(tree_frame, orient="vertical")
        scrollx = AutoScrollbar(tree_frame, orient="horizontal")
        self.__make_menu()

        self.__drawing_tree.column("#0", stretch="yes")
        self.__drawing_tree.heading("#0", text="Drawing XXX-XXX")

        # Bind Buttons
        self.__drawing_tree.bind("<Double-1>", self.__double_click)
        self.__drawing_tree.bind("<ButtonRelease-1>", self.__single_click)

        # Configure Elements
        self.__drawing_tree.configure(
            yscrollcommand=scrolly.set, xscrollcommand=scrollx.set
        )
        scrolly.configure(command=self.__drawing_tree.yview)
        scrollx.configure(command=self.__drawing_tree.xview)

        # Tag colors
        self.__drawing_tree.tag_configure("none", background="#808080")
        self.__drawing_tree.tag_configure("95", background="#FFFFCC")
        self.__drawing_tree.tag_configure("85", background="#FFFF00")
        self.__drawing_tree.tag_configure("70", background="#F08080")
        self.__drawing_tree.tag_configure("50", background="#B22222")

        # Pack Elements
        scrolly.grid(row=0, column=1, sticky="ns")
        scrollx.grid(row=1, column=0, sticky="we")
        self.__drawing_tree.grid(row=0, column=0, sticky="nsew")

        # Pack Frames
        label_frame.pack(side="top", fill="x")
        tree_frame.pack(side="bottom", fill="both", expand=True)

        self.read_data(self.__data_reader.get_all_drawings())

    def read_data(self, items: List) -> None:
        """
        Passed a list of items in form [ part_id, parent_id, part_name, children ]
        need to recursively go through and add items for each of
        """
        for i in items:
            if i[1] == "":
                self.__read_data_helper(items, i)

    def get_parts(self) -> tuple:
        """returns tree information partid into the main ids section of the datafile
        form = ( parent, part_id, part_name, children ), (deleted items)
        """
        parts = []
        self.__save_data_helper("", parts)
        data = (parts, self.__deleted)
        self.__deleted = []
        return data

    def add_extracted_part(self, part: tuple):
        """adds a part from an extracted tuple of form ( part_name, conf )"""
        parent = self.__drawing_tree.item(self.__drawing_tree.focus(), "tags")[0]
        print(f"parent - {parent}")
        part_id = self.__id_creator()

        if float(part[1]) > 95:
            tag_color = ""
        elif float(part[1]) > 85:
            tag_color = "95"
        elif float(part[1]) > 70:
            tag_color = "85"
        elif float(part[1]) > 50:
            tag_color = "70"
        else:
            tag_color = "50"
        print(part[1])

        self.__app_add_item(part_id, parent, part[0].strip(), tag_color=tag_color)

    def __make_menu(self):
        self.__drop_menu = RightClickMenu(self.__drawing_tree)
        self.__drop_menu.add_command(label="Add Part", command=self.__user_add_item)
        self.__drop_menu.add_command(
            label="Add Child Part", command=self.__user_add_child
        )
        self.__drop_menu.add_separator()
        self.__drop_menu.add_command(label="Remove", command=self.__remove_item)
        self.__drop_menu.add_command(label="Edit", command=self.__edit_item)
        self.__drop_menu.add_separator()
        self.__drop_menu.add_command(label="Add Drawing File", command=self.__add_file)
        self.__drop_menu.add_command(
            label="Mark As No Drawing", command=self.__no_drawing
        )

    def __user_add_item(self):
        new_id = self.__id_creator()
        self.__drawing_tree.insert(
            parent=self.__drawing_tree.parent(self.__drop_menu.selection),
            index="end",
            iid=new_id,
            text="new part",
            tags=(new_id, "part_name", ""),
        )
        self.__edit_popup(new_id, "#0")

    def __user_add_child(self):
        new_id = self.__id_creator()
        self.__drawing_tree.item(self.__drop_menu.selection, open=True)
        self.__drawing_tree.insert(
            parent=self.__drop_menu.selection,
            index="end",
            iid=new_id,
            text="new part",
            tags=(new_id, "part_name", ""),
        )
        self.__edit_popup(new_id, "#0")

    def __remove_item(self):
        children = np.array(
            self.__drawing_tree.get_children(self.__drop_menu.selection)
        )
        parent = self.__drawing_tree.parent(self.__drop_menu.selection)
        old_children = np.array(self.__drawing_tree.get_children(parent))
        del_index = np.where(old_children == self.__drop_menu.selection)[0]
        old_children = np.delete(old_children, del_index)
        children = np.insert(old_children, del_index, children, axis=0)

        # mark as deleted, for deleting in file on save
        tags = self.__drawing_tree.item(self.__drop_menu.selection, "tags")
        self.__deleted.append(tags[0])
        if len(children) > 0:
            self.__drawing_tree.set_children(parent, *children)
        try:
            self.__drawing_tree.delete(self.__drop_menu.selection)
        except TclError as e:
            if self.debug:
                print(f"error in treeview - __remove_item \n{e}")

    def __edit_item(self):
        rowid = self.__drop_menu.selection
        column = self.__drop_menu.column
        self.__edit_popup(rowid, column)

    def __add_file(self):
        """
        Filebox popup leading to pdf drawing, utilize pdf2image to convert, then save to file
        ** this needs to move to the gui **
        """

        pdf_path = filedialog.askopenfilename(
            title="Select PDF",
            defaultextension=".pdf",
            filetypes=[("pdf file", ".pdf")],
        )
        part_id = self.__drop_menu.selection
        self.added_drawing.set(value=(part_id, pdf_path))

        # store in variable of shape ( part_id, pdf_path ) trace from gui

    def set_focus(self):
        new_curr_drawing = self.__drawing_tree.item(self.__drawing_tree.focus(), "tags")
        if self.cur_drawing.get() != new_curr_drawing:
            self.cur_drawing.set(new_curr_drawing)

    def __no_drawing(self):
        try:
            # what row and column was clicked on
            rowid = self.__drop_menu.selection
            tags = self.__drawing_tree.item(rowid, "tags")
            self.__drawing_tree.item(rowid, tags=(tags[0], tags[1], "none"))

        except ValueError as e:
            # occurs when double click not on an item
            if self.debug:
                print(f"error in treeview - __no_drawing \n{e}")

    def __double_click(self, event: Event):
        """
        Executed, when a row is double-clicked. Opens
        editable text Entry above the row so that the row text can be edited
        """
        region = self.__drawing_tree.identify("region", event.x, event.y)
        if region == "heading":
            self.cur_drawing.set("root_drawing")
            # go to the root drawing image
        else:
            self.set_focus()
        # edit on double click
        # try:
        #     # what row and column was clicked on
        #     rowid = self.__drawing_tree.identify_row(event.y)
        #     column = self.__drawing_tree.identify_column(event.x)
        #     self.__edit_popup(rowid, column)

        # except ValueError:
        #     # occurs when double click not on an item
        #     pass

    def __single_click(self, event: Event):
        region = self.__drawing_tree.identify("region", event.x, event.y)
        if region == "heading":
            self.cur_item.set("root_drawing")
            # go to the root drawing image
        else:
            new_curr_item = self.__drawing_tree.item(
                self.__drawing_tree.focus(), "tags"
            )
            if self.cur_item.get() != new_curr_item:
                # Determine if current item is different than before
                self.cur_item.set(new_curr_item)

    def __edit_popup(self, rowid: str, col: str):
        _, y, _, _ = self.__drawing_tree.bbox(rowid, col)

        # place Entry popup properly
        text = self.__drawing_tree.item(rowid, "text")

        entry_popup = EntryPopup(self.__drawing_tree, rowid, text, debug=self.debug)
        entry_popup.place(x=20, y=y + 10, anchor="w", relwidth=1)

    def __id_creator(self):
        self.item_id += 1
        return str(self.item_id)

    def __app_add_item(
        self, part_id: str, parent_id: str, part_name: str, tag_color=""
    ):
        """This is for adding items on file load"""
        self.__drawing_tree.insert(
            parent=parent_id,
            index="end",
            iid=part_id,
            text=part_name,
            tags=(part_id, part_name, tag_color),
        )
        if int(part_id) > self.item_id:
            self.item_id = int(part_id)
        self.__drawing_tree.item(part_id, open=True)

    def __read_data_helper(
        self,
        items: List,
        item: List,
    ):
        self.__app_add_item(item[0], item[1], item[2], item[3])
        for i in item[4]:
            for j in items:
                if i == j[0]:
                    self.__read_data_helper(items, j)

    def __save_data_helper(self, item: str, parts: List):
        children = self.__drawing_tree.get_children(item)
        for i in children:
            tags = self.__drawing_tree.item(i, "tags")
            parts.append(
                (item, tags[0], tags[1], tags[2], self.__drawing_tree.get_children(i))
            )
            self.__save_data_helper(i, parts)
