# Main window: HeaderBar, options bar, toolbox, canvas area, panels, statusbar
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

class PigmentWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Pigment")
        self.set_default_size(1280, 860)
        self.set_size_request(900, 600)

        # Root box stacks everything vertically
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(root)

        root.append(self._build_headerbar())
        root.append(self._build_optionsbar())

        workspace = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        workspace.set_vexpand(True)
        workspace.append(self._build_toolbox())
        workspace.append(self._build_canvas_area())
        workspace.append(self._build_panels())
        root.append(workspace)

        root.append(self._build_statusbar())

    # ── HEADER BAR ──────────────────────────────────────────────────────────
    def _build_headerbar(self):
        header = Adw.HeaderBar()

        # App logo/name in centre
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        logo = Gtk.Label(label="Pg")
        logo.add_css_class("pigment-logo-mark")
        name = Gtk.Label(label="Pigment")
        name.add_css_class("pigment-logo-name")
        version = Gtk.Label(label='0.1 "Buzz"')
        version.add_css_class("pigment-logo-version")
        title_box.append(logo)
        title_box.append(name)
        title_box.append(version)
        header.set_title_widget(title_box)

        # Dark mode toggle on the right
        self._dark = False
        self._theme_btn = Gtk.Button(label="☾  Dark")
        self._theme_btn.set_tooltip_text("Toggle dark mode")
        self._theme_btn.add_css_class("flat")
        self._theme_btn.connect("clicked", self._toggle_theme)
        header.pack_end(self._theme_btn)

        # New / Open buttons on the left
        new_btn = Gtk.Button(label="New")
        new_btn.add_css_class("flat")
        open_btn = Gtk.Button(label="Open")
        open_btn.add_css_class("flat")
        header.pack_start(new_btn)
        header.pack_start(open_btn)

        return header

    # ── OPTIONS BAR ─────────────────────────────────────────────────────────
    def _build_optionsbar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        bar.add_css_class("pigment-optionsbar")
        bar.set_margin_start(8)
        bar.set_margin_end(8)

        # Active tool indicator
        self._tool_label = Gtk.Label(label="🖌  Brush")
        self._tool_label.add_css_class("pigment-tool-chip")
        bar.append(self._tool_label)
        bar.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        # Brush options
        for label, value, width in [
            ("Size", "19", 4),
            ("Hardness", "80%", 5),
            ("Opacity", "85%", 5),
            ("Flow", "100%", 5),
        ]:
            lbl = Gtk.Label(label=label)
            lbl.add_css_class("pigment-ob-label")
            entry = Gtk.Entry()
            entry.set_text(value)
            entry.set_width_chars(width)
            entry.add_css_class("pigment-ob-entry")
            bar.append(lbl)
            bar.append(entry)
            bar.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        # Blend mode dropdown
        mode_lbl = Gtk.Label(label="Mode")
        mode_lbl.add_css_class("pigment-ob-label")
        modes = Gtk.StringList.new(["Normal","Multiply","Screen","Overlay","Soft Light","Hard Light","Difference","Luminosity"])
        mode_drop = Gtk.DropDown(model=modes)
        mode_drop.add_css_class("pigment-ob-dropdown")
        bar.append(mode_lbl)
        bar.append(mode_drop)

        return bar

    # ── TOOLBOX ─────────────────────────────────────────────────────────────
    def _build_toolbox(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add_css_class("pigment-toolbox")
        scroll.set_size_request(44, -1)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(5)
        box.set_margin_end(5)

        # (icon, tooltip, tool_id)
        tools = [
            ("⊹", "Move (V)",          "move"),
            ("⬚", "Marquee (M)",        "marquee"),
            ("⌖", "Lasso (L)",          "lasso"),
            ("✦", "Magic Wand (W)",     "wand"),
            None,
            ("⌗", "Crop (C)",           "crop"),
            ("⧉", "Slice (K)",          "slice"),
            None,
            ("✚", "Healing Brush (J)",  "heal"),
            ("🖌", "Brush (B)",          "brush"),
            ("⎘", "Clone Stamp (S)",    "clone"),
            ("◻", "Eraser (E)",         "eraser"),
            None,
            ("▦", "Gradient (G)",       "gradient"),
            ("⬡", "Paint Bucket",       "bucket"),
            None,
            ("◎", "Blur / Sharpen (R)", "blur"),
            ("◑", "Dodge / Burn (O)",   "dodge"),
            None,
            ("✒", "Pen (P)",            "pen"),
            ("T",  "Type (T)",           "type"),
            ("▭", "Shape (U)",           "shape"),
            None,
            ("✥", "Hand (H)",           "hand"),
            ("⊕", "Zoom (Z)",           "zoom"),
        ]

        self._tool_buttons = {}
        self._active_tool_id = None

        for item in tools:
            if item is None:
                sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
                sep.set_margin_top(3)
                sep.set_margin_bottom(3)
                box.append(sep)
                continue
            icon, tooltip, tool_id = item
            btn = Gtk.Button(label=icon)
            btn.set_tooltip_text(tooltip)
            btn.add_css_class("pigment-tool-btn")
            btn.connect("clicked", self._on_tool_clicked, tool_id)
            self._tool_buttons[tool_id] = btn
            box.append(btn)

        # Activate brush by default
        self._set_active_tool("brush")

        # Color swatches at the bottom
        box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        swatch_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        swatch_box.set_margin_top(6)
        fg_btn = Gtk.ColorDialogButton()
        fg_btn.set_tooltip_text("Foreground color")
        bg_btn = Gtk.ColorDialogButton()
        bg_btn.set_tooltip_text("Background color")
        swatch_box.append(Gtk.Label(label="FG/BG"))
        swatch_box.append(fg_btn)
        swatch_box.append(bg_btn)
        box.append(swatch_box)

        scroll.set_child(box)
        return scroll

    # ── CANVAS AREA ─────────────────────────────────────────────────────────
    def _build_canvas_area(self):
        frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame.set_hexpand(True)
        frame.add_css_class("pigment-canvas-area")

        # Placeholder until Phase 2 implements Cairo canvas
        lbl = Gtk.Label()
        lbl.set_markup('<span size="large" foreground="#888888">Canvas — Cairo rendering arrives in Phase 2</span>')
        lbl.set_vexpand(True)
        lbl.set_hexpand(True)
        frame.append(lbl)

        return frame

    # ── RIGHT PANELS ─────────────────────────────────────────────────────────
    def _build_panels(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.add_css_class("pigment-panels")
        box.set_size_request(220, -1)

        notebook = Gtk.Notebook()
        notebook.set_vexpand(True)
        notebook.set_tab_pos(Gtk.PositionType.TOP)

        # Navigator tab
        nav_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        nav_box.set_margin_top(8); nav_box.set_margin_bottom(8)
        nav_box.set_margin_start(8); nav_box.set_margin_end(8)
        nav_thumb = Gtk.Box()
        nav_thumb.add_css_class("pigment-nav-thumb")
        nav_thumb.set_size_request(-1, 90)
        nav_box.append(nav_thumb)
        zoom_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        zoom_row.append(Gtk.Label(label="−"))
        zoom_sl = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 5, 3200, 1)
        zoom_sl.set_value(67); zoom_sl.set_hexpand(True); zoom_sl.set_draw_value(False)
        zoom_row.append(zoom_sl)
        zoom_row.append(Gtk.Label(label="+"))
        self._zoom_label = Gtk.Label(label="66.7%")
        zoom_row.append(self._zoom_label)
        nav_box.append(zoom_row)
        notebook.append_page(nav_box, Gtk.Label(label="Navigator"))

        # Color tab
        color_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        color_box.set_margin_top(8); color_box.set_margin_bottom(8)
        color_box.set_margin_start(8); color_box.set_margin_end(8)
        color_btn = Gtk.ColorDialogButton()
        color_btn.set_hexpand(True)
        color_box.append(color_btn)
        for name, val in [("R", 160), ("G", 90), ("B", 200)]:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            row.append(Gtk.Label(label=name))
            sl = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 255, 1)
            sl.set_value(val); sl.set_hexpand(True); sl.set_draw_value(False)
            row.append(sl)
            row.append(Gtk.Label(label=str(val)))
            color_box.append(row)
        notebook.append_page(color_box, Gtk.Label(label="Color"))

        # History tab
        hist_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        hist_box.set_margin_top(8); hist_box.set_margin_bottom(8)
        hist_box.set_margin_start(8); hist_box.set_margin_end(8)
        for step in ["Open", "New Layer", "Brush", "Brush", "Levels"]:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            thumb = Gtk.Box()
            thumb.add_css_class("pigment-layer-thumb")
            thumb.set_size_request(22, 16)
            row.append(thumb)
            row.append(Gtk.Label(label=step, xalign=0))
            hist_box.append(row)
        notebook.append_page(hist_box, Gtk.Label(label="History"))

        # Layers tab
        layers_outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        layers_outer.set_margin_top(8); layers_outer.set_margin_bottom(4)
        layers_outer.set_margin_start(8); layers_outer.set_margin_end(8)

        # Blend mode + opacity row
        blend_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        blend_row.set_margin_bottom(4)
        blend_strings = Gtk.StringList.new(["Normal","Multiply","Screen","Overlay"])
        blend_drop = Gtk.DropDown(model=blend_strings)
        blend_drop.set_hexpand(True)
        blend_row.append(blend_drop)
        blend_row.append(Gtk.Label(label="Opacity"))
        op_entry = Gtk.Entry(); op_entry.set_text("100%"); op_entry.set_width_chars(5)
        blend_row.append(op_entry)
        layers_outer.append(blend_row)

        # Layer rows
        layers_data = [
            ("👁", "Levels 1",   "Adjustment", "#667eea"),
            ("👁", "Title Text", "Text",        "#f8f8f8"),
            ("👁", "Layer 3",    "RGB · Active","#c4956a"),
            ("👁", "Layer 2",    "Multiply",    "#7a5c3a"),
            ("👁", "Background", "Locked",      "#e8d5b0"),
        ]
        for eye, name, meta, color in layers_data:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            row.add_css_class("pigment-layer-row")
            row.append(Gtk.Label(label=eye))
            thumb = Gtk.Box()
            thumb.add_css_class("pigment-layer-thumb")
            thumb.set_size_request(26, 20)
            row.append(thumb)
            info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            n = Gtk.Label(label=name, xalign=0)
            n.add_css_class("pigment-layer-name")
            m = Gtk.Label(label=meta, xalign=0)
            m.add_css_class("pigment-layer-meta")
            info.append(n); info.append(m)
            row.append(info)
            layers_outer.append(row)

        # Footer buttons
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        footer.set_margin_top(6)
        for label, tip in [("ƒ","Add style"),("⬜","Add mask"),("◑","Adjustment"),("📁","New group"),("＋","New layer"),("⌫","Delete")]:
            b = Gtk.Button(label=label)
            b.set_tooltip_text(tip)
            b.set_hexpand(True)
            b.add_css_class("flat")
            footer.append(b)
        layers_outer.append(footer)

        notebook.append_page(layers_outer, Gtk.Label(label="Layers"))

        box.append(notebook)
        return box

    # ── STATUS BAR ──────────────────────────────────────────────────────────
    def _build_statusbar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        bar.add_css_class("pigment-statusbar")
        bar.set_margin_start(12); bar.set_margin_end(12)

        for text in ['Pigment 0.1 "Buzz"', "Python 3.13 · GTK 4.18", "No document open"]:
            bar.append(Gtk.Label(label=text))
            bar.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        return bar

    # ── HELPERS ─────────────────────────────────────────────────────────────
    def _on_tool_clicked(self, btn, tool_id):
        self._set_active_tool(tool_id)

    def _set_active_tool(self, tool_id):
        if self._active_tool_id and self._active_tool_id in self._tool_buttons:
            self._tool_buttons[self._active_tool_id].remove_css_class("pigment-tool-active")
        self._active_tool_id = tool_id
        if tool_id in self._tool_buttons:
            self._tool_buttons[tool_id].add_css_class("pigment-tool-active")

    def _toggle_theme(self, btn):
        self._dark = not self._dark
        manager = Adw.StyleManager.get_default()
        if self._dark:
            manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
            self._theme_btn.set_label("☀  Light")
        else:
            manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
            self._theme_btn.set_label("☾  Dark")
