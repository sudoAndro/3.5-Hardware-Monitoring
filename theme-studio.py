#!/usr/bin/env python
# SPDX-License-Identifier: GPL-3.0-or-later
#
# theme-studio.py: "sudoAndro Studio" – Steuerzentrale und WYSIWYG-Editor fuer den
# turing-smart-screen-python System-Monitor (Turing Smart Screen 3.5").
# Seiten: Start (Monitor-Steuerung), Studio (Drag&Drop-Editor), Einstellungen, Info.
# Basiert auf der Rendering-Pipeline von theme-editor.py (GPL-3.0), UI eigenstaendig.
#
# Aufruf:  python theme-studio.py [Themename]

from library.pythoncheck import check_python_version

check_python_version()

import copy
import logging
import os
import shutil
import subprocess
import sys

import yaml

try:
    import tkinter as tk
    from tkinter import ttk, colorchooser, filedialog, messagebox, simpledialog
    from PIL import Image, ImageTk, ImageFont, ImageOps
except ImportError:
    print("[FEHLER] Tkinter/Pillow nicht installiert.")
    sys.exit(1)

import library.log

library.log.logger.setLevel(logging.ERROR)

# Erster Start: config.yaml aus der Vorlage anlegen (die persoenliche config.yaml
# ist nicht Teil des Repos, weil sie API-Key und Standort enthaelt)
_here = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__))
if not os.path.exists(os.path.join(_here, "config.yaml")) and \
        os.path.exists(os.path.join(_here, "config.example.yaml")):
    shutil.copy(os.path.join(_here, "config.example.yaml"), os.path.join(_here, "config.yaml"))

# Kaputte/geloeschte Theme-Referenz in config.yaml reparieren, BEVOR library.config
# importiert wird: library/config.py laedt beim reinen Import (Modul-Ebene) sofort das
# dort eingetragene Theme und beendet den kompletten Prozess lautlos (sys.exit/os._exit),
# falls der Ordner fehlt - ohne sichtbares Fenster oder Fehlermeldung bei pythonw/.exe.
try:
    _cfg_path = os.path.join(_here, "config.yaml")
    with open(_cfg_path, "rt", encoding="utf8") as f:
        _cfg_text = f.read()
    _cfg = yaml.safe_load(_cfg_text) or {}
    _theme_name = (_cfg.get("config") or {}).get("THEME", "")
    _themes_root = os.path.join(_here, "res", "themes")
    if not os.path.isfile(os.path.join(_themes_root, _theme_name, "theme.yaml")):
        _fallback = "sudoAndro" if os.path.isfile(
            os.path.join(_themes_root, "sudoAndro", "theme.yaml")) else None
        if _fallback is None:
            for _name in sorted(os.listdir(_themes_root)):
                if os.path.isfile(os.path.join(_themes_root, _name, "theme.yaml")):
                    _fallback = _name
                    break
        if _fallback:
            import re as _re
            _cfg_text_new = _re.sub(r"(?m)^(\s*THEME:\s*).*$", r"\g<1>" + _fallback,
                                    _cfg_text, count=1)
            if _cfg_text_new != _cfg_text:
                with open(_cfg_path, "wt", encoding="utf8") as f:
                    f.write(_cfg_text_new)
except Exception:
    pass  # Im Zweifel unveraendert lassen - der normale Fallback in main() greift dann noch

# ---------------------------------------------------------------- Konfiguration vor Display-Import
from library import config

config.CONFIG_DATA["config"]["HW_SENSORS"] = "STATIC"  # Editor nutzt immer statische Beispieldaten
config.CONFIG_DATA["display"]["REVISION"] = "SIMU"  # Editor rendert nie auf das echte Display

THEMES_DIR = os.path.join(str(config.MAIN_DIRECTORY), "res", "themes")
FONTS_DIR = os.path.join(str(config.MAIN_DIRECTORY), "res", "fonts")

DEFAULT_FONT = "jetbrains-mono/JetBrainsMono-Bold.ttf"
TASK_NAME = "TuringSmartScreen"
APP_VERSION = "1.0"

# ---------------------------------------------------------------- sudoAndro Farbwelt
C_BG = "#0b0e14"          # Fenster-Hintergrund
C_SIDEBAR = "#0e1420"     # Seitenleiste
C_PANEL = "#131a26"       # Panels / Karten
C_FIELD = "#1b2433"       # Eingabefelder
C_ACCENT = "#00aeff"      # sudoAndro-Cyan
C_ACCENT_DARK = "#0077b3"
C_FG = "#e6edf3"          # Haupttext
C_FG_DIM = "#8b98a5"      # Nebentext
C_OK = "#3ddc84"
C_ERR = "#ff5555"

# ---------------------------------------------------------------- Deutsche Bezeichnungen
TOKEN_DE = {
    "STATS": "Sensoren", "static_text": "Feste Texte", "static_images": "Bilder",
    "CPU": "CPU", "GPU": "GPU", "MEMORY": "RAM", "DISK": "Festplatte", "NET": "Netzwerk",
    "DATE": "Datum/Uhr", "UPTIME": "Laufzeit", "WEATHER": "Wetter", "PING": "Ping", "CUSTOM": "Eigene",
    "PERCENTAGE": "Auslastung", "FREQUENCY": "Takt", "TEMPERATURE": "Temperatur", "FAN_SPEED": "Lüfter",
    "LOAD": "Load", "ONE": "1min", "FIVE": "5min", "FIFTEEN": "15min",
    "MEMORY_PERCENT": "VRAM %", "MEMORY_USED": "VRAM belegt", "MEMORY_TOTAL": "VRAM gesamt", "FPS": "FPS",
    "SWAP": "Swap", "VIRTUAL": "Arbeitsspeicher", "USED": "Belegt", "FREE": "Frei", "TOTAL": "Gesamt",
    "PERCENT_TEXT": "Prozent", "ETH": "LAN", "WLO": "WLAN",
    "UPLOAD": "Upload", "UPLOADED": "Hochgeladen", "DOWNLOAD": "Download", "DOWNLOADED": "Heruntergeladen",
    "DAY": "Datum", "HOUR": "Uhrzeit", "SECONDS": "Sekunden", "FORMATTED": "Formatiert",
    "TEMPERATURE_FELT": "Gefühlt", "UPDATE_TIME": "Aktualisiert", "HUMIDITY": "Luftfeuchte",
    "WEATHER_DESCRIPTION": "Beschreibung",
    "TEXT": "Text", "GRAPH": "Balken", "RADIAL": "Ring", "LINE_GRAPH": "Verlauf",
    "ICON": "Symbol",
}

PROP_DE = {
    "SHOW": "Sichtbar", "SHOW_UNIT": "Einheit anzeigen", "SHOW_TEXT": "Wert anzeigen",
    "X": "X", "Y": "Y", "WIDTH": "Breite", "HEIGHT": "Höhe", "RADIUS": "Radius",
    "FONT": "Schriftart", "FONT_SIZE": "Schriftgröße", "FONT_COLOR": "Schriftfarbe",
    "BACKGROUND_COLOR": "Hintergrundfarbe", "BACKGROUND_IMAGE": "Hintergrundbild",
    "TEXT": "Text", "PATH": "Datei",
    "MIN_VALUE": "Min-Wert", "MAX_VALUE": "Max-Wert", "BAR_COLOR": "Balkenfarbe",
    "BAR_OUTLINE": "Balken-Rahmen", "BAR_BACKGROUND_COLOR": "Balken-Hintergrund",
    "DRAW_BAR_BACKGROUND": "Balken-Hintergrund zeichnen", "BAR_DECORATION": "Balken-Deko",
    "ANGLE_START": "Startwinkel", "ANGLE_END": "Endwinkel", "ANGLE_STEPS": "Winkel-Schritte",
    "ANGLE_SEP": "Winkel-Abstand", "CLOCKWISE": "Im Uhrzeigersinn",
    "LINE_COLOR": "Linienfarbe", "LINE_WIDTH": "Linienbreite", "HISTORY_SIZE": "Historie (Werte)",
    "AUTOSCALE": "Auto-Skalierung", "AXIS": "Achsen anzeigen", "AXIS_COLOR": "Achsenfarbe",
    "ANCHOR": "Ausrichtung", "ALIGN": "Textausrichtung",
}

BOOL_KEYS = {"SHOW", "SHOW_UNIT", "SHOW_TEXT", "BAR_OUTLINE", "DRAW_BAR_BACKGROUND",
             "CLOCKWISE", "AUTOSCALE", "AXIS"}
COLOR_KEYS = {"FONT_COLOR", "BACKGROUND_COLOR", "BAR_COLOR", "BAR_BACKGROUND_COLOR",
              "LINE_COLOR", "AXIS_COLOR"}
