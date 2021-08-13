"""
Methods for preprocessing the image before OCR can be done
The main purpose of this module is to extract the bounding boxes of the table so the
OCR class can use them to perform OCR on the images

Functions:
    + get_boxes                = uses all private functions to extract the table 
                                 structure from the image
    - correct_rotation         = rotates to make the table straight, will only work
                                 if mostly straight already
    - check_boxes              = makes sure the number of boxes found is greater than
                                 1, if not it returns the image dimensions
    - get_inverted             = gets inverted image
    - get_vertical_lines       = gets the vertical lines from the table image
    - get_horizontal_lines     = gets the horizontal lines from the table image
    - combine_lines            = makes an images of just the extracted lines
    - overlay_lines            = places lines on the original img
    - sort_contours            = gets the bounding boxes from the contour lines
    - get_bounding_boxes       = uses sort contours to get the boxes in a [x,y,x2,y2] format
    - sort_bounding_boxes      = sorts bounding boxes into an array the shape of the table
    - get_center               = gets the center pixel height of each row
    - get_shape_cnt            = gets the number of columns
    - get_final_boxes          = get the final boxes in the correct format

"""
from typing import Any, List
import numpy as np
import cv2


def get_boxes(image: np.ndarray) -> tuple((Any, list)):
    """
    Uses the private helper functions to construct the bounding boxes for the image table
    Returns:
        [
            Bitnot image (should have lines excluded mostly, will help with OCR)
            Array of all final bounding boxes [x, y, width, height]
        ]

    """
    image = _correct_rotation(image)
    invert = _get_inverted(image)
    combined_lines = _combine_lines(
        _get_vertical_lines(image, invert), _get_horizontal_lines(image, invert)
    )
    boxes = _get_bounding_boxes(combined_lines)
    boxes = _check_boxes(image, boxes)
    boxes = _sort_bounding_boxes(boxes)
    return (_overlay_lines(image, combined_lines), _get_final_boxes(boxes))


def _correct_rotation(img: np.ndarray) -> np.ndarray:
    """if image is rotated correct for this and return it"""
    edges = cv2.Canny(img, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10
    )
    avg_slope = 0
    cnt = 0
    try:
        for line in lines:
            rise = line[0][3] - line[0][1]
            run = line[0][2] - line[0][0]
            if run != 0:
                if rise / run < 0.5:
                    avg_slope += rise / run
                    cnt += 1
        avg_slope = avg_slope / cnt

        image_center = tuple(np.array(img.shape[1::-1]) / 2)
        rot_mat = cv2.getRotationMatrix2D(
            image_center, np.arctan(avg_slope) * 180 / np.pi, 1.0
        )
        result = cv2.warpAffine(img, rot_mat, img.shape[1::-1], flags=cv2.INTER_LINEAR)
        return result
    except TypeError:
        return img


def _check_boxes(img: np.ndarray, boxes: List[List[int]]) -> List:
    if len(boxes) > 1:
        return boxes
    return [[0, 0, img.shape[1], img.shape[0]]]


def _get_inverted(image: np.ndarray) -> np.ndarray:
    _, inverted_image = cv2.threshold(
        image, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU
    )
    return 255 - inverted_image


def _get_vertical_lines(image: np.ndarray, inverted_image: np.ndarray) -> np.ndarray:
    kernel_len = np.array(image).shape[1] // 25
    ver_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_len))
    vertical_lines = cv2.erode(inverted_image, ver_kernel, iterations=3)
    return cv2.dilate(vertical_lines, ver_kernel, iterations=3)


def _get_horizontal_lines(image: np.ndarray, inverted_image: np.ndarray) -> np.ndarray:
    kernel_len = np.array(image).shape[1] // 10
    hor_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))
    horizontal_lines = cv2.erode(inverted_image, hor_kernel, iterations=3)
    return cv2.dilate(horizontal_lines, hor_kernel, iterations=3)


def _combine_lines(
    vertical_lines: np.ndarray, horizontal_lines: np.ndarray
) -> np.ndarray:
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    combined_lines = cv2.addWeighted(vertical_lines, 0.5, horizontal_lines, 0.5, 0.0)
    combined_lines = cv2.erode(~combined_lines, kernel, iterations=2)
    _, combined_lines = cv2.threshold(
        combined_lines, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU
    )
    return combined_lines


def _overlay_lines(image: np.ndarray, combined_lines: np.ndarray) -> np.ndarray:
    bitxor = cv2.bitwise_xor(image, combined_lines)
    return cv2.bitwise_not(bitxor)


def _sort_contours(contours: List, method: str = "ttb") -> tuple:
    reverse = False
    i = 0
    if method in ("rtl", "btt"):
        reverse = True
    if method in ("ttb", "ltr"):
        i = 1
    bounding_boxes = [cv2.boundingRect(c) for c in contours]
    contours, _ = zip(
        *sorted(zip(contours, bounding_boxes), key=lambda b: b[1][i], reverse=reverse)
    )
    return contours


def _get_bounding_boxes(combined_lines: np.ndarray) -> List:
    contours, _ = cv2.findContours(
        combined_lines, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )
    contours = _sort_contours(contours)
    boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w < 1000 and h < 500:
            boxes.append([x, y, w, h])
    return boxes


def _sort_bounding_boxes(boxes: List) -> List:
    rows, col = [], []
    mean_height = np.mean([box[3] for box in boxes])
    if len(boxes) == 1:
        return [boxes]
    for i in boxes:
        if boxes.index(i) == 0:
            col.append(i)
            prev = i
        else:
            if i[1] <= prev[1] + mean_height / 2:
                col.append(i)
                prev = i
                if boxes.index(i) == len(boxes) - 1:
                    rows.append(col)
            else:
                rows.append(col)
                col = []
                prev = i
                col.append(i)
    return rows


def _get_center(rows: List) -> np.ndarray:
    center = [int(rows[0][j][0] + rows[0][j][2] / 2) for j in range(len(rows[0]))]
    center = np.array(center)
    center.sort()
    return center


def _get_shape_cnt(rows: List) -> int:
    col_cnt = 0
    for i in rows:
        temp_col_cnt = len(i)
        if temp_col_cnt > col_cnt:
            col_cnt = temp_col_cnt  # for ragged tables
    return col_cnt


def _get_final_boxes(rows: List) -> List:
    """This handles for ragged tables that may be input"""
    final_boxes = []
    center = _get_center(rows)
    col_cnt = _get_shape_cnt(rows)
    for i in rows:
        lis = []
        for _ in range(col_cnt):
            lis.append([])
        for j in i:
            diff = abs(center - (j[0] + j[2] / 4))
            minimum = min(diff)
            indexing = list(diff).index(minimum)
            lis[indexing].append(j)
        final_boxes.append(lis)
    return final_boxes
