# DragTK
# Copyright (c) 2025-2026 Marcus Douglas
# Licensed under the MIT License. See LICENSE file for details.
# Last Updated: 2026-04-26
# Version 1.0.0


# Imports
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog, colorchooser
import json
import tempfile
import subprocess
import sys
import os
from collections import defaultdict
import re
import keyword
import builtins
import tkinter.font as tkfont
import traceback
import datetime
import shutil
import threading
import difflib
import gc


# ---------------- General Utility functions ----------------


# Increments name of elements as they are added to canvas e.g. button1, button2, etc
def next_name(counter, base):
    counter[base] += 1
    return f"{base}{counter[base]}"

def last_name(counter, base):
    #counter[base] -= 1
    return f"{base}{counter[base]}"

# Check for python install on user machine (Test this works adequately)
def find_python():
    # try common names
    for exe in ["python", "python3", "py"]:
        path = shutil.which(exe)
        if path:
            return path
    return None


def is_frozen():
    return getattr(sys, 'frozen', False)

# Finding resources
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except Exception:
        base_path = os.path.abspath(".")  # normal dev mode

    return os.path.join(base_path, relative_path)


# ---------------- Other Classes ----------------

# Custom askstring class
class CustomAskString(simpledialog.Dialog):
    
    def __init__(self, parent, title, prompt):
        self.prompt = prompt
        self.result = None
        super().__init__(parent, title)

    def body(self, master):

        icon_path = resource_path("assets/icon.ico")

        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        else:
            print("Icon missing:", icon_path)
        #self.iconbitmap(icon_path)

        tk.Label(master, text=self.prompt).pack(padx=10, pady=10)
        self.entry = tk.Entry(master)
        self.entry.pack(padx=10, pady=5)
        return self.entry

    def apply(self):
        self.result = self.entry.get()



class RadioGroupDialog(tk.Toplevel):
    def __init__(self, parent, existing_groups):
        super().__init__(parent)
        self.result = None
        self.existing_groups = list(existing_groups)

        self.title("Radiobutton Group")
        self.geometry("360x300")
        self.minsize(320, 260)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        # Theme colours
        t = parent.THEMES.get(parent.mode.get(), parent.THEMES["light"])
        bg       = t["bg"]
        panel    = t["panel"]
        fg       = t["fg"]
        entry_bg = t["entry_bg"]
        header   = t["selected_bg"]

        self.configure(bg=bg)

        try:
            icon_path = resource_path("assets/icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except:
            pass

        # Center
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 180
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 150
        self.geometry(f"+{x}+{y}")

        # ---- Header ----
        tk.Label(self, text=" Radiobutton Group", bg=header, fg="white",
                 font=("Calibri", 11, "bold"), anchor="w", padx=8
                 ).pack(fill=tk.X)

        pad = tk.Frame(self, bg=bg)
        pad.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        # ---- Select or create ----
        tk.Label(pad, text="Select existing group or type a new name:",
                 bg=bg, fg=fg, font=("Calibri", 10)).pack(anchor="w", pady=(0, 4))

        self.group_var = tk.StringVar()
        self.combo = ttk.Combobox(pad, textvariable=self.group_var,
                                  values=self.existing_groups, font=("Calibri", 10))
        self.combo.pack(fill=tk.X, pady=(0, 8))
        if self.existing_groups:
            self.combo.set(self.existing_groups[0])

        # ---- Existing groups list ----
        tk.Label(pad, text="Existing groups:", bg=bg, fg=fg,
                 font=("Calibri", 10)).pack(anchor="w")

        list_frame = tk.Frame(pad, bg=bg)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 8))

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.group_list = tk.Listbox(list_frame, font=("Consolas", 10),
                                     bg=entry_bg, fg=fg,
                                     selectbackground=header,
                                     selectforeground="white",
                                     yscrollcommand=scrollbar.set,
                                     height=5)
        self.group_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.group_list.yview)

        for g in self.existing_groups:
            self.group_list.insert(tk.END, g)

        # Clicking list sets combobox
        self.group_list.bind("<<ListboxSelect>>", self._on_list_select)

        # ---- Delete button ----
        btn_row = tk.Frame(pad, bg=bg)
        btn_row.pack(fill=tk.X)

        tk.Button(btn_row, text="🗑 Delete selected group",
                  bg=panel, fg=fg, relief="flat", bd=1,
                  font=("Calibri", 9), cursor="hand2",
                  command=self._delete_group
                  ).pack(side=tk.LEFT)

        # ---- OK / Cancel ----
        tk.Frame(self, bg=t["border_col"], height=1).pack(fill=tk.X, pady=(4, 0))

        button_bar = tk.Frame(self, bg=bg)
        button_bar.pack(fill=tk.X, padx=12, pady=8)

        tk.Button(button_bar, text="Cancel", command=self.destroy,
                  bg=panel, fg=fg, relief="raised", bd=2, padx=10
                  ).pack(side=tk.RIGHT, padx=(4, 0))

        tk.Button(button_bar, text="OK", command=self._confirm,
                  bg=header, fg="white", relief="raised", bd=2, padx=10,
                  font=("Calibri", 10, "bold"), cursor="hand2"
                  ).pack(side=tk.RIGHT)

        self.combo.focus_set()
        self.bind("<Return>", lambda e: self._confirm())
        self.bind("<Escape>", lambda e: self.destroy())

        self.wait_window()

    def _on_list_select(self, event):
        sel = self.group_list.curselection()
        if sel:
            self.group_var.set(self.group_list.get(sel[0]))

    def _delete_group(self):
        sel = self.group_list.curselection()
        if not sel:
            return
        group = self.group_list.get(sel[0])
        if messagebox.askyesno("Delete Group",
                               f"Delete group '{group}'?\n\nRadiobuttons in this group will need reassigning.",
                               parent=self):
            self.group_list.delete(sel[0])
            self.existing_groups.remove(group)
            self.combo.configure(values=self.existing_groups)
            if self.group_var.get() == group:
                self.group_var.set(self.existing_groups[0] if self.existing_groups else "")

    def _confirm(self):
        val = self.group_var.get().strip()
        if not val:
            messagebox.showwarning("No Group", "Please enter or select a group name.", parent=self)
            return
        self.result = val
        self.destroy()


# ---------------- Main Application ----------------

