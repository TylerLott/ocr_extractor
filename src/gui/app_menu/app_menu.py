"""
This module is the main application menu
"""
import sys
from tkinter import Menu


class AppMenu(Menu):
    """
    Main top bar menu for the application

    ** this still needs to be attached to application functions through
       the gui, im not sure what the best way to do that is going to be...

    Methods:
        - make_file_menu            =
        - make_edit_menu            =
        - make_view_menu            =
        - make_tools_menu           =
        - make_help_menu            =
        - save_exit_app             =
        - exit_app                  =
        + placeholder_command       =

    Attributes:
        - bg
        - fg
        - gui
        + file
        + edit
        + view
        + tools
        + help

    """

    def __init__(self, master, gui, bg="white", fg="black"):
        Menu.__init__(self, master)
        self.master = master
        self.__gui = gui
        self.__bg = bg
        self.__fg = fg
        self.__make_file_menu()
        self.__make_edit_menu()
        self.__make_view_menu()
        self.__make_tools_menu()
        self.__make_help_menu()

    def __make_file_menu(self):
        self.file = Menu(self, tearoff=False, bg=self.__bg, fg=self.__fg)
        self.add_cascade(label="File", menu=self.file)

        # Add Commands
        self.file.add_command(
            label="New Project", command=self.__new_file, accelerator="Ctrl+N"
        )
        self.file.add_command(
            label="Open Project", command=self.__open_file, accelerator="Ctrl+O"
        )
        self.file.add_separator()
        self.file.add_command(
            label="Save Project", command=self.__save_file, accelerator="Ctrl+S"
        )
        self.file.add_command(label="Export to xlsx", command=self.placeholder_command)
        self.file.add_separator()
        self.file.add_command(label="Preferences", command=self.placeholder_command)
        self.file.add_separator()
        self.file.add_command(label="Save and Exit", command=self.__save_exit_app)
        self.file.add_command(label="Exit", command=self.__exit_app)

        # Add Key Bindings
        self.master.bind_all("<Control-n>", self.__new_file)
        self.master.bind_all("<Control-o>", self.__open_file)
        self.master.bind_all("<Control-s>", self.__save_file)

    def __make_edit_menu(self):
        self.edit = Menu(self, tearoff=False, bg=self.__bg, fg=self.__fg)
        self.add_cascade(label="Edit", menu=self.edit)

        # Add Commands
        self.edit.add_command(
            label="Undo", command=self.placeholder_command, accelerator="Ctrl+Z"
        )
        self.edit.add_command(
            label="Redo", command=self.placeholder_command, accelerator="Ctrl+Y"
        )
        self.edit.add_separator()
        self.edit.add_command(label="Add Part", command=self.placeholder_command)
        self.edit.add_command(label="Add Child Part", command=self.placeholder_command)
        self.edit.add_command(label="Add Drawing pdf", command=self.placeholder_command)
        self.edit.add_separator()
        self.edit.add_command(
            label="Rotate Clockwise", command=self.placeholder_command
        )
        self.edit.add_command(
            label="Rotate Counter Clockwise", command=self.placeholder_command
        )
        self.edit.add_separator()
        self.edit.add_command(
            label="Cut", command=self.placeholder_command, accelerator="Ctrl+C"
        )
        self.edit.add_command(
            label="Copy", command=self.placeholder_command, accelerator="Ctrl+X"
        )
        self.edit.add_command(
            label="Paste", command=self.placeholder_command, accelerator="Ctrl+V"
        )

        # Add Key Bindings
        self.master.bind_all("<Control-z>", self.placeholder_command)
        self.master.bind_all("<Control-y>", self.placeholder_command)
        self.master.bind_all("<Control-c>", self.placeholder_command)
        self.master.bind_all("<Control-x>", self.placeholder_command)
        self.master.bind_all("<Control-v>", self.placeholder_command)

    def __make_view_menu(self):
        self.view = Menu(self, tearoff=False, bg=self.__bg, fg=self.__fg)
        self.add_cascade(label="View", menu=self.view)

        # Add Commands
        self.view.add_command(label="Zoom", command=self.placeholder_command)
        self.view.add_command(label="Adjust Windows", command=self.placeholder_command)

        # Add Key Bindings

    def __make_tools_menu(self):
        self.tools = Menu(self, tearoff=False, bg=self.__bg, fg=self.__fg)
        self.add_cascade(label="Tools", menu=self.tools)

        # Add Commands
        self.tools.add_command(label="TO Extractor", command=self.placeholder_command)
        self.tools.add_command(label="Options...", command=self.placeholder_command)

        # Add Key Bindings

    def __make_help_menu(self):
        self.help = Menu(self, tearoff=False, bg=self.__bg, fg=self.__fg)
        self.add_cascade(label="Help", menu=self.help)

        # Add Commands
        self.help.add_command(label="Welcome", command=self.placeholder_command)
        self.help.add_command(label="Getting Started", command=self.placeholder_command)
        self.help.add_command(label="Documentation", command=self.placeholder_command)
        self.help.add_separator()
        self.help.add_command(label="About", command=self.placeholder_command)

        # Add Key Bindings

    def __save_exit_app(self):
        # save functionality
        self.__gui.save_file()
        sys.exit(0)

    def __save_file(self, *_):
        self.__gui.save_file()

    def __open_file(self, *_):
        self.__gui.open_file()

    def __new_file(self):
        self.__gui.new_file()

    def __exit_app(self):
        sys.exit(0)

    def placeholder_command(self, *_):
        print("executed menu placeholder")
