import math
import json
import copy

import cv2
import numpy as np
import tkinter as tk
from tkinter import *
from PIL import Image, ImageTk

gui_resolution = (1800, 1000)
gui_update_ms = 10

app_tile_area = (1600, 800)  # Main tiling area
app_context_area = (200, 800)  # Options area
app_selection_area = (1800, 200)  # Tile selection area

grid_entry = (8, 8)
green, red, blue, black = (0, 230, 0), (230, 0, 0), (0, 0, 230), (0, 0, 0)
null_tile = np.zeros((grid_entry[1], grid_entry[0], 3), np.uint8)  # What an empty tile looks like
out_json_name = 'out.json'

layer_number_to_name = {  # Strings for context area
    0: 'Background',
    1: 'Object',
    2: 'Entity',
    3: 'Foreground',
    4: 'Effect',
    5: 'Lighting'
}

out_json_strs = {  # Json beginnings/endings for writine out json, NOT reading in
    0: '"listBG":[',
    1: '"listOBJ":[',
    2: '"listENT":[',
    3: '"listFG":[',
    4: '"listEFF":[',
    5: '"listLIT":['
}


class JSONEntry:
    """JSON wrapper for tile data
    """
    def __init__(self, x: int, y: int, tile: int):
        self._x = x
        self._y = y
        self._tile = tile

    def get_y(self):
        return self._y

    def set_y(self, y: int):
        self._y = y

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, separators=(',', ':'))

    def __str__(self) -> str:
        return f'JSON Wrapper at x:{self._x} y:{self._y} tile:{self._tile}'


