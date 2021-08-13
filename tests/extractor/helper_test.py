"""
Tests for helper functions for processing the images for OCR
"""

from typing import Any
import os
import cv2
from src.extractor.extractor import get_boxes


def test_get_boxes() -> tuple((Any, list)):
    path = os.path.join(os.getcwd(), r"data\test\test2.png")
    img = cv2.imread(path, 0)
    get_boxes(img)
