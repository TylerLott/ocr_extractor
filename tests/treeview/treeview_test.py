"""
These are the tests for the treeview Widget in the application
"""
import sys
from tkinter import Tk, Frame

sys.path.append(
    "C:\\Users\\M54611\\Desktop\\Innovation\\Drawing_Tree_Tool\\drawing_tree_tool\\src"
)

from gui.treeview.treeview import DrawingTreeview


def test_treeview() -> None:
    data = [
        ["1", "", ["2", "3"], "part1"],
        ["2", "1", [""], "part2"],
        ["3", "1", [""], "part3"],
    ]
    app = Tk()
    tree_frame = Frame(app)
    tree = DrawingTreeview(tree_frame)

    tree.read_data(data)

    assert tree.item_id == 3