INT_KEYS = {"X", "Y", "WIDTH", "HEIGHT", "RADIUS", "FONT_SIZE", "MIN_VALUE", "MAX_VALUE",
            "ANGLE_START", "ANGLE_END", "ANGLE_STEPS", "ANGLE_SEP", "LINE_WIDTH", "HISTORY_SIZE"}
HIDDEN_KEYS = {"INTERVAL"}

PROP_ORDER = ["SHOW", "TEXT", "X", "Y", "WIDTH", "HEIGHT", "RADIUS", "FONT", "FONT_SIZE",
              "FONT_COLOR", "BACKGROUND_COLOR", "BACKGROUND_IMAGE", "SHOW_UNIT", "SHOW_TEXT",
              "MIN_VALUE", "MAX_VALUE", "BAR_COLOR", "BAR_OUTLINE", "BAR_BACKGROUND_COLOR",
              "DRAW_BAR_BACKGROUND", "LINE_COLOR", "LINE_WIDTH", "HISTORY_SIZE", "AUTOSCALE",
              "AXIS", "AXIS_COLOR", "ANGLE_START", "ANGLE_END", "ANGLE_STEPS", "ANGLE_SEP",
              "CLOCKWISE", "PATH", "ANCHOR", "ALIGN"]

KIND_TEXT, KIND_GRAPH, KIND_RADIAL, KIND_LINE = "TEXT", "GRAPH", "RADIAL", "LINE_GRAPH"
ALL_KINDS = [KIND_TEXT, KIND_GRAPH, KIND_RADIAL, KIND_LINE]
KIND_DE = {KIND_TEXT: "Text", KIND_GRAPH: "Balken", KIND_RADIAL: "Ring", KIND_LINE: "Verlaufsgraph"}

SENSOR_PALETTE = [
    ("CPU Auslastung", ("CPU", "PERCENTAGE"), ALL_KINDS),
    ("CPU Temperatur", ("CPU", "TEMPERATURE"), ALL_KINDS),
    ("CPU Takt", ("CPU", "FREQUENCY"), [KIND_TEXT, KIND_GRAPH, KIND_LINE]),
    ("CPU Lüfter", ("CPU", "FAN_SPEED"), [KIND_TEXT, KIND_GRAPH, KIND_RADIAL]),
    ("GPU Auslastung", ("GPU", "PERCENTAGE"), ALL_KINDS),
    ("GPU Temperatur", ("GPU", "TEMPERATURE"), ALL_KINDS),
    ("GPU VRAM %", ("GPU", "MEMORY_PERCENT"), [KIND_TEXT, KIND_GRAPH, KIND_RADIAL]),
    ("GPU VRAM belegt", ("GPU", "MEMORY_USED"), [KIND_TEXT]),
    ("GPU VRAM gesamt", ("GPU", "MEMORY_TOTAL"), [KIND_TEXT]),
    ("GPU Lüfter", ("GPU", "FAN_SPEED"), [KIND_TEXT, KIND_GRAPH, KIND_RADIAL]),
    ("GPU Takt", ("GPU", "FREQUENCY"), [KIND_TEXT, KIND_GRAPH, KIND_LINE]),
    ("GPU FPS", ("GPU", "FPS"), [KIND_TEXT, KIND_GRAPH, KIND_LINE]),
    ("RAM Prozent", ("MEMORY", "VIRTUAL", "PERCENT_TEXT"), [KIND_TEXT]),
    ("RAM belegt", ("MEMORY", "VIRTUAL", "USED"), [KIND_TEXT]),
    ("RAM frei", ("MEMORY", "VIRTUAL", "FREE"), [KIND_TEXT]),
    ("RAM gesamt", ("MEMORY", "VIRTUAL", "TOTAL"), [KIND_TEXT]),
    ("RAM Balken/Ring", ("MEMORY", "VIRTUAL"), [KIND_GRAPH, KIND_RADIAL, KIND_LINE]),
    ("Festplatte belegt", ("DISK", "USED", "TEXT"), [KIND_TEXT]),
    ("Festplatte Prozent", ("DISK", "USED", "PERCENT_TEXT"), [KIND_TEXT]),
    ("Festplatte frei", ("DISK", "FREE", "TEXT"), [KIND_TEXT]),
    ("Festplatte gesamt", ("DISK", "TOTAL", "TEXT"), [KIND_TEXT]),
    ("Festplatte Balken/Ring", ("DISK", "USED"), [KIND_GRAPH, KIND_RADIAL]),
    ("LAN Download", ("NET", "ETH", "DOWNLOAD", "TEXT"), [KIND_TEXT]),
    ("LAN Upload", ("NET", "ETH", "UPLOAD", "TEXT"), [KIND_TEXT]),
    ("WLAN Download", ("NET", "WLO", "DOWNLOAD", "TEXT"), [KIND_TEXT]),
    ("WLAN Upload", ("NET", "WLO", "UPLOAD", "TEXT"), [KIND_TEXT]),
    ("Datum", ("DATE", "DAY", "TEXT"), [KIND_TEXT]),
    ("Uhrzeit", ("DATE", "HOUR", "TEXT"), [KIND_TEXT]),
    ("Laufzeit (Uptime)", ("UPTIME", "FORMATTED", "TEXT"), [KIND_TEXT]),
    ("Wetter Symbol", ("WEATHER", "ICON"), [KIND_TEXT]),
    ("Wetter Temperatur", ("WEATHER", "TEMPERATURE", "TEXT"), [KIND_TEXT]),
    ("Wetter gefühlt", ("WEATHER", "TEMPERATURE_FELT", "TEXT"), [KIND_TEXT]),
    ("Wetter Beschreibung", ("WEATHER", "WEATHER_DESCRIPTION", "TEXT"), [KIND_TEXT]),
    ("Wetter Luftfeuchte", ("WEATHER", "HUMIDITY", "TEXT"), [KIND_TEXT]),
    ("Ping", ("PING", "TEXT"), [KIND_TEXT]),
]

GROUP_INTERVAL = {"CPU": 1, "GPU": 1, "MEMORY": 5, "DISK": 10, "NET": 1, "DATE": 1,
                  "UPTIME": 5, "WEATHER": 300, "PING": 5}


# ---------------------------------------------------------------- Hilfsfunktionen
def color_to_hex(value):
    try:
        if isinstance(value, str):
            r, g, b = [int(v) for v in value.split(",")]
        elif isinstance(value, (list, tuple)):
            r, g, b = value[:3]
        else:
            return "#ffffff"
        return "#%02x%02x%02x" % (r, g, b)
    except Exception:
        return "#ffffff"


def hex_to_color(hx):
    hx = hx.lstrip("#")
    return "%d, %d, %d" % (int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16))


def list_fonts():
    fonts = []
    for root, _dirs, files in os.walk(FONTS_DIR):
        for f in files:
            if f.lower().endswith((".ttf", ".otf")):
                rel = os.path.relpath(os.path.join(root, f), FONTS_DIR)
                fonts.append(rel.replace("\\", "/"))
    return sorted(fonts)


def list_themes():
    themes = []
    for name in sorted(os.listdir(THEMES_DIR), key=str.casefold):
        yml = os.path.join(THEMES_DIR, name, "theme.yaml")
        if not os.path.isfile(yml):
            continue
        try:
            with open(yml, "rt", encoding="utf8") as f:
                data = yaml.safe_load(f)
            size = (data or {}).get("display", {}).get("DISPLAY_SIZE", '3.5"')
        except Exception:
            continue
        if size == '3.5"':
            themes.append(name)
    return themes


def de_label(path):
    parts = [TOKEN_DE.get(p, p) for p in path if p not in ("STATS",)]
    return " › ".join(parts)


def task_running():
    """Prueft ueber schtasks, ob der Display-Monitor laeuft."""
    try:
        out = subprocess.run(["schtasks", "/query", "/tn", TASK_NAME, "/fo", "LIST"],
                             capture_output=True, text=True, timeout=10,
                             creationflags=subprocess.CREATE_NO_WINDOW)
        if out.returncode != 0:
            return None  # Aufgabe existiert nicht
        for line in out.stdout.splitlines():
            if line.strip().startswith(("Status", "Zustand")):
                val = line.split(":", 1)[1].strip().lower()
                return ("ausgef" in val) or ("running" in val)
    except Exception:
        pass
    return None


class Element:
    def __init__(self, path, node):
        self.path = path  # Tupel, z.B. ("STATS","CPU","TEMPERATURE","TEXT")
        self.node = node  # direkte Referenz in das Theme-Dict

    @property
    def visible(self):
        if self.path[0] in ("static_text", "static_images"):
            return True
        return bool(self.node.get("SHOW", False))

    @property
    def label(self):
        return de_label(self.path)