class GUIBuilderApp(tk.Tk):
    
    def __init__(self):
        
        super().__init__()


        # Path to app icon
        icon_path = resource_path("assets/icon.ico")

        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        else:
            print("Icon missing:", icon_path)

        # Basic attributes
        self.title("DragTK")
        self.geometry("1200x800")
        self.state("zoomed")
        self.minsize(900, 600)

        
        # if subprocess app is running (threads)
        self.running = False # Flag for if app is running (helps threading later)
        

        self.protected_enabled = True   # Enable code editor protection (stop user overwrites of app generated code)
        self.custom_font_size = 10      # default font size
        self.apply_saved_settings()     # Apply user saved settings

        self.canvas_scale_mode = "Fully Responsive" # Default cavas scaling mode

        self.undo_stack = []    # Undo action stack
        self.redo_stack = []    # Redo action stack

        self.global_props = {}  # Global properties

        self.grid_size = 10     # Determines number of pixels grid snapping occurs by on canvas

        self._highlight_after_id = None  # for debounce timer
        

        # State
        self.counters = defaultdict(int)    # for naming widget elements added by user (autonum e.g. label1, label2, etc)
        self.elements = {}                  # dict of name(id) -> metadata
        self.selected = None                    # Currently selected element on canvas
        self.mode = tk.StringVar(value="light") # Default app theme

        # Default project settings
        self.canvas_width_var = tk.StringVar(value="800")
        self.canvas_height_var = tk.StringVar(value="400")
        self.canvas_title_var = tk.StringVar(value="My Project")
        self.project_bg_color = tk.StringVar(value="#FFFFFF")


        # Default project status - Clean + no current save path
        self.dirty = False
        self.current_save_path = None
        self.last_saved_code = "default"    # Tracks copy of project code from last time project was saved
        

        # Function when closing app
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Stores group names for radio button widgets
        self.radio_groups = {}

        # Create UI, apply themes, generate code
        
        self._create_ui()

        # Called after create_ui to manually set height of debug output area
        self.update_idletasks()
        self.after(200, self._set_initial_sash)

        
        self._apply_theme()

  
        self.apply_settings_to_ui()
        
        self.normal_generate_code()
        self._update_protected_tags()

    # For controlling initial height of debug output area
    def _set_initial_sash(self):
        try:
            total = self.center_split.winfo_height()
            # Give debug panel a fixed small height currently 250
            sash_pos = max(100, total - 250)
            self.center_split.sashpos(0, sash_pos)
        except Exception as e:
            print("Sash error:", e)



    def _create_ui(self):

        # ---------------- STYLE ----------------
        self.style = ttk.Style()
        self.style.theme_use('default')

        custom_font_size = ("Calibri", self.custom_font_size)
        self.style.configure("TNotebook.Tab", font=("Calibri", 11))
        self.style.configure("TButton", padding=6)

        # ---------------- MENU ----------------
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        options_menu = tk.Menu(menubar, tearoff=0)
        run_menu = tk.Menu(menubar, tearoff=0)
        help_menu = tk.Menu(menubar, tearoff=0)

        menubar.add_cascade(label="File", menu=file_menu)
        menubar.add_cascade(label="Options", menu=options_menu)
        menubar.add_cascade(label="Run", menu=run_menu)
        menubar.add_cascade(label="Help", menu=help_menu)

        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_separator()
        file_menu.add_command(label="Save                Ctrl+S", command=self.save_project)
        file_menu.add_command(label="Save As           Ctrl+Shift+S", command=self.save_project_as)
        file_menu.add_command(label="Export .py", command=self.export_code)
        file_menu.add_separator()
        file_menu.add_command(label="Open Project", command=self.load_project)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)

        #options_menu.add_command(label="Toggle Theme         Ctrl+T", command=self.toggle_theme)
        options_menu.add_command(label="Editor Settings", command=self.open_editor_settings)
        #options_menu.add_command(label="Fun Mode 🎨", command=self.toggle_fun_mode)
        #options_menu.add_command(label="Retro Mode 🖥", command=self.toggle_retro_mode)

        run_menu.add_command(label="Run (F5)", command=self.run_code)
        run_menu.add_command(label="Stop", command=self.stop_process)

        help_menu.add_command(label="About", command=self.show_about)


        # ---------------- TOOLBAR ----------------
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        btn_params = {"side": tk.LEFT, "padx": 2}

        # --- File actions ---
        ttk.Button(toolbar, text="📄 New", command=self.new_project, style="Flat.TButton").pack(**btn_params)
        ttk.Button(toolbar, text="📂 Open", command=self.load_project, style="Flat.TButton").pack(**btn_params)
        ttk.Button(toolbar, text="💾 Save", command=self.save_project, style="Flat.TButton").pack(**btn_params)
        ttk.Button(toolbar, text="📝 Save As", command=self.save_project_as, style="Flat.TButton").pack(**btn_params)
        ttk.Button(toolbar, text="📤 Export", command=self.export_code, style="Flat.TButton").pack(**btn_params)

        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)

        # --- Edit actions ---
        ttk.Button(toolbar, text="↶ Undo", command=self._custom_undo, style="Flat.TButton").pack(**btn_params)
        ttk.Button(toolbar, text="↷ Redo", command=self._custom_redo, style="Flat.TButton").pack(**btn_params)

        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)

        # --- Run controls ---
        ttk.Button(toolbar, text="▶ Run", command=self.run_code, style="Run.TButton").pack(**btn_params)
        ttk.Button(toolbar, text="■ Stop", command=self.stop_process, style="Stop.TButton").pack(**btn_params)

        # ---------------- MAIN LAYOUT ----------------
        main_pane = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        # LEFT SIDEBAR (widgets)
        left_container = ttk.Frame(main_pane, width=160)
        main_pane.add(left_container, weight=0)
        

        # CENTER NOTEBOOK (Canvas <-> Code tabs)
        center_container = ttk.Frame(main_pane)
        main_pane.add(center_container, weight=3)

        center_split = ttk.Panedwindow(center_container, orient=tk.VERTICAL)
        center_split.pack(fill=tk.BOTH, expand=True)

        # TOP: Notebook (Canvas + Code)
        top_container = ttk.Frame(center_split)
        center_split.add(top_container, weight=4)

        self.center_tabs = ttk.Notebook(top_container)
        self.center_tabs.pack(fill=tk.BOTH, expand=True)

        # ---------------- LEFT: WIDGETS ----------------
        self.widgets_header = tk.Label(
            left_container,
            text=" Widgets ",
            anchor="w",
            padx=8
        )
        self.widgets_header.pack(fill=tk.X)

        self.widgets_frame = tk.Frame(left_container)
        self.widgets_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_params = {'fill': tk.X, 'pady': 0}

        ttk.Button(self.widgets_frame, text="🏷 Label", command=lambda: self.add_element('Label', 'new'), style="Flat.TButton").pack(**btn_params)
        ttk.Button(self.widgets_frame, text="🔘 Button", command=lambda: self.add_element('Button', 'new'), style="Flat.TButton").pack(**btn_params)
        ttk.Button(self.widgets_frame, text="⌨ Entry", command=lambda: self.add_element('Entry', 'new'), style="Flat.TButton").pack(**btn_params)
        ttk.Button(self.widgets_frame, text="📊 Treeview", command=lambda: self.add_element('Treeview', 'new'), style="Flat.TButton").pack(**btn_params)
        ttk.Button(self.widgets_frame, text="☑ Checkbutton", command=lambda: self.add_element('Checkbutton', 'new'), style="Flat.TButton").pack(**btn_params)
        ttk.Button(self.widgets_frame, text="🔘 Radiobutton", command=lambda: self.add_element('Radiobutton', 'new'), style="Flat.TButton").pack(**btn_params)
        ttk.Button(self.widgets_frame, text="📝 Text Area", command=lambda: self.add_element('TextArea', 'new'), style="Flat.TButton").pack(**btn_params)
        ttk.Button(self.widgets_frame, text="📋 Listbox", command=lambda: self.add_element('Listbox', 'new'), style="Flat.TButton").pack(**btn_params)
        ttk.Button(self.widgets_frame, text="📂 Combobox", command=lambda: self.add_element('Combobox', 'new'), style="Flat.TButton").pack(**btn_params)
        ttk.Button(self.widgets_frame, text="🖼 Image", command=self.add_image_element, style="Flat.TButton").pack(**btn_params)

        # ---------------- PROPERTIES (TABS) ----------------
        prop_frame = ttk.Frame(main_pane)
        main_pane.add(prop_frame, weight=0)

        prop_tabs = ttk.Notebook(prop_frame)
        prop_tabs.pack(fill=tk.BOTH, expand=True)

        widget_tab = ttk.Frame(prop_tabs)
        canvas_tab = ttk.Frame(prop_tabs)

        prop_tabs.add(widget_tab, text="Widget Properties")
        prop_tabs.add(canvas_tab, text="Canvas Properties")

        # ---- Widget Properties ----
        container = ttk.Frame(widget_tab)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        container.columnconfigure(0, weight=0)
        container.columnconfigure(1, weight=1)

        
        # Row number
        r = 0

        def add_entry(label):
            nonlocal r

            ttk.Label(container, text=label, font=custom_font_size).grid(row=r, column=0, sticky="w", pady=2)
            entry = ttk.Entry(container, font=custom_font_size)
            entry.grid(row=r, column=1, sticky="ew", pady=2) #ipady=4
            r += 1
            return entry

        # --- Core properties ---
        self.prop_id = add_entry("ID:")

        ttk.Label(container, text="Type:", font=custom_font_size).grid(row=r, column=0, sticky="w", pady=2)
        self.prop_type = ttk.Label(container, text="-", font=custom_font_size)
        self.prop_type.grid(row=r, column=1, sticky="w", pady=2)
        r += 1

        self.prop_text = add_entry("Text:")
        self.prop_x = add_entry("X:")
        self.prop_y = add_entry("Y:")
        self.prop_w = add_entry("Width:")
        self.prop_h = add_entry("Height:")

        # --- Font Family ---
        ttk.Label(container, text="Font Family:", font=custom_font_size).grid(row=r, column=0, sticky="w", pady=2)
        self.prop_font_family = ttk.Combobox(
            container,
            values=["Consolas", "Courier New", "Arial", "Times New Roman", "Calibri",
                    "Comic Sans MS", "Verdana", "Tahoma", "Georgia"],
            state="readonly",
            font=custom_font_size, style="Light.TCombobox"
        )
        self.prop_font_family.grid(row=r, column=1, sticky="ew", pady=2)
        r += 1

        # --- Font Size ---
        ttk.Label(container, text="Font Size:", font=custom_font_size).grid(row=r, column=0, sticky="w", pady=2)
        self.prop_font_size = ttk.Spinbox(container, from_=6, to=72, font=custom_font_size)
        self.prop_font_size.grid(row=r, column=1, sticky="ew", pady=2, ipady=4)
        r += 1

        # --- Text Color ---
        ttk.Label(container, text="Text Color:", font=custom_font_size).grid(row=r, column=0, sticky="w", pady=2)
        self.prop_fg = ttk.Entry(container, font=custom_font_size)
        self.prop_fg.grid(row=r, column=1, sticky="ew", pady=2)

        self.fg_button = tk.Button(
            container,
            width=2,
            height=1,
            bg=self.prop_fg.get() if self.prop_fg.get() else "#ffffff",
            relief="solid",
            command=self.pick_fg_color
        )
        self.fg_button.grid(row=r, column=2, sticky="w", padx=2)
        r += 1

        # --- Background Color ---
        ttk.Label(container, text="Background Color:", font=custom_font_size).grid(row=r, column=0, sticky="w", pady=2)
        self.prop_bg = ttk.Entry(container, font=custom_font_size)
        self.prop_bg.grid(row=r, column=1, sticky="ew", pady=2)

        self.bg_button = tk.Button(
            container,
            width=2,
            height=1,
            bg=self.prop_bg.get() if self.prop_bg.get() else "#ffffff",
            relief="solid",
            command=self.pick_bg_color
        )
        self.bg_button.grid(row=r, column=2, sticky="w", padx=2)
        r += 1

        # --- Apply Button ---
        self.apply_btn = ttk.Button(container, text="Apply", command=self.apply_button_pressed, style="Accent.TButton")
        self.apply_btn.grid(row=r, column=0, columnspan=2, pady=10)

        # ---- Canvas Properties ----
        c = ttk.Frame(canvas_tab)
        c.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        c.columnconfigure(0, weight=0)
        c.columnconfigure(1, weight=1)

        r2 = 0  # separate row counter

        def add_canvas_entry(label):
            nonlocal r2

            ttk.Label(c, text=label, font=custom_font_size).grid(
                row=r2, column=0, sticky="w", pady=2
            )

            entry = ttk.Entry(c, textvariable=None, font=custom_font_size)
            entry.grid(row=r2, column=1, sticky="ew", pady=2)

            r2 += 1
            return entry

        # Title
        ttk.Label(c, text="Title:", font=custom_font_size).grid(row=r2, column=0, sticky="w", pady=2)
        self.canvas_title_entry = ttk.Entry(c, textvariable=self.canvas_title_var, font=custom_font_size)
        self.canvas_title_entry.grid(row=r2, column=1, sticky="ew", pady=2)
        r2 += 1

        # Width
        ttk.Label(c, text="Width:", font=custom_font_size).grid(row=r2, column=0, sticky="w", pady=2)
        self.canvas_width_entry = ttk.Entry(c, textvariable=self.canvas_width_var, font=custom_font_size)
        self.canvas_width_entry.grid(row=r2, column=1, sticky="ew", pady=2)
        r2 += 1

        # Height
        ttk.Label(c, text="Height:", font=custom_font_size).grid(row=r2, column=0, sticky="w", pady=2)
        self.canvas_height_entry = ttk.Entry(c, textvariable=self.canvas_height_var, font=custom_font_size)
        self.canvas_height_entry.grid(row=r2, column=1, sticky="ew", pady=2)
        r2 += 1

        ttk.Label(c, text="Background Color:", font=custom_font_size).grid(row=r2, column=0, sticky="w", pady=2)

        bg_row = ttk.Frame(c)
        bg_row.grid(row=r2, column=1, sticky="ew", pady=2)

        self.canvas_bg_entry = ttk.Entry(bg_row, textvariable=self.project_bg_color, font=custom_font_size)
        self.canvas_bg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.canvas_bg_button = tk.Button(
            bg_row,
            width=2,
            height=1,
            bg=self.project_bg_color.get() or "#ffffff",
            relief="solid",
            command=self.pick_canvas_bg_color
        )
        self.canvas_bg_button.pack(side=tk.LEFT, padx=(4, 0))

        r2 += 1

        # Scale mode
        ttk.Label(c, text="Scale Mode:", font=custom_font_size).grid(row=r2, column=0, sticky="w", pady=2)

        self.scale_mode_var = tk.StringVar(value="Fully Responsive")

        self.scale_mode_combo = ttk.Combobox(
            c,
            textvariable=self.scale_mode_var,
            state="readonly",
            values=[
                "Fully Responsive",
                "Responsive Width Only",
                "Fixed Layout"
            ],
            font=custom_font_size
        )

        self.scale_mode_combo.grid(row=r2, column=1, sticky="ew", pady=2)

        r2 += 1

        # --- Grid Snapping Toggle ---
        ttk.Label(c, text="Grid Snapping:", font=custom_font_size).grid(
            row=r2, column=0, sticky="w", pady=2
        )

        self.grid_snap_var = tk.BooleanVar(value=True)  # ON by default

        self.grid_snap_check = ttk.Checkbutton(
            c,
            variable=self.grid_snap_var,
            command=self._toggle_grid_snap
        )
        self.grid_snap_check.grid(row=r2, column=1, sticky="w", pady=2)

        r2 += 1

        

        ttk.Button(
            c,
            text="Apply Canvas Settings",
            command=lambda: self.apply_canvas_size("apply_btn"),
            style="Accent.TButton"
        ).grid(row=r2, column=0, columnspan=2, pady=10)

        # ---------------- CANVAS TAB ----------------
        canvas_tab = ttk.Frame(self.center_tabs)
        self.center_tabs.add(canvas_tab, text="Canvas")

        self.canvas_header = tk.Label(
            canvas_tab,
            text=" Design Canvas ",
            anchor="w",
            padx=8
        )
        self.canvas_header.pack(fill=tk.X)

        # --- Outer scrollable viewport ---
        self.canvas_outer = tk.Frame(canvas_tab)
        self.canvas_outer.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbars
        h_scroll = tk.Scrollbar(self.canvas_outer, orient=tk.HORIZONTAL)  # tk not ttk
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        v_scroll = tk.Scrollbar(self.canvas_outer, orient=tk.VERTICAL)    # tk not ttk
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Viewport canvas (the scrollable surface)
        self.viewport = tk.Canvas(
            self.canvas_outer,
            xscrollcommand=h_scroll.set,
            yscrollcommand=v_scroll.set,
            bg="#c0c0c0",  # neutral grey surround so design area stands out
            cursor="arrow"
        )
        self.viewport.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        h_scroll.config(command=self.viewport.xview)
        v_scroll.config(command=self.viewport.yview)

        # --- Inner design canvas (fixed size, user's project dimensions) ---
        canvas_w = int(self.canvas_width_var.get())
        canvas_h = int(self.canvas_height_var.get())

        self.canvas = tk.Canvas(
            self.viewport,
            bg="white",
            width=canvas_w,
            height=canvas_h,
            highlightthickness=1,
            highlightbackground="#aaaaaa"
        )

        # Embed the design canvas inside the viewport
        self.canvas_window = self.viewport.create_window(
            10, 10,  # small padding from top-left
            anchor="nw",
            window=self.canvas
        )

        # Set scroll region to fit the canvas + padding
        self.viewport.configure(
            scrollregion=(0, 0, canvas_w + 20, canvas_h + 20)
        )

        # Mouse wheel scrolling
        def _on_mousewheel(event):
            self.viewport.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _on_shift_mousewheel(event):
            self.viewport.xview_scroll(int(-1 * (event.delta / 120)), "units")

        self.viewport.bind("<MouseWheel>", _on_mousewheel)
        self.viewport.bind("<Shift-MouseWheel>", _on_shift_mousewheel)

        # ---- Global Properties Tab ----
        global_tab = ttk.Frame(prop_tabs)
        prop_tabs.add(global_tab, text="Global Widget Properties")

        global_outer = tk.Frame(global_tab)
        global_outer.pack(fill=tk.BOTH, expand=True)

        # Scrollable container
        global_canvas = tk.Canvas(global_outer, highlightthickness=0)
        global_scroll = ttk.Scrollbar(global_outer, orient="vertical", command=global_canvas.yview)
        global_canvas.configure(yscrollcommand=global_scroll.set)
        global_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        global_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        global_content = ttk.Frame(global_canvas)
        global_content_window = global_canvas.create_window((0, 0), window=global_content, anchor="nw")

        def _on_global_content_configure(e):
            global_canvas.configure(scrollregion=global_canvas.bbox("all"))
        def _on_global_canvas_configure(e):
            global_canvas.itemconfig(global_content_window, width=e.width)

        global_content.bind("<Configure>", _on_global_content_configure)
        global_canvas.bind("<Configure>", _on_global_canvas_configure)
        global_canvas.bind("<MouseWheel>", lambda e: global_canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units"))

        gpad = ttk.Frame(global_content)
        gpad.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        gpad.columnconfigure(1, weight=1)

        # Widget types that have font/color properties
        global_widget_types = [
            ("Label",       "🏷"),
            ("Button",      "🔘"),
            ("Entry",       "⌨"),
            ("Checkbutton", "☑"),
            ("Radiobutton", "🔘"),
        ]

        # Save references for theme updates
        self.global_props_canvas = global_canvas
        self.global_props_content = global_content
        self.global_props_pad = gpad

        def make_section(parent, wtype, icon, row_start):
            r = row_start

            # Section header
            header = tk.Label(parent, text=f" {icon} {wtype} ",
                              anchor="w", padx=6, font=("Calibri", 10, "bold"))
            header.grid(row=r, column=0, columnspan=3, sticky="ew", pady=(10, 2))
            r += 1

            tk.Frame(parent, height=1).grid(
                row=r, column=0, columnspan=3, sticky="ew", pady=(0, 4))
            r += 1

            vars_dict = {}

            # Font Family
            ttk.Label(parent, text="Font Family:", font=custom_font_size).grid(
                row=r, column=0, sticky="w", pady=2)
            ff_var = tk.StringVar(value="Arial")
            ff_combo = ttk.Combobox(parent,
                values=["Consolas", "Courier New", "Arial", "Times New Roman",
                        "Calibri", "Comic Sans MS", "Verdana", "Tahoma", "Georgia"],
                textvariable=ff_var, state="readonly",
                font=custom_font_size, width=12)
            ff_combo.grid(row=r, column=1, columnspan=2, sticky="ew", pady=2)
            vars_dict["font_family"] = ff_var
            r += 1

            # Font Size
            ttk.Label(parent, text="Font Size:", font=custom_font_size).grid(
                row=r, column=0, sticky="w", pady=2)
            fs_var = tk.IntVar(value=12)
            ttk.Spinbox(parent, from_=6, to=72, textvariable=fs_var,
                        font=custom_font_size, width=6).grid(
                row=r, column=1, sticky="w", pady=2)
            vars_dict["font_size"] = fs_var
            r += 1

            # Foreground
            ttk.Label(parent, text="Text Color:", font=custom_font_size).grid(
                row=r, column=0, sticky="w", pady=2)
            fg_var = tk.StringVar(value="#000000")
            fg_entry = ttk.Entry(parent, textvariable=fg_var,
                                 font=custom_font_size, width=10)
            fg_entry.grid(row=r, column=1, sticky="ew", pady=2)

            fg_swatch = tk.Button(parent, width=2, height=1,
                                  bg=fg_var.get(), relief="solid",
                                  command=lambda v=fg_var, s=None: _pick_global_color(v, fg_swatch_ref))
            fg_swatch.grid(row=r, column=2, sticky="w", padx=2)
            fg_swatch_ref = fg_swatch
            fg_var.trace_add("write", lambda *a, v=fg_var, s=fg_swatch: _update_swatch(v, s))
            vars_dict["foreground"] = fg_var
            r += 1

            # Background
            ttk.Label(parent, text="BG Color:", font=custom_font_size).grid(
                row=r, column=0, sticky="w", pady=2)
            bg_var = tk.StringVar(value="#ffffff")
            bg_entry = ttk.Entry(parent, textvariable=bg_var,
                                 font=custom_font_size, width=10)
            bg_entry.grid(row=r, column=1, sticky="ew", pady=2)

            bg_swatch = tk.Button(parent, width=2, height=1,
                                  bg=bg_var.get(), relief="solid",
                                  command=lambda v=bg_var, s=None: _pick_global_color(v, bg_swatch_ref))
            bg_swatch.grid(row=r, column=2, sticky="w", padx=2)
            bg_swatch_ref = bg_swatch
            bg_var.trace_add("write", lambda *a, v=bg_var, s=bg_swatch: _update_swatch(v, s))
            vars_dict["background"] = bg_var
            r += 1

            # Apply button
            ttk.Button(parent, text=f"Apply to all {wtype}s",
                       style="Accent.TButton",
                       command=lambda t=wtype, v=vars_dict: _apply_global(t, v)
                       ).grid(row=r, column=0, columnspan=3, sticky="ew", pady=(4, 2))
            r += 1

            self.global_props[wtype] = vars_dict
            return r

        def _update_swatch(var, swatch):
            try:
                swatch.config(bg=var.get())
            except Exception:
                pass

        def _pick_global_color(var, swatch):
            from tkinter import colorchooser
            color = colorchooser.askcolor(color=var.get())[1]
            if color:
                var.set(color)
                try:
                    swatch.config(bg=color)
                except Exception:
                    pass

        def _apply_global(wtype, vars_dict):
            changed = False
            for name, props in self.elements.items():
                if props["type"] != wtype:
                    continue
                props["font_family"]  = vars_dict["font_family"].get()
                props["font_size"]    = int(vars_dict["font_size"].get())
                props["foreground"]   = vars_dict["foreground"].get()
                props["background"]   = vars_dict["background"].get()
                self._update_element(name)
                changed = True

            if changed:
                self.normal_generate_code()
                self._update_protected_tags()
                self.show_toast(f"Applied to all {wtype}s")
            else:
                self.show_toast(f"No {wtype}s on canvas")

        # Build all sections
        current_row = 0
        gpad.columnconfigure(1, weight=1)
        for wtype, icon in global_widget_types:
            current_row = make_section(gpad, wtype, icon, current_row)

        

        # ---------------- CODE TAB ----------------
        code_tab = ttk.Frame(self.center_tabs)
        self.center_tabs.add(code_tab, text="Code")

        self.code_header = tk.Label(
            code_tab,
            text=" Code Editor ",
            anchor="w",
            padx=8
        )
        self.code_header.pack(fill=tk.X)

        code_frame = ttk.Frame(code_tab)
        code_frame.pack(fill=tk.BOTH, expand=True)

        self.setup_code_editor(parent=code_frame)
        

        # ---------------- DEBUG (BOTTOM) ----------------

        debug_container = ttk.Frame(center_split)
        center_split.add(debug_container, weight=0)

        # Make self reference to help set initial debug window size
        self.center_split = center_split
        

        self.debug_header = tk.Label(
            debug_container,
            text=" Output ",
            anchor="w",
            padx=8
        )
        self.debug_header.pack(fill=tk.X)

        # --- Frame to hold text + scrollbar ---
        debug_frame = ttk.Frame(debug_container)
        debug_frame.pack(fill=tk.BOTH, expand=True)

        # --- Scrollbar ---
        self.debug_scroll = tk.Scrollbar(debug_frame, orient="vertical")  # tk not ttk, saved as self
        self.debug_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Text widget ---
        self.syntax_output = tk.Text(
            debug_frame,
            wrap="word",
            font=("Consolas", 11),
            yscrollcommand=self.debug_scroll.set
        )
        self.syntax_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.debug_scroll.config(command=self.syntax_output.yview)

        # Start disabled to prevent user typing in debug output
        self.syntax_output.configure(state="disabled")


        
        self._draw_canvas_boundary()
        
        self.apply_saved_settings()
        self.apply_settings_to_ui()

        self.update_window_title_with_path("untitled")

        # ---------------- BINDS ----------------

        def _show_canvas_context(event):
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label='Paste', 
                             command=lambda: self.paste_element(self.selected))
            
            def cleanup():
                try:
                    menu.destroy()
                except Exception:
                    pass

            menu.bind("<Unmap>", lambda e: self.after(100, cleanup))
            menu.tk_popup(event.x_root, event.y_root)

        self.canvas.bind('<Button-3>', _show_canvas_context)

        self.canvas.bind('<Button-1>', self.canvas_click)
        self.viewport.bind('<Button-1>', self.canvas_click)

        self.canvas.bind('<Button-3>', _show_canvas_context)
        
        self.bind('<F5>', lambda e: self.run_code())
        self.bind('<Delete>', lambda e: self.delete_selected())
        self.bind_all("<Control-s>", lambda e: self.save_project())
        self.bind_all("<Control-S>", lambda e: self.save_project_as())
        self.bind_all("<Control-t>", lambda e: self.toggle_theme())
        
        self.bind_all("<Control-z>", self._custom_undo)
        self.bind_all("<Control-y>", self._custom_redo)

        self.bind("<Control-c>", lambda e: self._conditional_copy(e, self.selected))
        self.bind("<Control-v>", lambda e: self._conditional_paste(e, self.selected))

        

        # Mac style redo bind
        #self.code_text.bind("<Control-Shift-Z>", self._custom_redo, add="+")

        # Handle syntax_output behaviour when reading from input() line
        self.syntax_output.bind("<Return>", self._on_user_input, add="+")
        self.syntax_output.bind("<Key>", self._prevent_editing_output, add="+")
        


    # -------------- Self utility / helper functions --------------

    def _show_element_menu(self, event, name):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label='Properties', command=lambda: self.select_element(name))
        menu.add_command(label='Copy',       command=lambda: self.copy_element(name))
        menu.add_command(label='Paste',      command=lambda: self.paste_element(name))
        menu.add_command(label='Delete',     command=lambda: self.delete_selected_on_click(name))

        # Add radiobutton group option if applicable
        props = self.elements.get(name, {})
        if props.get('type') == 'Radiobutton':
            menu.add_separator()
            current_group = props.get('_radio_group_name', 'None')
            menu.add_command(
                label=f'Group: {current_group}  ✎',
                command=lambda: self._change_radio_group(name)
            )

        def cleanup():
            try:
                menu.destroy()
            except Exception:
                pass

        menu.bind("<Unmap>", lambda e: self.after(100, cleanup))
        menu.tk_popup(event.x_root, event.y_root)


    def _change_radio_group(self, name):
        props = self.elements.get(name)
        if not props:
            return

        existing_groups = sorted({
            p.get('_radio_group_name')
            for p in self.elements.values()
            if p['type'] == 'Radiobutton' and '_radio_group_name' in p
        })

        dialog = RadioGroupDialog(self, existing_groups)
        new_group = dialog.result

        if not new_group or new_group == props.get('_radio_group_name'):
            return

        # Update the group
        props['_radio_group_name'] = new_group

        if new_group not in self.radio_groups:
            self.radio_groups[new_group] = tk.StringVar(value='')

        props['_radio_group_var'] = self.radio_groups[new_group]

        # Update the visual widget's variable
        widget = props.get('_widget')
        if widget and hasattr(widget, 'configure'):
            try:
                widget.configure(variable=self.radio_groups[new_group])
            except Exception:
                pass

        self.normal_generate_code()
        self._update_protected_tags()
        self.show_toast(f"Group changed to '{new_group}'")

    
    # Option to toggle grid snapping (either 10px or 1px)
    def _toggle_grid_snap(self):
        if self.grid_snap_var.get():
            self.grid_size = 10
        else:
            self.grid_size = 1


    # Custom copy func to prevent actions on protected app generated code
    def _on_ctrl_copy(self, event=None):
        if not getattr(self, "protected_enabled", True):
            return None  # protection off — allow everything
        sel = self.code_text.tag_ranges(tk.SEL)
        if sel and self.code_text.tag_nextrange("protected", sel[0], sel[1]):
            tk.messagebox.showwarning("Protected Code", "You cannot copy protected sections.")
            return "break"
        return None


    # Custom cut func to prevent actions on protected app generated code
    def _on_ctrl_cut(self, event=None):
        if not getattr(self, "protected_enabled", True):
            return None
        sel = self.code_text.tag_ranges(tk.SEL)
        if sel and self.code_text.tag_nextrange("protected", sel[0], sel[1]):
            tk.messagebox.showwarning("Protected Code", "You cannot cut protected sections.")
            return "break"
        return None


    # Custom paste func to prevent actions on protected app generated code
    def _on_ctrl_paste(self, event=None):
        if not getattr(self, "protected_enabled", True):
            return None
        index = self.code_text.index("insert")
        if "protected" in self.code_text.tag_names(index):
            tk.messagebox.showwarning("Protected Code", "You cannot paste into a protected section.")
            return "break"
        sel = self.code_text.tag_ranges(tk.SEL)
        if sel and self.code_text.tag_nextrange("protected", sel[0], sel[1]):
            tk.messagebox.showwarning("Protected Code", "You cannot paste over protected sections.")
            return "break"
        return None

    

    # Log to debug output area
    def output_log(self, text):
        
        MAX_CHARS = 10000 # Buffer of 10000 chars (don't display > 10000 chars to save performance

        self.syntax_output.configure(state="normal") # Make editable

        # Insert new text
        self.syntax_output.insert(tk.END, text)

        # Trim from top if too long
        current_length = int(self.syntax_output.index('end-1c').split('.')[1])
        total_chars = len(self.syntax_output.get("1.0", "end-1c"))

        if total_chars > MAX_CHARS:
            excess = total_chars - MAX_CHARS
            self.syntax_output.delete("1.0", f"1.0 + {excess}c")

        self.syntax_output.see(tk.END)

        # Update input start safely
        self.input_start_index = self.syntax_output.index("insert")
        
        
        
    # Send typed input on input()
    def send_input(self, text):
        if hasattr(self, "current_process") and self.current_process:
            try:
                if self.current_process.stdin:
                    self.current_process.stdin.write(text + "\n")
                    self.current_process.stdin.flush()
            except Exception as e:
                print("Input error:", e)

    
    def _on_user_input(self, event=None):
        widget = self.syntax_output

        # Get ONLY user-typed part
        start = self.input_start_index
        end = widget.index("insert lineend")

        text = widget.get(start, end).strip()

        # Move cursor to end + newline
        widget.insert(tk.END, "\n")
        widget.see(tk.END)

        # Send to subprocess
        self.send_input(text)
        

        return "break"



    def _prevent_editing_output(self, event):
        
        widget = self.syntax_output

        # Keys that should STILL WORK
        allowed_keys = (
            "Left", "Right", "Up", "Down",
            "Home", "End", "Prior", "Next",  # navigation
        )

        if event.keysym in allowed_keys:
            return None

        # Allow copy shortcuts
        if (event.state & 0x4) and event.keysym.lower() == "c":  # Ctrl+C
            return None

        # Only block if trying to edit BEFORE input zone
        if widget.compare("insert", "<", self.input_start_index):
            return "break"

        
    # Pick bg color for developing app canvas
    def pick_canvas_bg_color(self):
        
        color = colorchooser.askcolor(title="Choose Canvas Background")

        if color and color[1]:
            
            self.project_bg_color.set(color[1])
            #self.apply_canvas_size()  # applies color change immediately
            self.canvas_bg_button.config(bg=color[1])


    # Update widget property color swatches to selected widget colors
    def update_color_swatches(self):
        self.fg_button.config(bg=self.prop_fg.get())
        self.bg_button.config(bg=self.prop_bg.get())

    
    # FG color selector for widgets. Triggers on button press
    def pick_fg_color(self):
        if not self.selected:
            return
        color = colorchooser.askcolor(title="Select Text Color")
        
        if color and color[1]:
            self.prop_fg.delete(0, tk.END)
            self.prop_fg.insert(0, color[1])
            #self.apply_properties()  # immediately apply to the widget
            self.fg_button.config(bg=color[1])

    # BG color selector for widgets. Triggers on button press
    def pick_bg_color(self):
        if not self.selected:
            return
        color = colorchooser.askcolor(title="Select Background Color")
        if color and color[1]:
            self.prop_bg.delete(0, tk.END)
            self.prop_bg.insert(0, color[1])
            #self.apply_properties()
            self.bg_button.config(bg=color[1])


    # Reset the undo and redo stacks
    def reset_stacks(self):
        self.undo_stack = []
        self.redo_stack = []

    # Custom undo function
    # Not fully built properly but better than nothing
    # Needs work
    def _custom_undo(self, event=None):
        if len(self.undo_stack) > 0:
            last_action = self.undo_stack[-1]
            self.redo_stack.append(self.undo_stack[-1])
            del self.undo_stack[-1]

            if last_action['type'] == "code_editor_text":
                # Save scroll position before replacing text
                yview = self.code_text.yview()
                self.code_text.delete('1.0', tk.END)
                self.code_text.insert('1.0', last_action['text'])
                self.do_full_highlight()
                # Restore scroll position
                self.code_text.yview_moveto(yview[0])
                self.line_numbers.yview_moveto(yview[0])
                self.center_tabs.select(1)
            else:
                if last_action['action_type'] == "add":
                    self._undo_delete_element(last_action['name'])
                elif last_action['action_type'] == "del":
                    self.add_element_from_undo_redo(last_action, 'copy', 'undo') # was new instead of copy but not sure why?

                self.center_tabs.select(0)

            self._update_protected_tags()
        #print("Undo after UNDO ---")
        #self.stack_out(self.undo_stack)

        #print("Redo after UNDO ---")
        #self.stack_out(self.redo_stack)


    # Custom redo function
    # Not fully built properly but better than nothing
    # Needs work
    def _custom_redo(self, event=None):
        if len(self.redo_stack) > 0:
            last_action = self.redo_stack[-1]
            del self.redo_stack[-1]

            if last_action['type'] == "code_editor_text":
                yview = self.code_text.yview()
                self.code_text.delete('1.0', tk.END)
                self.code_text.insert('1.0', last_action['text'])
                self.do_full_highlight()
                self.code_text.yview_moveto(yview[0])
                self.line_numbers.yview_moveto(yview[0])
                self.undo_stack.append(last_action)
                self.center_tabs.select(1)
            else:
                if last_action['action_type'] == "del":
                    self.add_element_from_undo_redo(last_action, 'copy', 'redo')
                else:
                    self.add_element_from_undo_redo(last_action, 'copy', 'redo')

                self.center_tabs.select(0)

            self._update_protected_tags()

        #print("Undo after REDO ---")
        #self.stack_out(self.undo_stack)

        #print("Redo after REDO ---")
        #self.stack_out(self.redo_stack)
            

    

    # Protect code areas from editing
    # Protecting code that's auto generated by the app
    def _setup_protected_code_areas(self):
        
        # Initialize protected code area handling.
        # Configure the tag for protected sections
        self.code_text.tag_configure("protected", foreground="grey")

        # Tag initially
        self._update_protected_tags()


    def _update_protected_tags(self):
        self.code_text.tag_remove("protected", "1.0", tk.END)
        lines = self.code_text.get("1.0", tk.END).splitlines()

        # Lines that must never be edited
        protected_exact = {
            "# --- BUTTON FUNCTIONS ---",
            "# --- COMBOBOX OPTION LOADER FUNCTIONS ---",
            "# --- LISTBOX OPTION LOADER FUNCTIONS ---",
            "# --- TREEVIEW FUNCTIONS ---",
            "# --- ON LOAD ---",
        }

        # Find insert section bounds
        try:
            insert_start_idx = lines.index("# ==========================START=============================") + 1
            insert_end_idx   = lines.index("# ============================END=============================") + 1
            if insert_end_idx != -1:
                self.code_text.tag_add("protected", f"{insert_end_idx}.0", f"{insert_end_idx}.end")
        except ValueError:
            insert_start_idx = insert_end_idx = -1

        # Protect special function definitions OUTSIDE the insert section
        # and exact section marker lines
        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            if stripped in protected_exact:
                self.code_text.tag_add("protected", f"{line_num}.0", f"{line_num}.end")

            if ((line_num < insert_start_idx or line_num > insert_end_idx)
                    and stripped.startswith(("def on_", "def load_", "def get_"))
                    and stripped.endswith("():")):
                self.code_text.tag_add("protected", f"{line_num}.0", f"{line_num}.end")

        # Protect the auto-generated GUI section after the marker — your original logic
        for line_num, line in enumerate(lines, start=1):
            if line.strip() == "# -------------- Auto Generated GUI Code -------------- #":
                for protect_line in range(line_num, len(lines) + 1):
                    self.code_text.tag_add("protected", f"{protect_line}.0", f"{protect_line}.end")
                break



    # Stops user from deleted protected code areas
    def _on_code_keypress(self, event):
        if not getattr(self, "protected_enabled", True):
            return

        # Allow non-editing keys through
        allowed_keys = (
            "Left", "Right", "Up", "Down",
            "Home", "End", "Prior", "Next",
            "Shift_L", "Shift_R", "Control_L", "Control_R",
            "Alt_L", "Alt_R", "F1", "F2", "F3", "F4", "F5",
        )
        if event.keysym in allowed_keys:
            return None
        # Allow copy
        if (event.state & 0x4) and event.keysym.lower() == "c":
            return None

        try:
            widget = self.code_text

            # ---- SELECTION CHECK ----
            # If there's a selection, block if any part of it touches protected
            sel = widget.tag_ranges(tk.SEL)
            if sel:
                sel_start, sel_end = sel[0], sel[1]
                # Check if selection overlaps any protected region
                protected_ranges = widget.tag_ranges("protected")
                for i in range(0, len(protected_ranges), 2):
                    p_start = protected_ranges[i]
                    p_end   = protected_ranges[i + 1]
                    # Overlap if sel_start < p_end and sel_end > p_start
                    if widget.compare(sel_start, "<", p_end) and widget.compare(sel_end, ">", p_start):
                        tk.messagebox.showwarning(
                            "Protected Code",
                            "Your selection includes protected code that cannot be edited."
                        )
                        return "break"

            # ---- CURSOR CHECK ----
            index = widget.index("insert")

            # For backspace, the char being deleted is the one before the cursor
            if event.keysym == "BackSpace":
                check_index = widget.index(f"{index}-1c")
            elif event.keysym == "Delete":
                check_index = index
            else:
                check_index = index

            if "protected" in widget.tag_names(check_index):
                tk.messagebox.showwarning(
                    "Protected Code",
                    "You cannot edit this line.\n\n"
                    "This section is managed by the application."
                )
                return "break"

            # ---- MARKER LINE CHECK (keep your existing logic) ----
            lines = widget.get("1.0", tk.END).splitlines()
            start_line = end_line = None
            for i, line in enumerate(lines, start=1):
                stripped = line.strip()
                if stripped in (
                    "# ==========================START=============================",
                    "# ============================END============================="
                ):
                    if start_line is None:
                        start_line = i
                    else:
                        end_line = i

            if start_line and end_line:
                cursor_line = int(index.split('.')[0])
                if cursor_line in (start_line, end_line):
                    tk.messagebox.showwarning(
                        "Protected Line",
                        "You cannot edit this line.\n\n"
                        "These markers define the safe code region."
                    )
                    return "break"

        except tk.TclError:
            pass



    # Prevents user from clicking protected code areas
    def _on_mouse_click(self, event):

        if not getattr(self, "protected_enabled", True):
            return  # protection disabled - allow everything
        
        # Prevent cursor from entering protected areas.
        index = self.code_text.index(f"@{event.x},{event.y}")
        if "protected" in self.code_text.tag_names(index):
            # Move cursor to nearest editable area (start of insert section)
            try:
                ranges = self.code_text.tag_ranges("protected")
                if ranges:
                    self.code_text.mark_set("insert", ranges[0])
            except tk.TclError:
                pass
            return "break"


    # Open editor settings window
    # Allows user to make prefernece choices e.g. app theme
    def open_editor_settings(self):
        
        if hasattr(self, "_settings_window") and self._settings_window.winfo_exists():
            self._settings_window.lift()
            return

        win = self._settings_window = tk.Toplevel(self)
        win.title("Editor Settings")
        win.geometry("460x580")
        win.minsize(420, 500)
        win.resizable(True, True)

        try:
            icon_path = resource_path("assets/icon.ico")
            if os.path.exists(icon_path):
                win.iconbitmap(icon_path)
        except:
            pass

        win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 230
        y = self.winfo_y() + (self.winfo_height() // 2) - 290
        win.geometry(f"+{x}+{y}")
        win.transient(self)
        win.grab_set()

        # -------- THEME COLORS --------
        t = self.THEMES.get(self.mode.get(), self.THEMES["light"])
        bg        = t["bg"]
        panel     = t["panel"]
        fg        = t["fg"]
        entry_bg  = t["entry_bg"]
        accent    = t["accent"]
        header_bg = t["selected_bg"]

        win.configure(bg=bg)

        style = ttk.Style(win)
        style.configure("Settings.TLabel",      background=bg,       foreground=fg)
        style.configure("Settings.TCheckbutton",background=bg,       foreground=fg)
        style.configure("Settings.TFrame",      background=bg)
        style.configure("Settings.TEntry",      fieldbackground=entry_bg, foreground=fg)
        style.configure("Settings.TCombobox",   fieldbackground=entry_bg, foreground=fg)
        style.configure("Settings.TSpinbox",    fieldbackground=entry_bg, foreground=fg)
        style.configure("Section.TLabel",       background=header_bg, foreground="white",
                        font=("Calibri", 10, "bold"), padding=(8, 4))

        # -------- VARIABLES --------
        current_font    = tkfont.Font(font=self.code_text.cget("font"))
        font_size_var   = tk.IntVar(value=current_font.cget("size"))
        font_family_var = tk.StringVar(value=current_font.cget("family"))
        bg_color_var    = tk.StringVar(value=self.code_text.cget("bg"))
        protected_var   = tk.BooleanVar(value=self.protected_enabled)
        ui_font_size_var= tk.IntVar(value=self.custom_font_size)

        # -------- HELPERS --------
        def section_header(parent, text):
            ttk.Label(parent, text=text, style="Section.TLabel").pack(fill=tk.X, pady=(10, 4))

        def divider(parent):
            tk.Frame(parent, bg=header_bg, height=1).pack(fill=tk.X, pady=2)

        def row_frame(parent):
            f = tk.Frame(parent, bg=bg)
            f.pack(fill=tk.X, pady=3)
            f.columnconfigure(1, weight=1)
            return f

        def add_row(parent, label, widget_fn):
            f = row_frame(parent)
            tk.Label(f, text=label, bg=bg, fg=fg, anchor="w",
                     font=("Calibri", 10)).grid(row=0, column=0, sticky="w", padx=(0, 10), ipadx=4)
            w = widget_fn(f)
            w.grid(row=0, column=1, sticky="ew")
            return w

        # -------- SCROLLABLE MAIN AREA --------
        outer = tk.Frame(win, bg=bg)
        outer.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        canvas_scroll = tk.Canvas(outer, bg=bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas_scroll.yview)
        canvas_scroll.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas_scroll.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        content = tk.Frame(canvas_scroll, bg=bg)
        content_window = canvas_scroll.create_window((0, 0), window=content, anchor="nw")

        def on_content_configure(e):
            canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))
        def on_canvas_configure(e):
            canvas_scroll.itemconfig(content_window, width=e.width)

        content.bind("<Configure>", on_content_configure)
        canvas_scroll.bind("<Configure>", on_canvas_configure)
        canvas_scroll.bind("<MouseWheel>", lambda e: canvas_scroll.yview_scroll(
            int(-1 * (e.delta / 120)), "units"))

        pad = tk.Frame(content, bg=bg)
        pad.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # ======== SECTION: THEME ========
        section_header(pad, "  🎨  Appearance")

        theme_frame = tk.Frame(pad, bg=bg)
        theme_frame.pack(fill=tk.X, pady=4)

        theme_buttons = [
            ("☀ Light",  "light"),
            ("🌙 Dark",   "dark"),
            ("🍭 Candy",    "fun"),
            ("🖥 Retro",  "retro"),
        ]

        def make_theme_btn(parent, label, mode_val):
            is_active = self.mode.get() == mode_val
            btn = tk.Button(
                parent,
                text=label,
                bg=header_bg if is_active else panel,
                fg="white" if is_active else fg,
                font=("Calibri", 10, "bold" if is_active else "normal"),
                relief="sunken" if is_active else "raised",
                bd=2,
                padx=8, pady=4,
                cursor="hand2",
                command=lambda m=mode_val: switch_theme(m)
            )
            btn.pack(side=tk.LEFT, padx=3)
            return btn

        theme_btn_refs = []
        def switch_theme(new_mode):
            self.mode.set(new_mode)
            self._apply_theme()
            # Update the background color entry to reflect the new theme's code bg
            t2 = self.THEMES.get(new_mode, self.THEMES["light"])
            bg_color_var.set(t2["code_bg"])
            # Refresh button states
            for btn, (_, mv) in zip(theme_btn_refs, theme_buttons):
                active = self.mode.get() == mv
                t2 = self.THEMES.get(self.mode.get(), self.THEMES["light"])
                btn.config(
                    bg=t2["header"] if active else t2["panel"],
                    fg="white" if active else t2["fg"],
                    relief="sunken" if active else "raised",
                    font=("Calibri", 10, "bold" if active else "normal")
                )

        for label, mv in theme_buttons:
            theme_btn_refs.append(make_theme_btn(theme_frame, label, mv))

        divider(pad)

        # ======== SECTION: CODE EDITOR ========
        section_header(pad, "  ✏️  Code Editor")

        add_row(pad, "Font Size:",
                lambda f: ttk.Spinbox(f, from_=6, to=48, textvariable=font_size_var,
                                      width=6, style="Settings.TSpinbox"))

        add_row(pad, "Font Family:",
                lambda f: ttk.Combobox(f,
                    values=["Consolas", "Courier New", "Arial", "Times New Roman",
                            "Calibri", "Comic Sans MS", "Verdana", "Tahoma", "Georgia"],
                    textvariable=font_family_var, state="readonly",
                    style="Settings.TCombobox"))

        # Background row with colour picker
        bg_row_f = row_frame(pad)
        tk.Label(bg_row_f, text="Background:", bg=bg, fg=fg,
                 anchor="w", font=("Calibri", 10)).grid(row=0, column=0, sticky="w", padx=(0,10))
        bg_inner = tk.Frame(bg_row_f, bg=bg)
        bg_inner.grid(row=0, column=1, sticky="ew")
        bg_row_f.columnconfigure(1, weight=1)

        bg_entry = ttk.Entry(bg_inner, textvariable=bg_color_var, style="Settings.TEntry")
        bg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def choose_color():
            color = colorchooser.askcolor()[1]
            if color:
                bg_color_var.set(color)

        tk.Button(bg_inner, text="⬛", command=choose_color,
                  bg=panel, fg=fg, relief="raised", bd=1, padx=4).pack(side=tk.LEFT, padx=(4, 0))

        divider(pad)

        # ======== SECTION: BEHAVIOUR ========
        section_header(pad, "  ⚙️  Behaviour")

        def on_toggle_protected():
            if not protected_var.get():
                result = messagebox.askyesno(
                    "Disable Protected Code?",
                    "Disabling protected code editing is NOT recommended.\n\n"
                    "It may lead to improper behaviour, broken UI generation, "
                    "or corruption of your project.\n\nAre you sure?"
                )
                if not result:
                    protected_var.set(True)

        cb_frame = tk.Frame(pad, bg=bg)
        cb_frame.pack(fill=tk.X, pady=4)
        ttk.Checkbutton(cb_frame, text="Enable protected code editing",
                        variable=protected_var, command=on_toggle_protected,
                        style="Settings.TCheckbutton").pack(anchor="w")

        divider(pad)

        # ======== SECTION: APPLICATION ========
        section_header(pad, "  🖼  Application")

        add_row(pad, "UI Font Size:",
                lambda f: ttk.Spinbox(f, from_=6, to=24, textvariable=ui_font_size_var,
                                      width=6, style="Settings.TSpinbox"))

        # -------- BUTTON BAR --------
        button_bar = tk.Frame(win, bg=bg, pady=8)
        button_bar.pack(fill=tk.X, padx=15, pady=(0, 10))

        tk.Frame(button_bar, bg=t["border_col"], height=1).pack(fill=tk.X, pady=(0, 8))

        def apply_settings():
            current_font.configure(size=font_size_var.get(), family=font_family_var.get())
            self.code_text.config(font=current_font, bg=bg_color_var.get())
            self.line_numbers.config(font=current_font)
            self.protected_enabled = protected_var.get()
            self.custom_font_size = ui_font_size_var.get()
            self.save_user_settings({
                "font_size": font_size_var.get(),
                "font_family": font_family_var.get(),
                "bg_color": bg_color_var.get(),
                "protected_enabled": self.protected_enabled,
                "custom_font_size": self.custom_font_size,
                "mode": self.mode.get()
            })
            self.show_toast("Settings applied")
            messagebox.showinfo("Settings Saved",
                "Settings saved.\n\nSome changes require restarting the application.")

        def restore_defaults():
            if not messagebox.askyesno("Restore Defaults", "Reset all settings to default values?"):
                return
            d = self.get_default_settings()
            font_size_var.set(d["font_size"])
            font_family_var.set(d["font_family"])
            bg_color_var.set(d["bg_color"])
            protected_var.set(d["protected_enabled"])
            ui_font_size_var.set(d["custom_font_size"])

        ttk.Button(button_bar, text="Restore Defaults", command=restore_defaults).pack(side=tk.LEFT)
        ttk.Button(button_bar, text="Close",  command=win.destroy).pack(side=tk.RIGHT)
        ttk.Button(button_bar, text="Apply",  command=apply_settings).pack(side=tk.RIGHT, padx=5)

        win.focus_set()
        win.wait_window()



    # Get or establish the settings directory. 
    # For exe (frozen): prompts user on first run (or if settings location lost) to choose location,
    # then remembers it via a small pointer file next to the exe.
    # For py: uses a 'settings' folder next to the script.
    def get_settings_dir(self):
        
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            exe_dir = os.path.dirname(sys.executable)
            pointer_file = os.path.join(exe_dir, ".settings_location")

            if os.path.exists(pointer_file):
                # Read previously chosen location
                with open(pointer_file, "r", encoding="utf-8") as f:
                    saved_dir = f.read().strip()
                if os.path.isdir(saved_dir):
                    return saved_dir
                # Directory no longer exists — re-prompt
            
            # First run or missing dir — ask user where to save settings
            messagebox.showinfo(
                "Settings Location",
                "Welcome to DragTK!\n\n"
                "Please choose a folder where your settings will be saved.\n"
                "This only needs to be done once or again if you change your installation path."
            )
            chosen = filedialog.askdirectory(
                title="Choose Settings Folder",
                initialdir=exe_dir
            )
            if not chosen:
                # User cancelled — fall back to exe directory
                chosen = exe_dir

            # Save the pointer so we remember next time
            with open(pointer_file, "w", encoding="utf-8") as f:
                f.write(chosen)

            return chosen

        else:
            # Running in dev — use settings/ next to script
            return os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings")


    # Default app settings (restore to default)
    def get_default_settings(self):
        return {
            "font_size": 12,
            "font_family": "Consolas",
            "bg_color": "white",
            "protected_enabled": True,
            "custom_font_size": 10,
            "mode": "light"
        }


    # Apply user settings
    def apply_saved_settings(self):
        settings = self.load_user_settings()

        try:
            self.custom_font_size    = settings.get("custom_font_size", 10)
            self.protected_enabled   = settings.get("protected_enabled", True)
            self.editor_font_size    = settings.get("font_size", 12)
            self.editor_font_family  = settings.get("font_family", "Consolas")
            self.editor_bg_color     = settings.get("bg_color", "white")
            self.mode                = tk.StringVar(value=settings.get("mode", "light"))
        except Exception as e:
            print("Failed to apply settings:", e)


    def apply_settings_to_ui(self):
        try:
            font = tkfont.Font(font=self.code_text.cget("font"))
            font.configure(
                size=self.editor_font_size,
                family=self.editor_font_family
            )

            self.code_text.config(font=font, bg=self.editor_bg_color)
            self.line_numbers.config(font=font, bg=self.editor_bg_color)

        except Exception as e:
            print("Failed to apply UI settings:", e)
            

    def get_settings_path(self):
        settings_dir = self.get_settings_dir()
        os.makedirs(settings_dir, exist_ok=True)
        return os.path.join(settings_dir, "user_settings.json")

    def save_user_settings(self, settings):
        try:
            path = self.get_settings_path()
            # Merge with defaults so we never save a partial file
            full_settings = self.get_default_settings()
            full_settings.update(settings)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(full_settings, f, indent=4)
        except Exception as e:
            print("Failed to save settings:", e)
            messagebox.showwarning(
                "Settings Save Failed",
                f"Could not save settings to:\n{path}\n\nError: {e}"
            )

    def load_user_settings(self):
        try:
            path = self.get_settings_path()

            if not os.path.exists(path):
                # First run — create file with defaults
                defaults = self.get_default_settings()
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(defaults, f, indent=4)
                return defaults

            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)

            # Fill in any missing keys with defaults (handles old settings files
            # that predate new settings being added)
            defaults = self.get_default_settings()
            for key, val in defaults.items():
                if key not in loaded:
                    loaded[key] = val

            return loaded

        except json.JSONDecodeError:
            # Corrupted file — back it up and reset to defaults
            path = self.get_settings_path()
            backup = path + ".bak"
            try:
                os.rename(path, backup)
            except Exception:
                pass
            messagebox.showwarning(
                "Settings Corrupted",
                f"Your settings file was corrupted and has been reset.\n"
                f"A backup was saved to:\n{backup}"
            )
            defaults = self.get_default_settings()
            self.save_user_settings(defaults)
            return defaults

        except Exception as e:
            print("Failed to load settings:", e)
            return self.get_default_settings()


    # Add an image element
    def add_image_element(self):
        
        # Open file dialog restricted to images
        filepath = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image Files", "*.png *.gif")]
        )

        if not filepath:
            return  # user cancelled

        # Changed to absolute pathing for better consistency in finding image again
        #rel_path = os.path.relpath(filepath, os.getcwd())
        abs_path = os.path.abspath(filepath)

        # Add as a new element
        name = next_name(self.counters, "image")
        props = {
            "type": "Image",
            "name": name,
            "text": abs_path,  # store path in text field
            "x": 50 + len(self.elements) * 20,
            "y": 50 + len(self.elements) * 20,
            "w": 120,
            "h": 120,
        }

        self.elements[name] = props
        self._create_visual(props)
        self.normal_generate_code()
        self._update_protected_tags()



    # Function to open about window
    def show_about(self):
        
        about_win = tk.Toplevel(self)
        about_win.title("About DragTK")
        about_win.geometry("400x450")

        icon_path = resource_path("assets/icon.ico")

        if os.path.exists(icon_path):
            about_win.iconbitmap(icon_path)
        else:
            print("Icon missing:", icon_path)

        about_win.resizable(False, False)

        # --- Top section ---
        top_frame = ttk.Frame(about_win, padding=10)
        top_frame.pack(fill="x")

        # Logo
        try:
            logo_img = tk.PhotoImage(file=resource_path("assets/logo.png"))  # adjust path as needed
            logo_img = logo_img.subsample(10, 10)  # shrink to 1/4 size in both dimensions
            logo_label = ttk.Label(top_frame, image=logo_img)
            logo_label.image = logo_img  # keep reference
            logo_label.pack()
        except Exception as e:
            ttk.Label(top_frame, text="[Logo missing]", font=("Arial", 10, "italic")).pack()

        ttk.Label(top_frame, text="DragTK", font=("Arial", 16, "bold")).pack(pady=(5, 0))
        ttk.Label(top_frame, text="A simple GUI Builder for Tkinter and Python", font=("Arial", 10)).pack()
        ttk.Label(top_frame, text="Contact: support@dragtk.com", font=("Arial", 9)).pack()

        # --- Bottom section ---
        bottom_frame = ttk.Frame(about_win, padding=10)
        bottom_frame.pack(fill="x", pady=(20, 0))

        def show_text_file(title, path):
            win = tk.Toplevel(self)
            win.title(title)
            win.geometry("500x400")
            try:
                with open(resource_path(path), "r", encoding="utf-8") as f:
                    content = f.read()
            except FileNotFoundError:
                content = f"{title} file not found."
            text_widget = tk.Text(win, wrap="word")
            text_widget.insert("1.0", content)
            text_widget.config(state="disabled")
            text_widget.pack(fill="both", expand=True)

        ttk.Button(bottom_frame, text="License", 
                   command=lambda: show_text_file("License", "LICENSE.txt")).pack(fill="x", pady=2)
        ttk.Button(bottom_frame, text="Copyright", 
                   command=lambda: show_text_file("Copyright", "COPYRIGHT.txt")).pack(fill="x", pady=2)
        """ttk.Button(bottom_frame, text="README", 
                   command=lambda: show_text_file("README", "README.txt")).pack(fill="x", pady=2)"""



    # Draw the canvas boundary where the app visually exists
    def _draw_canvas_boundary(self):

        # Clear previous drawings
        if hasattr(self, '_canvas_items'):
            for item in self._canvas_items:
                self.canvas.delete(item)

        self._canvas_items = []

        w = getattr(self, 'canvas_width', 800)
        h = getattr(self, 'canvas_height', 400)
        title = getattr(self, 'canvas_title', self.canvas_title_var.get())

        margin_x = 20
        margin_y = 20
        title_height = 30

        # Total space the boundary drawing occupies
        total_w = w + (margin_x * 2)
        total_h = h + (margin_y * 2) + title_height

        # Resize the inner canvas to fit the full boundary + margins
        self.canvas.configure(width=total_w, height=total_h)

        # Keep the viewport scroll region in sync
        if hasattr(self, 'viewport'):
            self.viewport.configure(
                scrollregion=(0, 0, total_w + 20, total_h + 20)
            )

        # --- Main window body ---
        body = self.canvas.create_rectangle(
            margin_x,
            margin_y + title_height,
            margin_x + w,
            margin_y + title_height + h,
            outline="#333",
            dash=(),
            fill=self.project_bg_color.get(),
            width=2
        )

        # --- Fake title bar ---
        title_bar = self.canvas.create_rectangle(
            margin_x,
            margin_y,
            margin_x + w,
            margin_y + title_height,
            fill="#444",  # theme this later
            outline="#333",
            width=2
        )

        # --- Title text ---
        title_text = self.canvas.create_text(
            margin_x + 10,
            margin_y + title_height // 2,
            text=title,
            anchor="w",
            fill="white",
            font=("Calibri", 10, "bold")
        )
        

        # Store all items so we can delete them cleanly later
        self._canvas_items.extend([body, title_bar, title_text])


    # Shows a toast message popup in bottom right of window
    
    def show_toast(self, message="Settings applied", duration=2000):
        toast = tk.Toplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.attributes("-alpha", 0.0)

        if getattr(self, "mode", tk.StringVar(value="light")).get() == "dark":
            bg = "#333333"
            fg = "white"
        else:
            bg = "#dddddd"
            fg = "black"

        frame = tk.Frame(toast, bg=bg, bd=0, highlightthickness=0)
        frame.pack(fill="both", expand=True)

        label = tk.Label(frame, text=message, bg=bg, fg=fg, padx=12, pady=6)
        label.pack()
        toast.update_idletasks()
        height = toast.winfo_height()

        # --- Positioning ---
        self.update_idletasks()
        width = 200
        #height = 40

        start_x = self.winfo_rootx() + self.winfo_width() - width - 10
        start_y = self.winfo_rooty() + self.winfo_height()

        end_y = self.winfo_rooty() + self.winfo_height() - height - 10

        toast.geometry(f"{width}x{height}+{start_x}+{start_y}")

        # --- Animation ---
        steps = 15
        slide_delay = 10
        fade_delay = duration // steps

        def slide_in(step=0):
            if step <= steps:
                y = start_y - ((start_y - end_y) * (step / steps))
                alpha = step / steps
                toast.geometry(f"{width}x{height}+{start_x}+{int(y)}")
                toast.attributes("-alpha", alpha)
                toast.after(slide_delay, lambda: slide_in(step + 1))
            else:
                toast.after(duration, fade_out)

        def fade_out(step=0):
            if step <= steps:
                alpha = 1 - (step / steps)
                y = end_y + (10 * (step / steps))  # slight slide down while fading
                toast.geometry(f"{width}x{height}+{start_x}+{int(y)}")
                toast.attributes("-alpha", alpha)
                toast.after(slide_delay, lambda: fade_out(step + 1))
            else:
                toast.destroy()

        slide_in()


    # Now updates more than just size
    # Updates canvas properties including size, color, etc
    def apply_canvas_size(self, src):
        
        try:
            w = int(self.canvas_width_var.get())
            h = int(self.canvas_height_var.get())
            self.canvas_scale_mode = self.scale_mode_var.get()
            if w <= 0 or h <= 0:
                raise ValueError("Dimensions must be positive integers.")
        except ValueError as e:
            messagebox.showerror("Invalid Size", f"Invalid canvas size: {e}")
            return

        self.canvas_width = w
        self.canvas_height = h

        # _draw_canvas_boundary handles canvas + viewport sizing now
        self._draw_canvas_boundary()
        self.normal_generate_code()
        self._update_protected_tags()

        if src == "apply_btn":
            self.show_toast("Settings applied")
        elif src == "new_btn":
            self.show_toast("New project created")
        


    # Check for syntax errors and log to output
    def check_syntax(self, code_text):
        try:
            compile(code_text, "<string>", "exec")
            return True, None
        except SyntaxError as e:
            return False, e

    def write_syntax_error(self, text):
        
        def update():
            if self.syntax_output and self.syntax_output.winfo_exists():


                self.output_log(text)

        self.after(0, update)



    # Highlights line with errors in the code editor when an error is found
    def _highlight_error_line(self, lineno):

        # Add highlight tag style
        self.code_text.tag_configure("error_highlight", background="#ffcccc")

        # Highlight the whole line
        self.code_text.tag_add(
            "error_highlight",
            f"{lineno}.0",
            f"{lineno}.0 lineend"
        )
        
        # Scroll to the line
        self.code_text.see(f"{lineno}.0")

    # Call this when undo from code editor
    def undo_redo_code_text(self, event=None):

        current_code = self.code_text.get("1.0", "end-1c")

        props = {
            'type': "code_editor_text",
            'text': current_code
        }

        self.undo_stack.append(props)
        #self.redo_stack = []
        

    # Sets code as dirty (meaning a change has been made so project needs saved)
    def _on_code_modified(self, event=None):

        # flag
        self.code_text.edit_modified(False)

        current_code = self.code_text.get("1.0", "end-1c")

        

        if current_code != getattr(self, "last_saved_code", ""):

            if not self.dirty:
                self.dirty = True
                self.center_tabs.tab(1, text="Code *")
        else:
            if self.dirty:
                self.dirty = False
                

        
    # Sets canvas as dirty (meaning a change has been made so project needs saved)
    def _on_modification_made(self):

        self.dirty = True

        self.center_tabs.tab(0, text="Canvas *")


    # Helps handle double clicking text selection in the code editor
    def _select_word_on_double_click(self, event):
        widget = self.code_text

        index = widget.index(f"@{event.x},{event.y}")

        # Expand left
        start = index
        while True:
            prev = widget.index(f"{start} -1c")
            if widget.get(prev, start) in (" ", "\n", "\t", "(", ")", "\"", "'"):
                break
            if prev == start:
                break
            start = prev

        # Expand right
        end = index
        while True:
            nxt = widget.index(f"{end} +1c")
            if widget.get(end, nxt) in (" ", "\n", "\t", "(", ")", "\"", "'"):
                break
            if nxt == end:
                break
            end = nxt

        widget.tag_remove("sel", "1.0", tk.END)
        widget.tag_add("sel", start, end)

        return "break"

    # When user types a single " for example it adds double ""
    def _handle_auto_pairs(self, event):
        widget = self.code_text
        char = event.char

        pairs = {
            "(": ")",
            "[": "]",
            "{": "}",
            '"': '"',
            "'": "'",
        }

        closing = {v: k for k, v in pairs.items()}

        # Current position
        index = widget.index("insert")
        next_char = widget.get(index)

        # --- SKIP OVER EXISTING CLOSING ---
        if char in closing:
            if next_char == char:
                widget.mark_set("insert", f"{index}+1c")
                return "break"

        # --- AUTO INSERT PAIR ---
        if char in pairs:
            # Special handling for quotes
            if char in ('"', "'"):
                if self._is_inside_string(index):
                    return None  # normal typing, no pairing

            widget.insert(index, char + pairs[char])
            widget.mark_set("insert", f"{index}+1c")
            return "break"

        return None

    def _is_inside_string(self, index):
        line_start = self.code_text.index(f"{index} linestart")
        text = self.code_text.get(line_start, index)

        # Count quotes
        single = text.count("'") - text.count("\\'")
        double = text.count('"') - text.count('\\"')

        return (single % 2 == 1) or (double % 2 == 1)
    

    # Setup the code editor
    def setup_code_editor(self, parent):

        # Custom tab behaviour
        def insert_tab(event):
            event.widget.insert('insert', '    ')
            return "break"

        # Custom backspace behaviour
        def smart_backspace(event):
            widget = event.widget
            index = widget.index("insert")

            # --- Delete matching closing pair if cursor is between them ---
            pairs = {"(": ")", "[": "]", "{": "}", '"': '"', "'": "'"}
            
            char_before = widget.get(f"{index}-1c", index)
            char_after = widget.get(index, f"{index}+1c")

            if char_before in pairs and pairs[char_before] == char_after:
                widget.delete(index, f"{index}+1c")  # delete closing pair first
                widget.delete(f"{index}-1c", index)  # then opening (cursor shifts left)
                return "break"

            # --- Original 4-space smart backspace ---
            line_start = widget.index(f"{index} linestart")
            text_before = widget.get(line_start, index)
            trailing_spaces = len(text_before) - len(text_before.rstrip(" "))
            if trailing_spaces >= 4:
                for _ in range(4):
                    widget.delete("insert-1c")
                return "break"

            return None

        # Auto indenting behaviour
        def auto_indent(event):
            current_line_index = self.code_text.index("insert linestart")
            current_line_text = self.code_text.get(current_line_index, f"{current_line_index} lineend")
            leading_spaces = len(current_line_text) - len(current_line_text.lstrip(' '))
            indent = ' ' * leading_spaces
            if current_line_text.strip().endswith(':'):
                indent += '    '
            self.code_text.insert("insert", "\n" + indent)

            # Reset horizontal scroll to follow the cursor
            self.code_text.see("insert")
            
            return "break"

        # --- Outer wrapper: stacks editor row + h_scroll vertically ---
        outer_frame = ttk.Frame(parent)
        outer_frame.pack(fill=tk.BOTH, expand=True)

        # --- Editor row: line numbers + code text + v_scroll ---
        editor_frame = ttk.Frame(outer_frame)
        editor_frame.pack(fill=tk.BOTH, expand=True)

        # Line numbers
        self.line_numbers = tk.Text(
            editor_frame, width=5, padx=4, takefocus=0,
            background='lightgrey', state='disabled', wrap='none', font=('Consolas', 12)
        )
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # Vertical scrollbar
        self.y_scroll = tk.Scrollbar(editor_frame, orient=tk.VERTICAL)
        self.y_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Code text
        self.code_text = tk.Text(
            editor_frame, wrap=tk.NONE, undo=True,
            bg="white", fg="black", tabs=('1c')
        )
        self.code_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Horizontal scrollbar — sits below the editor row, does NOT cover line numbers
        self.x_scroll = tk.Scrollbar(outer_frame, orient=tk.HORIZONTAL)
        self.x_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        # Wire up scrollbars
        self.code_text.config(
            yscrollcommand=self._on_code_scroll,
            xscrollcommand=self.x_scroll.set      # ← horizontal
        )
        self.y_scroll.config(command=self._on_scrollbar)
        self.x_scroll.config(command=self.code_text.xview)  # ← horizontal

        # ------------ BINDS ------------
        font = tkfont.Font(family="Consolas", size=12)
        self.code_text.config(font=font)
        self.code_text.bind('<Tab>', insert_tab, add="+")
        self.code_text.bind('<Return>', auto_indent, add="+")
        self.code_text.bind("<Key>", self._handle_auto_pairs, add="+")
        self.code_text.bind("<Key>", self._on_code_keypress, add="+")
        self.code_text.bind("<BackSpace>", smart_backspace, add="+")
        self.code_text.bind("<BackSpace>", self._on_code_keypress, add="+")
        self.code_text.bind("<Delete>", self._on_code_keypress, add="+")
        self.code_text.bind("<Button-1>", self._on_mouse_click)
        self.code_text.bind("<Button-3>", self._open_code_context_menu, add="+")
        self.code_text.bind("<Control-c>", self._on_ctrl_copy, add="+")
        self.code_text.bind("<Control-C>", self._on_ctrl_copy, add="+")
        self.code_text.bind("<Control-x>", self._on_ctrl_cut, add="+")
        self.code_text.bind("<Control-X>", self._on_ctrl_cut, add="+")
        self.code_text.bind("<Control-v>", self._on_ctrl_paste, add="+")
        self.code_text.bind("<Control-V>", self._on_ctrl_paste, add="+")
        self.code_text.bind("<Control-z>", self._custom_undo, add="+")
        self.code_text.bind("<Control-y>", self._custom_redo, add="+")

        self.code_text.bind('<KeyRelease>', lambda e: self._update_line_numbers(), add="+")
        self.code_text.bind('<MouseWheel>', lambda e: self._update_line_numbers(), add="+")
        self.code_text.bind('<Button-4>', lambda e: self._update_line_numbers(), add="+")
        self.code_text.bind('<Button-5>', lambda e: self._update_line_numbers(), add="+")
        self.code_text.bind('<BackSpace>', lambda e: self._update_line_numbers(), add="+")
        self.code_text.bind('<Configure>', lambda e: self._update_line_numbers(), add="+")

        self._update_line_numbers()

        self.code_text.bind("<KeyRelease>", self.highlight_syntax, add="+")
        # Also re-highlight when scrolling so newly visible lines get coloured
        self.code_text.bind("<MouseWheel>", lambda e: self.highlight_syntax(), add="+")
        self.code_text.bind("<Key>", self.undo_redo_code_text, add="+")
        self.code_text.bind("<<Modified>>", self._on_code_modified, add="+")
        self.code_text.bind("<Double-1>", self._select_word_on_double_click, add="+")

        self._setup_protected_code_areas()
        

        

    # Scrollbar callbacks
    def _on_code_scroll(self, first, last):
        self.line_numbers.yview_moveto(first)
        self.y_scroll.set(first, last)

    def _on_scrollbar(self, *args):
        self.code_text.yview(*args)
        self.line_numbers.yview(*args)

    # Update line numbers for each line in code editor
    def _update_line_numbers(self, event=None):
        yview = self.code_text.yview()  # returns (first, last)
        
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', 'end')
        line_count = int(self.code_text.index('end-1c').split('.')[0])
        line_numbers_str = "\n".join(str(i) for i in range(1, line_count + 1)) + '\n'
        self.line_numbers.insert('1.0', line_numbers_str)
        self.line_numbers.config(state='disabled')
        
        # Restore scroll position
        # Typing in editor was resetting line number position
        #self.code_text.yview_moveto(yview[0])
        self.line_numbers.yview_moveto(yview[0])


    # Marks key Python syntax with colored text
    # This call will call a performance friendly syntax highlight update
    def highlight_syntax(self, event=None):
        """Debounced entry point — called on keyrelease."""
        # Cancel any pending highlight call
        if self._highlight_after_id:
            self.after_cancel(self._highlight_after_id)
        # Schedule highlight after 300ms of inactivity
        self._highlight_after_id = self.after(100, self._do_highlight)

    # Updates code editor with syntax colouring
    # This call is not performance friendly and should be used minimally
    # only when whole code needs updated
    # This was the original highlight_syntax method
    def do_full_highlight(self, event=None):
        self.code_text.tag_remove("keyword", "1.0", tk.END)
        self.code_text.tag_remove("comment", "1.0", tk.END)
        self.code_text.tag_remove("string", "1.0", tk.END)
        self.code_text.tag_remove("builtin", "1.0", tk.END)

        text = self.code_text.get("1.0", tk.END)

        # Track spans already tagged (comments) so strings don't override them
        spans = []

        # 1. Comments first
        comment_pattern = re.compile(r"#.*")
        for match in comment_pattern.finditer(text):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            self.code_text.tag_add("comment", start, end)
            spans.append((match.start(), match.end()))

        # is this character position inside a comment?
        def in_comment(pos):
            return any(s <= pos < e for s, e in spans)

        # 2. String highlighting — skips anything inside a comment span
        lines = text.splitlines(keepends=True)

        char_index = 0
        in_triple = False
        triple_delim = None
        triple_start = None

        for line in lines:
            i = 0
            line_start = char_index

            while i < len(line):
                ch = line[i]
                global_i = line_start + i

                if in_triple:
                    if line[i:i+3] == triple_delim:
                        i += 3
                        in_triple = False
                        self.code_text.tag_add(
                            "string",
                            f"1.0 + {triple_start} chars",
                            f"1.0 + {global_i + 3} chars"
                        )
                        continue
                else:
                    # Skip if we're inside a comment
                    if in_comment(global_i):
                        i += 1
                        continue

                    if line[i:i+3] in ('"""', "'''"):
                        in_triple = True
                        triple_delim = line[i:i+3]
                        triple_start = global_i
                        i += 3
                        continue

                    if ch in ("'", '"'):
                        quote = ch
                        start = global_i
                        end_found = False
                        j = i + 1

                        while j < len(line):
                            # Stop scanning if we hit a comment mid-line
                            if in_comment(line_start + j):
                                break
                            if line[j] == quote:
                                end = line_start + j + 1
                                self.code_text.tag_add(
                                    "string",
                                    f"1.0 + {start} chars",
                                    f"1.0 + {end} chars"
                                )
                                i = j
                                end_found = True
                                break
                            j += 1

                        if not end_found:
                            end = line_start + len(line)
                            self.code_text.tag_add(
                                "string",
                                f"1.0 + {start} chars",
                                f"1.0 + {end} chars"
                            )
                            i = len(line)

                i += 1

            if in_triple and triple_start is not None:
                self.code_text.tag_add(
                    "string",
                    f"1.0 + {triple_start} chars",
                    f"1.0 + {line_start + len(line)} chars"
                )

            char_index += len(line)

        # 3. Keywords — skip comment and string spans
        for kw in keyword.kwlist:
            for match in re.finditer(rf"\b{kw}\b", text):
                if any(s <= match.start() < e or s < match.end() <= e for s, e in spans):
                    continue
                self.code_text.tag_add("keyword", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")

        # 4. Builtins — skip comment and string spans
        for bi in dir(builtins):
            for match in re.finditer(rf"\b{bi}\b", text):
                if any(s <= match.start() < e or s < match.end() <= e for s, e in spans):
                    continue
                self.code_text.tag_add("builtin", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")

    # Performance friendly syntax highlighting
    def _do_highlight(self):
        self._highlight_after_id = None
        text = self.code_text.get("1.0", tk.END)

        # ---- Only highlight the visible region + small buffer ----
        top, bottom = self.code_text.yview()
        total_lines = int(self.code_text.index("end-1c").split(".")[0])
        first_line = max(1, int(top * total_lines) - 20)
        last_line  = min(total_lines, int(bottom * total_lines) + 20)

        region_start = f"{first_line}.0"
        region_end   = f"{last_line}.end"

        # Clear tags only in visible region — much faster than clearing all
        for tag in ("keyword", "comment", "string", "builtin"):
            self.code_text.tag_remove(tag, region_start, region_end)

        # Get just the visible text with its offset for correct indexing
        region_text = self.code_text.get(region_start, region_end)
        # char offset of region_start from "1.0"
        offset = len(self.code_text.get("1.0", region_start))

        spans = []  # track comment/string spans to prevent overlap

        # ---- 1. Comments ----
        for match in re.compile(r"#.*").finditer(region_text):
            abs_start = offset + match.start()
            abs_end   = offset + match.end()
            self.code_text.tag_add("comment",
                f"1.0 + {abs_start} chars",
                f"1.0 + {abs_end} chars")
            spans.append((match.start(), match.end()))

        def in_comment(pos):
            return any(s <= pos < e for s, e in spans)

        # ---- 2. Strings ----
        lines = region_text.splitlines(keepends=True)
        char_index = 0
        in_triple = False
        triple_delim = None
        triple_start = None

        for line in lines:
            i = 0
            line_start = char_index

            while i < len(line):
                ch = line[i]
                global_i = line_start + i

                if in_triple:
                    if line[i:i+3] == triple_delim:
                        i += 3
                        in_triple = False
                        self.code_text.tag_add("string",
                            f"1.0 + {offset + triple_start} chars",
                            f"1.0 + {offset + global_i + 3} chars")
                        continue
                else:
                    if in_comment(global_i):
                        i += 1
                        continue
                    if line[i:i+3] in ('"""', "'''"):
                        in_triple = True
                        triple_delim = line[i:i+3]
                        triple_start = global_i
                        i += 3
                        continue
                    if ch in ("'", '"'):
                        quote = ch
                        start = global_i
                        end_found = False
                        j = i + 1
                        while j < len(line):
                            if in_comment(line_start + j):
                                break
                            if line[j] == quote:
                                self.code_text.tag_add("string",
                                    f"1.0 + {offset + start} chars",
                                    f"1.0 + {offset + line_start + j + 1} chars")
                                i = j
                                end_found = True
                                break
                            j += 1
                        if not end_found:
                            self.code_text.tag_add("string",
                                f"1.0 + {offset + start} chars",
                                f"1.0 + {offset + line_start + len(line)} chars")
                            i = len(line)
                i += 1

            if in_triple and triple_start is not None:
                self.code_text.tag_add("string",
                    f"1.0 + {offset + triple_start} chars",
                    f"1.0 + {offset + line_start + len(line)} chars")

            char_index += len(line)

        # ---- 3. Keywords — compiled patterns, checked against spans ----
        # Pre-compile all keyword patterns once at class level for speed
        if not hasattr(self, '_kw_pattern'):
            kw = "|".join(rf"\b{re.escape(k)}\b" for k in keyword.kwlist)
            self._kw_pattern = re.compile(kw)

        for match in self._kw_pattern.finditer(region_text):
            if any(s <= match.start() < e or s < match.end() <= e for s, e in spans):
                continue
            self.code_text.tag_add("keyword",
                f"1.0 + {offset + match.start()} chars",
                f"1.0 + {offset + match.end()} chars")

        # ---- 4. Builtins — compiled once, filtered to avoid clashing with keywords ----
        if not hasattr(self, '_builtin_pattern'):
            bi_list = [b for b in dir(builtins) if b not in keyword.kwlist]
            bi = "|".join(rf"\b{re.escape(b)}\b" for b in bi_list)
            self._builtin_pattern = re.compile(bi)

        for match in self._builtin_pattern.finditer(region_text):
            if any(s <= match.start() < e or s < match.end() <= e for s, e in spans):
                continue
            self.code_text.tag_add("builtin",
                f"1.0 + {offset + match.start()} chars",
                f"1.0 + {offset + match.end()} chars")


    # ------------------- Element management ---------------------------------

    # Adding an element via undo / redo action
    # For different undo / redo stack behaviour handling
    def add_element_from_undo_redo(self, props, src, action_origin):

        if props['action_type'] == "del" and action_origin == "redo":

            prop_cop = props.copy()
            self.undo_stack.append(prop_cop)
            self._undo_delete_element(prop_cop['name'])

        elif props['action_type'] == "add" and action_origin == "redo":
            prop_cop = props.copy()
            self.undo_stack.append(prop_cop)
            self.elements[props['name']] = props
            self._create_visual(props)
            self.normal_generate_code()
            self._update_protected_tags()
            

        elif action_origin == "undo":

            self.elements[props['name']] = props
            self._create_visual(props)
            self.normal_generate_code()
            self._update_protected_tags()


        # Reset the redo stack when a new element is added from buttons
        if src == "new":
            self.redo_stack = []

    # Where does a widget spawn when added
    # Makes sure they spawn inside canvas
    def _get_next_spawn_position(self, w, h):
        #Calculate next spawn position that stays within canvas bounds and wraps.
        canvas_w = getattr(self, 'canvas_width', 800)
        canvas_h = getattr(self, 'canvas_height', 400)

        # Margin offsets matching _draw_canvas_boundary
        margin_x = 20
        margin_y = 50  # accounts for title bar

        # Count existing elements to determine position
        count = len(self.elements)
        cols = max(1, (canvas_w - margin_x * 2) // (w + 10))

        col = count % cols
        row = count // cols

        x = margin_x + col * (w + 10)
        y = margin_y + row * (h + 10)

        # If run out of vertical space, wrap back to top with slight offset
        max_y = margin_y + canvas_h - h - 10
        if y > max_y:
            x = margin_x + ((count * 10) % (canvas_w - margin_x - w))
            y = margin_y + ((count * 10) % (canvas_h - margin_y - h))

        return int(x), int(y)

    def _get_default_size(self, eltype):
        sizes = {
            'Label':       (120, 30),
            'Button':      (120, 35),
            'Entry':       (150, 30),
            'TextArea':    (200, 100),
            'Listbox':     (150, 100),
            'Combobox':    (150, 30),
            'Treeview':    (200, 120),
            'Checkbutton': (130, 30),
            'Radiobutton': (130, 30),
            'Image':       (150, 150),
        }
        return sizes.get(eltype, (120, 40))
    
    # Called when user clicked an add widget button.
    # First function which is called when adding a widget to the canvas
    def add_element(self, eltype, src):
        name = next_name(self.counters, eltype.lower())

        # Special handling for radiobutton
        if eltype == "Radiobutton":
            existing_groups = sorted({
                p.get('_radio_group_name')
                for p in self.elements.values()
                if p['type'] == 'Radiobutton' and '_radio_group_name' in p
            })
            dialog = RadioGroupDialog(self, existing_groups)
            choice = dialog.result
            if not choice:
                return

        if src == 'new':
            default_w, default_h = self._get_default_size(eltype)
            x, y = self._get_next_spawn_position(default_w, default_h)
        else:
            x, y = 50, 50
            default_w, default_h = 100, 30

        # default properties — now uses x, y, default_w, default_h
        props = {
            'type': eltype,
            'name': name,
            'text': eltype,
            'x': x,           # now uses spawn position
            'y': y,           # now uses spawn position
            'w': default_w,   # was hardcoded 100
            'h': default_h,   # was hardcoded 30
        }

        if eltype == "Entry":
            props['text'] = ""
            props['font_family'] = "Arial"
            props['font_size'] = 12
            props['foreground'] = "#000000"
            props['background'] = "#FFFFFF"
        elif eltype == "Label":
            props['font_family'] = "Arial"
            props['font_size'] = 12
            props['foreground'] = "#000000"
            props['background'] = "#FFFFFF"
        elif eltype == "Button":
            props['font_family'] = "Arial"
            props['font_size'] = 12
            props['foreground'] = "#000000"
            props['background'] = "#FFFFFF"
        elif eltype == "TextArea":
            props['text'] = ""
        elif eltype == "Listbox":
            props['text'] = ""
        elif eltype == "Combobox":
            props['text'] = ""
        elif eltype == "Checkbutton":
            props['font_family'] = "Arial"
            props['font_size'] = 12
            props['foreground'] = "#000000"
            props['background'] = "#FFFFFF"
        elif eltype == "Radiobutton":
            props['_radio_group_name'] = choice
            props['font_family'] = "Arial"
            props['font_size'] = 12
            props['foreground'] = "#000000"
            props['background'] = "#FFFFFF"
        elif eltype == "Image":
            # Image has its own flow, override props
            file_path = filedialog.askopenfilename(
                title="Select Image",
                initialdir="images/",
                filetypes=[("Image files", "*.png *.gif *.ppm *.pgm")]
            )
            if not file_path:
                return
            img = tk.PhotoImage(file=file_path)
            props.update({
                "text": file_path,
                "w": 200,
                "h": 200,
                "_original_img": img,
                "_photo": img,
            })


        self.elements[name] = props
        self._create_visual(props)
        self.normal_generate_code()
        self._update_protected_tags()

        props['action_type'] = 'add'
        undo_copy = {k: v for k, v in props.items() if not k.startswith('_')}
        self.undo_stack.append(undo_copy)

        # Reset the redo stack when a new element is added from buttons
        if src == "new":
            self.redo_stack = []

    # For debugging output - not used in prod
    def stack_out(self, stack):

        for i in range(len(stack)):
            print(i, stack[i]['name'], stack[i]['action_type'])


    # For making sure when copy and pasting in the code editor or other entries
    # it does not result in copy and pasting in the canvas
    def _conditional_copy(self, event, name):
        focused = self.focus_get()
        
        if focused == self.code_text or (hasattr(focused, 'winfo_class') and focused.winfo_class() in ['Text', 'Entry', 'TEntry']):
            # Let text widget handle it normally
            return
        else:
            self.copy_element(name)

    # For making sure when copy and pasting in the code editor or other entries
    # it does not result in copy and pasting in the canvas
    def _conditional_paste(self, event, name=None):
        focused = self.focus_get()
        if focused == self.code_text or (hasattr(focused, 'winfo_class') and 
           focused.winfo_class() in ['Text', 'Entry', 'TEntry']):
            return
        self.paste_element()

    # Copy an element (widget)
    def copy_element(self, name):
        element = self.elements.get(name)
        if not element:
            return
        self.select_element(name)
        # Strip private widget refs — only store serialisable properties
        self.copied_element = {
            k: v for k, v in element.items()
            if not k.startswith('_') or k == '_radio_group_name'
        }


    # Paste an element (widget)
    def paste_element(self, name=None):
        if not hasattr(self, "copied_element") or not self.copied_element:
            return

        eltype = self.copied_element.get('type')
        if not eltype:
            return

        new_name = next_name(self.counters, eltype.lower())

        # Fresh copy with no stale widget refs
        new_props = {
            k: v for k, v in self.copied_element.items()
            if not k.startswith('_')
        }
        new_props['name'] = new_name
        new_props['x'] = new_props.get('x', 50) + 20
        new_props['y'] = new_props.get('y', 50) + 20

        # ---- Handle radiobutton group BEFORE adding to elements ----
        if eltype == 'Radiobutton':
            # Restore the group name from copied element (it was stripped)
            original_group = self.copied_element.get('_radio_group_name')

            existing_groups = sorted({
                p.get('_radio_group_name')
                for p in self.elements.values()
                if p['type'] == 'Radiobutton' and p.get('_radio_group_name')
            })

            dialog = RadioGroupDialog(self, existing_groups)
            choice = dialog.result
            if not choice:
                return  # user cancelled — don't paste

            new_props['_radio_group_name'] = choice

        self.elements[new_name] = new_props
        self._create_visual(new_props)
        self.normal_generate_code()
        self._update_protected_tags()

        # Push to undo stack — clean copy
        undo_copy = {k: v for k, v in new_props.items() if not k.startswith('_')}
        undo_copy['action_type'] = 'add'
        self.undo_stack.append(undo_copy)
        self.redo_stack.clear()



    # Called in apply_properties() at the bottom
    # Updates elements with property changes
    def _update_element(self, name=None):
        
        # Update the visual widget and bindings for element 'name'.
        # If name is None, use self.selected.
        
        if name is None:
            name = self.selected
        if not name or name not in self.elements:
            return
        
        props = self.elements[name]
        widget = props.get('_widget')
        frame = props.get('_frame')

        text = props.get('text', '')

        if widget:
            if isinstance(widget, ttk.Entry):
                widget.delete(0, tk.END)
                widget.insert(0, text)

            elif props["type"] == "Label":
                font_family = props.get('font_family', "Arial")
                font_size = props.get('font_size', 12)
                fg = props.get('foreground', "#000000")
                bg = props.get('background', "#FFFFFF")
                widget.config(
                    text=text,
                    font=(font_family, font_size),
                    fg=fg,
                    bg=bg
                )
                if frame:
                    frame.config(bg=bg)  # also update frame background

            elif props["type"] == "Button":
                # Update text
                widget.config(text=text)
                # Create or update a unique style per button
                style_name = f"{name}.TButton"
                style = ttk.Style()
                style.configure(
                    style_name,
                    font=(props.get('font_family', 'Arial'), props.get('font_size', 12)),
                    foreground=props.get('foreground', '#000000'),
                    background=props.get('background', '#FFFFFF')
                )
                widget.config(style=style_name)

            elif props["type"] == "Entry" and widget:
                font_family = props.get('font_family', "Arial")
                font_size = props.get('font_size', 12)
                fg = props.get('foreground', "#000000")
                bg = props.get('background', "#FFFFFF")
                widget.config(
                    font=(font_family, font_size),
                    fg=fg,
                    bg=bg
                )
                widget.delete(0, tk.END)
                widget.insert(0, text)
                frame.config(bg=bg)  # make frame blend too


            elif props["type"] == "Checkbutton" and widget:
                widget.config(text=text)
                style_name = f"{name}.TCheckbutton"
                style = ttk.Style()
                style.configure(
                    style_name,
                    font=(props.get("font_family", "Arial"), props.get("font_size", 12)),
                    foreground=props.get("foreground", "#000000"),
                    background=props.get("background", "#FFFFFF"),
                )
                widget.config(style=style_name)

            elif props["type"] == "Radiobutton" and widget:
                widget.config(text=text)
                style_name = f"{name}.TRadiobutton"
                style = ttk.Style()
                style.configure(
                    style_name,
                    font=(props.get("font_family", "Arial"), props.get("font_size", 12)),
                    foreground=props.get("foreground", "#000000"),
                    background=props.get("background", "#FFFFFF"),
                )
                widget.config(style=style_name)


            elif props["type"] == "Image":
                orig = props.get("_original_img")
                cid = props.get('_window_id')
                if orig and cid:
                    ow, oh = orig.width(), orig.height()
                    if ow > 0 and oh > 0 and props["w"] > 0 and props["h"] > 0:
                        x_factor = max(1, ow // props["w"])
                        y_factor = max(1, oh // props["h"])
                        scaled = orig.subsample(x_factor, y_factor)
                        props["_photo"] = scaled
                        #self.image_cache[cid] = scaled  # keep reference
                        #self.canvas.itemconfig(cid, image=scaled)

            else:
                try:
                    widget.config(text=text)
                except Exception:
                    pass

        # Update canvas position and size
        if props.get('_window_id'):
            self.canvas.coords(props['_window_id'], props['x'], props['y'])
            self.canvas.itemconfigure(props['_window_id'], width=props['w'], height=props['h'])
            self.canvas.itemconfig(props['_window_id'], tags=(name,))

        # Rebind events to avoid stale lambdas
        if frame:
            frame.bind('<Button-1>', lambda e, n=name: self._on_mouse_down(e, n))
            frame.bind('<B1-Motion>', lambda e, n=name: self._on_mouse_move(e, n))
            frame.bind('<ButtonRelease-1>', lambda e, n=name: self._on_mouse_up(e, n))
            frame.bind('<Motion>', lambda e, n=name: self._update_cursor(e, n))

        if widget:
            widget.bind('<Button-1>', lambda e, n=name: self._on_mouse_down(e, n))
            widget.bind('<B1-Motion>', lambda e, n=name: self._on_mouse_move(e, n))
            widget.bind('<ButtonRelease-1>', lambda e, n=name: self._on_mouse_up(e, n))
            widget.bind('<Motion>', lambda e, n=name: self._update_cursor(e, n))
            

    
            

    # Creates the actual widget onto the canvas. Called in add_element() and paste_element()
    def _create_visual(self, props):
        self._on_modification_made()

        eltype = props['type']
        name   = props['name']
        text   = props.get('text', name)
        x, y, w, h = props['x'], props['y'], props['w'], props['h']

        frame  = tk.Frame(self.canvas)
        widget = None

        if eltype == 'Label':
            widget = tk.Label(frame, text=text,
                font=(props.get('font_family', 'Arial'), props.get('font_size', 12)),
                fg=props.get('foreground', "#000000"),
                bg=props.get('background', "#FFFFFF"))

        elif eltype == 'Button':
            style_name = f"{name}.TButton"
            # FIX: reuse self.style instead of creating new ttk.Style() each time
            self.style.configure(style_name,
                font=(props.get('font_family', 'Arial'), props.get('font_size', 12)),
                foreground=props.get('foreground', '#000000'),
                background=props.get('background', '#FFFFFF'))
            widget = ttk.Button(frame, text=text,
                command=lambda n=name: self._on_builder_button_click(n),
                style=style_name)

        elif eltype == 'Entry':
            widget = tk.Entry(frame,
                font=(props.get('font_family', 'Arial'), props.get('font_size', 12)),
                fg=props.get('foreground', '#000000'),
                bg=props.get('background', '#FFFFFF'))
            widget.insert(0, text)

        elif eltype == 'TextArea':
            widget = tk.Text(frame, width=20, height=5)

        elif eltype == 'Listbox':
            widget = tk.Listbox(frame)
            for item in ("Item 1", "Item 2", "Item 3"):
                widget.insert(tk.END, item)

        elif eltype == 'Combobox':
            widget = ttk.Combobox(frame, values=["Option 1", "Option 2", "Option 3"])
            widget.set(text)

        elif eltype == 'Treeview':
            widget = ttk.Treeview(frame, columns=('c1',), show='headings', height=3)
            widget.heading('c1', text='Column')
            widget.insert('', 'end', values=(text,))

        elif eltype == 'Checkbutton':
            var = tk.BooleanVar(value=False)
            props['_var'] = var
            style_name = f"{name}.TCheckbutton"
            self.style.configure(style_name,  # FIX: reuse self.style
                font=(props.get('font_family', 'Arial'), props.get('font_size', 12)),
                foreground=props.get('foreground', '#000000'),
                background=props.get('background', '#FFFFFF'))
            widget = ttk.Checkbutton(frame, text=text, variable=var,
                onvalue=True, offvalue=False, style=style_name)

        elif eltype == 'Radiobutton':
            choice = props.get('_radio_group_name')
            if not choice:
                existing_groups = sorted({
                    p.get('_radio_group_name')
                    for p in self.elements.values()
                    if p['type'] == 'Radiobutton' and '_radio_group_name' in p
                })
                dialog = RadioGroupDialog(self, existing_groups)
                choice = dialog.result
                if not choice:
                    return
                props['_radio_group_name'] = choice

            if choice not in self.radio_groups:
                self.radio_groups[choice] = tk.StringVar(value='')
            var = self.radio_groups[choice]
            props['_radio_group_var'] = var

            style_name = f"{name}.TRadiobutton"
            self.style.configure(style_name,  # FIX: reuse self.style
                font=(props.get('font_family', 'Arial'), props.get('font_size', 12)),
                foreground=props.get('foreground', '#000000'),
                background=props.get('background', '#FFFFFF'))
            widget = ttk.Radiobutton(frame, text=text, variable=var,
                value=text, style=style_name)

        elif eltype == 'Image':
            try:
                img = tk.PhotoImage(file=text)
                widget = tk.Canvas(frame, highlightthickness=0)
                widget.original_image = img
                widget.scaled_image   = img
                widget.image_id       = widget.create_image(0, 0, anchor="nw", image=img)

                def resize_image(event, widget=widget):
                    widget.delete(widget.image_id)
                    ow, oh = widget.original_image.width(), widget.original_image.height()
                    if event.width > 0 and event.height > 0:
                        x_factor = max(1, round(ow / event.width))
                        y_factor = max(1, round(oh / event.height))
                        scaled = widget.original_image.subsample(x_factor, y_factor)
                        widget.scaled_image = scaled
                        widget.image_id = widget.create_image(0, 0, anchor="nw", image=scaled)
                    widget.config(width=event.width, height=event.height)

                widget.bind("<Configure>", resize_image)
            except Exception as e:
                print("Image error:", e)
                widget = ttk.Label(frame, text=f'Image load failed.\n\nPath:{text}')
        else:
            widget = ttk.Label(frame, text=f"{eltype}")

        widget.pack(fill=tk.BOTH, expand=True)

        window_id = self.canvas.create_window(x, y, window=frame, anchor='nw',
                                              width=w, height=h, tags=(name,))
        props['_window_id'] = window_id
        props['_frame']     = frame
        props['_widget']    = widget

        # Event bindings
        for target in (frame, widget):
            target.bind('<Button-1>',        lambda e, n=name: self._on_mouse_down(e, n))
            target.bind('<B1-Motion>',       lambda e, n=name: self._on_mouse_move(e, n))
            target.bind('<ButtonRelease-1>', lambda e, n=name: self._on_mouse_up(e, n))
            target.bind('<Motion>',          lambda e, n=name: self._update_cursor(e, n))
            target.bind('<Button-3>',        lambda e, n=name: self._show_element_menu(e, n))

        widget.bind('<Double-1>', lambda e, n=name: self.widget_double_click(e, n))



    # Double clicking a widget opens a dialog to let the user set the text value for the widget
    def widget_double_click(self, event, name):
        self.select_element(name)
        element = self.elements.get(name)
        if not element:
            return

        old_text = element.get('text', '')
        dialog = CustomAskString(self, "Edit Text", f"Enter new text for {name}:")
        new_text = dialog.result
        #new_text = simpledialog.askstring("Edit Text", f"Enter new text for {name}:", initialvalue=old_text)

        if new_text is not None:
            element['text'] = new_text

            # Update the property editor live
            self.prop_text.delete(0, tk.END)
            self.prop_text.insert(0, new_text)

            # Let _update_element handle updating the widget itself
            self._update_element(name)

            # Regenerate the code
            self.normal_generate_code()
            self._update_protected_tags()



    # Changes the mouse cursor to directional arrows
    # when near the corner or sides of a widget to indicate
    # the widget can be resized with click and drag
    def _update_cursor(self, event, name):
        props = self.elements[name]
        w = props['w']
        h = props['h']
        x = event.x
        y = event.y
        border_threshold = 8

        cursor = ''

        near_left = (0 <= x <= border_threshold)
        near_right = (w - border_threshold <= x <= w)
        near_top = (0 <= y <= border_threshold)
        near_bottom = (h - border_threshold <= y <= h)

        if near_left and near_top:
            cursor = "size_nw_se"
        elif near_right and near_top:
            cursor = "size_ne_sw"
        elif near_left and near_bottom:
            cursor = "size_ne_sw"
        elif near_right and near_bottom:
            cursor = "size_nw_se"
        elif near_top:
            cursor = "sb_v_double_arrow"
        elif near_bottom:
            cursor = "sb_v_double_arrow"
        elif near_left:
            cursor = "sb_h_double_arrow"
        elif near_right:
            cursor = "sb_h_double_arrow"
        else:
            cursor = "" # default mouse


        frame = props['_frame']

        def apply_cursor(widget, cursor_type):
            try:
                widget.config(cursor=cursor_type)
            except:
                pass
            for child in widget.winfo_children():
                apply_cursor(child, cursor_type)

        cursor_type = cursor if cursor else "arrow"

        apply_cursor(frame, cursor_type)


    # Function for resizing widgets or dragging them around canvas
    def _on_mouse_down(self, event, name):
        
        props = self.elements[name]

        # Only call select_element if this isn't already selected
        # avoids redundant property panel updates and highlight redraws

        if self.selected != name:
            self.select_element(name)
        else:
            self.selected = name

        # Calculate mouse position relative to element
        x = event.x
        y = event.y
        w = props['w']
        h = props['h']

        border_threshold = 8  # pixels near edge to start resize

        resizing = None
        
        # Check if near right edge
        if w - border_threshold <= x <= w:
            resizing = 'right'
        # Check if near bottom edge
        
        if h - border_threshold <= y <= h:
            if resizing:
                resizing = 'corner'  # bottom-right corner
            else:
                resizing = 'bottom'
                
        # Check if near left edge
        if 0 <= x <= border_threshold:
            resizing = 'left'
            
        # Check if near top edge
        if 0 <= y <= border_threshold:
            if resizing in ('right', 'corner'):
                resizing = 'top-right'
            elif resizing == 'bottom':
                resizing = 'top-bottom'
            else:
                resizing = 'top'

        if resizing:
            self._resize_mode = resizing
            self._resize_start = (event.x_root, event.y_root)
            self._resize_orig = (props['x'], props['y'], props['w'], props['h'])
        else:
            # dragging mode
            self._resize_mode = None
            self._drag_start = (event.x_root, event.y_root)
            self._drag_orig = (props['x'], props['y'])

        # Track whether anything actually moved
        self._interaction_moved = False


    # Either resizes widgets or moves them over the canvas
    def _on_mouse_move(self, event, name):

        # Mark that mouse has moved
        self._interaction_moved = True
        props = self.elements[name]

        self._on_modification_made()

        if hasattr(self, '_resize_mode') and self._resize_mode:
            # resizing logic
            dx = event.x_root - self._resize_start[0]
            dy = event.y_root - self._resize_start[1]
            x0, y0, w0, h0 = self._resize_orig

            new_x, new_y, new_w, new_h = x0, y0, w0, h0
            min_size = 20
            #self.grid_size = 10  # snap size for resizing

            mode = self._resize_mode
            if mode == 'right':
                new_w = max(min_size, w0 + dx)
            elif mode == 'bottom':
                new_h = max(min_size, h0 + dy)
            elif mode == 'corner':
                new_w = max(min_size, w0 + dx)
                new_h = max(min_size, h0 + dy)
            elif mode == 'left':
                new_x = x0 + dx
                new_w = max(min_size, w0 - dx)
                if new_w == min_size:
                    new_x = x0 + (w0 - min_size)
            elif mode == 'top':
                new_y = y0 + dy
                new_h = max(min_size, h0 - dy)
                if new_h == min_size:
                    new_y = y0 + (h0 - min_size)
            elif mode == 'top-right':
                new_y = y0 + dy
                new_h = max(min_size, h0 - dy)
                if new_h == min_size:
                    new_y = y0 + (h0 - min_size)
                new_w = max(min_size, w0 + dx)

            # Snap width/height to nearest 10px (now grid_size)
            new_w = round(new_w / self.grid_size) * self.grid_size
            new_h = round(new_h / self.grid_size) * self.grid_size

            # Also snap x/y if adjusting from left or top
            new_x = round(new_x / self.grid_size) * self.grid_size
            new_y = round(new_y / self.grid_size) * self.grid_size

            props['x'], props['y'], props['w'], props['h'] = int(new_x), int(new_y), int(new_w), int(new_h)

            self.canvas.coords(props['_window_id'], props['x'], props['y'])
            self.canvas.itemconfig(props['_window_id'], width=props['w'], height=props['h'])
            if self.selected == name:
                self._highlight_selected()
                self.prop_x.delete(0, tk.END); self.prop_x.insert(0, props['x'])
                self.prop_y.delete(0, tk.END); self.prop_y.insert(0, props['y'])
                self.prop_w.delete(0, tk.END); self.prop_w.insert(0, props['w'])
                self.prop_h.delete(0, tk.END); self.prop_h.insert(0, props['h'])
                #self._update_element(name)

        elif hasattr(self, '_drag_start'):
            # dragging logic
            dx = event.x_root - self._drag_start[0]
            dy = event.y_root - self._drag_start[1]
            new_x = self._drag_orig[0] + dx
            new_y = self._drag_orig[1] + dy

            # Snap to grid (10px increments)
            #grid_size = 10
            new_x = round(new_x / self.grid_size) * self.grid_size
            new_y = round(new_y / self.grid_size) * self.grid_size

            props['x'], props['y'] = int(new_x), int(new_y)
            self.canvas.coords(props['_window_id'], props['x'], props['y'])

            if self.selected == name:
                self._highlight_selected()
                self.prop_x.delete(0, tk.END); self.prop_x.insert(0, props['x'])
                self.prop_y.delete(0, tk.END); self.prop_y.insert(0, props['y'])
                #self._update_element(name)

    # Reset on mouse up
    def _on_mouse_up(self, event, name):
        
        # reset drag/resize states
        self._resize_mode = None
        self._drag_start = None
        #self._update_element(name)
        
        #self.apply_properties()
        # Only apply properties if widget was actually dragged or resized
        # Means user can just click / select without tiggering code being dirty
        if getattr(self, '_interaction_moved', False):
            self._interaction_moved = False
            self.apply_properties()
        else:
            self._interaction_moved = False


    # Default command when a button in the canvas design pane is clicked
    # Just defaults to no action as no action should be possible
    # as it is only for design not functionality
    def _on_builder_button_click(self, name):
        pass

    # Identify selected element
    def select_element(self, name):

        if name not in self.elements:
            return
        
        self.selected = name
        props = self.elements[name]

        self.prop_id.delete(0, tk.END)
        self.prop_id.insert(0, props['name'])
        type_label = props['type']
        if props['type'] == 'Radiobutton':
            group = props.get('_radio_group_name', '?')
            type_label = f"Radiobutton  [{group}]"
        self.prop_type.config(text=type_label)
        self.prop_text.delete(0, tk.END)
        self.prop_text.insert(0, props.get('text', ''))
        self.prop_x.delete(0, tk.END)
        self.prop_x.insert(0, str(props.get('x', 0)))
        self.prop_y.delete(0, tk.END)
        self.prop_y.insert(0, str(props.get('y', 0)))
        self.prop_w.delete(0, tk.END)
        self.prop_w.insert(0, str(props.get('w', 0)))
        self.prop_h.delete(0, tk.END)
        self.prop_h.insert(0, str(props.get('h', 0)))

        if props["type"] in ("Label", "Button", "Entry", "Checkbutton", "Radiobutton"):
            self.prop_font_family.set(props.get("font_family", "Arial"))
            self.prop_font_size.delete(0, tk.END)
            self.prop_font_size.insert(0, props.get("font_size", 12))
            self.prop_fg.delete(0, tk.END)
            self.prop_fg.insert(0, props.get("foreground", "black"))
            self.prop_bg.delete(0, tk.END)
            self.prop_bg.insert(0, props.get("background", "white"))

            self.update_color_swatches()
        else:
            # Clear or disable them for widget types without font/color
            self.prop_font_family.set("")
            self.prop_font_size.delete(0, tk.END)
            self.prop_fg.delete(0, tk.END)
            self.prop_bg.delete(0, tk.END)

        self._highlight_selected()


    # Highlights the selected canvas element
    def _highlight_selected(self):
        # remove existing highlight
        self.canvas.delete('selrect')
        if not self.selected: return
        props = self.elements[self.selected]
        wid = props.get('_window_id')
        if not wid: return
        bbox = self.canvas.bbox(wid)
        if not bbox: return
        x1, y1, x2, y2 = bbox
        rect = self.canvas.create_rectangle(x1-2, y1-2, x2+2, y2+2, outline='red', width=2, tags='selrect')
        self.canvas.tag_raise(rect)


    def _deselect_element(self):
        self.selected = None
        self.canvas.delete('selrect')
        self.prop_id.delete(0, tk.END)
        self.prop_type.config(text='-')
        self.prop_text.delete(0, tk.END)
        self.prop_x.delete(0, tk.END)
        self.prop_y.delete(0, tk.END)
        self.prop_w.delete(0, tk.END)
        self.prop_h.delete(0, tk.END)
        

    # Clear selected element if clicking empty space
    def canvas_click(self, event):

        # convert coords (important for scrolling)
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        # check topmost item under cursor
        items = self.canvas.find_overlapping(x, y, x, y)

        for it in reversed(items):
            tags = self.canvas.gettags(it)
            if not tags:
                continue

            name = tags[0]

            # only treat real widgets as selectable
            if name in self.elements:
                self.select_element(name)
                return

        self._deselect_element()

    def apply_button_pressed(self):

        try:
            new_name = self.prop_id.get().strip()
            self.show_toast(f"{new_name} properties updated.")
            self.apply_properties()
            
        except Exception as e:
            print(e)
        

    # Applies / reapplies all properties of widget / canvas globally
    def apply_properties(self):

        yview = self.code_text.yview()  # returns (first, last)
        

        existing_code = self.code_text.get('1.0', tk.END)
        

        if not self.selected:
            return

        props = self.elements[self.selected]
        old_name = self.selected
        new_name = self.prop_id.get().strip()


        # Validate new_name
        if not new_name:
            messagebox.showerror("Invalid Name", "ID cannot be empty.")
            self.prop_id.delete(0, tk.END)
            self.prop_id.insert(0, self.selected)
            return
        if not new_name.isidentifier():
            messagebox.showerror("Invalid Name", f"'{new_name}' is not a valid identifier.")
            self.prop_id.delete(0, tk.END)
            self.prop_id.insert(0, self.selected)
            return
        if keyword.iskeyword(new_name):
            messagebox.showerror("Invalid Name", f"'{new_name}' is a reserved Python keyword.")
            self.prop_id.delete(0, tk.END)
            self.prop_id.insert(0, self.selected)
            return
        if new_name != old_name and new_name in self.elements:
            messagebox.showerror("Invalid Name", f"An element with ID '{new_name}' already exists.")
            self.prop_id.delete(0, tk.END)
            self.prop_id.insert(0, self.selected)
            return

        # If name changed, update function names in the editor code text
        # IMPORTANT BIT OF CODE
        # When element ID is changed, this makes sure any associated functions
        # receive an update function name matching the new element ID
        # Otherwise, custom written code for the function would be lost
        if new_name != old_name:


            for snapshot in self.undo_stack:
                if isinstance(snapshot, dict) and snapshot.get('name') == old_name:
                    snapshot['name'] = new_name

            for snapshot in self.redo_stack:
                if isinstance(snapshot, dict) and snapshot.get('name') == old_name:
                    snapshot['name'] = new_name
            
            # Patterns of function names to rename
            func_patterns = [
                (f"on_{old_name}_click", f"on_{new_name}_click"),
                (f"get_{old_name}_data", f"get_{new_name}_data"),
                (f"load_{old_name}_options", f"load_{new_name}_options"),
            ]

            updated_code = existing_code
            for old_func, new_func in func_patterns:
                updated_code = re.sub(rf"\b{re.escape(old_func)}\b", new_func, updated_code)

            # Update the code text widget with replaced function names
            self.code_text.delete('1.0', tk.END)
            self.code_text.insert('1.0', updated_code)

            # Restore scroll position
            # Typing in editor was resetting line number position
            self.code_text.yview_moveto(yview[0])
            self.line_numbers.yview_moveto(yview[0])

            # Rename element dict key and update UI bindings as before
            self.elements[new_name] = self.elements.pop(old_name)
            props = self.elements[new_name]
            props['name'] = new_name

            if '_window_id' in props:
                self.canvas.itemconfig(props['_window_id'], tags=(new_name,))

            frame = props.get('_frame')
            widget = props.get('_widget')
            if frame:
                frame.bind('<Button-1>', lambda e, n=new_name: self._on_mouse_down(e, n))
                frame.bind('<B1-Motion>', lambda e, n=new_name: self._on_mouse_move(e, n))
                frame.bind('<ButtonRelease-1>', lambda e, n=new_name: self._on_mouse_up(e, n))
                frame.bind('<Motion>', lambda e, n=new_name: self._update_cursor(e, n))
            if widget:
                widget.bind('<Button-1>', lambda e, n=new_name: self._on_mouse_down(e, n))
                widget.bind('<B1-Motion>', lambda e, n=new_name: self._on_mouse_move(e, n))
                widget.bind('<ButtonRelease-1>', lambda e, n=new_name: self._on_mouse_up(e, n))
                widget.bind('<Motion>', lambda e, n=new_name: self._update_cursor(e, n))
                widget.bind('<Double-1>', lambda e, n=new_name: self.widget_double_click(e, new_name))

            self.selected = new_name

        # Update properties: text, x, y, w, h
        props['text'] = self.prop_text.get()
        try:
            props['x'] = int(self.prop_x.get())
            props['y'] = int(self.prop_y.get())
            props['w'] = int(self.prop_w.get())
            props['h'] = int(self.prop_h.get())
            
            if props["type"] in ("Label", "Button", "Entry", "Checkbutton", "Radiobutton"):
                props["font_family"] = self.prop_font_family.get() or "Arial"
                props["font_size"] = int(self.prop_font_size.get() or 12)
                props["foreground"] = self.prop_fg.get() or "black"
                props["background"] = self.prop_bg.get() or "white"


        except ValueError:
            messagebox.showerror("Invalid Input", "Position and size must be integers.")
            return

        self._update_element(self.selected)
        self.normal_generate_code()
        self._update_protected_tags()
        

    # Deletes an element (widget)
    def _undo_delete_element(self, name):
        
        if name not in self.elements: return
        props = self.elements.pop(name)
        wid = props.get('_window_id')
        if wid:
            self.canvas.delete(wid)
        if self.selected == name:
            self.selected = None
            self.canvas.delete('selrect')
        self.normal_generate_code()
        self._update_protected_tags()


    # Deletes an element (widget)
    def _delete_element(self, name):
        #print(vars(app))
        self._on_modification_made()

        if name not in self.elements:
            return

        props = self.elements.pop(name)

        # ---- Destroy embedded widget and frame ----
        widget = props.get('_widget')
        frame  = props.get('_frame')

        for w in [widget, frame]:
            if w:
                try:
                    w.unbind_all("<Button-1>")
                    w.unbind_all("<B1-Motion>")
                    w.unbind_all("<ButtonRelease-1>")
                    w.unbind_all("<Motion>")
                    w.unbind_all("<Double-1>")
                    w.destroy()
                except Exception:
                    pass

        # ---- Remove canvas item ----
        wid = props.get('_window_id')
        if wid:
            try:
                self.canvas.delete(wid)
            except Exception:
                pass

        # ---- Drop image references so PhotoImage can be GC'd ----
        for key in ('_photo', '_photo_orig', '_original_img'):
            if key in props:
                props[key] = None

        # ---- Drop tk variable references ----
        for key in ('_var', '_radio_group_var'):
            if key in props:
                props[key] = None

        # ---- Clear selection if this was selected ----
        if self.selected == name:
            self.selected = None
            self.canvas.delete('selrect')
            if hasattr(self, '_sel_rect_id'):
                self._sel_rect_id = None

        # ---- Push to undo stack ----
        prop_copy = {
            k: v for k, v in props.items()
            if not k.startswith('_')  # strip all private widget refs
        }
        prop_copy['action_type'] = 'del'
        self.undo_stack.append(prop_copy)

        self.normal_generate_code()
        self._update_protected_tags()

    def delete_selected_on_click(self, name):
        self.select_element(name)
        element = self.elements.get(name)
        if not element:
            return

        if name in self.elements:
            
            self._delete_element(self.selected)

    # Delets an element (widget)
    def delete_selected(self):
        if not self.selected: return
        self._delete_element(self.selected)

    # ------------------- Code generation & running --------------------------

    # Extracts user custom code which should be written between start and end markers
    # Code not written between these spaces may be lost
    def extract_custom_code(self, code_text):

        start_marker = '# ==========================START============================='
        end_marker = '# ============================END============================='

        start_idx = code_text.find(start_marker)
        end_idx = code_text.find(end_marker)

        # -------------------------
        # VALID CASE ONLY
        # -------------------------
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return code_text[start_idx + len(start_marker):end_idx].strip("\n")

        # -------------------------
        # BROKEN STATE - DO NOT GUESS
        # -------------------------
        if start_idx != -1 and end_idx == -1:
            self._trigger_merge_repair(code_text, missing="end_marker")
            return ""   # IMPORTANT: prevent duplication

        if start_idx == -1 and end_idx != -1:
            self._trigger_merge_repair(code_text, missing="start_marker")
            return ""

        # completely missing
        return ""

    # If protections fail, a merge code repair window opens to let user manually fix
    def _trigger_merge_repair(self, current_code, missing="unknown"):

        def apply_diff_highlight(a_text, b_text, a_widget, b_widget):

            a_lines = a_text.splitlines()
            b_lines = b_text.splitlines()

            diff = difflib.ndiff(a_lines, b_lines)

            a_widget.tag_remove("added", "1.0", tk.END)
            a_widget.tag_remove("removed", "1.0", tk.END)
            b_widget.tag_remove("added", "1.0", tk.END)
            b_widget.tag_remove("removed", "1.0", tk.END)

            a_idx = 1
            b_idx = 1

            for line in diff:
                code = line[:2]
                content = line[2:]

                if code == "  ":
                    a_idx += 1
                    b_idx += 1

                elif code == "- ":
                    # exists in A only removed
                    a_widget.tag_add(
                        "removed",
                        f"{a_idx}.0",
                        f"{a_idx}.end"
                    )
                    a_idx += 1

                elif code == "+ ":
                    # exists in B only added
                    b_widget.tag_add(
                        "added",
                        f"{b_idx}.0",
                        f"{b_idx}.end"
                    )
                    b_idx += 1

        win = tk.Toplevel(self)
        win.title("Code Integrity Recovery")
        #win.geometry("1000x650")
        self._center_window(win, 1000, 800)

        icon_path = resource_path("assets/icon.ico")

        if os.path.exists(icon_path):
            win.iconbitmap(icon_path)
        else:
            print("Icon missing:", icon_path)


        is_dark = getattr(self, "mode", tk.StringVar(value="light")).get() == "dark"

        bg = "#2e2e2e" if is_dark else "#ffffff"
        panel_bg = "#1e1e1e" if is_dark else "#f5f5f5"
        text_bg_active = "#2a2a2a" if is_dark else "#fffdf5"
        text_bg_safe = "#252a33" if is_dark else "#f5f7ff"
        fg = "white" if is_dark else "black"
        

        # ---------------- HEADER ----------------
        header_frame = ttk.Frame(win)
        header_frame.pack(fill="x", padx=12, pady=10)

        # Title (bold)
        ttk.Label(
            header_frame,
            text=f"⚠ Code structure integrity issue detected ({missing})",
            font=("Arial", 12, "bold"),
            foreground="red"
        ).pack(anchor="w", pady=(0, 6))

        # Explanation
        ttk.Label(
            header_frame,
            text=(
                "Your project relies on START and END markers to define the safe user-editable region.\n"
                "These markers separate your custom code from code automatically generated by the app."
            ),
            font=("Arial", 10),
            justify="left",
            wraplength=850
        ).pack(anchor="w", pady=(0, 8))

        # Risk heading
        ttk.Label(
            header_frame,
            text="What happens if markers are missing:",
            font=("Arial", 10, "bold"),
            foreground="red"
        ).pack(anchor="w")

        # Risk list
        ttk.Label(
            header_frame,
            text=(
                "• Custom code may be overwritten during regeneration\n"
                "• Widget handlers may break or reset\n"
                "• You may lose recent logic changes"
            ),
            font=("Arial", 10),
            justify="left",
            wraplength=850
        ).pack(anchor="w", pady=(0, 8))

        # Decision heading
        ttk.Label(
            header_frame,
            text="What should you do?",
            font=("Arial", 10, "bold")
        ).pack(anchor="w")

        # Recommendation
        ttk.Label(
            header_frame,
            text=(
                "• Current State → Recommended (keeps latest work, but requires manual marker repair)\n"
                "• Stable Snapshot → Will automatically fix start and end markers but you are at risk of losing recent changes\n\n"
                "Recommended: keep Current State and reinsert START/END markers using right-click menu manually."
            ),
            font=("Arial", 10),
            justify="left",
            wraplength=850
        ).pack(anchor="w")

        # ---------------- MAIN CONTAINER ----------------
        container = ttk.Frame(win)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(1, weight=1)

        # =========================
        # LEFT PANEL - ACTIVE VERSION
        # =========================
        left_label = ttk.Label(container, text="Current State")
        left_label.grid(row=0, column=0, sticky="w", padx=5)

        left = tk.Text(container, wrap="none", bg="#fffdf5")
        left.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        left.insert("1.0", current_code)

        # =========================
        # RIGHT PANEL - STABLE SNAPSHOT
        # =========================
        right_label = ttk.Label(container, text="Last Stable Snapshot")
        right_label.grid(row=0, column=1, sticky="w", padx=5)

        right = tk.Text(container, wrap="none", bg="#f5f7ff")
        right.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        safe = getattr(self, "_last_safe_code", "")
        right.insert("1.0", safe)

        left.tag_configure("removed", background="#ffe6e6")
        left.tag_configure("added", background="#e6ffe6")
        left.tag_configure("changed", background="#fff6cc")

        right.tag_configure("removed", background="#ffe6e6")
        right.tag_configure("added", background="#e6ffe6")
        right.tag_configure("changed", background="#fff6cc")

        apply_diff_highlight(current_code, safe, left, right)

        # ---------------- ACTION BAR ----------------
        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill="x", padx=10, pady=10)

        def restore_active():
            self.code_text.delete("1.0", tk.END)
            self.code_text.insert("1.0", left.get("1.0", tk.END))
            win.destroy()
            self._open_marker_repair_prompt()
            self.do_full_highlight()

        def restore_snapshot():
            self.code_text.delete("1.0", tk.END)
            self.code_text.insert("1.0", right.get("1.0", tk.END))
            win.destroy()
            self.do_full_highlight()

        def disable_close():
            pass

        win.protocol("WM_DELETE_WINDOW", disable_close)

        

        ttk.Button(
            btn_frame,
            text="Keep Current State",
            command=restore_active
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame,
            text="Restore to Stable Snapshot",
            command=restore_snapshot
        ).pack(side="left", padx=5)

        win.configure(bg=bg)

        left.config(bg=text_bg_active, fg=fg, insertbackground=fg)
        right.config(bg=text_bg_safe, fg=fg, insertbackground=fg)


    def _open_marker_repair_prompt(self):

        win = tk.Toplevel(self)
        win.title("Marker Requirement Notice")
        self._center_window(win, 520, 280)
        win.resizable(False, False)

        icon_path = resource_path("assets/icon.ico")

        if os.path.exists(icon_path):
            win.iconbitmap(icon_path)
        else:
            print("Icon missing:", icon_path)

        is_dark = getattr(self, "mode", tk.StringVar(value="light")).get() == "dark"

        bg = "#2e2e2e" if is_dark else "#ffffff"
        fg = "#ffffff" if is_dark else "#111111"
        sub_fg = "#cfcfcf" if is_dark else "#444444"
        warn_fg = "#ff5c5c"

        win.configure(bg=bg)

        container = ttk.Frame(win)
        container.pack(fill="both", expand=True, padx=14, pady=14)

        # ---------------- TITLE ----------------
        ttk.Label(
            container,
            text="⚠ Marker Integrity Issue Detected",
            font=("Arial", 12, "bold"),
            foreground=warn_fg
        ).pack(anchor="w", pady=(0, 8))

        # ---------------- EXPLANATION ----------------
        ttk.Label(
            container,
            text=(
                "Your project uses START and END markers to define the safe user-editable region.\n"
                "These markers separate your custom code from automatically generated code."
            ),
            font=("Arial", 10),
            foreground=sub_fg,
            justify="left",
            wraplength=480
        ).pack(anchor="w", pady=(0, 10))

        # ---------------- WARNING ----------------
        ttk.Label(
            container,
            text="Without valid markers:",
            font=("Arial", 10, "bold"),
            foreground=warn_fg
        ).pack(anchor="w")

        ttk.Label(
            container,
            text=(
                "• Your custom code may be overwritten\n"
                "• Widget handlers may break\n"
                "• Recent changes may be lost during regeneration"
            ),
            font=("Arial", 10),
            foreground=sub_fg,
            justify="left",
            wraplength=480
        ).pack(anchor="w", pady=(0, 10))

        # ---------------- INSTRUCTIONS ----------------
        ttk.Label(
            container,
            text="How to fix:",
            font=("Arial", 10, "bold"),
            foreground=fg
        ).pack(anchor="w")

        ttk.Label(
            container,
            text=(
                "Right-click inside the editor → Insert START / END marker.\n"
                "Both markers must exist before continuing."
            ),
            font=("Arial", 10),
            foreground=sub_fg,
            justify="left",
            wraplength=480
        ).pack(anchor="w", pady=(0, 12))

        # ---------------- BUTTON STYLE ----------------
        style = ttk.Style()
        style.configure(
            "Accent.TButton",
            font=("Arial", 10, "bold"),
            padding=6
        )

        btn = ttk.Button(
            container,
            text="I Understand",
            style="Accent.TButton",
            command=win.destroy
        )
        btn.pack(pady=(6, 0))

        # ---------------- HOVER EFFECT (manual) ----------------
        def on_enter(e):
            btn.configure(style="Hover.TButton")

        def on_leave(e):
            btn.configure(style="Accent.TButton")

        style.configure(
            "Hover.TButton",
            font=("Arial", 10, "bold"),
            padding=6
        )

        # light/dark aware hover colors
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)


    # Helper to center sub windows
    def _center_window(self, win, width, height):
        self.update_idletasks()

        x = self.winfo_x()
        y = self.winfo_y()

        parent_width = self.winfo_width()
        parent_height = self.winfo_height()

        pos_x = x + (parent_width // 2) - (width // 2)
        pos_y = y + (parent_height // 2) - (height // 2)

        win.geometry(f"{width}x{height}+{pos_x}+{pos_y}")


    # Opens the right click menu (when right clicking on code)
    def _open_code_context_menu(self, event):

        menu = tk.Menu(self.code_text, tearoff=0)

        # ---------------- EDIT ACTIONS ----------------
        def cut():
            
            if not getattr(self, "protected_enabled", True):
                self.code_text.event_generate("<<Cut>>")
                return

            sel = self.code_text.tag_ranges(tk.SEL)

            if sel:
                if self.code_text.tag_nextrange("protected", sel[0], sel[1]):
                    tk.messagebox.showwarning(
                        "Protected Code",
                        "You cannot cut protected sections."
                    )
                    return

            self.code_text.event_generate("<<Cut>>")

        def copy():

            if not getattr(self, "protected_enabled", True):
                self.code_text.event_generate("<<Copy>>")
                return

            sel = self.code_text.tag_ranges(tk.SEL)

            if sel:
                if self.code_text.tag_nextrange("protected", sel[0], sel[1]):
                    tk.messagebox.showwarning(
                        "Protected Code",
                        "You cannot copy protected sections."
                    )
                    return

            self.code_text.event_generate("<<Copy>>")

        def paste():

            if not getattr(self, "protected_enabled", True):
                self.code_text.event_generate("<<Paste>>")
                self.do_full_highlight()
                return

            # get insertion point (where paste would go)
            index = self.code_text.index("insert")

            # block paste if cursor is in protected zone
            if "protected" in self.code_text.tag_names(index):
                tk.messagebox.showwarning(
                    "Protected Code",
                    "You cannot paste into a protected section."
                )
                return

            # also block if selection overlaps protected
            sel = self.code_text.tag_ranges(tk.SEL)
            if sel:
                if self.code_text.tag_nextrange("protected", sel[0], sel[1]):
                    tk.messagebox.showwarning(
                        "Protected Code",
                        "You cannot paste over protected sections."
                    )
                    return

            self.code_text.event_generate("<<Paste>>")
            self.do_full_highlight()

        # ---------------- MARKER ACTIONS ----------------
        def insert_start():
            self.code_text.insert(tk.INSERT, "\n# ==========================START=============================\n")

        def insert_end():
            self.code_text.insert(tk.INSERT, "\n# ============================END=============================\n")

        # ---------------- MENU ITEMS ----------------
        menu.add_command(label="Cut", command=cut)
        menu.add_command(label="Copy", command=copy)
        menu.add_command(label="Paste", command=paste)

        menu.add_separator()

        menu.add_command(label="Insert START Marker", command=insert_start)
        menu.add_command(label="Insert END Marker", command=insert_end)

        # ---------------- SHOW MENU ----------------
        menu.tk_popup(event.x_root, event.y_root)



    def extract_and_preserve_handlers(self, code_text):
        
        # Extracts handler function bodies (on_X_click, get_X_data, load_X_options)
        # and preserves everything written below the function until the next handler
        # or any of the key comment markers or EOF.
        
        if not hasattr(self, 'preserved_handlers'):
            self.preserved_handlers = {}

        # Key section markers where extraction should stop
        stop_markers = [
            r"# --- COMBOBOX OPTION LOADER FUNCTIONS ---",
            r"# --- LISTBOX OPTION LOADER FUNCTIONS ---",
            r"# --- TREEVIEW FUNCTIONS ---",
            r"# --- ON LOAD ---", 
            r"# -------------- Auto Generated GUI Code -------------- #"
        ]
        stop_pattern = "|".join(stop_markers)

        # Pattern:
        # - Match def <handler>(...):
        # - Capture everything until the next 'def' at start of line OR any stop marker OR EOF
        pattern = re.compile(
            r"^def\s+(on_\w+_click|get_\w+_data|load_\w+_options|on_load)\s*\([^)]*\):\n"
            r"(.*?)(?=^def\s|^(" + stop_pattern + r")|\Z)",
            re.MULTILINE | re.DOTALL
        )

        for match in pattern.finditer(code_text):
            func_name = match.group(1)
            body = match.group(2).rstrip("\n")
            self.preserved_handlers[func_name] = body



    # When loading a project, generate code based on saved custom code
    def on_load_generate_code(self):
        
        custom_code = getattr(self, 'custom_code', '')

        # Pass saved code into generate_code
        self.generate_code(custom_code)

    # When project is already loaded, pass existing code in the editor to generate_code
    def normal_generate_code(self):

        # Extract and store handler bodies before regenerating
        existing_code = self.code_text.get('1.0', tk.END)
        self.extract_and_preserve_handlers(existing_code)
        custom_code = self.extract_custom_code(existing_code)
        self.generate_code(custom_code)



    # This function builds the project code
    # Main sections are:
    # - Imports (the default hardcoded ones)
    # - Users custom code (to go between start and end marker comments)
    #   - User can add additional imports at the top of their section if they like of course
    # - Special generated functions for buttons, treeviews, listboxes, and comboboxes are loaded
    #   - There are in part auto generated
    # - GUI element code is appended at the bottom
    def generate_code(self, existing_code):

        self.last_saved_code = self.code_text.get("1.0", "end-1c")
        
        # Make sure preserved_handlers exists
        if not hasattr(self, 'preserved_handlers'):
            self.preserved_handlers = {}

        # Remember scroll position
        yview = self.code_text.yview()

        lines = []
        lines.append('import tkinter as tk')
        lines.append('from tkinter import ttk, messagebox, simpledialog')
        lines.append('')

        # --- Custom Code Section ---

        lines.append('# ============================================================')
        lines.append('# 🟢 USER CODE SECTION (SAFE ZONE - WRITE YOUR CODE HERE)')
        lines.append('# ============================================================')
        lines.append('# ✏️ Write your custom code below this line')
        lines.append('# ⚠️ This section is NOT overwritten by the generator')
        lines.append('# ⚠️ Do NOT write outside this section or your changes may be lost')
        lines.append('# ==========================START=============================\n')
        lines.append('')
        

        if existing_code:
            lines.append(existing_code.rstrip('\n'))
        #lines.append('')
        #lines.append('\n# !!!!!!!!!!!! INSERT YOUR CODE ABOVE THIS COMMENT !!!!!!!!!!!! #\n')

        lines.append('')
        lines.append('\n# ============================END=============================')
        lines.append('# 🟢 END USER CODE SECTION')
        lines.append('# ============================================================\n')

        lines.append('# ---------------- Widget Handlers ---------------- #\n')
        lines.append('# Automatically generated handlers for widgets.\n')
        lines.append('# TIP:\n')
        lines.append('# The Widget Handlers section is partially managed by the application.')
        lines.append('# Only add or modify code inside the generated handler functions.')
        lines.append('# Any code outside these functions may be removed during regeneration.')
        lines.append('# Actions such as adding or moving existing widgets in the canvas will trigger regeneration.')


        # --- BUTTON FUNCTIONS ---
        lines.append('\n# --- BUTTON FUNCTIONS ---\n')
        for name, p in self.elements.items():
            if p['type'] == 'Button':
                func_name = f"on_{name}_click"
                lines.append(f"def {func_name}():")
                if func_name in self.preserved_handlers:
                    lines.append(self.preserved_handlers[func_name])
                else:
                    lines.append(f"    # Code for {func_name}")
                    lines.append("    pass")
                lines.append('')


        # --- COMBOBOX LOADER FUNCTIONS ---
        lines.append('\n# --- COMBOBOX OPTION LOADER FUNCTIONS ---\n')
        for name, p in self.elements.items():
            if p['type'] == 'Combobox':
                func_name = f"load_{name}_options"
                lines.append(f"def {func_name}():")
                if func_name in self.preserved_handlers:
                    lines.append(self.preserved_handlers[func_name])
                else:
                    lines.append(f"    # Return the list of options for {name}")
                    lines.append("    return ['Option 1', 'Option 2', 'Option 3']")
                lines.append('')

        # --- LISTBOX LOADER FUNCTIONS ---
        lines.append('\n# --- LISTBOX OPTION LOADER FUNCTIONS ---\n')
        for name, p in self.elements.items():
            if p['type'] == 'Listbox':
                func_name = f"load_{name}_options"
                lines.append(f"def {func_name}():")
                if func_name in self.preserved_handlers:
                    lines.append(self.preserved_handlers[func_name])
                else:
                    lines.append(f"    # Return the list of items for {name}")
                    lines.append("    return ['Item 1', 'Item 2', 'Item 3']")
                lines.append('')

        # --- TREEVIEW DATA FUNCTIONS ---
        lines.append('\n# --- TREEVIEW FUNCTIONS ---\n')
        for name, p in self.elements.items():
            if p['type'] == 'Treeview':
                func_name = f"get_{name}_data"
                lines.append(f"def {func_name}():")
                if func_name in self.preserved_handlers:
                    lines.append(self.preserved_handlers[func_name])
                else:
                    lines.append("    # Replace with your own data retrieval logic")
                    lines.append("    headers = (\"Name\", \"Age\", \"Job\")")
                    lines.append("    sample_data = [")
                    lines.append("        (\"Alice\", \"25\", \"Teacher\"),")
                    lines.append("        (\"Bob\", \"30\", \"Engineer\"),")
                    lines.append("        (\"Charlie\", \"35\", \"Designer\")")
                    lines.append("    ]")
                    lines.append("    return headers, sample_data")
                lines.append('')


        # ---- ON LOAD FUNCTION (mandatory, preserved, called after all widgets init) ----
        lines.append('\n# --- ON LOAD ---\n')
        lines.append('# Called automatically after all widgets are created.')
        lines.append('# Use this to run any startup logic for your app.\n')
        lines.append('def on_load():')
        if 'on_load' in self.preserved_handlers:
            lines.append(self.preserved_handlers['on_load'])
        else:
            lines.append('    pass')
        lines.append('')

        # --- GUI CREATION SECTION ---
        lines.append('\n# -------------- Auto Generated GUI Code -------------- #\n')
        lines.append('# TIP:\n')
        lines.append('# This code is fully managed by the application and cannot be overwritten.\n')
        lines.append('root = tk.Tk()')
        lines.append('style = ttk.Style(root)')
        
        # Match generated app theme to current IDE theme
        mode = self.mode.get()
        if mode == "retro":
            lines.append('style.theme_use("classic")')
        else:
            lines.append('style.theme_use("clam")')


        title = getattr(self, 'canvas_title_var', None)
        if title:
            canvas_title = self.canvas_title_var.get()
        else:
            canvas_title = "Generated GUI"
        lines.append(f'root.title({json.dumps(canvas_title)})')

        width = getattr(self, 'canvas_width', 800)
        height = getattr(self, 'canvas_height', 400)
        lines.append(f'root.geometry("{width}x{height}")\n')

        # Apply canvas background color
        canvas_bg = getattr(self, 'project_bg_color', None)
        bg_color = canvas_bg.get() if canvas_bg else "#FFFFFF"
        self.canvas_bg_button.config(bg=bg_color)
        
        lines.append(f'root.configure(bg={json.dumps(bg_color)})')
        

        # --- Special variables ---
        radio_groups_done = set()
        for name, p in self.elements.items():
            if p['type'] == 'Checkbutton':
                lines.append(f"{name}_var = tk.BooleanVar()")
            elif p['type'] == 'Radiobutton':
                group_name = p.get('_radio_group_name', name)
                if group_name not in radio_groups_done:
                    lines.append(f"{group_name} = tk.StringVar()")
                    radio_groups_done.add(group_name)
        lines.append('')

        # --- Widget creation ---
        for name, p in self.elements.items():
            t = p['type']

            if t == 'Label':
                lines.append(
                    f"{name} = tk.Label(root, "
                    f"text={json.dumps(p.get('text',''))}, "
                    f"font=({json.dumps(p.get('font_family','Arial'))}, {p.get('font_size',12)}), "
                    f"fg={json.dumps(p.get('foreground','#000000'))}, "
                    f"bg={json.dumps(p.get('background','#FFFFFF'))})"
                )

            elif t == 'Button':
                func_name = f"on_{name}_click"
                style_name = f"{name}.TButton"

                base_bg = p.get('background', '#FFFFFF')
                fg = p.get('foreground', '#000000')

                # auto hover color (slightly darker or lighter depending on brightness)
                def hex_to_luma(h):
                    h = h.lstrip("#")
                    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
                    return (0.299*r + 0.587*g + 0.114*b)

                try:
                    hover_bg = self._adjust_color(base_bg, 0.85 if hex_to_luma(base_bg) > 140 else 1.2)
                except:
                    hover_bg = '#ffffff'

                lines.append(f"style_{name} = ttk.Style()")

                lines.append(f"style_{name}.configure('{style_name}', "
                             f"font=({json.dumps(p.get('font_family','Arial'))}, {p.get('font_size',12)}), "
                             f"foreground={json.dumps(fg)}, "
                             f"background={json.dumps(base_bg)})")

                # (hover effect)
                lines.append(f"style_{name}.map('{style_name}', "
                             f"background=[('active', {json.dumps(hover_bg)})])")

                lines.append(f"{name} = ttk.Button(root, text={json.dumps(p.get('text',''))}, "
                             f"command={func_name}, style='{style_name}')")

            elif t == 'Entry':
                lines.append(
                    f"{name} = tk.Entry(root, "
                    f"font=({json.dumps(p.get('font_family','Arial'))}, {p.get('font_size',12)}), "
                    f"fg={json.dumps(p.get('foreground','#000000'))}, "
                    f"bg={json.dumps(p.get('background','#FFFFFF'))})"
                )
                if p.get('text'):
                    lines.append(f"{name}.insert(0, {json.dumps(p.get('text'))})")

            elif t == 'TextArea':
                lines.append(f"{name} = tk.Text(root, wrap='word')")
                if p.get('text'):
                    lines.append(f"{name}.insert('1.0', {json.dumps(p.get('text'))})")

            elif t == 'Treeview':
                func_name = f"get_{name}_data"
                lines.append(f"headers, rows = {func_name}()")
                lines.append(f"{name} = ttk.Treeview(root, columns=headers, show='headings')")
                lines.append(f"for col in headers:")
                lines.append(f"    {name}.heading(col, text=col)")
                lines.append(f"    {name}.column(col, width=max(len(str(col)), 10) * 10)")
                lines.append(f"for row in rows:")
                lines.append(f"    {name}.insert('', 'end', values=row)")

            elif t == 'Checkbutton':
                style_name = f"{name}.TCheckbutton"
                lines.append(f"style_{name} = ttk.Style()")
                lines.append(f"style_{name}.configure('{style_name}', "
                             f"font=({json.dumps(p.get('font_family','Arial'))}, {p.get('font_size',12)}), "
                             f"foreground={json.dumps(p.get('foreground','#000000'))}, "
                             f"background={json.dumps(p.get('background','#FFFFFF'))})")
                lines.append(f"{name} = ttk.Checkbutton(root, text={json.dumps(p.get('text',''))}, "
                             f"variable={name}_var, onvalue=True, offvalue=False, style='{style_name}')")

            elif t == 'Radiobutton':
                group_name = p.get('_radio_group_name', name)
                style_name = f"{name}.TRadiobutton"
                lines.append(f"style_{name} = ttk.Style()")
                lines.append(f"style_{name}.configure('{style_name}', "
                             f"font=({json.dumps(p.get('font_family','Arial'))}, {p.get('font_size',12)}), "
                             f"foreground={json.dumps(p.get('foreground','#000000'))}, "
                             f"background={json.dumps(p.get('background','#FFFFFF'))})")
                lines.append(f"{name} = ttk.Radiobutton(root, text={json.dumps(p.get('text',''))}, "
                             f"variable={group_name}, value={json.dumps(p.get('text',''))}, style='{style_name}')")

            elif t == 'Listbox':
                func_name = f"load_{name}_options"
                lines.append(f"{name} = tk.Listbox(root)")
                lines.append(f"for item in {func_name}():")
                lines.append(f"    {name}.insert(tk.END, item)")

            elif t == 'Combobox':
                func_name = f"load_{name}_options"
                style_name = f"{name}.TCombobox"
                lines.append(f"style_{name} = ttk.Style()")
                lines.append(f"style_{name}.configure('{style_name}', "
                             f"font=({json.dumps(p.get('font_family','Arial'))}, {p.get('font_size',12)}), "
                             f"foreground={json.dumps(p.get('foreground','#000000'))}, "
                             f"fieldbackground={json.dumps(p.get('background','#FFFFFF'))})")
                lines.append(f"{name} = ttk.Combobox(root, values={func_name}(), style='{style_name}')")
                if p.get('text'):
                    lines.append(f"{name}.set({json.dumps(p.get('text'))})")

            elif t == "Image":
                img_path = json.dumps(p["text"])
                lines.append(f"try:")
                lines.append(f"    {name}_photo_orig = tk.PhotoImage(file={img_path})")
                lines.append(f"    {name}_photo = {name}_photo_orig.subsample(" 
                             f"max(1, {name}_photo_orig.width() // {p['w']}), "
                             f"max(1, {name}_photo_orig.height() // {p['h']}))")
                lines.append(f"    {name} = tk.Label(root, image={name}_photo)")
                lines.append(f"except Exception as e:")
                #lines.append(f"    print(f'⚠️ Could not load image for {name}: {{e}}')")
                lines.append(f"    error_m = 'Image load failed.'")
                lines.append(f"    error_m += '\\n\\nHas the image'")
                lines.append(f"    error_m += '\\npath changed?'")
                lines.append(f"    error_m += '\\n\\nPath:{img_path}'")
                lines.append(f"    {name} = tk.Label(root, text=error_m)")

            else:
                lines.append(f"# Unsupported type: {t}")


            # Exists incase canvas properties entry for width / height are ''
            def _safe_int(value, default):
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return default

            canvas_w = _safe_int(self.canvas_width_var.get(), 800)
            canvas_h = _safe_int(self.canvas_height_var.get(), 400)

            # !!! IMPORTANT !!!
            # Note after .place for x and y positions we subtract by 20. these are offsets
            # related to the margins in the draw_canvas_boundary function

            relx = (p['x'] - 20) / canvas_w
            rely = (p['y'] - 50) / canvas_h
            relw = p['w'] / canvas_w
            relh = p['h'] / canvas_h

            mode = getattr(self, "canvas_scale_mode", "Fully Responsive")

            if mode == "Fully Responsive":
                lines.append(
                    f"{name}.place(relx={relx:.4f}, rely={rely:.4f}, "
                    f"relwidth={relw:.4f}, relheight={relh:.4f})\n"
                )

            elif mode == "Responsive Width Only":
                lines.append(
                    f"{name}.place(relx={relx:.4f}, rely={rely:.4f}, "
                    f"relwidth={relw:.4f}, height={p['h']})\n"
                )

            elif mode == "Fixed Layout":
                lines.append(
                    f"{name}.place(x={p['x']-20}, y={p['y']-50}, "
                    f"width={p['w']}, height={p['h']})\n"
                )
            
        lines.append("\n# Run startup logic")
        lines.append("on_load()")
        lines.append("root.mainloop()\n")

        # Update the editor
        code = '\n'.join(lines)
        self.code_text.config(undo=False)
        self.code_text.delete('1.0', tk.END)
        self.code_text.insert('1.0', code)
        #self.code_text.config(undo=True)
        self.do_full_highlight()
        self._update_line_numbers()
        self.code_text.yview_moveto(yview[0])
        self.line_numbers.yview_moveto(yview[0])

        self._last_safe_code = self.code_text.get("1.0", tk.END)
        

        return code


    # Used in def genere_code
    # Purpose is users can select bg color of buttons
    # When buttons are generated this is called to make so
    # the hover color of buttons in users app is scaled based on
    # the bg color
    def _adjust_color(self, hex_color, factor=1.2):
        # Lighten or darken a hex color.
        hex_color = hex_color.lstrip("#")

        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        r = max(0, min(255, int(r * factor)))
        g = max(0, min(255, int(g * factor)))
        b = max(0, min(255, int(b * factor)))

        return f"#{r:02x}{g:02x}{b:02x}"

    # Clear the syntax output log
    def clear_syntax_output(self):
        self.syntax_output.configure(state="normal")
        self.syntax_output.delete("1.0", tk.END)
        self.syntax_output.configure(state="disabled")
        
        self.code_text.tag_remove("error_highlight", "1.0", tk.END)


    # Called when clicking the run button.
    # Opens a subprocess to run the users built GUI app
    def run_code(self):

        # Stop any current app (close it)
        self.stop_process()

        self.clear_syntax_output()

        

        # If dirty tell user they must save
        if self.dirty:
            result = messagebox.askokcancel(
                "Unsaved Changes",
                "You must save before running.\n\nClick OK to save, or Cancel to stop."
            )

            if not result:
                return

            """if not self.save_project():
                return"""

        code = self.code_text.get('1.0', tk.END)


        is_valid, error = self.check_syntax(code)

        if not is_valid:
            #print("not valid")
            self.syntax_output.delete("1.0", tk.END)

            self.output_log(f"\n🛑 Error. Execution failed.\n\n")
            self.output_log(f"❌ Syntax Error on line {error.lineno}, column {error.offset}:\n"
                f"{error.text.strip()}\n{error.msg}\n")


            self._highlight_error_line(error.lineno)
            return  # Stop — do not run subprocess if error


        # Enforce project save before run
        saved = self.save_project()

        # If not saved cancel
        if not saved:

            return


        self.running = True
        self.output_log("▶ Running...\n\n")
        

        # Write temp file
        tf = tempfile.NamedTemporaryFile(delete=False, suffix='.py', mode='w', encoding='utf-8')
        tf.write(code)
        tf.close()


        # Find python
        python_exe = "python"
        if getattr(sys, 'frozen', False):
            python_exe = find_python()
            if not python_exe:
                messagebox.showerror(
                    "Python Not Found",
                    "Python is not installed or not in PATH."
                )
                return
        else:
            python_exe = sys.executable

        self.run_start_time = datetime.datetime.now()

        try:
            process = subprocess.Popen(
                [python_exe, "-u", tf.name],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Merging with STDOUT
                #stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            self.current_process = process
            this_process = process


            def extract_line_number(error_text):
                match = re.search(r'line (\d+)', error_text)
                if match:
                    return int(match.group(1))
                return None


            def read_stdout():
                
                # Read char-by-char so input() prompts (no newline) appear immediately.
                
                buf = []
                while True:
                    char = process.stdout.read(1)  # blocks until data arrives — CPU efficient
                    if not char:
                        break
                    buf.append(char)

                    # Flush buffer on newline, or if we see a prompt-like pattern (no newline)
                    # We flush immediately so input() prompts appear without waiting for \n
                    self.after(0, lambda c=char: self.output_log(c))



            def read_output():
                # .read1() is key: it reads available data without waiting for a newline
                # We use iter() to keep calling it until it returns an empty string
                try:
                    for chunk in iter(lambda: process.stdout.read(4096), ""):
                        if not self.running:
                            break
                        
                        if chunk:
                            # Schedule the UI update
                            self.after(0, lambda c=chunk: self.output_log(c))
                            
                except (InterfaceError, ValueError):
                    # Handle cases where the process is closed while reading
                    pass
                    


            def monitor_process():
                process.wait()

                def update_ui():
                    # Only fire if this is still the current active process
                    if self.current_process is not this_process:
                        return

                    elapsed = (datetime.datetime.now() - self.run_start_time).total_seconds()

                    if not self.running:
                        # Stopped manually
                        #self.output_log(f"\n\nStopped after {elapsed:.2f}s\n")
                        self.last_verified = datetime.datetime.now()
                        self.output_log(f"\nFinished in {elapsed:.2f}s  ·  Time: {self.last_verified.strftime('%H:%M:%S')}\n")
                    elif not error_state["found"]:
                        # Finished naturally
                        self.last_verified = datetime.datetime.now()
                        self.output_log(f"\nFinished in {elapsed:.2f}s  ·  Time: {self.last_verified.strftime('%H:%M:%S')}\n")

                    self.running = False

                self.after(100, update_ui)

            error_state = {"found": False}
            
            threading.Thread(target=monitor_process, daemon=True).start()
            #threading.Thread(target=read_output, daemon=True).start()
            threading.Thread(target=read_stdout, daemon=True).start()
            #threading.Thread(target=read_stderr, daemon=True).start()


        except Exception as e:
            messagebox.showerror('Run Error', str(e))

    def stop_process(self, user_stopped=True):
        if user_stopped:
            self.running = False
        if hasattr(self, "current_process") and self.current_process:
            if self.current_process.poll() is None:
                self.current_process.kill()

    # ------------------- Theme, Save/Load ----------------------------------

    # -------- THEME DEFINITIONS --------
    THEMES = {
        "light": {
            "bg": "#f5f5f5", "panel": "#ffffff", "header": "#EEEEEE",
            "fg": "#000000", "entry_bg": "#ffffff", "accent": "#dddddd",
            "hover_bg": "#cce7ff", "selected_bg": "#226cb5",
            "frame_bg": "#ffffff", "border_col": "#d0d0d0",
            "viewport_bg": "#c0c0c0", "scrollbar_bg": "#f0f0f0",
            "scrollbar_trough": "#e0e0e0", "scrollbar_active": "#aaaaaa",
            "canvas_bg": "white", "output_fg": "#333333",
            "code_bg": "white", "code_fg": "black", "code_cursor": "black",
            "line_num_bg": "white", "line_num_fg": "black",
            "kw_col": "blue", "builtin_col": "purple",
            "comment_col": "red", "string_col": "green",
            "font": ("Calibri", 10), "tab_font": ("Calibri", 11),
            "btn_relief": "flat", "btn_border": 0,
        },
        "dark": {
            "bg": "#1e1e1e", "panel": "#2b2b2b", "header": "#333333",
            "fg": "#ffffff", "entry_bg": "#000000", "accent": "#3a3a3a",
            "hover_bg": "#3a3a3a", "selected_bg": "#666666",
            "frame_bg": "#2b2b2b", "border_col": "#3a3a3a",
            "viewport_bg": "#2b2b2b", "scrollbar_bg": "#2b2b2b",
            "scrollbar_trough": "#1e1e1e", "scrollbar_active": "#555555",
            "canvas_bg": "#1e1e1e", "output_fg": "#EEEEEE",
            "code_bg": "#000000", "code_fg": "white", "code_cursor": "white",
            "line_num_bg": "#000000", "line_num_fg": "white",
            "kw_col": "orange", "builtin_col": "orange",
            "comment_col": "grey", "string_col": "lightgreen",
            "font": ("Calibri", 10), "tab_font": ("Calibri", 11),
            "btn_relief": "flat", "btn_border": 0,
        },
        "fun": {
            "bg": "#fff9f0", "panel": "#ffffff", "header": "#ff85a1",
            "fg": "#00aeff", "entry_bg": "#fffde7", "accent": "#ffea73",
            "hover_bg": "#ffd6e7", "selected_bg": "#ff85a1",
            "frame_bg": "#fff0f6", "border_col": "#ffb3c6",
            "viewport_bg": "#ffd6e7", "scrollbar_bg": "#ffb3c6",
            "scrollbar_trough": "#ffe4ec", "scrollbar_active": "#ff85a1",
            "canvas_bg": "#fffde7", "output_fg": "#333333",
            "code_bg": "#fffde7", "code_fg": "#333333", "code_cursor": "#ff85a1",
            "line_num_bg": "#ffd6e7", "line_num_fg": "#333333",
            "kw_col": "#e64980", "builtin_col": "#7950f2",
            "comment_col": "#40c057", "string_col": "#f76707",
            "font": ("Comic Sans MS", 10, "bold"), "tab_font": ("Comic Sans MS", 11, "bold"),
            "btn_relief": "raised", "btn_border": 2, "header_fg": "#ffffff",
        },
        "retro": {
            "bg": "#c0c0c0", "panel": "#d4d0c8", "header": "#000080",
            "fg": "#000000", "entry_bg": "#ffffff", "accent": "#d4d0c8",
            "hover_bg": "#000080", "selected_bg": "#000080",
            "frame_bg": "#d4d0c8", "border_col": "#808080",
            "viewport_bg": "#808080", "scrollbar_bg": "#c0c0c0",
            "scrollbar_trough": "#d4d0c8", "scrollbar_active": "#000080",
            "canvas_bg": "white", "output_fg": "#000000",
            "code_bg": "#ffffff", "code_fg": "#000000", "code_cursor": "#000000",
            "line_num_bg": "#d4d0c8", "line_num_fg": "#000000",
            "kw_col": "#000080", "builtin_col": "#800000",
            "comment_col": "#008000", "string_col": "#800080",
            "font": ("Consolas", 10), "tab_font": ("Consolas", 10, "bold"),
            "btn_relief": "raised", "btn_border": 2, "header_fg": "#ffffff",
        },
    }

    FUN_WIDGET_BUTTONS = [
        ("🏷 Label",       "#ffd6e7"),
        ("🔘 Button",      "#d0f4de"),
        ("⌨ Entry",        "#fff3bf"),
        ("📊 Treeview",    "#d0ebff"),
        ("☑ Checkbutton",  "#ffe8cc"),
        ("🔘 Radiobutton", "#e5dbff"),
        ("📝 Text Area",   "#c5f6fa"),
        ("📋 Listbox",     "#d3f9d8"),
        ("📂 Combobox",    "#fff0f6"),
        ("🖼 Image",       "#ffe3e3"),
    ]

    def toggle_theme(self):
        if self.mode.get() in ("light", "fun"):
            self.mode.set("dark")
        else:
            self.mode.set("light")
        self._apply_theme()

    def toggle_fun_mode(self):
        self.mode.set("light" if self.mode.get() == "fun" else "fun")
        self._apply_theme()

    def toggle_retro_mode(self):
        self.mode.set("light" if self.mode.get() == "retro" else "retro")
        self._apply_theme()

    def _apply_theme(self):
        mode = self.mode.get()
        t = self.THEMES[mode]
        fun = mode == "fun"
        retro = mode == "retro"
        font = t["font"]
        fs = self.custom_font_size

        if retro:
            self.style.theme_use("classic")
        else:
            self.style.theme_use("default")

        # -------- ENTRY / SPIN / COMBO STYLE NAMES --------
        entry_style = f"{mode.capitalize()}.TEntry"
        spin_style  = f"{mode.capitalize()}.TSpinbox"
        combo_style = f"{mode.capitalize()}.TCombobox"

        # -------- ROOT + GLOBAL TTK --------
        self.configure(bg=t["bg"])
        self.style.configure(".",        background=t["bg"],    foreground=t["fg"])
        self.style.configure("TFrame",   background=t["bg"])
        self.style.configure("TLabel",   background=t["bg"],    foreground=t["fg"])

        # -------- HEADERS --------
        header_configs = {
            self.canvas_header:  (
                " 🎨 Design Canvas " if fun else "[ Design Canvas ]" if retro else " Design Canvas ",
                t["header"],
                t["header_fg"] if retro or fun else t["fg"]
            ),
            self.code_header:    (
                " 💻 Code Editor " if fun else "[ Code Editor ]" if retro else " Code Editor ",
                "#a9e34b" if fun else t["header"],
                t["header_fg"] if retro or fun else t["fg"]
            ),
            self.debug_header:   (
                " 🖥 Output " if fun else "[ Output ]" if retro else " Output ",
                "#74c0fc" if fun else t["header"],
                t["header_fg"] if retro or fun else t["fg"]
            ),
            self.widgets_header: (
                " 🧩 Widgets " if fun else "[ Widgets ]" if retro else " Widgets ",
                "#ffa94d" if fun else t["header"],
                t["header_fg"] if retro or fun else t["fg"]
            ),
        }
        for widget, (text, bg, fg) in header_configs.items():
            widget.config(text=text, bg=bg, fg=fg)

        # -------- WIDGET SIDEBAR BUTTONS --------
        widget_commands = [
            lambda: self.add_element('Label', 'new'),
            lambda: self.add_element('Button', 'new'),
            lambda: self.add_element('Entry', 'new'),
            lambda: self.add_element('Treeview', 'new'),
            lambda: self.add_element('Checkbutton', 'new'),
            lambda: self.add_element('Radiobutton', 'new'),
            lambda: self.add_element('TextArea', 'new'),
            lambda: self.add_element('Listbox', 'new'),
            lambda: self.add_element('Combobox', 'new'),
            self.add_image_element,
        ]

        # Clear and rebuild widget buttons so colours update
        for child in self.widgets_frame.winfo_children():
            child.destroy()

        if fun:
            for (label, color), cmd in zip(self.FUN_WIDGET_BUTTONS, widget_commands):
                btn = tk.Button(
                    self.widgets_frame,
                    text=label,
                    command=cmd,
                    bg=color,
                    fg="#ff00b3",
                    font=("Comic Sans MS", fs, "bold"),
                    relief="raised",
                    bd=2,
                    anchor="w",
                    padx=6,
                    cursor="hand2"
                )
                btn.pack(fill=tk.X, pady=1)

        elif retro:
            labels = [
                "🏷 Label", "🔘 Button", "⌨ Entry", "📊 Treeview",
                "☑ Checkbutton", "🔘 Radiobutton", "📝 Text Area",
                "📋 Listbox", "📂 Combobox", "🖼 Image"
            ]
            for label, cmd in zip(labels, widget_commands):
                btn = tk.Button(
                    self.widgets_frame,
                    text=label,
                    command=cmd,
                    bg="#d4d0c8",
                    fg="#000000",
                    font=("Consolas", fs),
                    relief="raised",
                    bd=2,
                    anchor="w",
                    padx=6,
                    cursor="arrow"
                )
                btn.pack(fill=tk.X, pady=1)
        else:
            labels = [
                "🏷 Label", "🔘 Button", "⌨ Entry", "📊 Treeview",
                "☑ Checkbutton", "🔘 Radiobutton", "📝 Text Area",
                "📋 Listbox", "📂 Combobox", "🖼 Image"
            ]
            for label, cmd in zip(labels, widget_commands):
                ttk.Button(
                    self.widgets_frame,
                    text=label,
                    command=cmd,
                    style="Flat.TButton"
                ).pack(fill=tk.X, pady=0)

        # -------- WIDGETS FRAME --------
        self.widgets_frame.configure(
            bg=t["frame_bg"],
            highlightbackground=t["border_col"],
            highlightthickness=1
        )

        # -------- BUTTON STYLES --------
        self.style.configure("Flat.TButton",
            borderwidth=t["btn_border"], relief=t["btn_relief"], padding=6,
            font=(font[0], fs) + ((font[2],) if len(font) > 2 else ()), anchor="w"
        )
        self.style.map("Flat.TButton",
            background=[("active", t["hover_bg"])],
            relief=[("pressed", "sunken" if fun else "flat"), ("!pressed", t["btn_relief"])]
        )
        self.style.configure("Accent.TButton",
            borderwidth=t["btn_border"], relief=t["btn_relief"], padding=6,
            background=t["accent"], foreground=t["fg"],
            font=(font[0], fs) + ((font[2],) if len(font) > 2 else ())
        )
        self.style.map("Accent.TButton",
            background=[("active", "#fff2a6" if fun else ("#666666" if mode == "dark" else "#bbbbbb"))]
        )
        self.style.configure("Run.TButton",
            borderwidth=t["btn_border"], relief=t["btn_relief"], padding=6,
            background="#69db7c" if fun else "#6de067", foreground="white",
            font=(font[0], fs) + ((font[2],) if len(font) > 2 else ())
        )
        self.style.map("Run.TButton",
            background=[("active", "#4da848")],
            relief=[("pressed", "sunken" if fun else "flat"), ("!pressed", t["btn_relief"])]
        )
        self.style.configure("Stop.TButton",
            borderwidth=t["btn_border"], relief=t["btn_relief"], padding=6,
            background="#ff6b6b" if fun else "#ff7575", foreground="white",
            font=(font[0], fs) + ((font[2],) if len(font) > 2 else ())
        )
        self.style.map("Stop.TButton",
            background=[("active", "#db4b4b")],
            relief=[("pressed", "sunken" if fun else "flat"), ("!pressed", t["btn_relief"])]
        )

        # -------- NOTEBOOK --------
        self.style.configure("TNotebook",
            background=t["bg"], borderwidth=0, relief="flat"
        )
        self.style.configure("TNotebook.Tab",
            background=t["panel"], foreground=t["fg"],
            borderwidth=t["btn_border"],
            padding=[8 if fun else 6, 4 if fun else 2],
            font=t["tab_font"], relief=t["btn_relief"]
        )
        self.style.map("TNotebook.Tab",
            background=[("selected", t["selected_bg"]), ("!selected", t["panel"])],
            foreground=[("selected", "white"), ("!selected", t["fg"])],
            relief=[("selected", t["btn_relief"]), ("!selected", t["btn_relief"])]
        )

        # -------- ENTRY / SPINBOX / COMBOBOX --------
        self.style.configure(entry_style,
            fieldbackground=t["entry_bg"], foreground=t["fg"], insertcolor=t["fg"]
        )
        self.style.configure(spin_style,
            fieldbackground=t["entry_bg"], foreground=t["fg"],
            insertcolor=t["fg"], arrowcolor=t["fg"]
        )
        self.style.configure(combo_style,
            fieldbackground=t["entry_bg"], background=t["panel"],
            foreground=t["fg"], arrowcolor=t["fg"]
        )
        self.style.map(combo_style,
            fieldbackground=[("readonly", t["entry_bg"])],
            foreground=[("readonly", t["fg"])],
            background=[("readonly", t["panel"])]
        )

        for w in [
            self.prop_id, self.prop_text, self.prop_x, self.prop_y,
            self.prop_w, self.prop_h, self.prop_fg, self.prop_bg,
            self.canvas_title_entry, self.canvas_width_entry,
            self.canvas_height_entry, self.canvas_bg_entry,
        ]:
            w.config(style=entry_style)

        self.prop_font_size.config(style=spin_style)
        self.prop_font_family.config(style=combo_style)

        # -------- CANVAS + VIEWPORT --------
        self.canvas.config(bg=t["canvas_bg"])
        self.syntax_output.config(bg=t["panel"], fg=t["output_fg"])

        if hasattr(self, 'viewport'):
            self.viewport.configure(bg=t["viewport_bg"])
        if hasattr(self, 'canvas_outer'):
            self.canvas_outer.configure(bg=t["viewport_bg"], highlightthickness=0)

        # -------- SCROLLBARS --------
        for attr in ('v_scroll', 'h_scroll', 'y_scroll', 'x_scroll', 'debug_scroll'):
            sb = getattr(self, attr, None)
            if sb:
                sb.configure(
                    bg=t["scrollbar_bg"],
                    troughcolor=t["scrollbar_trough"],
                    activebackground=t["scrollbar_active"],
                    relief="flat", borderwidth=0
                )

        # -------- CODE EDITOR --------
        self.code_text.config(
            bg=t["code_bg"], fg=t["code_fg"], insertbackground=t["code_cursor"]
        )
        self.line_numbers.config(bg=t["line_num_bg"], fg=t["line_num_fg"])
        self.code_text.tag_configure("keyword",  foreground=t["kw_col"])
        self.code_text.tag_configure("builtin",  foreground=t["builtin_col"])
        self.code_text.tag_configure("comment",  foreground=t["comment_col"])
        self.code_text.tag_configure("string",   foreground=t["string_col"])

        self.do_full_highlight()

        # -------- GLOBAL PROPERTIES TAB --------
        if hasattr(self, 'global_props'):
            # Update the scrollable canvas background
            if hasattr(self, 'global_props_canvas'):
                self.global_props_canvas.configure(bg=t["bg"])
            if hasattr(self, 'global_props_content'):
                self.global_props_content.configure(style="TFrame")

            # Walk all widgets inside gpad and restyle them
            def _restyle_global_tab(widget):
                cls = widget.winfo_class()
                try:
                    if cls == "Label":
                        # Section headers (bold) get header bg, others get normal bg
                        font_str = str(widget.cget("font"))
                        if "bold" in font_str:
                            widget.config(bg=t["header"], fg=fg)
                        else:
                            widget.config(bg=t["bg"], fg=t["fg"])
                    elif cls == "Frame":
                        widget.config(bg=t["border_col"] if widget.cget("height") == 1 else t["bg"])
                    elif cls in ("TFrame", "TLabel"):
                        pass  # handled by global ttk style
                    elif cls == "TEntry":
                        widget.config(style=entry_style)
                    elif cls == "TSpinbox":
                        widget.config(style=spin_style)
                    elif cls == "TCombobox":
                        widget.config(style=combo_style)
                    elif cls == "TButton":
                        widget.config(style="Accent.TButton")
                except Exception:
                    pass
                for child in widget.winfo_children():
                    _restyle_global_tab(child)

            if hasattr(self, 'global_props_pad'):
                _restyle_global_tab(self.global_props_pad)
    

    # Function for saving project as
    def save_project_as(self):
        
        # Always ask for a new save location (Save As)
        path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON Files', '*.json')])
        if not path:
            return  # user cancelled

        self.current_save_path = path

        # Call save logic but force saving to this new path
        self._save_to_path(path)


    # Saving logic function
    def _save_to_path(self, path):
        export = {
            'elements': {},
            'custom_code': '',
            'preserved_handlers': {}
        }

        # Save elements
        for name, p in self.elements.items():
            element_data = {k: v for k, v in p.items() if not k.startswith('_')}
            if '_radio_group_name' in p:
                element_data['_radio_group_name'] = p['_radio_group_name']
            export['elements'][name] = element_data

        export['canvas_width'] = getattr(self, 'canvas_width', 800)
        export['canvas_height'] = getattr(self, 'canvas_height', 400)
        export['canvas_title'] = self.canvas_title_var.get()
        export['canvas_bg'] = self.project_bg_color.get()

        existing_code = self.code_text.get('1.0', tk.END)
        export['custom_code'] = self.extract_custom_code(existing_code)

        # --- Preserve handlers using the improved pattern ---
        stop_markers = [
            r"# --- COMBOBOX OPTION LOADER FUNCTIONS ---",
            r"# --- LISTBOX OPTION LOADER FUNCTIONS ---",
            r"# --- TREEVIEW FUNCTIONS ---",
            r"# --- ON LOAD ---", 
            r"# -------------- Auto Generated GUI Code -------------- #"
        ]
        stop_pattern = "|".join(stop_markers)

        pattern = re.compile(
            r"^def\s+(on_\w+_click|get_\w+_data|load_\w+_options|on_load)\s*\([^)]*\):\n"
            r"(.*?)(?=^def\s|^(" + stop_pattern + r")|\Z)",
            re.MULTILINE | re.DOTALL
        )

        for match in pattern.finditer(existing_code):
            func_name = match.group(1)
            body = match.group(2).rstrip("\n")
            export['preserved_handlers'][func_name] = body

        # Save to JSON
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(export, f, indent=2)

        self.dirty = False
        self.center_tabs.tab(0, text="Canvas")
        self.center_tabs.tab(1, text="Code")
        self.update_window_title_with_path(path)
        self.last_saved_code = self.code_text.get("1.0", "end-1c")

        self.show_toast("Project saved!")

        return True


    # Save function (not save as)
    def save_project(self):
        if self.current_save_path is None:
            path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON Files', '*.json')])
            if not path:
                return False
            self.current_save_path = path
        else:
            path = self.current_save_path

        self._save_to_path(path)

        return self._save_to_path(path)


    # Updates window title with path of saved project / file (file opened and being edited in the app)
    def update_window_title_with_path(self, path):
        
        self.title(f"{path}")


    # Load a saved project (as json)
    def load_project(self):

        # Prevent accidental loss of unsaved work
        if self.dirty:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved work.\n\nDo you want to save before loading another project?"
            )

            if result is None:  # Cancel
                return

            if result is True:  # Save first
                if not self.save_project():
                    return  # user cancelled save dialog

            # if False continue without saving
        
        path = filedialog.askopenfilename(filetypes=[('JSON Files', '*.json')])
        if not path:
            return

        self.clear_syntax_output()

        self.code_text.delete("1.0", tk.END)

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self._clear_canvas()
        

        # Restore elements
        for name, p in data.get('elements', {}).items():
            base = p['type'].lower()
            try:
                num = int(''.join(filter(str.isdigit, name[len(base):])))
                if num > self.counters[base]:
                    self.counters[base] = num
            except Exception:
                pass
            self.elements[name] = p
            self._create_visual(p)

        # Restore canvas size and apply it
        self.canvas_width = data.get('canvas_width', 800)
        self.canvas_height = data.get('canvas_height', 400)
        canvas_title = data.get('canvas_title', 'Generated GUI')
        self.canvas_bg = data.get('canvas_bg', '#FFFFFF')
        self.project_bg_color.set(self.canvas_bg)

        self.canvas_title_var.set(canvas_title)
        self.canvas_width_var.set(str(self.canvas_width))
        self.canvas_height_var.set(str(self.canvas_height))
        self.canvas.config(scrollregion=(0, 0, self.canvas_width, self.canvas_height))
        self.canvas.config(width=self.canvas_width, height=self.canvas_height)

        # Restore custom code + preserved handlers
        self.custom_code = data.get('custom_code', '')
        self.preserved_handlers = data.get('preserved_handlers', {})

        

        self.dirty = False
        self.center_tabs.tab(0, text="Canvas")
        self.center_tabs.tab(1, text="Code")
        self.current_save_path = path  # the loaded file path
        self.update_window_title_with_path(path)

        # Re-generate code using loaded code and handlers
        self._draw_canvas_boundary()
        self.on_load_generate_code()
        self.last_saved_code = self.code_text.get("1.0", "end-1c")
        self._update_protected_tags()

        self.reset_stacks()
        
        self.show_toast("Project loaded.")
        

        

    # Function to support closing the app
    # Used to warn user about unsaved changes
    def on_close(self):
        if self.dirty:
            result = messagebox.askyesnocancel("Unsaved Changes",
                "You have unsaved changes. Would you like to save before exiting?")
            if result is True:
                # User chose yes save
                self.save_project()
                # Then close
                self.running = False
                self.stop_process()   # kill subprocess first
                self.destroy()
            elif result is False:
                # User chose no close without saving
                self.running = False
                self.stop_process()   # kill subprocess first
                self.destroy()
            else:
                # Cancel
                return
        else:
            self.running = False
            self.stop_process()   # kill subprocess first
            self.destroy()


    # For exporting code in the code editor to a .py file
    def export_code(self):
        # Export the code editor contents as a .py file.
        from tkinter import filedialog, messagebox

        # Ask where to save
        file_path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")],
            title="Export Python Code"
        )

        if not file_path:
            return  # User cancelled

        try:
            code_content = self.code_text.get("1.0", tk.END).strip()
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code_content)
            messagebox.showinfo("Export Successful", f"Code exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"An error occurred:\n{e}")

    # Create a new project
    # Warns user any unsaved changes will be lost
    def new_project(self):
        
        

        # Check for unsaved changes
        if self.dirty:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved work.\n\nDo you want to save before creating a new project?"
            )


            if result is None:  # Cancel
                return

            if result is True:  # Yes, save first
                if not self.save_project():
                    return  # user cancelled save dialog

        # if result is False continue without saving

        self.clear_syntax_output()

        # Reset project
        self.current_save_path = None

        # Clear properties input fields
        self.prop_id.delete(0, tk.END)
        self.prop_text.delete(0, tk.END)
        self.prop_x.delete(0, tk.END)
        self.prop_y.delete(0, tk.END)
        self.prop_w.delete(0, tk.END)
        self.prop_h.delete(0, tk.END)

        # Clear the code editor text
        self.code_text.delete('1.0', tk.END)

        # Reset selected element
        self.selected = None

        # Clear preserved handlers if present
        if hasattr(self, 'preserved_handlers'):
            self.preserved_handlers.clear()

        # Clear custom code
        self.custom_code = ''

        # Reset elements and related state
        self.elements = {}  # name -> metadata
        self.radio_groups = {}
        self.counters = defaultdict(int)  # for naming

        # Clear canvas visuals
        #self.canvas.delete("all")
        self._clear_canvas()

        # Update existing StringVars
        self.canvas_width_var.set("800")
        self.canvas_height_var.set("400")
        self.canvas_title_var.set("My Project")
        self.project_bg_color.set("#FFFFFF")


        # Update canvas config to reflect new sizes
        self.canvas.config(
            scrollregion=(0, 0, int(self.canvas_width_var.get()), int(self.canvas_height_var.get())),
            width=int(self.canvas_width_var.get()),
            height=int(self.canvas_height_var.get())
        )

        # Apply canvas size changes
        self.apply_canvas_size("new_btn")

        # Regenerate code to clear the editor properly
        self.normal_generate_code()
        self._update_protected_tags()

        self.center_tabs.tab(0, text="Canvas")
        self.center_tabs.tab(1, text="Code")

        self.update_window_title_with_path("untitled")

        self.reset_stacks()


    # Clear the canvas
    def _clear_canvas(self):
        # Destroy all embedded widgets and remove canvas items
        for name, props in list(self.elements.items()):
            widget = props.get('_widget')
            frame  = props.get('_frame')
            wid    = props.get('_window_id')

            for w in [widget, frame]:
                if w:
                    try:
                        w.unbind_all("<Button-1>")
                        w.unbind_all("<B1-Motion>")
                        w.unbind_all("<ButtonRelease-1>")
                        w.unbind_all("<Motion>")
                        w.unbind_all("<Double-1>")
                        w.destroy()
                    except Exception:
                        pass

            if wid:
                try:
                    self.canvas.delete(wid)
                except Exception:
                    pass

            # Drop all private references — widget, image, tk vars
            for key in list(props.keys()):
                if key.startswith('_'):
                    props[key] = None

        self.elements.clear()
        self.selected = None
        self._sel_rect_id = None

        # Clear canvas completely including boundary drawings
        self.canvas.delete("all")
        self._canvas_items = []

        # Clear image cache (redundant)
        #if hasattr(self, 'image_cache'):
            #self.image_cache.clear()

        # Clear radio groups — hold tk.StringVar references
        self.radio_groups.clear()

        # Clear stacks — hold element snapshots including image refs
        if hasattr(self, 'undo_stack'):
            self.undo_stack.clear()
        if hasattr(self, 'redo_stack'):
            self.redo_stack.clear()

        # Clear preserved handlers from previous project
        if hasattr(self, 'preserved_handlers'):
            self.preserved_handlers.clear()

        # Reset counters so new project starts fresh
        self.counters = defaultdict(int)

        
        gc.collect()



if __name__ == '__main__':
    app = GUIBuilderApp()
    app.mainloop()
