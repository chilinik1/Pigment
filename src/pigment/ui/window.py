# Main window: HeaderBar, options bar, toolbox, canvas, panels, statusbar
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gdk
from pigment.ui.canvas import PigmentCanvas
from pigment.core.document import Document

class PigmentWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Pigment")
        self.set_default_size(1280, 860)
        self.set_size_request(900, 600)

        self._documents = []
        self._active_doc = None

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

        self._dark = False
        self._theme_btn = Gtk.Button(label="☾  Dark")
        self._theme_btn.add_css_class("flat")
        self._theme_btn.connect("clicked", self._toggle_theme)
        header.pack_end(self._theme_btn)

        new_btn = Gtk.Button(label="New")
        new_btn.add_css_class("flat")
        new_btn.connect("clicked", self._on_new_document)
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

        self._tool_chip = Gtk.Label(label="🖌  Brush")
        self._tool_chip.add_css_class("pigment-tool-chip")
        bar.append(self._tool_chip)
        bar.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        for label, value, width in [
            ("Size", "19", 4), ("Hardness", "80%", 5),
            ("Opacity", "85%", 5), ("Flow", "100%", 5),
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

        mode_lbl = Gtk.Label(label="Mode")
        mode_lbl.add_css_class("pigment-ob-label")
        modes = Gtk.StringList.new(
            ["Normal","Multiply","Screen","Overlay","Soft Light","Hard Light","Difference","Luminosity"]
        )
        mode_drop = Gtk.DropDown(model=modes)
        bar.append(mode_lbl)
        bar.append(mode_drop)

        # Zoom display on the far right
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        bar.append(spacer)
        self._zoom_label = Gtk.Label(label="–")
        self._zoom_label.add_css_class("pigment-ob-label")
        zoom_out_btn = Gtk.Button(label="−")
        zoom_out_btn.add_css_class("flat")
        zoom_out_btn.connect("clicked", lambda _: self._canvas.zoom_out())
        zoom_in_btn = Gtk.Button(label="+")
        zoom_in_btn.add_css_class("flat")
        zoom_in_btn.connect("clicked", lambda _: self._canvas.zoom_in())
        fit_btn = Gtk.Button(label="Fit")
        fit_btn.add_css_class("flat")
        fit_btn.connect("clicked", lambda _: self._canvas.zoom_fit())
        bar.append(zoom_out_btn)
        bar.append(self._zoom_label)
        bar.append(zoom_in_btn)
        bar.append(fit_btn)

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

        tools = [
            ("⊹","Move (V)","move"),         ("⬚","Marquee (M)","marquee"),
            ("⌖","Lasso (L)","lasso"),        ("✦","Magic Wand (W)","wand"),
            None,
            ("⌗","Crop (C)","crop"),          ("⧉","Slice (K)","slice"),
            None,
            ("✚","Healing Brush (J)","heal"), ("🖌","Brush (B)","brush"),
            ("⎘","Clone Stamp (S)","clone"),  ("◻","Eraser (E)","eraser"),
            None,
            ("▦","Gradient (G)","gradient"),  ("⬡","Paint Bucket","bucket"),
            None,
            ("◎","Blur/Sharpen (R)","blur"),  ("◑","Dodge/Burn (O)","dodge"),
            None,
            ("✒","Pen (P)","pen"),            ("T","Type (T)","type"),
            ("▭","Shape (U)","shape"),
            None,
            ("✥","Hand (H)","hand"),          ("⊕","Zoom (Z)","zoom"),
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

        self._set_active_tool("brush")

        box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        swatch_lbl = Gtk.Label(label="FG/BG")
        swatch_lbl.add_css_class("pigment-ob-label")
        box.append(swatch_lbl)

        scroll.set_child(box)
        return scroll

    # ── CANVAS AREA ─────────────────────────────────────────────────────────
    def _build_canvas_area(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_hexpand(True)
        box.set_vexpand(True)

        # Document tab bar
        self._tab_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        self._tab_bar.add_css_class("pigment-tabbar")
        box.append(self._tab_bar)

        # The real Cairo canvas
        self._canvas = PigmentCanvas()
        self._canvas.on_zoom_changed = self._on_zoom_changed
        box.append(self._canvas)

        return box

    # ── RIGHT PANELS ─────────────────────────────────────────────────────────
    def _build_panels(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.add_css_class("pigment-panels")
        box.set_size_request(220, -1)

        notebook = Gtk.Notebook()
        notebook.set_vexpand(True)

        # Navigator
        nav_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        nav_box.set_margin_top(8); nav_box.set_margin_bottom(8)
        nav_box.set_margin_start(8); nav_box.set_margin_end(8)
        self._nav_thumb = Gtk.DrawingArea()
        self._nav_thumb.set_size_request(-1, 90)
        self._nav_thumb.add_css_class("pigment-nav-thumb")
        self._nav_thumb.set_draw_func(self._draw_nav_thumb)
        nav_box.append(self._nav_thumb)
        zoom_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        zoom_row.append(Gtk.Label(label="−"))
        self._nav_slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 5, 3200, 1)
        self._nav_slider.set_value(100)
        self._nav_slider.set_hexpand(True)
        self._nav_slider.set_draw_value(False)
        self._nav_slider.connect("value-changed", self._on_nav_slider)
        zoom_row.append(self._nav_slider)
        zoom_row.append(Gtk.Label(label="+"))
        self._nav_zoom_label = Gtk.Label(label="100%")
        zoom_row.append(self._nav_zoom_label)
        nav_box.append(zoom_row)
        notebook.append_page(nav_box, Gtk.Label(label="Navigator"))

        # Color
        color_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        color_box.set_margin_top(8); color_box.set_margin_bottom(8)
        color_box.set_margin_start(8); color_box.set_margin_end(8)
        for ch_name, val in [("R", 0), ("G", 0), ("B", 0)]:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            row.append(Gtk.Label(label=ch_name))
            sl = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 255, 1)
            sl.set_value(val); sl.set_hexpand(True); sl.set_draw_value(False)
            row.append(sl)
            row.append(Gtk.Label(label=str(val)))
            color_box.append(row)
        notebook.append_page(color_box, Gtk.Label(label="Color"))

        # History
        hist_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        hist_box.set_margin_top(8); hist_box.set_margin_bottom(8)
        hist_box.set_margin_start(8); hist_box.set_margin_end(8)
        self._history_box = hist_box
        notebook.append_page(hist_box, Gtk.Label(label="History"))

        # Layers
        layers_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        layers_box.set_margin_top(8); layers_box.set_margin_bottom(8)
        layers_box.set_margin_start(8); layers_box.set_margin_end(8)
        blend_strings = Gtk.StringList.new(["Normal","Multiply","Screen","Overlay"])
        blend_drop = Gtk.DropDown(model=blend_strings)
        blend_drop.set_hexpand(True)
        layers_box.append(blend_drop)
        self._layers_box = layers_box
        notebook.append_page(layers_box, Gtk.Label(label="Layers"))

        box.append(notebook)
        return box

    # ── STATUS BAR ──────────────────────────────────────────────────────────
    def _build_statusbar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        bar.add_css_class("pigment-statusbar")
        bar.set_margin_start(12); bar.set_margin_end(12)
        self._status_doc   = Gtk.Label(label='Pigment 0.1 "Buzz"')
        self._status_info  = Gtk.Label(label="Python 3.13 · GTK 4.18")
        self._status_coord = Gtk.Label(label="No document open")
        for w in [self._status_doc, self._status_info, self._status_coord]:
            bar.append(w)
            bar.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        return bar

    # ── NEW DOCUMENT DIALOG ──────────────────────────────────────────────────
    def _on_new_document(self, _btn):
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="New Document",
            body="Enter the canvas dimensions:",
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("create", "Create")
        dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)

        # Width / Height entries
        grid = Gtk.Grid(column_spacing=8, row_spacing=6)
        grid.set_margin_top(8)
        grid.attach(Gtk.Label(label="Width",  xalign=0), 0, 0, 1, 1)
        grid.attach(Gtk.Label(label="Height", xalign=0), 0, 1, 1, 1)
        w_entry = Gtk.Entry(); w_entry.set_text("1920"); w_entry.set_width_chars(8)
        h_entry = Gtk.Entry(); h_entry.set_text("1080"); h_entry.set_width_chars(8)
        grid.attach(w_entry, 1, 0, 1, 1)
        grid.attach(h_entry, 1, 1, 1, 1)
        grid.attach(Gtk.Label(label="px", xalign=0), 2, 0, 1, 1)
        grid.attach(Gtk.Label(label="px", xalign=0), 2, 1, 1, 1)
        dialog.set_extra_child(grid)

        def on_response(dlg, response):
            if response == "create":
                try:
                    w = max(1, min(16000, int(w_entry.get_text())))
                    h = max(1, min(16000, int(h_entry.get_text())))
                except ValueError:
                    return
                self._create_document(w, h)
            dialog.destroy()

        dialog.connect("response", on_response)
        dialog.present()

    def _create_document(self, width: int, height: int):
        doc = Document(width, height, name="Untitled")
        self._documents.append(doc)
        self._active_doc = doc

        # Add a tab
        tab_btn = Gtk.Button(label=f"{doc.name}  ×")
        tab_btn.add_css_class("flat")
        tab_btn.add_css_class("pigment-tab-btn")
        tab_btn.connect("clicked", lambda _: None)
        self._tab_bar.append(tab_btn)

        # Send to canvas
        self._canvas.set_document(doc)

        # Update status
        self._status_doc.set_text(f"{doc.name} — {width}×{height} px")
        self._status_info.set_text("RGB 8-bit")
        self._zoom_label.set_text(f"{self._canvas.zoom_percent:.1f}%")

    # ── NAVIGATOR THUMB ──────────────────────────────────────────────────────
    def _draw_nav_thumb(self, area, cr, width, height):
        if not self._active_doc:
            cr.set_source_rgb(0.55, 0.38, 0.25)
            cr.paint()
            return
        # Draw the document pixels scaled into the thumb
        import cairo as _cairo
        doc = self._active_doc
        surf = self._canvas._numpy_to_cairo(doc.pixels)
        scale_x = width  / doc.width
        scale_y = height / doc.height
        scale   = min(scale_x, scale_y)
        ox = (width  - doc.width  * scale) / 2
        oy = (height - doc.height * scale) / 2
        cr.set_source_rgb(0.2, 0.2, 0.2)
        cr.paint()
        cr.save()
        cr.translate(ox, oy)
        cr.scale(scale, scale)
        cr.set_source_surface(surf, 0, 0)
        cr.paint()
        cr.restore()

    # ── ZOOM SYNC ────────────────────────────────────────────────────────────
    def _on_zoom_changed(self, zoom: float):
        pct = zoom * 100
        self._zoom_label.set_text(f"{pct:.1f}%")
        self._nav_zoom_label.set_text(f"{pct:.1f}%")
        # Prevent slider feedback loop
        self._nav_slider.handler_block_by_func(self._on_nav_slider)
        self._nav_slider.set_value(pct)
        self._nav_slider.handler_unblock_by_func(self._on_nav_slider)
        self._nav_thumb.queue_draw()

    def _on_nav_slider(self, slider):
        zoom = slider.get_value() / 100.0
        self._canvas._set_zoom(zoom, center=True)

    # ── TOOL SWITCHING ───────────────────────────────────────────────────────
    def _on_tool_clicked(self, btn, tool_id):
        self._set_active_tool(tool_id)

    def _set_active_tool(self, tool_id):
        if self._active_tool_id and self._active_tool_id in self._tool_buttons:
            self._tool_buttons[self._active_tool_id].remove_css_class("pigment-tool-active")
        self._active_tool_id = tool_id
        if tool_id in self._tool_buttons:
            self._tool_buttons[tool_id].add_css_class("pigment-tool-active")

    # ── THEME TOGGLE ─────────────────────────────────────────────────────────
    def _toggle_theme(self, btn):
        self._dark = not self._dark
        manager = Adw.StyleManager.get_default()
        if self._dark:
            manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
            self._theme_btn.set_label("☀  Light")
        else:
            manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
            self._theme_btn.set_label("☾  Dark")
