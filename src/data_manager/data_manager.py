"""
This module deals with saving and reading data for the application

Data Structure of .bci file:
root
 |
 |--- ids : group
 |     |
 |     |--- part_id --- attrs{parent: parent_id, part_name: part_name, children: (children)}
 |      ...
 |
 |--- images : group
 |      |
 |      |--- drawing_id : group --- attrs{total_imgs: int, 'drawing': 'drawing_name', parts: (parts)}
 |      |        |
 |      |        |--- page1.png : dataset
 |      |         ...
 |       ...
 |
 |
 |
 |--- extracted_data : group
 |          |
 |          |--- drawing_id : group
 |          |       |
 |          |       |--- page1 : group
 |          |       |     |
 |          |       |     |---extracted_info1 : dataset  -- attr{boundingbox}
 |          |        ...   ...
 |           ...
 |
 |
 |--- user_data : group
            |
            |---part_id : group --- attrs{'part': 'part_name' ... data}
             ...

"""
from threading import Thread
from typing import List
import h5py
import numpy as np
from pdf2image import convert_from_path
from PyPDF2 import PdfFileReader

from gui.components.loading_popup.loading_popup import LoadingPopup


class DataWriter:
    """
    This class handles all writing to the file

    Methods:
        + insert_drawing            = inserts a new part into the file ids section
        + insert_images             = inserts an array of images under a part name
        + insert_image              = deletes old image of name, and creates new one
        + insert_extract_data       = inserts the extracted data for a part number and img
        + insert_user_data          = inserts the table data for a part into the file
        + del_img_arr               = deletes all images for a part number
        + del_drawing               = deletes a part number from ids section of file
        - get_num_extractions       = get how many extractions have been done on a
                                      part and img returns the next index

    Attributes:
        + debug
        + filename

    """

    def __init__(self, file_path: str, debug=False) -> None:
        self.debug = debug
        self.filename = file_path

        with h5py.File(self.filename, "r+") as f:
            groups = ["ids", "images", "extracted_data", "user_data"]
            for i in groups:
                if i not in f:
                    f.create_group(i)

    def save_drawings(self, parts: list, deleted: list) -> bool:
        for i in parts:
            self.insert_drawing(i[0], i[1], i[2], i[3], i[4])
        for i in deleted:
            self.del_drawing(i)

    def insert_drawing(
        self, parent: str, part_id: str, part_name: str, tag_color: str, children: tuple
    ) -> bool:
        """
        Treeview will use this for inserting,
        """
        with h5py.File(self.filename, "a") as f:

            try:
                f.create_group(f"ids/{part_id}")
                print(f"inputting {part_id}")
            except ValueError as e:
                if self.debug:
                    print(f"error in DataWriter - insert_drawing \n {e}")
            try:
                f[f"ids/{part_id}"].attrs["parent"] = parent
                f[f"ids/{part_id}"].attrs["part_name"] = part_name
                f[f"ids/{part_id}"].attrs["tag_color"] = tag_color
                f[f"ids/{part_id}"].attrs["children"] = children
            except ValueError as e:
                if self.debug:
                    print(f"error in DataWriter - insert_drawing \n {e}")
                return False
        return True

    def insert_images(self, part_id: str, pdf_path: str, gui_root, refresh) -> bool:
        """
        Should insert into the images group with the drawing_id assigned by treeview
        """
        with h5py.File(self.filename, "a") as f:
            try:  # deletes group if already exists
                del f["images"][part_id]
            except KeyError:
                pass

        def thread_task():
            loading = LoadingPopup(
                gui_root, title="Uploading pdf...", desc="Uploading pdf, please wait..."
            )
            with open(pdf_path, "rb") as pdf:
                pdf_reader = PdfFileReader(pdf)
                num_pgs = pdf_reader.getNumPages()
            for i in range(1, num_pgs + 1):
                img = convert_from_path(
                    pdf_path,
                    grayscale=True,
                    first_page=i,
                    last_page=i,
                    poppler_path=r"bin/Poppler",
                )
                loading.change_progress(i * 100 / num_pgs)
                part_name = part_id + f"-{i-1}"
                self.insert_image(part_id, part_name, np.array(img[0]))
            refresh()

        load_thread = Thread(target=thread_task)
        load_thread.start()

    def insert_image(self, part_id: str, part_name: str, img: np.array) -> bool:
        """
        Deletes an image if it exists in the data file, creates a single image
        in data file
        """
        with h5py.File(self.filename, "a") as f:
            try:
                del f["images"][part_id][part_name]
            except KeyError:
                pass
            try:
                f.create_dataset(
                    f"images/{part_id}/{part_name}",
                    data=img,
                    compression="gzip",
                    compression_opts=9,
                )
            except ValueError as e:
                if self.debug:
                    print(f"error in DataWriter - insert_image \n {e}")
                return False
        return True

    def insert_extract_data(
        self, drawing_id: str, img_id: str, data, meta_data
    ) -> bool:
        """
        The extracted data will only be stored so I am able to create a dataset more easily
        the application should deliver the information immediately into the input
        feild, which the user can then change (thus there will be overlap between some
        information here and in the user data - because we need to create a dataset of
        validated information)
        """
        new_id = self.__get_num_extractions(drawing_id, img_id)
        with h5py.File(self.filename, "a") as f:
            try:
                f.create_dataset(
                    f"extracted_data/{drawing_id}/{img_id}/{new_id}", data=data
                )
                f[f"extracted_data/{drawing_id}/{img_id}/{new_id}"].attrs[
                    "bounding_box"
                ] = meta_data
            except ValueError as e:
                if self.debug:
                    print(f"error in DataWriter - insert_extract_data \n {e}")
                return False

    def insert_user_data(self, drawing_id: str, data: dict) -> bool:
        """Insert table data into the datafile"""
        with h5py.File(self.filename, "a") as f:
            for key in data.keys():
                try:
                    f.create_dataset(f"user_data/{drawing_id}", data=[])
                except ValueError:
                    # happens if already in datafile
                    pass
                try:
                    f["user_data"][drawing_id].attrs[key] = data[key]
                except ValueError as e:
                    if self.debug:
                        print(f"error in DataWriter - insert_user_data \n {e}")
                    return False
        return True

    def del_img_arr(self, drawing_id: str) -> bool:
        """delete all of the images for an item in the data file"""
        with h5py.File(self.filename, "a") as f:
            try:
                del f["images"][drawing_id]
            except KeyError as e:
                if self.debug:
                    print(f"error in DataWriter - del_img_arr \n {e}")
                return False
        return True

    def del_drawing(self, part_id: str) -> bool:
        """delete a drawing from the ids table in the data file"""
        with h5py.File(self.filename, "a") as f:
            try:
                del f["ids"][part_id]
            except KeyError as e:
                if self.debug:
                    print(f"error in DataWriter - del_drawing \n {e}")
                return False

    def __get_num_extractions(self, drawing_id: str, img_id: str) -> int:
        """get the number of entries in the extraction"""
        with h5py.File(self.filename, "r") as f:
            if f"extracted_data/{drawing_id}/{img_id}" in f:
                return len(f[f"extracted_data/{drawing_id}/{img_id}"])
            else:
                return 0


