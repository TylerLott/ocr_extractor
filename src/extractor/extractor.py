"""
Main image processing class
Must be initialized with an image path
"""
from threading import Thread
from tkinter import Variable
import pytesseract
import numpy as np

from .helper import get_boxes
from gui.components.loading_popup.loading_popup import LoadingPopup


class TableExtractor:
    """
    Runs OCR on table image

    Methods:
        + extract_table        = run the extraction, return an array of extracted text
        - correct_bounding     = change bounding boxes from (x,y,w,h) -> (x1,y1,x2,y2)
        - run_tesseract        = uses tesseract with a custom config


    Attributes:
        + data
        + root
        - image


    """

    def __init__(self, gui_root):
        pytesseract.pytesseract.tesseract_cmd = r"bin\Tesseract-OCR\tesseract.exe"
        self.data = Variable(value=None)
        self.__image = None
        self.root = gui_root

    def extract_table(self, img: np.ndarray, bounding_box: list) -> None:
        """
        Run table extraction and return array of shape(rows, columns)
        """

        def thread_work(bounding_box):
            loading = LoadingPopup(
                self.root,
                title="Running OCR",
                desc="Extracting table data, please wait",
            )
            bounding_box = self.__correct_bounding(bounding_box)
            self.__image = img[
                int(bounding_box[1]) : int(bounding_box[3] + bounding_box[1]),
                int(bounding_box[0]) : int(bounding_box[2] + bounding_box[0]),
            ]
            processed_image, bounding_boxes = get_boxes(self.__image)

            load_length = len(bounding_boxes)
            load_i = 0

            row = []
            for i in bounding_boxes:
                for j in i:
                    if len(j) == 0:
                        row.append(["", -2])
                    else:
                        col = []
                        for k in j:
                            y, x, w, h = (
                                k[0],
                                k[1],
                                k[2],
                                k[3],
                            )
                            cropped_img = processed_image[x : x + h, y : y + w]
                            col = self.__run_tesseract(cropped_img)
                        row.append(col)
                loading.change_progress(load_i * 100 / load_length)
                load_i += 1

            arr = np.array(row)
            loading.change_progress(100)
            self.data.set(
                value=arr.reshape(
                    (len(bounding_boxes), len(bounding_boxes[0]), 2)
                ).tolist()
            )

        ocr_thread = Thread(target=thread_work, args=[bounding_box])
        ocr_thread.start()

    def __correct_bounding(self, box: list) -> list:
        x, y, x2, y2 = 0, 0, 0, 0
        if int(box[2]) < 0:
            x = int(box[0]) + int(box[2])
            x2 = abs(int(box[2]))
            box[0] = x
            box[2] = x2
        if int(box[3]) < 0:
            y = int(box[1]) + int(box[3])
            y2 = abs(int(box[3]))
            box[1] = y
            box[3] = y2

        return box

    def __run_tesseract(self, image: np.ndarray) -> list:
        tesseract_config = """-c tessedit_char_whitelist=
            "01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.-/ '"
            --psm 7 --oem 1"""
        out = pytesseract.image_to_data(
            image,
            lang="eng",
            config=tesseract_config,
            output_type=pytesseract.Output.DICT,
        )
        ind = np.where(np.array(out.get("conf")) != "-1")
        text = ""
        conf = 0
        if len(ind[0]) >= 1:
            for i in ind[0]:
                text = " ".join([text, out.get("text")[i]])
                conf += float(out.get("conf")[i])
            conf = conf / len(ind[0])
        if text == "" and conf == 0:
            conf = -2  # this denotes a empty space predition
        return [text, conf]
