"""
This module contains the main part information table
"""
from tkinter import Frame, ttk
from gui.components.label_frame.label_frame import LabelFrame
from data_manager.data_manager import DataWriter
from .tabs.tabs import (
    DrawingInfoTab,
    MaterialTab,
    MiscTab,
    PaintTab,
    PlatingTab,
    PrimerTab,
)


class DrawingTable(Frame):
    """
    Side table for viewing individual part information

    Methods:
        + change_part          = switches the information in the table for the part that is shown

    Attributes:
        + debug
        + drawing_id
        + part_id
        - data_writer
        - label_frame
        - table_frame
        - sections

    """

    def __init__(self, master: Frame, data_writer: DataWriter, debug=False):
        self.debug = debug
        Frame.__init__(self, master)

        self.__data_writer = data_writer
        self.drawing_id = None
        self.part_id = None

        # Define Frames
        self.__label_frame = LabelFrame(self, "Part XXX-XXX")
        self.__table_frame = ttk.Notebook(self)

        drawing_info = DrawingInfoTab(self.__table_frame, debug=self.debug)
        material_info = MaterialTab(self.__table_frame, debug=self.debug)
        plating_info = PlatingTab(self.__table_frame, debug=self.debug)
        primer_info = PrimerTab(self.__table_frame, debug=self.debug)
        paint_info = PaintTab(self.__table_frame, debug=self.debug)
        misc_info = MiscTab(self.__table_frame, debug=self.debug)

        self.__sections = {
            "drawing_info": drawing_info,
            "material_info": material_info,
            "plating_info": plating_info,
            "primer_info": primer_info,
            "paint_info": paint_info,
            "misc_info": misc_info,
        }

        self.__table_frame.add(drawing_info, text="Drawing")
        self.__table_frame.add(material_info, text="Material")
        self.__table_frame.add(plating_info, text="Plating")
        self.__table_frame.add(primer_info, text="Primer")
        self.__table_frame.add(paint_info, text="Paint")
        self.__table_frame.add(misc_info, text="Misc")

        # Pack Frames
        self.__label_frame.pack(side="top", fill="x")
        self.__table_frame.pack(side="bottom", fill="both", expand=True)

    def change_part(self, part_id: str, part_name: str, data: list):
        """render and unrender current frame
        also save old information and query for any part information in the file"""
        self.__label_frame.label_text.set(value="Part " + part_name)
        if self.part_id:
            for i in self.__sections.items():
                self.__data_writer.insert_user_data(self.part_id, i[1].get_info())

        for i in self.__sections.items():
            i[1].set_info(data)

        self.part_id = part_id

    def save_data(self):
        """save the current table data"""
        if self.part_id:
            for i in self.__sections.items():
                self.__data_writer.insert_user_data(self.part_id, i[1].get_info())