class DataReader:
    """
    This class deals with all reading information from the file

    Methods:
        + get_all_drawings          = returns a list of all part numbers in file
        + get_img_arr               = returns all images for a part number
        + get_user_data             = get the table data that the user has input


    Attributes:
        + debug
        + filename
    """

    def __init__(self, file_path: str, debug=False) -> None:
        self.debug = debug
        self.filename = file_path

    def get_all_drawings(self) -> np.ndarray:
        """returns an array of form [ part_id, drawing_id, parent_id, children, part_name ]"""
        with h5py.File(self.filename, "r") as f:
            res = []
            for i in f["ids"]:
                parent = f["ids"][i].attrs["parent"]
                part_name = f["ids"][i].attrs["part_name"]
                tag_color = f["ids"][i].attrs["tag_color"]
                children = f["ids"][i].attrs["children"]
                res.append([i, parent, part_name, tag_color, children])
            return res

    def get_img_arr(self, drawing_id: str) -> List:
        """returns all drawing files for a specified part"""
        with h5py.File(self.filename, "r") as f:
            try:
                return [
                    f["images"][drawing_id][i][:] for i in f["images"][drawing_id]
                ], list(f["images"][drawing_id])
            except KeyError as e:
                if self.debug:
                    print(f"error in DataReader - get_img_arr \n {e}")

    def get_img(self, drawing_id: str, page: int):
        with h5py.File(self.filename, "r") as f:
            try:
                print(f"drawingid - {drawing_id}")
                print(f"page - {page}")
                images = [f["images"][drawing_id][i] for i in f["images"][drawing_id]]
                img = f["images"][drawing_id][drawing_id + f"-{page-1}"][:]
                num_images = len(images)
                return img, num_images
            except KeyError as e:
                if self.debug:
                    print(f"error in DataReader - get_img_arr \n {e}")
            except ValueError as e:
                if self.debug:
                    print(f"error in DataReader - get_img_arr \n {e}")

    def get_user_data(self, drawing_id: str) -> List:
        """returns the table data for a specified part"""
        with h5py.File(self.filename, "r") as f:
            # User data is stored in the attributes of the part_id group
            try:
                return [i for i in f["user_data"][drawing_id].attrs.items()]
            except KeyError as e:
                if self.debug:
                    print(f"error in DataReader - get_user_data \n {e}")