class GUIWindow(tk.Frame):
    """Main GUI Application thread
    """

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
        self.tiling_event_x, self.tiling_event_y = 0, 0
        self.tiling_clicked, self.tiling_right_clicked = False, False
        # Generate Grid
        self.max_tiles_tiling_x = int(math.floor(app_tile_area[0] / ((grid_entry[0]) + self.tiles_spacing)))
        self.max_tiles_tiling_y = int(math.floor(app_tile_area[1] / ((grid_entry[1]) + self.tiles_spacing)))
        self.tiling_canvas_x = self.max_tiles_tiling_x * ((grid_entry[0]) + self.tiles_spacing) + 1
        self.tiling_canvas_y = self.max_tiles_tiling_y * ((grid_entry[1]) + self.tiles_spacing) + 1
        self.tiling_canvas = np.zeros((self.tiling_canvas_y, self.tiling_canvas_x, 3), np.uint8)
        # Fill tile data with dummy values
        self.tiling_canvas_tiles = []
        for i in range(self.max_tiles_tiling_x * self.max_tiles_tiling_y):
            self.tiling_canvas_tiles.append(-1)
        # Set up other layers on the map
        self.tiling_tiles_all = []
        [self.tiling_tiles_all.append(copy.deepcopy(self.tiling_canvas_tiles))
         for i in range(len(layer_number_to_name))]
        # Calculate grid placement
        self.tiling_grid_locations_x, self.tiling_grid_locations_y = [0], [0]
        for i in range(self.max_tiles_tiling_x):
            self.tiling_grid_locations_x.append((i * grid_entry[0]) + (1 * i))
        for i in range(self.max_tiles_tiling_y):
            self.tiling_grid_locations_y.append((i * grid_entry[1]) + (1 * i))
        # Render the grid
        for i in range(len(self.tiling_grid_locations_x)):
            self.tiling_canvas = cv2.line(self.tiling_canvas, (self.tiling_grid_locations_x[i], 0),
                                          (self.tiling_grid_locations_x[i], self.max_tiles_tiling_y * grid_entry[1] +
                                           self.max_tiles_tiling_y), black, 1)
        for i in range(len(self.tiling_grid_locations_y)):
            self.tiling_canvas = cv2.line(self.tiling_canvas, (0, self.tiling_grid_locations_y[i]),
                                          (self.max_tiles_tiling_x * grid_entry[0] + self.max_tiles_tiling_x,
                                           self.tiling_grid_locations_y[i]), black, 1)
        # Set the Canvas to tkinter
        self.tiling_canvas_modified = self.tiling_canvas.copy()
        self.tiling_im = Image.fromarray(self.tiling_canvas)
        self.tiling_im_tk = ImageTk.PhotoImage(image=self.tiling_im)
        self.tiling_im_tk_canvas = tk.Canvas(master=self.tiling_area, width=self.tiling_canvas_x,
                                             height=self.tiling_canvas_y, bg='grey')
        self.tiling_im_tk_cv_cfg = self.tiling_im_tk_canvas.create_image((0, 0), anchor=tk.NW, image=self.tiling_im_tk)
        self.tiling_im_tk_canvas.bind('<Motion>', self.tiling_area_mouse_motion)
        self.tiling_im_tk_canvas.bind('<Button-1>', self.tiling_area_mouse_click)
        self.tiling_im_tk_canvas.bind('<Button-3>', self.tiling_area_mouse_click_right)
        self.tiling_current_hovered_tile, self.tiling_current_selected_tile = -1, -1
        self.tiling_current_selected_tile_right = -1

        # Selection Area
        # Temp hard code of tilemap size, intention is for user to input at runtime
        self.total_selections_x, self.total_selections_y = 16, 10
        self.sel_tile = -1
        self.sel_event_x, self.sel_event_y = 0, 0
        self.sel_clicked = False
        # Generate tiles from image
        self.tilemap = cv2.imread('tilemap.png')
        self.tilemap = cv2.cvtColor(self.tilemap, cv2.COLOR_BGR2RGB)
        self.sel_tiles_cv = []
        self.start_coordinate_x, self.start_coordinate_y = 0, 0
        for i in range(self.total_selections_y):
            for j in range(self.total_selections_x):
                self.sel_tiles_cv.append(
                    self.tilemap[i * grid_entry[0] +
                                 (self.tiles_spacing_size * i):(i * grid_entry[0] + grid_entry[0]) + (self.tiles_spacing_size * i), j * grid_entry[1] + (self.tiles_spacing_size * j):(j * grid_entry[1] + grid_entry[1]) + (self.tiles_spacing_size * j)])
        # Render tiles to new opencv image
        self.sel_max_tiles_x = int(math.floor(app_selection_area[0] / ((grid_entry[0] * 4) + self.tiles_spacing)))
        self.sel_max_tiles_y = int(
            math.ceil((self.total_selections_x * self.total_selections_y) / self.sel_max_tiles_x))
        self.selection_canvas_x = self.sel_max_tiles_x * ((grid_entry[0] * 4) + self.tiles_spacing) + 1
        self.selection_canvas_y = self.sel_max_tiles_y * ((grid_entry[1] * 4) + self.tiles_spacing) + 1
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
        self.load_map_btn = Button(master=self.context_area, text='LOAD JSON', anchor='n', command=self.read_json)
        self.write_json_btn = Button(master=self.context_area, text='SAVE JSON', anchor='n', command=self.write_json)
        self.layers_text, self.layers_selected_btns = [], []
        [self.layers_text.append(Button(master=self.context_area, text=f'{layer_number_to_name[i]}', anchor='n'))
         for i in range(len(layer_number_to_name))]
        self.tiling_current_layer = 0
        self.tk_layers_selected_value = IntVar(master=self.context_area, value=self.tiling_current_layer)
        [self.layers_selected_btns.append(Radiobutton(master=self.context_area, variable=self.tk_layers_selected_value,
                                                      padx=0, pady=0, value=i)) for i in range(len(self.layers_text))]

        # Grids
        self.tiling_area.grid(row=0, column=1, sticky=W)
        self.context_area.grid(row=0, column=0, sticky=W)
        self.selection_area.grid(row=1, column=0, sticky=W, columnspan=2)
        self.tiling_im_tk_canvas.grid(row=0, column=0, sticky=NW)
        self.sel_im_tk_canvas.grid(row=0, column=0, sticky=NW)
        # Context Menu
        self.load_map_btn.grid(row=0, column=0)
        self.write_json_btn.grid(row=0, column=1)
        [self.layers_text[i].grid(row=i+1, column=0, columnspan=2) for i in range(len(self.layers_text))]
        [self.layers_selected_btns[i].grid(row=i+1, column=2) for i in range(len(self.layers_selected_btns))]

        # Start the GUI
        self.tiling_canvas_tiles = self.tiling_tiles_all[self.tiling_current_layer]
        self.update()

    def get_coordinates_at_tiling_tile(self, tile: int) -> list:
        """Returns as [x1, x2, y1, y2]
        """
        row = int(math.floor(tile / self.max_tiles_tiling_x))
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
        row = int(math.floor(tile / self.sel_max_tiles_x))
        column = tile
        while column >= self.sel_max_tiles_x:
            column = column - self.sel_max_tiles_x
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
            tmp = row * self.sel_max_tiles_x + column
            if tmp < len(self.sel_tiles_cv):
                return tmp
            return -1
        else:
            return column

    def redraw_canvas(self) -> None:
        """Redraws the canvas when the layer is switched.
        """
        self.tiling_canvas_modified = np.zeros((self.tiling_canvas_y, self.tiling_canvas_x, 3), np.uint8)
        for i in range(len(self.tiling_tiles_all[self.tiling_current_layer])):
            if self.tiling_tiles_all[self.tiling_current_layer][i] is not -1:
                self.draw_tile_to_tiling_canvas_no_render(coordinates=self.get_coordinates_at_tiling_tile(i),
                                                          tile=self.tiling_tiles_all[self.tiling_current_layer][i])
        # Update Canvas
        self.tiling_im_tk = ImageTk.PhotoImage(Image.fromarray(self.tiling_canvas_modified))
        self.tiling_im_tk_canvas.itemconfig(self.tiling_im_tk_cv_cfg, image=self.tiling_im_tk)

    def draw_tile_to_tiling_canvas(self) -> None:
        coords_tile = self.get_coordinates_at_tiling_tile(self.tiling_current_hovered_tile)
        self.tiling_canvas_modified[coords_tile[2]:coords_tile[3], coords_tile[0]:coords_tile[1]] = \
            self.sel_tiles_cv[self.current_selection_selected_tile]
        # Update Canvas
        self.tiling_im_tk = ImageTk.PhotoImage(Image.fromarray(self.tiling_canvas_modified))
        self.tiling_im_tk_canvas.itemconfig(self.tiling_im_tk_cv_cfg, image=self.tiling_im_tk)

    def draw_tile_to_tiling_canvas_no_render(self, coordinates, tile) -> None:
        """Behavior is similar to draw_tile_to_tiling_canvas, but does not render the canvas with an itemconfig call.
        Used for updating multiple tiles at once to redraw the entire canvas.
        """
        self.tiling_canvas_modified[coordinates[2]:coordinates[3], coordinates[0]:coordinates[1]] = \
            self.sel_tiles_cv[tile]

    def draw_tile_removal_to_tiling_canvas(self) -> None:
        """Removes pixel data from where a tile was, setting it to default empty values.
        """
        coords_tile = self.get_coordinates_at_tiling_tile(self.tiling_current_hovered_tile)
        self.tiling_canvas_modified[coords_tile[2]:coords_tile[3], coords_tile[0]:coords_tile[1]] = null_tile
        self.tiling_im_tk = ImageTk.PhotoImage(Image.fromarray(self.tiling_canvas_modified))
        self.tiling_im_tk_canvas.itemconfig(self.tiling_im_tk_cv_cfg, image=self.tiling_im_tk)

    def draw_square_tiling_tiles(self, coords_tile: list) -> None:
        self.tiling_canvas = self.tiling_canvas_modified.copy()
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

    def tiling_area_mouse_click_right(self, event) -> None:
        self.tiling_right_clicked = True

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
        all_map_entries = []
        # Json preambles for object data, can be edited here temporarily instead of user defined in GUI
        # May change this later so other users can define layer names
        out_start, out_end_mid, out_end = '{', '],', '}'
        out = out_start
        for i in range(len(self.tiling_tiles_all)):
            all_map_entries.append([])
            for j in range(len(self.tiling_tiles_all[i])):
                if self.tiling_tiles_all[i][j] != -1:
                    # Calculate Coordinates
                    _y = int(math.floor(j / self.max_tiles_tiling_x))
                    if j >= self.max_tiles_tiling_x:
                        _x = j - _y * self.max_tiles_tiling_x
                    else:
                        _x = j
                    # Export to json wrapper object
                    all_map_entries[i].append(JSONEntry(x=_x, y=_y, tile=self.tiling_tiles_all[i][j]))
        # Invert y axis for Unity, opencv draws from top left y=0, Unity uses a math x-y plot
        max_entry = 0
        for i in all_map_entries[0]:
            if max_entry < i.get_y():
                max_entry = i.get_y()
        for i in all_map_entries:
            [j.set_y(y=(max_entry - j.get_y())) for j in i]  # Invert
        # Write to json
        for i in range(len(all_map_entries)):
            set_val = False
            out = out + out_json_strs[i]
            for j in all_map_entries[i]:
                set_val = True
                out = out + j.to_json()
                out = out + ','
            if set_val:
                out = out[:-1] + out_end_mid
            else:
                out = out + out_end_mid
        out = out[:-1] + out_end
        text = open(out_json_name, 'w')
        _ = text.write(out)
        text.close()

    def read_json(self) -> None:
        """Read json map data from disk.
        """
        self.tiling_tiles_all = []   # Clear map data that already exists
        # Load json from disk
        tiles_by_layer = []
        text = open(out_json_name, 'r')
        tiles = json.load(text)
        [tiles_by_layer.append(tiles[list(tiles.keys())[i]]) for i in range(len(tiles.keys()))]
        data_l0 = []
        [data_l0.append(tiles_by_layer[0][i]) for i in range(len(tiles_by_layer[0]))]
        print(tiles_by_layer)
        print(data_l0)
        # Load object data into tiles
        # Update the tilemap

    def update(self) -> None:
        """Update elements of the GUI
        """
        # Update the layer in the tiling layer if we swapped layers
        if self.tk_layers_selected_value.get() is not self.tiling_current_layer:
            self.tiling_current_layer = self.tk_layers_selected_value.get()
            self.tiling_canvas_tiles = self.tiling_tiles_all[self.tiling_current_layer]
            self.redraw_canvas()
        # Get the tile being edited in the tiling layer
        if self.tiling_clicked and not self.tiling_right_clicked:  # User left clicked to place tile
            self.tiling_current_selected_tile = self.get_tile_at_tiling_coordinate(self.tiling_event_x,
                                                                                   self.tiling_event_y)
        if self.tiling_right_clicked and not self.tiling_clicked:  # User right clicked to remove tile
            self.tiling_current_selected_tile_right = self.get_tile_at_tiling_coordinate(self.tiling_event_x,
                                                                                         self.tiling_event_y)
        # Update the tiling area
        if self.tiling_event_x != 0 or self.tiling_event_y != 0:
            # Draw blue square on the hovered tile
            self.tiling_current_hovered_tile = self.get_tile_at_tiling_coordinate(self.tiling_event_x,
                                                                                  self.tiling_event_y)
            self.draw_square_tiling_tiles(self.get_coordinates_at_tiling_tile(self.tiling_current_hovered_tile))
            # Draw the selected tile on a left click
            if self.tiling_clicked and not self.tiling_right_clicked:
                if self.current_selection_selected_tile > -1:  # Check if a tile is selected in the first place
                    self.tiling_canvas_tiles[self.tiling_current_selected_tile] = self.current_selection_selected_tile
                self.draw_tile_to_tiling_canvas()
            # Remove the tile on a right click
            if self.tiling_right_clicked and not self.tiling_clicked:
                self.tiling_canvas_tiles[self.tiling_current_selected_tile_right] = -1  # Clear the tile data
                self.draw_tile_removal_to_tiling_canvas()  # Draw removed tile
        else:
            self.tiling_current_hovered_tile = -1
        # Update the selection area
        if self.sel_event_x != 0 or self.sel_event_y != 0:
            # Calculate hovered tile location
            self.current_selection_hovered_tile = self.get_tile_at_selection_coordinate(self.sel_event_x,
                                                                                        self.sel_event_y)
        else:
            self.current_selection_hovered_tile = -1
        # Draw green and red squares in the selection area, green = hovered, red = selected
        self.sel_tile = self.get_tile_at_selection_coordinate(self.sel_event_x, self.sel_event_y)
        self.draw_squares_selection_tiles(self.get_coordinates_at_selection_tile(self.sel_tile))
        # Get tile swapped to in the selection layer
        if self.sel_clicked:
            self.current_selection_selected_tile = self.get_tile_at_selection_coordinate(self.sel_event_x,
                                                                                         self.sel_event_y)
            self.sel_clicked = False
        self.tiling_clicked = False
        self.tiling_right_clicked = False
        # Call this function again
        self.after(gui_update_ms, self.update)


def main():
    """Sets up and starts the GUI.
    """
    # Start GUI
    gui_window = tk.Tk()
    gui_window.geometry(str(gui_resolution[0]) + 'x' + str(gui_resolution[1]))
    gui_application = GUIWindow(gui_window)
    gui_application.tk_master.mainloop()


if __name__ == '__main__':
    main()
