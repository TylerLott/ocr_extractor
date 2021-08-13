"""
This module creates a zoomable, panable, and highlightable image canvas in tkinter

Should refactor into several classes
    Main CanvasImage
        Highlight box
        Zoom
        Pan
"""
import math
from typing import List
import warnings
import tkinter as tk

from tkinter import Event, ttk, Button, Frame, Label
from PIL import Image, ImageTk

from gui.components.auto_scrollbar.auto_scrollbar import AutoScrollbar
from extractor.extractor import TableExtractor


class CanvasImage:
    """
    Display and zoom image
    This should be refactored to split jobs to reduce attributes and lines in __init__
    the path passed in should be a BytesIO file so you dont have to save to disk ever

    Methods:
        + refresh_img            = switches the image shown
        + smaller                = resizes the image proportionally
        + grid                   = grids the canvas
        + pack                   = cannot use pack
        + place                  = cannot use place
        - create_box_buttons     = creates the buttons that appear to confirm bounding box
        - scroll_x               = scroll img x
        - scroll_y               = scroll img y
        - show_image             = shows the image on the canvas and allows zoom and pan
        - on_button_press        = starts bounding box drawing
        - on_move_press          = expands rectangle as the cursor is moves
        - on_button_release      = finishes the bounding box
        - move_from              = pan the image start
        - move_to                = pan the image end
        + outside                = detects if cursor is outside of image bounds
        - wheel                  = attaches the wheel to zoom
        - keystroke              = attaches numpad to pan directions
        - get_img_mouse_pos      = gets the mouse position relative to image pixels
        + crop                   = crops the image
        + destroy                = exits the app cleanly

    Attributes:
        - extractor
        + width
        - previous_state
        - imframe
        - image
        + container
        + rect
        + start_x
        + start_y
        - scale
        - curr_img
        - pyramid
        - delta
        - filter
        + canvas
        + loading
        + ok_btn
        + del_btn
        - huge
        - huge_size
        - band_width
        - offset
        - tile
        + imwidth
        + imheight
        - reduction
        + table_box

    """

    def __init__(self, parent: Frame, img, extractor: TableExtractor, width=650):
        """Initialize the ImageFrame"""
        self.__extractor = extractor
        self.width = width
        self.__previous_state = 0  # previous state of the keyboard
        self.__imframe = ttk.Frame(parent)  # placeholder of the ImageFrame object
        self.__reduction = 2  # reduction degree of image pyramid
        self.__image = None
        self.container = None
        self.rect = None
        self.start_x = None
        self.start_y = None
        self.__scale = None
        self.__curr_img = None
        self.__pyramid = None
        self.__delta = 1.3  # zoom magnitude
        self.__filter = (
            Image.ANTIALIAS
        )  # could be: NEAREST, BILINEAR, BICUBIC and ANTIALIAS

        # Vertical and horizontal scrollbars for canvas
        hbar = AutoScrollbar(self.__imframe, orient="horizontal")
        vbar = AutoScrollbar(self.__imframe, orient="vertical")
        hbar.grid(row=1, column=0, sticky="we")
        vbar.grid(row=0, column=1, sticky="ns")

        # Create canvas and bind it with scrollbars. Public for outer classes
        self.canvas = tk.Canvas(
            self.__imframe,
            highlightthickness=0,
            xscrollcommand=hbar.set,
            yscrollcommand=vbar.set,
            cursor="tcross",
            width=self.width,
            bg="#ffffff",
        )
        self.canvas.grid(row=0, column=0, sticky="nswe")
        self.canvas.update()  # wait till canvas is created

        hbar.configure(command=self.__scroll_x)  # bind scrollbars to the canvas
        vbar.configure(command=self.__scroll_y)

        # Bind events to the Canvas
        self.canvas.bind(
            "<Configure>", lambda event: self.__show_image()
        )  # canvas is resized
        self.canvas.bind(
            "<ButtonPress-2>", self.__move_from
        )  # remember canvas position
        self.canvas.bind(
            "<B2-Motion>", self.__move_to
        )  # move canvas to the new position
        self.canvas.bind(
            "<ButtonRelease-2>", self.__on_button_release
        )  # move canvas to the new position
        self.canvas.bind(
            "<MouseWheel>", self.__wheel
        )  # zoom for Windows and MacOS, but not Linux
        self.canvas.bind(
            "<Button-5>", self.__wheel
        )  # zoom for Linux, wheel scroll down
        self.canvas.bind("<Button-4>", self.__wheel)  # zoom for Linux, wheel scroll up
        # Handle keystrokes in idle mode, because program slows down on a weak computers,
        # when too many key stroke events in the same time
        self.canvas.bind(
            "<Key>", lambda event: self.canvas.after_idle(self.__keystroke, event)
        )
        self.canvas.bind("<ButtonPress-1>", self.__on_button_press)
        self.canvas.bind("<B1-Motion>", self.__on_move_press)
        # self.canvas.bind("<B1-Motion>", self.on_button_press)
        self.canvas.bind("<ButtonRelease-1>", self.__on_button_release)
        self.canvas.configure(yscrollincrement="2m", xscrollincrement="2m")

        self.__create_box_buttons()
        self.refresh_img(img)

    def refresh_img(self, img):
        """Refreshes the image shown on the canvas"""
        self.canvas.grid_forget()
        self.canvas.update()

        # Loading Label
        loading = Label(
            self.__imframe,
            text="Loading...",
            font=("Arial", 20, "bold"),
            fg="#707070",
            bg="#F5F5F5",
            pady=20,
            padx=20,
        )
        loading.grid(row=0, column=0, sticky="nswe")
        loading.update()

        # print(img)
        self.path = img  # np array of image

        self.imscale = 1.0  # scale for the canvas image zoom, public for outer classes

        self.ok_btn.place_forget()
        self.del_btn.place_forget()
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = None
        self.start_x = None
        self.start_y = None
        # Decide if this image huge or not
        self.__huge = False  # huge or not
        self.__huge_size = 14000  # define size of the huge image
        self.__band_width = 1024  # width of the tile band
        Image.MAX_IMAGE_PIXELS = (
            1000000000  # suppress DecompressionBombError for the big image
        )
        with warnings.catch_warnings():  # suppress DecompressionBombWarning
            warnings.simplefilter("ignore")
            self.__image = Image.fromarray(self.path)  # open image, but down't load it
        self.imwidth, self.imheight = self.__image.size  # public for outer classes
        if (
            self.imwidth * self.imheight > self.__huge_size * self.__huge_size
            and self.__image.tile[0][0] == "raw"
        ):  # only raw images could be tiled
            self.__huge = True  # image is huge
            self.__offset = self.__image.tile[0][2]  # initial tile offset
            self.__tile = [
                self.__image.tile[0][0],  # it have to be 'raw'
                [0, 0, self.imwidth, 0],  # tile extent (a rectangle)
                self.__offset,
                self.__image.tile[0][3],
            ]  # list of arguments to the decoder
        # Create image pyramid
        self.__pyramid = (
            [self.smaller()] if self.__huge else [Image.fromarray(self.path)]
        )
        # Set ratio coefficient for image pyramid
        self.__ratio = (
            max(self.imwidth, self.imheight) / self.__huge_size if self.__huge else 1.0
        )
        self.__curr_img = 0  # current image from the pyramid
        self.__scale = self.imscale * self.__ratio  # image pyramide scale
        w, h = self.__pyramid[-1].size
        while w > 512 and h > 512:  # top pyramid image is around 512 pixels in size
            w /= self.__reduction  # divide on reduction degree
            h /= self.__reduction  # divide on reduction degree
            self.__pyramid.append(
                self.__pyramid[-1].resize((int(w), int(h)), self.__filter)
            )
        # Put image into container rectangle and use it to set proper coordinates to the image
        if self.container:
            self.canvas.delete(self.container)
        self.container = self.canvas.create_rectangle(
            (0, 0, self.imwidth, self.imheight), width=1
        )

        self.table_box = [0, 0, 0, 0]
        self.__show_image()  # show image on the canvas
        loading.grid_forget()
        self.canvas.grid(row=0, column=0, sticky="nswe")
        self.canvas.update()
        self.canvas.focus_set()  # set focus on the canvas

    def smaller(self):
        """Resize image proportionally and return smaller image"""
        w1, h1 = float(self.imwidth), float(self.imheight)
        w2, h2 = float(self.__huge_size), float(self.__huge_size)
        aspect_ratio1 = w1 / h1
        aspect_ratio2 = w2 / h2  # it equals to 1.0
        if aspect_ratio1 == aspect_ratio2:
            image = Image.new("RGB", (int(w2), int(h2)))
            k = h2 / h1  # compression ratio
            w = int(w2)  # band length
        elif aspect_ratio1 > aspect_ratio2:
            image = Image.new("RGB", (int(w2), int(w2 / aspect_ratio1)))
            k = h2 / w1  # compression ratio
            w = int(w2)  # band length
        else:  # aspect_ratio1 < aspect_ration2
            image = Image.new("RGB", (int(h2 * aspect_ratio1), int(h2)))
            k = h2 / h1  # compression ratio
            w = int(h2 * aspect_ratio1)  # band length
        i, j = 0, 1
        while i < self.imheight:
            band = min(self.__band_width, self.imheight - i)  # width of the tile band
            self.__tile[1][3] = band  # set band width
            self.__tile[2] = (
                self.__offset + self.imwidth * i * 3
            )  # tile offset (3 bytes per pixel)
            self.__image.close()
            self.__image = Image.fromarray(self.path)  # reopen / reset image
            self.__image.size = (self.imwidth, band)  # set size of the tile band
            self.__image.tile = [self.__tile]  # set tile
            cropped = self.__image.crop((0, 0, self.imwidth, band))  # crop tile band
            image.paste(
                cropped.resize((w, int(band * k) + 1), self.__filter), (0, int(i * k))
            )
            self.__image.close()
            i += band
            j += 1
        return image

    def grid(self, **kw):
        """Put CanvasImage widget on the parent widget"""
        self.__imframe.grid(**kw)  # place CanvasImage widget on the grid
        self.__imframe.grid(sticky="nswe")  # make frame container sticky
        self.__imframe.rowconfigure(0, weight=1)  # make canvas expandable
        self.__imframe.columnconfigure(0, weight=1)

    def pack(self, **kw):
        """Exception: cannot use pack with this widget"""
        raise Exception("Cannot use pack with the widget " + self.__class__.__name__)

    def place(self, **_):
        """Exception: cannot use place with this widget"""
        raise Exception("Cannot use place with the widget " + self.__class__.__name__)

    def __create_box_buttons(self):
        def del_rect():
            self.ok_btn.place_forget()
            self.del_btn.place_forget()
            self.canvas.delete(self.rect)
            self.rect = None

        def commit_rect():
            self.ok_btn.place_forget()
            self.del_btn.place_forget()
            self.canvas.delete(self.rect)
            self.rect = None
            self.__extractor.extract_table(self.path, self.table_box)

        ok_img = Image.open("data/images/check.png")
        ok_img = ImageTk.PhotoImage(ok_img)
        self.ok_btn = Button(
            self.canvas,
            image=ok_img,
            command=commit_rect,
            bg="#ffffff",
            activebackground="#ffffff",
            fg="#ffffff",
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
        )
        self.ok_btn.image = ok_img  # keeps reference so tkinter doesnt garbage collect

        del_img = Image.open("data/images/remove.png")
        del_img = ImageTk.PhotoImage(del_img)
        self.del_btn = Button(
            self.canvas,
            image=del_img,
            command=del_rect,
            bg="#ffffff",
            activebackground="#ffffff",
            fg="#ffffff",
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
        )
        self.del_btn.image = del_img

    # noinspection PyUnusedLocal
    def __scroll_x(self, *args, **_):
        """Scroll canvas horizontally and redraw the image"""
        self.canvas.xview(*args)  # scroll horizontally
        self.__show_image()  # redraw the image

    # noinspection PyUnusedLocal
    def __scroll_y(self, *args, **_):
        """Scroll canvas vertically and redraw the image"""
        self.canvas.yview(*args)  # scroll vertically
        self.__show_image()  # redraw the image

    def __show_image(self):
        """Show image on the Canvas. Implements correct image zoom almost like in Google Maps"""
        box_image = self.canvas.coords(self.container)  # get image area
        box_canvas = (
            self.canvas.canvasx(0),  # get visible area of the canvas
            self.canvas.canvasy(0),
            self.canvas.canvasx(self.canvas.winfo_width()),
            self.canvas.canvasy(self.canvas.winfo_height()),
        )
        box_img_int = tuple(
            map(int, box_image)
        )  # convert to integer or it will not work properly
        # Get scroll region box
        box_scroll = [
            min(box_img_int[0], box_canvas[0]),
            min(box_img_int[1], box_canvas[1]),
            max(box_img_int[2], box_canvas[2]),
            max(box_img_int[3], box_canvas[3]),
        ]
        # Horizontal part of the image is in the visible area
        if box_scroll[0] == box_canvas[0] and box_scroll[2] == box_canvas[2]:
            box_scroll[0] = box_img_int[0]
            box_scroll[2] = box_img_int[2]
        # Vertical part of the image is in the visible area
        if box_scroll[1] == box_canvas[1] and box_scroll[3] == box_canvas[3]:
            box_scroll[1] = box_img_int[1]
            box_scroll[3] = box_img_int[3]
        # Convert scroll region to tuple and to integer
        self.canvas.configure(
            scrollregion=tuple(map(int, box_scroll))
        )  # set scroll region
        x1 = max(
            box_canvas[0] - box_image[0], 0
        )  # get coordinates (x1,y1,x2,y2) of the image tile
        y1 = max(box_canvas[1] - box_image[1], 0)
        x2 = min(box_canvas[2], box_image[2]) - box_image[0]
        y2 = min(box_canvas[3], box_image[3]) - box_image[1]

        if (
            int(x2 - x1) > 0 and int(y2 - y1) > 0
        ):  # show image if it is in the visible area
            if self.__huge and self.__curr_img < 0:  # show huge image
                h = int((y2 - y1) / self.imscale)  # height of the tile band
                self.__tile[1][3] = h  # set the tile band height
                self.__tile[2] = (
                    self.__offset + self.imwidth * int(y1 / self.imscale) * 3
                )
                self.__image.close()
                self.__image = Image.open(self.path)  # reopen / reset image
                self.__image.size = (self.imwidth, h)  # set size of the tile band
                self.__image.tile = [self.__tile]
                image = self.__image.crop(
                    (int(x1 / self.imscale), 0, int(x2 / self.imscale), h)
                )
            else:  # show normal image
                image = self.__pyramid[
                    max(0, self.__curr_img)
                ].crop(  # crop current img from pyramid
                    (
                        int(x1 / self.__scale),
                        int(y1 / self.__scale),
                        int(x2 / self.__scale),
                        int(y2 / self.__scale),
                    )
                )

            imagetk = ImageTk.PhotoImage(
                image.resize((int(x2 - x1), int(y2 - y1)), self.__filter)
            )
            imageid = self.canvas.create_image(
                max(
                    box_canvas[0], box_img_int[0]
                ),  # x location of top left corner of viewport on canvas
                max(
                    box_canvas[1], box_img_int[1]
                ),  # y location of top left corner of viewport on canvas
                anchor="nw",
                image=imagetk,
            )
            # print(f" max 1: { max(box_canvas[0], box_img_int[0])}")
            self.canvas.lower(imageid)  # set image into background
            self.canvas.imagetk = (
                imagetk  # keep an extra reference to prevent garbage-collection
            )

    def __on_button_press(self, event: Event):
        # save mouse drag start position

        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)

        # create rectangle if not yet exist
        if not self.rect:
            self.rect = self.canvas.create_rectangle(
                event.x,
                event.y,
                event.x + 1,
                event.y + 1,
                outline="blue",
                fill="blue",
                stipple="gray12",
            )

            self.ok_btn.place(x=10, y=10)
            self.del_btn.place(x=60, y=10)

        else:
            self.ok_btn.place_forget()
            self.del_btn.place_forget()
            self.canvas.delete(self.rect)
            self.rect = None
        self.table_box[0], self.table_box[1] = self.__get_img_mouse_pos(
            event.x, event.y
        )

    def __on_move_press(self, event: Event):

        if not self.rect:
            self.rect = self.canvas.create_rectangle(
                event.x,
                event.y,
                event.x + 1,
                event.y + 1,
                outline="blue",
                fill="blue",
                stipple="gray12",
            )
            self.ok_btn.place(x=10, y=10)
            self.del_btn.place(x=60, y=10)

        curX = self.canvas.canvasx(event.x)
        curY = self.canvas.canvasy(event.y)
        self.canvas["cursor"] = "cross"

        # autoscroll when dragging near edge
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if event.x > 0.95 * w:
            self.canvas.xview_scroll(1, "units")
        elif event.x < 0.05 * w:
            self.canvas.xview_scroll(-1, "units")
        if event.y > 0.95 * h:
            self.canvas.yview_scroll(1, "units")
        elif event.y < 0.05 * h:
            self.canvas.yview_scroll(-1, "units")

        # expand rectangle as you drag the mouse
        self.canvas.coords(self.rect, self.start_x, self.start_y, curX, curY)

        x, y = self.__get_img_mouse_pos(event.x, event.y)
        self.table_box[2] = x - self.table_box[0]
        self.table_box[3] = y - self.table_box[1]
        # print(self.table_box)

    def __on_button_release(self, _):
        """Reset the cursor style"""
        self.canvas["cursor"] = "tcross"

    def __move_from(self, event: Event):
        """Remember previous coordinates for scrolling with the mouse"""
        self.canvas.scan_mark(event.x, event.y)
        self.canvas["cursor"] = "fleur"

    def __move_to(self, event: Event):
        """Drag (move) canvas to the new position"""
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.__show_image()  # zoom tile and show it on the canvas

    def outside(self, x: int, y: int):
        """Checks if the point (x,y) is outside the image area"""
        bbox = self.canvas.coords(self.container)  # get image area
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]:
            return False  # point (x,y) is inside the image area
        return True  # point (x,y) is outside the image area

    def __wheel(self, event: Event):
        """Zoom with mouse wheel"""
        x = self.canvas.canvasx(event.x)  # get coordinates of the event on the canvas
        y = self.canvas.canvasy(event.y)
        if self.outside(x, y):
            return  # zoom only inside image area
        scale = 1.0
        # Respond to Linux (event.num) or Windows (event.delta) wheel event
        if event.num == 5 or event.delta == -120:  # scroll down, smaller
            if round(min(self.imwidth, self.imheight) * self.imscale) <= 30:
                return  # image is less than 30 pixels
            self.imscale /= self.__delta
            scale /= self.__delta
        if event.num == 4 or event.delta == 120:  # scroll up, bigger
            i = min(self.canvas.winfo_width(), self.canvas.winfo_height()) >> 1
            if i < self.imscale:
                return  # 1 pixel is bigger than the visible area
            self.imscale *= self.__delta
            scale *= self.__delta
        # Take appropriate image from the pyramid
        k = self.imscale * self.__ratio  # temporary coefficient
        self.__curr_img = min(
            (-1) * int(math.log(k, self.__reduction)), len(self.__pyramid) - 1
        )
        self.__scale = k * math.pow(self.__reduction, max(0, self.__curr_img))
        #
        self.canvas.scale("all", x, y, scale, scale)  # rescale all objects
        # Redraw some figures before showing image on the screen
        self.__show_image()

    def __keystroke(self, event: Event):
        """Scrolling with the keyboard.
        Independent from the language of the keyboard, CapsLock, <Ctrl>+<key>, etc."""
        if (
            event.state - self.__previous_state == 4
        ):  # means that the Control key is pressed
            pass  # do nothing if Control key is pressed
        else:
            self.__previous_state = event.state  # remember the last keystroke state
            # Up, Down, Left, Right keystrokes
            if event.keycode in [
                68,
                39,
                102,
            ]:  # scroll right: keys 'D', 'Right' or 'Numpad-6'
                self.__scroll_x("scroll", 1, "unit", event=event)
            elif event.keycode in [
                65,
                37,
                100,
            ]:  # scroll left: keys 'A', 'Left' or 'Numpad-4'
                self.__scroll_x("scroll", -1, "unit", event=event)
            elif event.keycode in [
                87,
                38,
                104,
            ]:  # scroll up: keys 'W', 'Up' or 'Numpad-8'
                self.__scroll_y("scroll", -1, "unit", event=event)
            elif event.keycode in [
                83,
                40,
                98,
            ]:  # scroll down: keys 'S', 'Down' or 'Numpad-2'
                self.__scroll_y("scroll", 1, "unit", event=event)

    def __get_img_mouse_pos(self, x: int, y: int):
        box_image = self.canvas.coords(self.container)  # get image area
        box_canvas = (
            self.canvas.canvasx(0),  # get visible area of the canvas
            self.canvas.canvasy(0),
            self.canvas.canvasx(self.canvas.winfo_width()),
            self.canvas.canvasy(self.canvas.winfo_height()),
        )
        box_img_int = tuple(
            map(int, box_image)
        )  # convert to integer or it will not work properly
        # Get scroll region box
        box_scroll = [
            min(box_img_int[0], box_canvas[0]),
            min(box_img_int[1], box_canvas[1]),
            max(box_img_int[2], box_canvas[2]),
            max(box_img_int[3], box_canvas[3]),
        ]
        # Horizontal part of the image is in the visible area
        if box_scroll[0] == box_canvas[0] and box_scroll[2] == box_canvas[2]:
            box_scroll[0] = box_img_int[0]
            box_scroll[2] = box_img_int[2]
        # Vertical part of the image is in the visible area
        if box_scroll[1] == box_canvas[1] and box_scroll[3] == box_canvas[3]:
            box_scroll[1] = box_img_int[1]
            box_scroll[3] = box_img_int[3]
        # Convert scroll region to tuple and to integer
        self.canvas.configure(
            scrollregion=tuple(map(int, box_scroll))
        )  # set scroll region
        x1 = max(box_canvas[0] - box_image[0], 0)
        y1 = max(box_canvas[1] - box_image[1], 0)
        x2 = min(box_canvas[2], box_image[2]) - box_image[0]
        y2 = min(box_canvas[3], box_image[3]) - box_image[1]
        can_width = self.canvas.winfo_width()
        can_height = self.canvas.winfo_height()

        pyramid_adjust = 2 ** self.__curr_img

        spacing_x = ((box_canvas[0] - box_image[0]) / self.__scale) * pyramid_adjust
        spacing_y = ((box_canvas[1] - box_image[1]) / self.__scale) * pyramid_adjust
        spacing_x2 = ((box_canvas[2] - box_image[2]) / self.__scale) * pyramid_adjust
        spacing_y2 = ((box_canvas[3] - box_image[3]) / self.__scale) * pyramid_adjust
        x1_new = (x1 / self.__scale) * pyramid_adjust
        x2_new = (x2 / self.__scale) * pyramid_adjust
        y1_new = (y1 / self.__scale) * pyramid_adjust
        y2_new = (y2 / self.__scale) * pyramid_adjust

        if box_canvas[0] - box_image[0] < 0:
            x1_new = x1_new + spacing_x
        if box_canvas[1] - box_image[1] < 0:
            y1_new = y1_new + spacing_y
        if box_canvas[2] - box_image[2] > 0:
            x2_new += spacing_x2
        if box_canvas[3] - box_image[3] > 0:
            y2_new += spacing_y2

        img_x = x1_new + (x2_new - x1_new) * (x / can_width)
        img_y = y1_new + (y2_new - y1_new) * (y / can_height)

        return img_x, img_y

    def crop(self, bbox: List):
        """Crop rectangle from the image and return it"""
        if self.__huge:  # image is huge and not totally in RAM
            band = bbox[3] - bbox[1]  # width of the tile band
            self.__tile[1][3] = band  # set the tile height
            self.__tile[2] = (
                self.__offset + self.imwidth * bbox[1] * 3
            )  # set offset of the band
            self.__image.close()
            self.__image = Image.open(self.path)  # reopen / reset image
            self.__image.size = (self.imwidth, band)  # set size of the tile band
            self.__image.tile = [self.__tile]
            return self.__image.crop((bbox[0], 0, bbox[2], band))

        return self.__pyramid[0].crop(bbox)

    def destroy(self):
        """ImageFrame destructor"""
        self.__image.close()
        map(lambda i: i.close, self.__pyramid)  # close all pyramid images
        del self.__pyramid[:]  # delete pyramid list
        del self.__pyramid  # delete pyramid variable
        self.canvas.destroy()
        self.__imframe.destroy()
