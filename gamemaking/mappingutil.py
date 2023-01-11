import sys as system
import os
import math
import tkinter

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

        # Tiling Area
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
        self.tiling_canvas = np.zeros((self.tiling_canvas_y, self.tiling_canvas_x, 3), np.uint8)
        print(f'Tile Canvas {self.max_tiles_tiling_x} {self.max_tiles_tiling_y} | '
              f'{self.tiling_canvas_x} {self.tiling_canvas_y}')
        # Render Grid
        self.tiling_canvas = np.zeros((self.tiling_canvas_y, self.tiling_canvas_x, 3), np.uint8)
        # Set the Canvas
        self.tiling_area.bind('<Motion>', self.tiling_area_mouse_motion)
        self.tiling_area.bind('<Button-1>', self.tiling_area_mouse_click)

        # Selection Area
        self.total_selections_x = 16
        self.total_selections_y = 10
        self.tile = -1
        self.sel_event_x = 0
        self.sel_event_y = 0
        self.sel_clicked = False
        # Generate tiles from image
        self.tilemap = cv2.imread('tilemap.png')
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
        self.pad = 1
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
        self.current_hovered_tile = -1
        self.current_selected_tile = -1

        # Grids
        self.tiling_area.grid(row=0, column=1, sticky=W)
        self.context_area.grid(row=0, column=0, sticky=W)
        self.selection_area.grid(row=1, column=0, sticky=W, columnspan=2)
        self.sel_im_tk_canvas.grid(row=0, column=0, sticky=NW)
        self.update()

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

    def draw_squares_selection_tiles(self, coords_blue: list) -> None:
        self.selection_canvas = self.selection_canvas_original.copy()
        if self.current_selected_tile > -1:
            # Draw red square
            coords_red = self.get_coordinates_at_selection_tile(self.current_selected_tile)
            self.selection_canvas = cv2.rectangle(self.selection_canvas, (coords_red[0], coords_red[2]),
                                                  (coords_red[1], coords_red[3]), red, 3)
        if self.tile > -1:
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

    def update(self) -> None:
        """Update elements of the GUI
        """
        if self.sel_event_x != 0 or self.sel_event_y != 0:
            self.current_hovered_tile = self.get_tile_at_selection_coordinate(self.sel_event_x, self.sel_event_y)
        else:
            self.current_hovered_tile = -1
        self.tile = self.get_tile_at_selection_coordinate(self.sel_event_x, self.sel_event_y)
        self.draw_squares_selection_tiles(self.get_coordinates_at_selection_tile(self.tile))
        print(f'{self.tiling_event_x} {self.tiling_event_y} {self.tiling_clicked} | {self.sel_event_x} '
              f'{self.sel_event_y} {self.sel_clicked} {self.current_hovered_tile}',
              self.get_coordinates_at_selection_tile(self.get_tile_at_selection_coordinate(
                  self.sel_event_x, self.sel_event_y)))
        if self.tiling_clicked:
            self.tiling_clicked = False
        if self.sel_clicked:
            self.current_selected_tile = self.get_tile_at_selection_coordinate(self.sel_event_x, self.sel_event_y)
            self.sel_clicked = False
        self.after(gui_update_ms, self.update)


def main():
    # Start GUI
    gui_window = tk.Tk()
    gui_window.geometry(str(gui_resolution[0]) + 'x' + str(gui_resolution[1]))
    gui_application = GUIWindow(gui_window)
    gui_window.mainloop()


if __name__ == '__main__':
    main()
