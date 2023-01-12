import sys as system
import os
import math
import json
import tkinter
import tkinter.tix

import cv2
import numpy as np

import tkinter as tk
from tkinter import *
from PIL import Image, ImageTk
from PIL import Image as PILImage

gui_resolution = (1800, 1000)
gui_update_ms = 10

app_tile_area = (1600, 800)  # Main tiling area
app_context_area = (200, 800)  # Options area
app_selection_area = (1800, 200)  # Tile selection area

grid_entry = (8, 8)
green = (0, 230, 0)
red = (230, 0, 0)
blue = (0, 0, 230)
# white = (230, 230, 230)
white = (0, 0, 0)


class JSONEntry:
    def __init__(self, x: int, y: int, tile: int):
        self._x = x
        self._y = y
        self._tile = tile

    def get_y(self):
        return self._y

    def set_y(self, y: int):
        self._y = y

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)


class GUIWindow(tk.Frame):
    def __init__(self, master):
        self.tk_master = master
        self.resolution = gui_resolution
        tk.Frame.__init__(self, self.tk_master)

        # Frames
        self.tiling_area = tk.Frame(master=self.tk_master, width=app_tile_area[0], height=app_tile_area[1], bg='black')
        self.context_area = tk.Frame(master=self.tk_master, width=app_context_area[0], height=app_context_area[1],
                                     bg='grey')
        self.selection_area = tk.Frame(master=self.tk_master, width=app_selection_area[0], height=app_selection_area[1],
                                       bg='red')

        self.tiles_spacing = 1  # Spacing between tiles
        self.pad = 1  # Spacing before first tile begins

        # Tiling Area
        self.tiling_tile = -1
        self.tiles_spacing_size = 1
        self.total_tiles_x = int(math.floor(app_tile_area[0] / grid_entry[0] + self.tiles_spacing_size))
        self.total_tiles_y = int(math.floor(app_tile_area[1] / grid_entry[1] + self.tiles_spacing_size))
        self.tk_tiles = []  # Tkinter display objects
        self.tiling_event_x = 0
        self.tiling_event_y = 0
        self.tiling_clicked = False
        # Generate Grid
        self.max_tiles_tiling_x = int(math.floor(app_tile_area[0] / ((grid_entry[0]) + self.tiles_spacing)))
        self.max_tiles_tiling_y = int(math.floor(app_tile_area[1] / ((grid_entry[1]) + self.tiles_spacing)))
        self.tiling_canvas_x = self.max_tiles_tiling_x * ((grid_entry[0]) + self.tiles_spacing) + 1
        self.tiling_canvas_y = self.max_tiles_tiling_y * ((grid_entry[1]) + self.tiles_spacing) + 1
        print(f'Tile Canvas {self.max_tiles_tiling_x} {self.max_tiles_tiling_y} | '
              f'{self.tiling_canvas_x} {self.tiling_canvas_y}')
        self.tiling_canvas = np.zeros((self.tiling_canvas_y, self.tiling_canvas_x, 3), np.uint8)
        # Fill tile data with dummy values
        self.tiling_canvas_tiles = []
        for i in range(self.max_tiles_tiling_x * self.max_tiles_tiling_y):
            self.tiling_canvas_tiles.append(-1)
        # Calculate grid placement
        self.tiling_grid_locations_x = [0]
        self.tiling_grid_locations_y = [0]
        for i in range(self.max_tiles_tiling_x):
            self.tiling_grid_locations_x.append((i * grid_entry[0]) + (1 * i))
        for i in range(self.max_tiles_tiling_y):
            self.tiling_grid_locations_y.append((i * grid_entry[1]) + (1 * i))
        # Render the grid
        for i in range(len(self.tiling_grid_locations_x)):
            self.tiling_canvas = cv2.line(self.tiling_canvas, (self.tiling_grid_locations_x[i], 0),
                                          (self.tiling_grid_locations_x[i], self.max_tiles_tiling_y * grid_entry[1] +
                                           self.max_tiles_tiling_y), white, 1)
        for i in range(len(self.tiling_grid_locations_y)):
            self.tiling_canvas = cv2.line(self.tiling_canvas, (0, self.tiling_grid_locations_y[i]),
                                          (self.max_tiles_tiling_x * grid_entry[0] + self.max_tiles_tiling_x,
                                           self.tiling_grid_locations_y[i]), white, 1)
        # cv2.imshow('img', self.tiling_canvas)
        # cv2.waitKey(ord('q'))
        # Set the Canvas to tkinter
        self.tiling_canvas_original = self.tiling_canvas.copy()
        self.tiling_im = Image.fromarray(self.tiling_canvas)
        self.tiling_im_tk = ImageTk.PhotoImage(image=self.tiling_im)
        self.tiling_im_tk_canvas = tk.Canvas(master=self.tiling_area, width=self.tiling_canvas_x,
                                             height=self.tiling_canvas_y, bg='grey')
        self.tiling_im_tk_cv_cfg = self.tiling_im_tk_canvas.create_image((0, 0), anchor=tk.NW, image=self.tiling_im_tk)
        self.tiling_im_tk_canvas.bind('<Motion>', self.tiling_area_mouse_motion)
        self.tiling_im_tk_canvas.bind('<Button-1>', self.tiling_area_mouse_click)
        self.tiling_current_hovered_tile = -1
        self.tiling_current_selected_tile = -1

        # Selection Area
        self.total_selections_x = 16
        self.total_selections_y = 10
        self.sel_tile = -1
        self.sel_event_x = 0
        self.sel_event_y = 0
        self.sel_clicked = False
        # Generate tiles from image
        self.tilemap = cv2.imread('tilemap.png')
        # cv2.imshow('img', self.tilemap)
        # cv2.waitKey(ord('q'))
        self.tilemap = cv2.cvtColor(self.tilemap, cv2.COLOR_BGR2RGB)
        self.sel_tiles_cv = []
        self.start_coordinate_x = 0
        self.start_coordinate_y = 0
        for i in range(self.total_selections_y):
            for j in range(self.total_selections_x):
                self.sel_tiles_cv.append(
                    self.tilemap[
                    i * grid_entry[0] + (self.tiles_spacing_size * i):(i * grid_entry[0] + grid_entry[0]) + (
                            self.tiles_spacing_size * i),
                    j * grid_entry[1] + (self.tiles_spacing_size * j):(j * grid_entry[1] + grid_entry[1]) + (
                            self.tiles_spacing_size * j)])
        # cv2.imwrite('img.png', self.sel_tiles_cv[69])
        # cv2.imshow('img', self.sel_tiles_cv[69])
        # cv2.waitKey(ord('q'))
        # Render tiles to new opencv image
        self.max_tiles_x = int(math.floor(app_selection_area[0] / ((grid_entry[0] * 4) + self.tiles_spacing)))
        self.max_tiles_y = int(math.ceil((self.total_selections_x * self.total_selections_y) / self.max_tiles_x))
        self.selection_canvas_x = self.max_tiles_x * ((grid_entry[0] * 4) + self.tiles_spacing) + 1
        self.selection_canvas_y = self.max_tiles_y * ((grid_entry[1] * 4) + self.tiles_spacing) + 1
        print(f'Selection Canvas {self.max_tiles_x} {self.max_tiles_y} | {self.selection_canvas_x} '
              f'{self.selection_canvas_y}')
        self.selection_canvas = np.zeros((self.selection_canvas_y, self.selection_canvas_x, 3), np.uint8)
        self.resized_tile_size = (grid_entry[0] * 4, grid_entry[1] * 4)
        # Resize tiles
        for i in range(len(self.sel_tiles_cv)):
            tile = self.get_coordinates_at_selection_tile(i)
            self.selection_canvas[tile[2]:tile[3], tile[0]:tile[1]] = cv2.resize(self.sel_tiles_cv[i],
                                                                                 self.resized_tile_size,
                                                                                 interpolation=cv2.INTER_LINEAR)
        # Set the canvas
        self.selection_canvas_original = self.selection_canvas.copy()
        self.sel_im = Image.fromarray(self.selection_canvas)
        self.sel_im_tk = ImageTk.PhotoImage(image=self.sel_im)
        self.sel_im_tk_canvas = tk.Canvas(master=self.selection_area, width=self.selection_canvas_x,
                                          height=self.selection_canvas_y, bg='grey')
        self.sel_im_tk_cv_cfg = self.sel_im_tk_canvas.create_image((0, 0), anchor=tk.NW, image=self.sel_im_tk)
        self.sel_im_tk_canvas.bind('<Motion>', self.selection_area_mouse_motion)
        self.sel_im_tk_canvas.bind('<Button-1>', self.selection_area_mouse_click)
        self.current_selection_hovered_tile = -1
        self.current_selection_selected_tile = -1

        # Context Area
        write_json_btn = Button(master=self.context_area, text='SAVE JSON', anchor='w', command=self.write_json)

        # Grids
        self.tiling_area.grid(row=0, column=1, sticky=W)
        self.context_area.grid(row=0, column=0, sticky=W)
        self.selection_area.grid(row=1, column=0, sticky=W, columnspan=2)
        self.tiling_im_tk_canvas.grid(row=0, column=0, sticky=NW)
        self.sel_im_tk_canvas.grid(row=0, column=0, sticky=NW)
        # Context Menu
        write_json_btn.grid(row=0, column=0, sticky=N)
        self.update()

    def get_coordinates_at_tiling_tile(self, tile: int) -> list:
        """Returns as [x1, x2, y1, y2]
        """
        row = int(math.floor(tile/self.max_tiles_tiling_x))
        column = tile
        while column >= self.max_tiles_tiling_x:
            column = column - self.max_tiles_tiling_x
        y1 = self.pad + (grid_entry[1] * row) + (row * self.tiles_spacing)
        y2 = self.pad + (grid_entry[1] * row + grid_entry[1]) + (row * self.tiles_spacing)
        x1 = self.pad + (grid_entry[0] * column) + (column * self.tiles_spacing)
        x2 = self.pad + (grid_entry[0] * column + grid_entry[0]) + (column * self.tiles_spacing)
        return [x1, x2, y1, y2]

    def get_coordinates_at_selection_tile(self, tile: int) -> list:
        """Returns as [x1, x2, y1, y2]
        """
        row = int(math.floor(tile / self.max_tiles_x))
        column = tile
        while column >= self.max_tiles_x:
            column = column - self.max_tiles_x
        y1 = self.pad + (self.resized_tile_size[1] * row) + (row * self.tiles_spacing)
        y2 = self.pad + (self.resized_tile_size[1] * row + self.resized_tile_size[1]) + (row * self.tiles_spacing)
        x1 = self.pad + (self.resized_tile_size[0] * column) + (column * self.tiles_spacing)
        x2 = self.pad + (self.resized_tile_size[0] * column + self.resized_tile_size[0]) + (column * self.tiles_spacing)
        return [x1, x2, y1, y2]

    def get_tile_at_tiling_coordinate(self, x: int, y: int) -> int:
        row = int(math.floor(y / (grid_entry[1] + self.tiles_spacing)))
        column = int(math.floor(x / (grid_entry[0] + self.tiles_spacing)))
        if row > 0:
            tmp = (row * self.max_tiles_tiling_x) + column
            if tmp < len(self.tiling_canvas_tiles):
                return tmp
            return -1
        else:
            return column

    def get_tile_at_selection_coordinate(self, x: int, y: int) -> int:
        row = int(math.floor(y / (self.resized_tile_size[1] + self.tiles_spacing)))
        column = int(math.floor(x / (self.resized_tile_size[0] + self.tiles_spacing)))
        if row > 0:
            tmp = row * self.max_tiles_x + column
            if tmp < len(self.sel_tiles_cv):
                return tmp
            return -1
        else:
            return column

    def draw_tile_to_tiling_canvas(self) -> None:
        coords_tile = self.get_coordinates_at_tiling_tile(self.tiling_current_hovered_tile)
        self.tiling_canvas_original[coords_tile[2]:coords_tile[3], coords_tile[0]:coords_tile[1]] = \
            self.sel_tiles_cv[self.current_selection_selected_tile]
        # Update Canvas
        self.tiling_im_tk = ImageTk.PhotoImage(Image.fromarray(self.tiling_canvas_original))
        self.tiling_im_tk_canvas.itemconfig(self.tiling_im_tk_cv_cfg, image=self.tiling_im_tk)
        # for i in range(len(self.tiling_canvas_tiles)):
        #    if self.tiling_canvas_tiles[i] != -1:
        #        print(self.tiling_canvas_tiles[i])

    def draw_square_tiling_tiles(self, coords_tile: list) -> None:
        self.tiling_canvas = self.tiling_canvas_original.copy()
        # Draw blue Square
        if self.tiling_current_hovered_tile > -1:
            self.tiling_canvas = cv2.rectangle(self.tiling_canvas, (coords_tile[0], coords_tile[2]),
                                               (coords_tile[1], coords_tile[3]), blue, 2)
        self.tiling_im_tk = ImageTk.PhotoImage(Image.fromarray(self.tiling_canvas))
        self.tiling_im_tk_canvas.itemconfig(self.tiling_im_tk_cv_cfg, image=self.tiling_im_tk)

    def draw_squares_selection_tiles(self, coords_blue: list) -> None:
        self.selection_canvas = self.selection_canvas_original.copy()
        if self.current_selection_selected_tile > -1:
            # Draw red square
            coords_red = self.get_coordinates_at_selection_tile(self.current_selection_selected_tile)
            self.selection_canvas = cv2.rectangle(self.selection_canvas, (coords_red[0], coords_red[2]),
                                                  (coords_red[1], coords_red[3]), red, 3)
        if self.sel_tile > -1:
            # Draw green square
            self.selection_canvas = cv2.rectangle(self.selection_canvas, (coords_blue[0], coords_blue[2]),
                                                  (coords_blue[1], coords_blue[3]), green, 3)
        self.sel_im_tk = ImageTk.PhotoImage(Image.fromarray(self.selection_canvas))
        self.sel_im_tk_canvas.itemconfig(self.sel_im_tk_cv_cfg, image=self.sel_im_tk)

    def tiling_area_mouse_click(self, event) -> None:
        self.tiling_clicked = True

    def selection_area_mouse_click(self, event) -> None:
        self.sel_clicked = True

    def tiling_area_mouse_motion(self, event) -> None:
        self.tiling_event_x = event.x
        self.tiling_event_y = event.y
        self.sel_event_x = 0
        self.sel_event_y = 0

    def selection_area_mouse_motion(self, event) -> None:
        self.sel_event_x = event.x
        self.sel_event_y = event.y
        self.tiling_event_x = 0
        self.tiling_event_y = 0

    def write_json(self) -> None:
        _x = 0
        _y = 0
        entries = []
        out_start = '{"list":['
        out_end = ']}'
        out = out_start
        for i in range(len(self.tiling_canvas_tiles)):
            if self.tiling_canvas_tiles[i] != -1:
                # Calculate coordinates
                _y = int(math.floor(i / self.max_tiles_tiling_x))
                if i >= self.max_tiles_tiling_x:
                    _x = i - _y * self.max_tiles_tiling_x
                else:
                    _x = i
                # Write to json
                entries.append(JSONEntry(x=_x, y=_y, tile=self.tiling_canvas_tiles[i]))

        # Invert y axis for Unity
        # Max and min algorithm for y-axis
        max_entry = 0
        min_entry = sys.maxsize
        for i in entries:
            if max_entry < i.get_y():
                max_entry = i.get_y()
            if min_entry > i.get_y():
                min_entry = i.get_y()
        delta = max_entry - min_entry
        cutoff = delta/2
        # Invert
        for i in range(len(entries)):
            entries[i].set_y(y=(max_entry - entries[i].get_y()))

        # Write to json
        for i in range(len(entries)):
            out = out + entries[i].to_json()
            if i != len(entries) - 1:
                out = out + ','
        out = out + out_end
        text = open('out.json', 'w')
        _ = text.write(out)
        text.close()

    def update(self) -> None:
        """Update elements of the GUI
        """
        # Check current hovered tiles

        # Update tile being edited
        if self.tiling_clicked:
            self.tiling_current_selected_tile = self.get_tile_at_tiling_coordinate(self.tiling_event_x,
                                                                                   self.tiling_event_y)
        # Tiling
        if self.tiling_event_x != 0 or self.tiling_event_y != 0:
            # Draw blue square on the hovered tile
            self.tiling_current_hovered_tile = self.get_tile_at_tiling_coordinate(self.tiling_event_x,
                                                                                  self.tiling_event_y)
            self.draw_square_tiling_tiles(self.get_coordinates_at_tiling_tile(self.tiling_current_hovered_tile))
            # Only draw the new tile on click
            if self.tiling_clicked:
                if self.current_selection_selected_tile > -1:
                    self.tiling_canvas_tiles[self.tiling_current_selected_tile] = self.current_selection_selected_tile
                self.draw_tile_to_tiling_canvas()
        else:
            self.tiling_current_hovered_tile = -1
        # Selection
        if self.sel_event_x != 0 or self.sel_event_y != 0:
            # Calculate hovered tile location
            self.current_selection_hovered_tile = self.get_tile_at_selection_coordinate(self.sel_event_x,
                                                                                        self.sel_event_y)
        else:
            self.current_selection_hovered_tile = -1
        # Draw green and red squares
        self.sel_tile = self.get_tile_at_selection_coordinate(self.sel_event_x, self.sel_event_y)
        self.draw_squares_selection_tiles(self.get_coordinates_at_selection_tile(self.sel_tile))
        """
        print(f'{self.tiling_event_x} {self.tiling_event_y} {self.tiling_clicked} '
              f'{self.tiling_current_hovered_tile} '
              f'{self.get_coordinates_at_tiling_tile(self.tiling_current_hovered_tile)} | {self.sel_event_x} '
              f'{self.sel_event_y} {self.sel_clicked} {self.current_selection_hovered_tile}',
              self.get_coordinates_at_selection_tile(self.get_tile_at_selection_coordinate(
                  self.sel_event_x, self.sel_event_y)))
        """

        if self.sel_clicked:
            self.current_selection_selected_tile = self.get_tile_at_selection_coordinate(self.sel_event_x, self.sel_event_y)
            self.sel_clicked = False
        self.tiling_clicked = False
        # Call this function again
        self.after(gui_update_ms, self.update)


def main():
    # Start GUI
    gui_window = tk.Tk()
    gui_window.geometry(str(gui_resolution[0]) + 'x' + str(gui_resolution[1]))
    gui_application = GUIWindow(gui_window)
    gui_window.mainloop()


if __name__ == '__main__':
    main()