# ---------------------------------------------------------------- Haupt-Anwendung
class ThemeStudio(tk.Tk):
    def __init__(self, theme_name):
        super().__init__()
        self.title("sudoAndro Studio")
        self.configure(bg=C_BG)
        self.minsize(1080, 620)
        self._setup_style()
        self._enable_dark_titlebar()
        try:
            icon_path = config.MAIN_DIRECTORY / "res/themes/sudoAndro/sudoandro-icon.png"
            if icon_path.exists():
                self.iconphoto(True, tk.PhotoImage(file=str(icon_path)))
        except Exception:
            pass

        self.fonts = list_fonts()
        self.theme_name = theme_name
        self.theme = None
        self.elements = []
        self.selected = None
        self.zoom = 1.5
        self.text_boxes = {}
        self.render_image = None
        self._drag = None
        self._render_pending = False
        self._undo = []
        self._backup_done = False
        self._prop_widgets = []
        self._nav_buttons = {}
        self._pages = {}

        self._wrap_display_text()
        self._build_ui()
        self.open_theme(theme_name)
        self.show_page("studio")

        self.bind("<Control-z>", lambda e: self.undo())
        self.bind("<Control-s>", lambda e: self.save())

    # ------------------------------------------------ Design
    def _setup_style(self):
        st = ttk.Style(self)
        st.theme_use("clam")
        st.configure(".", background=C_BG, foreground=C_FG, fieldbackground=C_FIELD,
                     bordercolor=C_PANEL, lightcolor=C_PANEL, darkcolor=C_PANEL,
                     troughcolor=C_FIELD, focuscolor=C_ACCENT, font=("Segoe UI", 10))
        st.configure("TFrame", background=C_BG)
        st.configure("Panel.TFrame", background=C_PANEL)
        st.configure("TLabel", background=C_BG, foreground=C_FG)
        st.configure("Panel.TLabel", background=C_PANEL, foreground=C_FG)
        st.configure("Dim.TLabel", background=C_BG, foreground=C_FG_DIM)
        st.configure("PanelDim.TLabel", background=C_PANEL, foreground=C_FG_DIM)
        st.configure("Title.TLabel", background=C_BG, foreground=C_FG,
                     font=("Segoe UI Semibold", 16))
        st.configure("Accent2.TLabel", background=C_BG, foreground=C_ACCENT,
                     font=("Segoe UI Semibold", 11))
        st.configure("TButton", background=C_FIELD, foreground=C_FG, borderwidth=0,
                     focusthickness=0, padding=(10, 6))
        st.map("TButton", background=[("active", "#26324a"), ("pressed", "#26324a")])
        st.configure("Accent.TButton", background=C_ACCENT, foreground="#001018",
                     font=("Segoe UI Semibold", 10), padding=(12, 6))
        st.map("Accent.TButton", background=[("active", "#33c1ff"), ("pressed", C_ACCENT_DARK)],
               foreground=[("active", "#001018")])
        st.configure("Danger.TButton", background="#3a1f28", foreground="#ff8899")
        st.map("Danger.TButton", background=[("active", "#552633")])
        st.configure("TCombobox", fieldbackground=C_FIELD, background=C_FIELD,
                     foreground=C_FG, arrowcolor=C_FG, selectbackground=C_FIELD,
                     selectforeground=C_FG)
        st.map("TCombobox", fieldbackground=[("readonly", C_FIELD)],
               foreground=[("readonly", C_FG)])
        st.configure("TEntry", fieldbackground=C_FIELD, foreground=C_FG,
                     insertcolor=C_FG)
        st.configure("TSpinbox", fieldbackground=C_FIELD, foreground=C_FG,
                     insertcolor=C_FG, arrowcolor=C_FG, background=C_FIELD)
        st.configure("TCheckbutton", background=C_PANEL, foreground=C_FG)
        st.map("TCheckbutton", background=[("active", C_PANEL)])
        st.configure("Treeview", background=C_PANEL, fieldbackground=C_PANEL,
                     foreground=C_FG, borderwidth=0, rowheight=24)
        st.map("Treeview", background=[("selected", C_ACCENT_DARK)],
               foreground=[("selected", "#ffffff")])
        st.configure("Vertical.TScrollbar", background=C_FIELD, troughcolor=C_BG,
                     arrowcolor=C_FG_DIM, bordercolor=C_BG)
        st.configure("TScale", background=C_BG)
        # Dropdown-Listen der Comboboxen
        self.option_add("*TCombobox*Listbox.background", C_FIELD)
        self.option_add("*TCombobox*Listbox.foreground", C_FG)
        self.option_add("*TCombobox*Listbox.selectBackground", C_ACCENT_DARK)
        self.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")

    def _enable_dark_titlebar(self):
        try:
            import ctypes
            self.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            value = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value),
                                                       ctypes.sizeof(value))
        except Exception:
            pass

    # ------------------------------------------------ Rendering
    def _wrap_display_text(self):
        from library.display import display
        self.display = display
        orig = display.lcd.DisplayText
        studio = self

        def wrapper(text, x=0, y=0, width=0, height=0, font=None, font_size=20, **kw):
            try:
                if width > 0 and height > 0:
                    w, h = width, height
                else:
                    f = ImageFont.truetype(font, font_size)
                    bb = f.getbbox(str(text))
                    w = width if width > 0 else (bb[2] - bb[0])
                    h = height if height > 0 else max(font_size, bb[3] - bb[1])
                studio.text_boxes[(int(x), int(y))] = (max(8, int(w)), max(8, int(h * 1.15)))
            except Exception:
                studio.text_boxes[(int(x), int(y))] = (max(30, font_size * 3), max(12, font_size))
            return orig(text=text, x=x, y=y, width=width, height=height,
                        font=font, font_size=font_size, **kw)

        display.lcd.DisplayText = wrapper

    def render(self):
        """Theme aus dem Speicher rendern -> PIL-Bild in self.render_image."""
        self.text_boxes.clear()
        # Bitmap-Cache leeren: library/lcd/lcd_comm.py cached Bilder dauerhaft nach
        # Dateipfad. Da im Studio Hintergrund-/Bilddateien jederzeit unter demselben
        # Namen ueberschrieben werden koennen, wuerde sonst die ALTE Version im
        # Speicher haengen bleiben, bis das Programm neu gestartet wird.
        if hasattr(self.display.lcd, "image_cache"):
            self.display.lcd.image_cache.clear()
        config.CONFIG_DATA["config"]["THEME"] = self.theme_name
        merged = copy.deepcopy(self.theme)
        config.THEME_DATA = merged
        config.copy_default(config.THEME_DEFAULT, config.THEME_DATA)
        config.THEME_DATA["PATH"] = os.path.join(THEMES_DIR, self.theme_name) + "/"

        import library.stats as stats
        d = self.display
        d.initialize_display()
        d.display_static_images()
        d.display_static_text()
        t = config.THEME_DATA["STATS"]
        try:
            if t["CPU"]["PERCENTAGE"].get("INTERVAL", 0) > 0: stats.CPU.percentage()
            if t["CPU"]["FREQUENCY"].get("INTERVAL", 0) > 0: stats.CPU.frequency()
            if t["CPU"]["LOAD"].get("INTERVAL", 0) > 0: stats.CPU.load()
            if t["CPU"]["TEMPERATURE"].get("INTERVAL", 0) > 0: stats.CPU.temperature()
            if t["CPU"]["FAN_SPEED"].get("INTERVAL", 0) > 0: stats.CPU.fan_speed()
            if t["GPU"].get("INTERVAL", 0) > 0: stats.Gpu.stats()
            if t["MEMORY"].get("INTERVAL", 0) > 0: stats.Memory.stats()
            if t["DISK"].get("INTERVAL", 0) > 0: stats.Disk.stats()
            if t["NET"].get("INTERVAL", 0) > 0: stats.Net.stats()
            if t["DATE"].get("INTERVAL", 0) > 0: stats.Date.stats()
            if t["UPTIME"].get("INTERVAL", 0) > 0: stats.SystemUptime.stats()
            if t["CUSTOM"].get("INTERVAL", 0) > 0: stats.Custom.stats()
            if t["WEATHER"].get("INTERVAL", 0) > 0: stats.Weather.stats()
            if t["PING"].get("INTERVAL", 0) > 0: stats.Ping.stats()
        except Exception as e:
            self.status.set("Fehler beim Rendern: %s" % e)
        self.render_image = self.display.lcd.screen_image.copy()

    # ------------------------------------------------ Elemente & Trefferflaechen
    def discover_elements(self):
        self.elements = []

        def add(path, node):
            self.elements.append(Element(path, node))

        for section in ("static_images", "static_text"):
            for name, node in (self.theme.get(section) or {}).items():
                if isinstance(node, dict) and "X" in node and "Y" in node:
                    add((section, name), node)

        def rec(node, path):
            if not isinstance(node, dict):
                return
            if "X" in node and "Y" in node:
                add(path, node)
                return
            for k, v in node.items():
                rec(v, path + (k,))

        rec(self.theme.get("STATS") or {}, ("STATS",))

    def element_bbox(self, el):
        n = el.node
        x = int(n.get("X", 0))
        y = int(n.get("Y", 0))
        if "RADIUS" in n:
            r = int(n.get("RADIUS", 20))
            return x - r, y - r, x + r, y + r
        if el.path[0] == "static_images" or ("WIDTH" in n and "HEIGHT" in n and "FONT" not in n):
            return x, y, x + int(n.get("WIDTH", 20)), y + int(n.get("HEIGHT", 20))
        box = self.text_boxes.get((x, y))
        if box:
            return x, y, x + box[0], y + box[1]
        fs = int(n.get("FONT_SIZE", 20))
        return x, y, x + fs * 4, y + int(fs * 1.3)

    def hit_test(self, px, py):
        best, best_area = None, None
        for el in self.elements:
            x0, y0, x1, y1 = self.element_bbox(el)
            if x0 - 2 <= px <= x1 + 2 and y0 - 2 <= py <= y1 + 2:
                area = (x1 - x0) * (y1 - y0)
                if el.path[:2] == ("static_images", "BACKGROUND"):
                    continue  # Hintergrund nicht per Klick waehlbar
                if best is None or area < best_area:
                    best, best_area = el, area
        return best

    # ------------------------------------------------ UI-Grundgeruest
    def _build_ui(self):
        # Seitenleiste
        sidebar = tk.Frame(self, bg=C_SIDEBAR, width=190)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        logo_frame = tk.Frame(sidebar, bg=C_SIDEBAR)
        logo_frame.pack(pady=(18, 8))
        try:
            logo_img = Image.open(
                str(config.MAIN_DIRECTORY / "res/themes/sudoAndro/sudoandro-icon.png")
            ).resize((72, 72), Image.LANCZOS)
            self._logo_tk = ImageTk.PhotoImage(logo_img)
            tk.Label(logo_frame, image=self._logo_tk, bg=C_SIDEBAR).pack()
        except Exception:
            pass
        wordmark = tk.Frame(sidebar, bg=C_SIDEBAR)
        wordmark.pack(pady=(0, 18))
        tk.Label(wordmark, text="sudo", fg=C_FG, bg=C_SIDEBAR,
                 font=("Segoe UI Semibold", 15)).pack(side=tk.LEFT)
        tk.Label(wordmark, text="Andro", fg=C_ACCENT, bg=C_SIDEBAR,
                 font=("Segoe UI Semibold", 15)).pack(side=tk.LEFT)

        for key, label in (("start", "  🏠  Start"), ("studio", "  🎨  Studio"),
                           ("settings", "  ⚙️  Einstellungen"), ("info", "  ℹ️  Info")):
            btn = tk.Button(sidebar, text=label, anchor="w", relief=tk.FLAT, bd=0,
                            bg=C_SIDEBAR, fg=C_FG_DIM, activebackground=C_PANEL,
                            activeforeground=C_FG, font=("Segoe UI", 12), cursor="hand2",
                            padx=16, pady=10, command=lambda k=key: self.show_page(k))
            btn.pack(fill=tk.X)
            self._nav_buttons[key] = btn

        tk.Label(sidebar, text="v%s" % APP_VERSION, bg=C_SIDEBAR, fg="#3a4656",
                 font=("Segoe UI", 9)).pack(side=tk.BOTTOM, pady=10)

        # Inhaltsbereich + Statusleiste
        content_holder = tk.Frame(self, bg=C_BG)
        content_holder.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.status = tk.StringVar(value="Bereit.")
        tk.Label(content_holder, textvariable=self.status, bg=C_SIDEBAR, fg=C_FG_DIM,
                 anchor="w", padx=12, pady=4, font=("Segoe UI", 9)).pack(
            side=tk.BOTTOM, fill=tk.X)

        self.content = tk.Frame(content_holder, bg=C_BG)
        self.content.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._pages["start"] = self._build_start_page()
        self._pages["studio"] = self._build_studio_page()
        self._pages["settings"] = self._build_settings_page()
        self._pages["info"] = self._build_info_page()

    def show_page(self, key):
        for k, page in self._pages.items():
            page.pack_forget()
        for k, btn in self._nav_buttons.items():
            btn.configure(bg=C_SIDEBAR, fg=C_FG_DIM)
        self._nav_buttons[key].configure(bg=C_PANEL, fg=C_ACCENT)
        self._pages[key].pack(fill=tk.BOTH, expand=True)
        if key == "start":
            self._refresh_start_page()
        elif key == "settings":
            self._load_settings_fields()

    # ================================================ Seite: Start
    def _build_start_page(self):
        page = tk.Frame(self.content, bg=C_BG)

        ttk.Label(page, text="Display-Monitor", style="Title.TLabel").pack(
            anchor="w", padx=24, pady=(20, 2))
        ttk.Label(page, text="Steuert das 3,5\"-Display (Turing Smart Screen, COM-Anschluss)",
                  style="Dim.TLabel").pack(anchor="w", padx=24)

        card = tk.Frame(page, bg=C_PANEL)
        card.pack(fill=tk.X, padx=24, pady=14)
        row = tk.Frame(card, bg=C_PANEL)
        row.pack(fill=tk.X, padx=16, pady=14)
        self.monitor_dot = tk.Label(row, text="●", bg=C_PANEL, fg=C_FG_DIM,
                                    font=("Segoe UI", 14))
        self.monitor_dot.pack(side=tk.LEFT)
        self.monitor_status = tk.Label(row, text="Status wird geprüft…", bg=C_PANEL,
                                       fg=C_FG, font=("Segoe UI", 11))
        self.monitor_status.pack(side=tk.LEFT, padx=8)
        ttk.Button(row, text="⟳ Neu starten", style="Accent.TButton",
                   command=self.monitor_restart).pack(side=tk.RIGHT, padx=4)
        ttk.Button(row, text="⏹ Stoppen", style="Danger.TButton",
                   command=self.monitor_stop).pack(side=tk.RIGHT, padx=4)

        ttk.Label(page, text="Aktives Theme", style="Title.TLabel").pack(
            anchor="w", padx=24, pady=(14, 2))
        theme_card = tk.Frame(page, bg=C_PANEL)
        theme_card.pack(fill=tk.BOTH, expand=True, padx=24, pady=(8, 20))
        left = tk.Frame(theme_card, bg=C_PANEL)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=16, pady=16)
        self.start_theme_var = tk.StringVar(value=self.theme_name)
        self.start_theme_combo = ttk.Combobox(left, textvariable=self.start_theme_var,
                                              values=list_themes(), state="readonly", width=26)
        self.start_theme_combo.pack(anchor="w")
        self.start_theme_combo.bind("<<ComboboxSelected>>",
                                    lambda e: self._update_start_preview())
        ttk.Button(left, text="✔ Aktivieren & an Display senden", style="Accent.TButton",
                   command=self.activate_theme_from_start).pack(anchor="w", pady=10)
        ttk.Button(left, text="🎨 Im Studio bearbeiten",
                   command=self.edit_theme_from_start).pack(anchor="w")
        self.start_preview_label = tk.Label(theme_card, bg=C_PANEL)
        self.start_preview_label.pack(side=tk.RIGHT, padx=16, pady=16)
        return page

    def _refresh_start_page(self):
        running = task_running()
        if running is True:
            self.monitor_dot.configure(fg=C_OK)
            self.monitor_status.configure(text="Monitor läuft – Display wird versorgt")
        elif running is False:
            self.monitor_dot.configure(fg=C_ERR)
            self.monitor_status.configure(text="Monitor gestoppt")
        else:
            self.monitor_dot.configure(fg=C_FG_DIM)
            self.monitor_status.configure(text="Aufgabe „%s“ nicht gefunden" % TASK_NAME)
        self.start_theme_combo["values"] = list_themes()
        try:
            active = config.load_yaml(config.MAIN_DIRECTORY / "config.yaml")["config"]["THEME"]
            self.start_theme_var.set(active)
        except Exception:
            pass
        self._update_start_preview()

    def _update_start_preview(self):
        name = self.start_theme_var.get()
        preview = os.path.join(THEMES_DIR, name, "preview.png")
        if not os.path.exists(preview):
            preview = os.path.join(THEMES_DIR, name, "background.png")
        try:
            img = Image.open(preview)
            img.thumbnail((420, 280), Image.LANCZOS)
            self._start_preview_tk = ImageTk.PhotoImage(img)
            self.start_preview_label.configure(image=self._start_preview_tk, text="")
        except Exception:
            self.start_preview_label.configure(image="", text="Keine Vorschau vorhanden",
                                               fg=C_FG_DIM, font=("Segoe UI", 11))

    def monitor_restart(self):
        subprocess.run(["schtasks", "/end", "/tn", TASK_NAME], capture_output=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)
        self.after(1500, lambda: (
            subprocess.run(["schtasks", "/run", "/tn", TASK_NAME], capture_output=True,
                           creationflags=subprocess.CREATE_NO_WINDOW),
            self.after(1500, self._refresh_start_page)))
        self.status.set("Monitor wird neu gestartet…")

    def monitor_stop(self):
        subprocess.run(["schtasks", "/end", "/tn", TASK_NAME], capture_output=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)
        self.after(1200, self._refresh_start_page)
        self.status.set("Monitor gestoppt.")

    def activate_theme_from_start(self):
        name = self.start_theme_var.get()
        self._set_active_theme_in_config(name)
        self.monitor_restart()
        self.status.set("Theme „%s“ aktiviert und an das Display gesendet." % name)

    def edit_theme_from_start(self):
        self.open_theme(self.start_theme_var.get())
        self.show_page("studio")

    def _set_active_theme_in_config(self, name):
        try:
            cfg_path = str(config.MAIN_DIRECTORY / "config.yaml")
            with open(cfg_path, "rt", encoding="utf8") as f:
                raw = f.read()
            cfg = yaml.safe_load(raw)
            old = cfg["config"].get("THEME")
            if old != name:
                raw = raw.replace("THEME: %s" % old, "THEME: %s" % name, 1)
                with open(cfg_path, "wt", encoding="utf8") as f:
                    f.write(raw)
        except Exception as e:
            self.status.set("config.yaml konnte nicht angepasst werden: %s" % e)

    # ================================================ Seite: Studio (Editor)
    def _build_studio_page(self):
        page = tk.Frame(self.content, bg=C_BG)

        top = tk.Frame(page, bg=C_BG)
        top.pack(side=tk.TOP, fill=tk.X, padx=10, pady=8)

        ttk.Label(top, text="Theme:").pack(side=tk.LEFT)
        self.theme_var = tk.StringVar(value=self.theme_name)
        self.theme_combo = ttk.Combobox(top, textvariable=self.theme_var, width=24,
                                        values=list_themes(), state="readonly")
        self.theme_combo.pack(side=tk.LEFT, padx=4)
        self.theme_combo.bind("<<ComboboxSelected>>", lambda e: self.open_theme(self.theme_var.get()))

        ttk.Button(top, text="Neues Theme…", command=self.new_theme).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text="Hintergrundbild…", command=self.choose_background).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text="💾 Speichern", command=self.save).pack(side=tk.LEFT, padx=(12, 2))
        ttk.Button(top, text="📺 An Display senden", style="Accent.TButton",
                   command=self.save_and_apply).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text="↩", width=3, command=self.undo).pack(side=tk.LEFT, padx=(12, 2))
        ttk.Button(top, text="＋", width=3, command=lambda: self.set_zoom(self.zoom + 0.2)).pack(
            side=tk.RIGHT)
        ttk.Button(top, text="－", width=3, command=lambda: self.set_zoom(self.zoom - 0.2)).pack(
            side=tk.RIGHT)
        ttk.Label(top, text="Zoom:", style="Dim.TLabel").pack(side=tk.RIGHT, padx=4)

        main = tk.Frame(page, bg=C_BG)
        main.pack(fill=tk.BOTH, expand=True)

        canvas_holder = tk.Frame(main, bg=C_BG)
        canvas_holder.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(canvas_holder, bg=C_BG, highlightthickness=0, cursor="tcross")
        self.canvas.pack(anchor="center", expand=True, padx=8, pady=8)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Control-MouseWheel>",
                         lambda e: self.set_zoom(self.zoom + (0.2 if e.delta > 0 else -0.2)))
        for key, dx, dy in (("<Left>", -1, 0), ("<Right>", 1, 0), ("<Up>", 0, -1), ("<Down>", 0, 1)):
            self.bind(key, lambda e, dx=dx, dy=dy: self.nudge(dx, dy))

        right = tk.Frame(main, bg=C_PANEL, width=350)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(4, 8), pady=8)
        right.pack_propagate(False)

        bar = tk.Frame(right, bg=C_PANEL)
        bar.pack(fill=tk.X, padx=8, pady=8)
        ttk.Button(bar, text="＋ Element hinzufügen", style="Accent.TButton",
                   command=self.add_element_dialog).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(bar, text="🗑", width=3, command=self.delete_element).pack(side=tk.LEFT, padx=4)

        ttk.Label(right, text="ELEMENTE", style="PanelDim.TLabel",
                  font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=10)
        tree_frame = tk.Frame(right, bg=C_PANEL)
        tree_frame.pack(fill=tk.BOTH, expand=False, padx=8, pady=(2, 6))
        self.tree = ttk.Treeview(tree_frame, show="tree", height=11, selectmode="browse")
        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.tag_configure("hidden", foreground=C_FG_DIM)

        ttk.Label(right, text="EIGENSCHAFTEN", style="PanelDim.TLabel",
                  font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=10, pady=(4, 0))
        prop_container = tk.Frame(right, bg=C_PANEL)
        prop_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=(2, 8))
        self.prop_canvas = tk.Canvas(prop_container, highlightthickness=0, bg=C_PANEL)
        prop_scroll = ttk.Scrollbar(prop_container, orient=tk.VERTICAL,
                                    command=self.prop_canvas.yview)
        self.prop_frame = tk.Frame(self.prop_canvas, bg=C_PANEL)
        self.prop_frame.bind("<Configure>",
                             lambda e: self.prop_canvas.configure(
                                 scrollregion=self.prop_canvas.bbox("all")))
        self.prop_canvas.create_window((0, 0), window=self.prop_frame, anchor="nw")
        self.prop_canvas.configure(yscrollcommand=prop_scroll.set)
        self.prop_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        prop_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        return page

    # ================================================ Seite: Einstellungen
    def _build_settings_page(self):
        page = tk.Frame(self.content, bg=C_BG)
        ttk.Label(page, text="Einstellungen", style="Title.TLabel").pack(
            anchor="w", padx=24, pady=(20, 2))
        ttk.Label(page, text="Änderungen gelten nach „Speichern & Monitor neu starten“",
                  style="Dim.TLabel").pack(anchor="w", padx=24)

        card = tk.Frame(page, bg=C_PANEL)
        card.pack(fill=tk.X, padx=24, pady=14)
        self._settings_vars = {}
        rows = [
            ("COM-Port", "COM_PORT", "z. B. COM3 oder AUTO"),
            ("Wetter API-Key", "WEATHER_API_KEY", "OpenWeatherMap-Schlüssel (kostenlos)"),
            ("Breitengrad", "WEATHER_LATITUDE", "z. B. 47.206959"),
            ("Längengrad", "WEATHER_LONGITUDE", "z. B. 7.533310"),
            ("Wetter-Sprache", "WEATHER_LANGUAGE", "de / en / fr / it"),
        ]
        for i, (label, key, hint) in enumerate(rows):
            tk.Label(card, text=label, bg=C_PANEL, fg=C_FG,
                     font=("Segoe UI", 10)).grid(row=i, column=0, sticky="w", padx=16, pady=8)
            var = tk.StringVar()
            self._settings_vars[key] = var
            ttk.Entry(card, textvariable=var, width=40).grid(row=i, column=1, padx=8, pady=8)
            tk.Label(card, text=hint, bg=C_PANEL, fg=C_FG_DIM,
                     font=("Segoe UI", 9)).grid(row=i, column=2, sticky="w", padx=8)

        i = len(rows)
        tk.Label(card, text="Display-Helligkeit", bg=C_PANEL, fg=C_FG,
                 font=("Segoe UI", 10)).grid(row=i, column=0, sticky="w", padx=16, pady=8)
        self._brightness_var = tk.IntVar(value=20)
        bright_frame = tk.Frame(card, bg=C_PANEL)
        bright_frame.grid(row=i, column=1, sticky="ew", padx=8)
        self._brightness_label = tk.Label(bright_frame, text="20 %", bg=C_PANEL, fg=C_ACCENT,
                                          width=5, font=("Segoe UI Semibold", 10))
        self._brightness_label.pack(side=tk.RIGHT)
        scale = ttk.Scale(bright_frame, from_=5, to=100, variable=self._brightness_var,
                          command=lambda v: self._brightness_label.configure(
                              text="%d %%" % float(v)))
        scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(card, text="Achtung: hohe Helligkeit = warmes Display", bg=C_PANEL,
                 fg=C_FG_DIM, font=("Segoe UI", 9)).grid(row=i, column=2, sticky="w", padx=8)

        btns = tk.Frame(page, bg=C_BG)
        btns.pack(anchor="w", padx=24, pady=6)
        ttk.Button(btns, text="💾 Speichern", command=self.save_settings).pack(side=tk.LEFT)
        ttk.Button(btns, text="💾 Speichern & Monitor neu starten", style="Accent.TButton",
                   command=lambda: (self.save_settings(), self.monitor_restart())).pack(
            side=tk.LEFT, padx=8)
        return page

    def _load_settings_fields(self):
        try:
            cfg = config.load_yaml(config.MAIN_DIRECTORY / "config.yaml")
            c = cfg.get("config", {})
            d = cfg.get("display", {})
            for key, var in self._settings_vars.items():
                var.set(str(c.get(key, "")))
            self._brightness_var.set(int(d.get("BRIGHTNESS", 20)))
            self._brightness_label.configure(text="%d %%" % self._brightness_var.get())
        except Exception as e:
            self.status.set("Einstellungen konnten nicht geladen werden: %s" % e)

    def save_settings(self):
        try:
            from ruamel.yaml import YAML
            ry = YAML()
            ry.preserve_quotes = True
            cfg_path = config.MAIN_DIRECTORY / "config.yaml"
            with open(cfg_path, "rt", encoding="utf8") as f:
                data = ry.load(f)
            for key, var in self._settings_vars.items():
                value = var.get().strip()
                data["config"][key] = value
            data["display"]["BRIGHTNESS"] = int(self._brightness_var.get())
            with open(cfg_path, "wt", encoding="utf8") as f:
                ry.dump(data, f)
            self.status.set("Einstellungen gespeichert.")
        except Exception as e:
            messagebox.showerror("sudoAndro Studio",
                                 "Einstellungen konnten nicht gespeichert werden:\n%s" % e)

    # ================================================ Seite: Info
    def _build_info_page(self):
        page = tk.Frame(self.content, bg=C_BG)
        box = tk.Frame(page, bg=C_BG)
        box.place(relx=0.5, rely=0.45, anchor="center")
        try:
            logo_img = Image.open(
                str(config.MAIN_DIRECTORY / "res/themes/sudoAndro/sudoandro-icon.png")
            ).resize((128, 128), Image.LANCZOS)
            self._info_logo_tk = ImageTk.PhotoImage(logo_img)
            tk.Label(box, image=self._info_logo_tk, bg=C_BG).pack(pady=8)
        except Exception:
            pass
        line = tk.Frame(box, bg=C_BG)
        line.pack()
        tk.Label(line, text="sudo", fg=C_FG, bg=C_BG,
                 font=("Segoe UI Semibold", 22)).pack(side=tk.LEFT)
        tk.Label(line, text="Andro", fg=C_ACCENT, bg=C_BG,
                 font=("Segoe UI Semibold", 22)).pack(side=tk.LEFT)
        tk.Label(line, text=" Studio", fg=C_FG_DIM, bg=C_BG,
                 font=("Segoe UI", 22)).pack(side=tk.LEFT)
        tk.Label(box, text="Version %s" % APP_VERSION, fg=C_FG_DIM, bg=C_BG,
                 font=("Segoe UI", 11)).pack(pady=(4, 12))
        tk.Label(box, text="Steuerzentrale & Theme-Editor für das 3,5\"-USB-Sensordisplay\n"
                           "(Turing Smart Screen, Revision A)",
                 fg=C_FG, bg=C_BG, font=("Segoe UI", 11), justify="center").pack()
        tk.Label(box, text="Basiert auf dem Open-Source-Projekt turing-smart-screen-python\n"
                           "Lizenz: GPL-3.0 – Quellcode bleibt offen und frei",
                 fg=C_FG_DIM, bg=C_BG, font=("Segoe UI", 10), justify="center").pack(pady=8)
        return page

    # ------------------------------------------------ Theme laden / anzeigen
    def open_theme(self, name):
        yml = os.path.join(THEMES_DIR, name, "theme.yaml")
        try:
            with open(yml, "rt", encoding="utf8") as f:
                self.theme = yaml.safe_load(f) or {}
        except Exception as e:
            messagebox.showerror("sudoAndro Studio", "Theme konnte nicht geladen werden:\n%s" % e)
            return
        self.theme_name = name
        self.theme_var.set(name)
        self.title("sudoAndro Studio – " + name)
        self.selected = None
        self._undo.clear()
        self._backup_done = False
        self.refresh(full=True)
        self.status.set("Theme „%s“ geladen." % name)

    def refresh(self, full=False):
        self.render()
        self.discover_elements()
        self.update_canvas()
        self.update_tree()
        if full:
            self.build_props()

    def set_zoom(self, z):
        self.zoom = max(0.6, min(4.0, z))
        self.update_canvas()

    def update_canvas(self):
        if self.render_image is None:
            return
        w = int(self.render_image.width * self.zoom)
        h = int(self.render_image.height * self.zoom)
        img = self.render_image.resize((w, h), Image.LANCZOS)
        self._tkimg = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self._tkimg, anchor="nw")
        self.canvas.configure(width=w, height=h)
        if self.selected is not None:
            x0, y0, x1, y1 = self.element_bbox(self.selected)
            z = self.zoom
            dash = None if self.selected.visible else (4, 3)
            self.canvas.create_rectangle(x0 * z, y0 * z, x1 * z, y1 * z,
                                         outline=C_ACCENT, width=2, dash=dash)

    def update_tree(self):
        self.tree.delete(*self.tree.get_children())
        self._iid_to_el = {}
        groups = {}
        for el in self.elements:
            group = el.path[1] if el.path[0] == "STATS" else el.path[0]
            gname = TOKEN_DE.get(group, group)
            if gname not in groups:
                groups[gname] = self.tree.insert("", tk.END, text=gname, open=True)
            label = de_label(el.path[1:] if el.path[0] == "STATS" else el.path[1:])
            if el.path[0] == "STATS":
                label = de_label(el.path[2:])
            tags = () if el.visible else ("hidden",)
            iid = self.tree.insert(groups[gname], tk.END, text=label or el.path[-1], tags=tags)
            self._iid_to_el[iid] = el
            if self.selected is not None and el.path == self.selected.path:
                self.tree.selection_set(iid)
                self.tree.see(iid)

    def on_tree_select(self, _event):
        sel = self.tree.selection()
        if sel and sel[0] in self._iid_to_el:
            self.selected = self._iid_to_el[sel[0]]
            self.update_canvas()
            self.build_props()

    # ------------------------------------------------ Canvas-Interaktion
    def on_press(self, event):
        px, py = int(event.x / self.zoom), int(event.y / self.zoom)
        el = self.hit_test(px, py)
        self.selected = el
        if el is not None:
            self._drag = (px - int(el.node.get("X", 0)), py - int(el.node.get("Y", 0)),
                          copy.deepcopy(self.theme))
            self.status.set("%s  (X=%d, Y=%d)" % (el.label, el.node.get("X", 0), el.node.get("Y", 0)))
        else:
            self.status.set("X=%d, Y=%d" % (px, py))
        self.update_canvas()
        self.update_tree()
        self.build_props()

    def on_drag(self, event):
        if self.selected is None or self._drag is None:
            return
        px, py = int(event.x / self.zoom), int(event.y / self.zoom)
        maxx, maxy = self.render_image.width, self.render_image.height
        nx = max(0, min(maxx, px - self._drag[0]))
        ny = max(0, min(maxy, py - self._drag[1]))
        self.selected.node["X"] = nx
        self.selected.node["Y"] = ny
        self.status.set("%s  (X=%d, Y=%d)" % (self.selected.label, nx, ny))
        if not self._render_pending:
            self._render_pending = True
            self.after(80, self._drag_render)

    def _drag_render(self):
        self._render_pending = False
        self.render()
        self.update_canvas()

    def on_release(self, _event):
        if self.selected is not None and self._drag is not None:
            self._push_undo(self._drag[2])
            self.refresh()
            self.build_props()
        self._drag = None

    def nudge(self, dx, dy):
        if self.selected is None:
            return
        self._push_undo(copy.deepcopy(self.theme))
        self.selected.node["X"] = max(0, int(self.selected.node.get("X", 0)) + dx)
        self.selected.node["Y"] = max(0, int(self.selected.node.get("Y", 0)) + dy)
        self.refresh()
        self.build_props()

    # ------------------------------------------------ Eigenschaften-Panel
    def build_props(self):
        for w in self._prop_widgets:
            w.destroy()
        self._prop_widgets = []
        el = self.selected
        if el is None:
            lbl = tk.Label(self.prop_frame, text="Kein Element ausgewählt.\n\n"
                                                 "Klicke ein Element in der Vorschau\n"
                                                 "oder in der Liste an.",
                           bg=C_PANEL, fg=C_FG_DIM, justify="left")
            lbl.grid(row=0, column=0, padx=8, pady=8, sticky=tk.W)
            self._prop_widgets.append(lbl)
            return

        title = tk.Label(self.prop_frame, text=el.label, bg=C_PANEL, fg=C_ACCENT,
                         font=("Segoe UI Semibold", 10), wraplength=300, justify="left")
        title.grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=8, pady=(4, 8))
        self._prop_widgets.append(title)

        keys = [k for k in PROP_ORDER if k in el.node] + \
               [k for k in el.node if k not in PROP_ORDER and k not in HIDDEN_KEYS]
        row = 1
        for key in keys:
            val = el.node[key]
            lab = tk.Label(self.prop_frame, text=PROP_DE.get(key, key) + ":",
                           bg=C_PANEL, fg=C_FG)
            lab.grid(row=row, column=0, sticky=tk.W, padx=8, pady=2)
            self._prop_widgets.append(lab)
            widget = self._make_prop_widget(el, key, val)
            widget.grid(row=row, column=1, sticky=tk.EW, padx=4, pady=2)
            self._prop_widgets.append(widget)
            row += 1

    def _commit(self, el, key, value):
        self._push_undo(copy.deepcopy(self.theme))
        el.node[key] = value
        self.refresh()

    def _make_prop_widget(self, el, key, val):
        f = self.prop_frame
        if key in BOOL_KEYS:
            var = tk.BooleanVar(value=bool(val) if not isinstance(val, str) else val.lower() == "true")
            cb = ttk.Checkbutton(f, variable=var,
                                 command=lambda: self._commit(el, key, var.get()))
            return cb
        if key in COLOR_KEYS:
            btn = tk.Button(f, text=str(val), bg=color_to_hex(val), bd=0, relief=tk.FLAT,
                            fg="#000000" if sum(int(c) for c in str(val).split(",")) > 380 else "#ffffff",
                            cursor="hand2")

            def pick():
                rgb, hx = colorchooser.askcolor(color=color_to_hex(el.node[key]), parent=self)
                if hx:
                    self._commit(el, key, hex_to_color(hx))
                    self.build_props()

            btn.configure(command=pick)
            return btn
        if key == "FONT":
            var = tk.StringVar(value=str(val))
            combo = ttk.Combobox(f, textvariable=var, values=self.fonts, width=24)
            combo.bind("<<ComboboxSelected>>", lambda e: self._commit(el, key, var.get()))
            return combo
        if key == "BACKGROUND_IMAGE":
            files = [fn for fn in os.listdir(os.path.join(THEMES_DIR, self.theme_name))
                     if fn.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))]
            var = tk.StringVar(value=str(val))
            combo = ttk.Combobox(f, textvariable=var, values=files, width=24)
            combo.bind("<<ComboboxSelected>>", lambda e: self._commit(el, key, var.get()))
            return combo
        if key in INT_KEYS:
            var = tk.StringVar(value=str(val))
            spin = ttk.Spinbox(f, from_=-500, to=4000, textvariable=var, width=8,
                               command=lambda: self._try_int_commit(el, key, var))
            spin.bind("<Return>", lambda e: self._try_int_commit(el, key, var))
            spin.bind("<FocusOut>", lambda e: self._try_int_commit(el, key, var))
            return spin
        var = tk.StringVar(value=str(val))
        entry = ttk.Entry(f, textvariable=var, width=26)
        entry.bind("<Return>", lambda e: self._commit(el, key, var.get()))
        entry.bind("<FocusOut>", lambda e: (str(val) != var.get()) and self._commit(el, key, var.get()))
        return entry

    def _try_int_commit(self, el, key, var):
        try:
            value = int(float(var.get()))
        except ValueError:
            return
        if el.node.get(key) != value:
            self._commit(el, key, value)

    # ------------------------------------------------ Elemente hinzufuegen / entfernen
    def _bg_kv(self):
        bg = (self.theme.get("static_images") or {}).get("BACKGROUND", {})
        if bg.get("PATH"):
            return {"BACKGROUND_IMAGE": bg["PATH"]}
        return {"BACKGROUND_COLOR": "0, 0, 0"}

    def _center(self):
        return self.render_image.width // 2 - 40, self.render_image.height // 2 - 10

    def _template(self, kind):
        cx, cy = self._center()
        bg = self._bg_kv()
        if kind == KIND_TEXT:
            return {"SHOW": True, "SHOW_UNIT": True, "X": cx, "Y": cy, "FONT": DEFAULT_FONT,
                    "FONT_SIZE": 22, "FONT_COLOR": "255, 255, 255", **bg}
        if kind == KIND_GRAPH:
            return {"SHOW": True, "X": cx, "Y": cy, "WIDTH": 150, "HEIGHT": 16,
                    "MIN_VALUE": 0, "MAX_VALUE": 100, "BAR_COLOR": "0, 160, 255",
                    "BAR_OUTLINE": True, **bg}
        if kind == KIND_RADIAL:
            return {"SHOW": True, "X": cx, "Y": cy, "RADIUS": 45, "WIDTH": 12,
                    "MIN_VALUE": 0, "MAX_VALUE": 100, "ANGLE_START": 110, "ANGLE_END": 250,
                    "ANGLE_STEPS": 10, "ANGLE_SEP": 0, "CLOCKWISE": True,
                    "BAR_COLOR": "0, 160, 255", "SHOW_TEXT": True, "SHOW_UNIT": True,
                    "FONT": DEFAULT_FONT, "FONT_SIZE": 18, "FONT_COLOR": "255, 255, 255", **bg}
        if kind == KIND_LINE:
            return {"SHOW": True, "X": cx, "Y": cy, "WIDTH": 160, "HEIGHT": 60,
                    "MIN_VALUE": 0, "MAX_VALUE": 100, "HISTORY_SIZE": 60, "AUTOSCALE": False,
                    "LINE_COLOR": "0, 160, 255", "LINE_WIDTH": 2, "AXIS": False, **bg}
        return {}

    def add_element_dialog(self):
        dlg = tk.Toplevel(self, bg=C_PANEL)
        dlg.title("Element hinzufügen")
        dlg.transient(self)
        dlg.grab_set()
        dlg.geometry("+%d+%d" % (self.winfo_rootx() + 260, self.winfo_rooty() + 160))

        tk.Label(dlg, text="Sensor / Element:", bg=C_PANEL, fg=C_FG).grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=(12, 4))
        names = [s[0] for s in SENSOR_PALETTE] + ["— Eigener Text —", "— Eigenes Bild —"]
        sensor_var = tk.StringVar(value=names[0])
        sensor_combo = ttk.Combobox(dlg, textvariable=sensor_var, values=names,
                                    state="readonly", width=32)
        sensor_combo.grid(row=0, column=1, padx=10, pady=(12, 4))

        tk.Label(dlg, text="Darstellung:", bg=C_PANEL, fg=C_FG).grid(
            row=1, column=0, sticky=tk.W, padx=10, pady=4)
        kind_var = tk.StringVar()
        kind_combo = ttk.Combobox(dlg, textvariable=kind_var, state="readonly", width=32)
        kind_combo.grid(row=1, column=1, padx=10, pady=4)

        def update_kinds(_e=None):
            name = sensor_var.get()
            if name.startswith("—"):
                kind_combo["values"] = ["—"]
                kind_var.set("—")
                return
            entry = next(s for s in SENSOR_PALETTE if s[0] == name)
            kind_combo["values"] = [KIND_DE[k] for k in entry[2]]
            kind_var.set(KIND_DE[entry[2][0]])

        sensor_combo.bind("<<ComboboxSelected>>", update_kinds)
        update_kinds()

        def ok():
            name = sensor_var.get()
            if name == "— Eigener Text —":
                self._add_static_text()
            elif name == "— Eigenes Bild —":
                self._add_static_image()
            else:
                entry = next(s for s in SENSOR_PALETTE if s[0] == name)
                kind = next(k for k, v in KIND_DE.items() if v == kind_var.get())
                self._add_stats_element(entry[1], kind)
            dlg.destroy()

        ttk.Button(dlg, text="Hinzufügen", style="Accent.TButton", command=ok).grid(
            row=2, column=0, padx=10, pady=12)
        ttk.Button(dlg, text="Abbrechen", command=dlg.destroy).grid(row=2, column=1, padx=10, pady=12)

    def _add_stats_element(self, base_path, kind):
        self._push_undo(copy.deepcopy(self.theme))
        node = self.theme.setdefault("STATS", {})
        full_path = base_path if base_path[-1] in ("TEXT", "ICON") else base_path + (kind,)
        for part in full_path[:-1]:
            node = node.setdefault(part, {})
        leaf = full_path[-1]
        if leaf in node:
            messagebox.showinfo("sudoAndro Studio",
                                "Dieses Element existiert bereits – es wird ausgewählt.")
        elif leaf == "ICON":
            cx, cy = self._center()
            node[leaf] = {"SHOW": True, "X": cx, "Y": cy, "WIDTH": 64, "HEIGHT": 64,
                          **self._bg_kv()}
        else:
            node[leaf] = self._template(KIND_TEXT if leaf not in (KIND_GRAPH, KIND_RADIAL, KIND_LINE)
                                        else leaf)
            if leaf == "TEXT" and base_path[0] in ("DATE", "UPTIME", "WEATHER"):
                node[leaf].pop("SHOW_UNIT", None)
        group = base_path[0]
        if group == "CPU":
            self.theme["STATS"]["CPU"][base_path[1]].setdefault(
                "INTERVAL", GROUP_INTERVAL["CPU"] if base_path[1] == "PERCENTAGE" else 5)
        else:
            self.theme["STATS"][group].setdefault("INTERVAL", GROUP_INTERVAL.get(group, 5))
        self.refresh(full=True)
        self._select_path(("STATS",) + full_path)
        if group == "WEATHER":
            self.status.set("Hinweis: Wetter braucht einen (kostenlosen) OpenWeatherMap-API-Key "
                            "– einstellbar unter ⚙️ Einstellungen.")

    def _add_static_text(self):
        text = simpledialog.askstring("Eigener Text", "Text eingeben:", parent=self)
        if not text:
            return
        self._push_undo(copy.deepcopy(self.theme))
        sec = self.theme.setdefault("static_text", {})
        name = "TEXT_%d" % (len(sec) + 1)
        while name in sec:
            name += "_2"
        cx, cy = self._center()
        sec[name] = {"TEXT": text, "X": cx, "Y": cy, "FONT": DEFAULT_FONT, "FONT_SIZE": 20,
                     "FONT_COLOR": "255, 255, 255", **self._bg_kv()}
        self.refresh(full=True)
        self._select_path(("static_text", name))

    def _add_static_image(self):
        file = filedialog.askopenfilename(parent=self, title="Bild wählen",
                                          filetypes=[("Bilder", "*.png *.jpg *.jpeg *.bmp")])
        if not file:
            return
        self._push_undo(copy.deepcopy(self.theme))
        dest_name = os.path.basename(file)
        shutil.copy(file, os.path.join(THEMES_DIR, self.theme_name, dest_name))
        with Image.open(file) as im:
            w, h = im.size
        sec = self.theme.setdefault("static_images", {})
        name = os.path.splitext(dest_name)[0].upper()
        while name in sec:
            name += "_2"
        sec[name] = {"PATH": dest_name, "X": 10, "Y": 10, "WIDTH": w, "HEIGHT": h}
        self.refresh(full=True)
        self._select_path(("static_images", name))

    def _select_path(self, path):
        for el in self.elements:
            if el.path == path:
                self.selected = el
                break
        self.update_canvas()
        self.update_tree()
        self.build_props()

    def delete_element(self):
        el = self.selected
        if el is None:
            return
        if el.path[:2] == ("static_images", "BACKGROUND"):
            # Der Hintergrund darf nie ganz fehlen (sonst rendert das Theme nicht mehr),
            # daher bietet der Loeschen-Knopf hier stattdessen direkt den Bildwechsel an
            messagebox.showinfo("sudoAndro Studio",
                                "Der Hintergrund kann nicht entfernt werden, nur ersetzt.\n"
                                "Der Dialog zum Bildwechsel öffnet sich jetzt.")
            self.choose_background()
            return
        if not messagebox.askyesno("sudoAndro Studio", "„%s“ wirklich entfernen?" % el.label):
            return
        self._push_undo(copy.deepcopy(self.theme))
        node = self.theme
        for part in el.path[:-1]:
            node = node[part]
        del node[el.path[-1]]
        path = el.path[:-1]
        while len(path) > 1:
            parent = self.theme
            for part in path[:-1]:
                parent = parent[part]
            child = parent[path[-1]]
            if isinstance(child, dict) and set(child.keys()) <= {"INTERVAL"}:
                del parent[path[-1]]
                path = path[:-1]
            else:
                break
        self.selected = None
        self.refresh(full=True)

    # ------------------------------------------------ Theme-Verwaltung
    def new_theme(self):
        name = simpledialog.askstring("Neues Theme", "Name des neuen Themes:", parent=self)
        if not name:
            return
        name = "".join(c for c in name if c not in '\\/:*?"<>|').strip()
        dest = os.path.join(THEMES_DIR, name)
        if os.path.exists(dest):
            messagebox.showerror("sudoAndro Studio", "Ein Theme mit diesem Namen existiert bereits.")
            return
        shutil.copytree(os.path.join(THEMES_DIR, self.theme_name), dest)
        for junk in ("preview.png", "theme.yaml.bak"):
            p = os.path.join(dest, junk)
            if os.path.exists(p):
                os.remove(p)
        self.theme_combo["values"] = list_themes()
        self.open_theme(name)

    def choose_background(self):
        file = filedialog.askopenfilename(
            parent=self, title="Hintergrundbild wählen",
            filetypes=[("Bilder", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("Alle Dateien", "*.*")])
        if not file:
            return
        w, h = self.render_image.width, self.render_image.height
        try:
            with Image.open(file) as im:
                im = im.convert("RGB")
                if im.size != (w, h):
                    if not messagebox.askyesno(
                            "sudoAndro Studio",
                            "Das Bild ist %dx%d, das Display %dx%d.\n"
                            "Soll es angepasst werden (Bildausschnitt füllen, Seitenverhältnis "
                            "bleibt erhalten - keine Verzerrung)?"
                            % (im.width, im.height, w, h)):
                        return
                    im = ImageOps.fit(im, (w, h), method=Image.LANCZOS, centering=(0.5, 0.5))
                dest = os.path.join(THEMES_DIR, self.theme_name, "background.png")
                im.save(dest, "PNG")
        except Exception as e:
            messagebox.showerror(
                "sudoAndro Studio",
                "Das Bild konnte nicht geladen werden:\n%s\n\n"
                "Tipp: iPhone-Fotos sind oft im HEIC-Format gespeichert, das Python nicht "
                "lesen kann. Bild z. B. per Windows-Fotos-App oder Snipping Tool einmal als "
                "PNG/JPG speichern und erneut versuchen." % e)
            return
        self._push_undo(copy.deepcopy(self.theme))
        sec = self.theme.setdefault("static_images", {})
        sec["BACKGROUND"] = {"PATH": "background.png", "X": 0, "Y": 0, "WIDTH": w, "HEIGHT": h}
        self.refresh(full=True)
        self.status.set("Hintergrundbild aktualisiert.")

    # ------------------------------------------------ Undo / Speichern / Anwenden
    def _push_undo(self, snapshot):
        self._undo.append(snapshot)
        if len(self._undo) > 50:
            self._undo.pop(0)

    def undo(self):
        if not self._undo:
            self.status.set("Nichts rückgängig zu machen.")
            return
        self.theme = self._undo.pop()
        self.selected = None
        self.refresh(full=True)
        self.status.set("Rückgängig gemacht.")

    def save(self):
        yml = os.path.join(THEMES_DIR, self.theme_name, "theme.yaml")
        if not self._backup_done and os.path.exists(yml):
            shutil.copy(yml, yml + ".bak")
            self._backup_done = True
        with open(yml, "wt", encoding="utf8") as f:
            f.write("---\n# Bearbeitet mit sudoAndro Studio\n")
            yaml.safe_dump(self.theme, f, sort_keys=False, allow_unicode=True,
                           default_flow_style=False)
        try:
            self.render_image.save(os.path.join(THEMES_DIR, self.theme_name, "preview.png"), "PNG")
        except Exception:
            pass
        self.status.set("Gespeichert: %s" % yml)

    def save_and_apply(self):
        self.save()
        self._set_active_theme_in_config(self.theme_name)
        self.monitor_restart()
        self.status.set("An das Display gesendet – der Monitor wurde neu gestartet.")


def main():
    themes = list_themes()
    if len(sys.argv) > 1 and sys.argv[1] in themes:
        start_theme = sys.argv[1]
    else:
        active = config.CONFIG_DATA["config"].get("THEME")
        start_theme = active if active in themes else (themes[0] if themes else None)
    if start_theme is None:
        print("Keine 3.5\"-Themes gefunden.")
        sys.exit(1)
    config.CONFIG_DATA["config"]["THEME"] = start_theme
    config.load_theme()
    app = ThemeStudio(start_theme)
    app.mainloop()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        import traceback
        log_path = os.path.join(str(config.MAIN_DIRECTORY), "theme-studio-error.log")
        with open(log_path, "wt", encoding="utf8") as f:
            f.write(traceback.format_exc())
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0, "sudoAndro Studio ist abgestürzt.\nDetails: theme-studio-error.log",
                "sudoAndro Studio", 0x10)
        except Exception:
            pass
        raise
