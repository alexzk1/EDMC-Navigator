import tkinter as tk
from os import path
from typing import ClassVar


class IconsCache:
    iconDir: ClassVar[str] = path.join(path.dirname(__file__), "icons")
    icons: ClassVar[dict[str, tk.PhotoImage]]


IconsCache.icons = {
    "left_arrow": tk.PhotoImage(file=path.join(IconsCache.iconDir, "left_arrow.gif")),
    "right_arrow": tk.PhotoImage(file=path.join(IconsCache.iconDir, "right_arrow.gif")),
    "view_open": tk.PhotoImage(file=path.join(IconsCache.iconDir, "view_open.gif")),
    "view_close": tk.PhotoImage(file=path.join(IconsCache.iconDir, "view_close.gif")),
    "view_sort": tk.PhotoImage(file=path.join(IconsCache.iconDir, "view_sort.gif")),
    "resize": tk.PhotoImage(file=path.join(IconsCache.iconDir, "resize.gif")),
}
