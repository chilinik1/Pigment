# Main window — Phase 6 — GNOME CSD + PS layout + accordion panels
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gdk, Gio, GLib
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
        self._color_rgb    = [0, 0, 0]
        self._bg_color_rgb = [255, 255, 255]
        self._rgb_sliders = {}
        self._rgb_value_labels = {}
        self._panel_visible = True

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(root)

        root.append(self._build_headerbar())
        root.append(self._build_optionsbar())
        root.append(self._build_tabbar())

        workspace = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        workspace.set_vexpand(True)

        self._toolbox_widget = self._build_toolbox()
        workspace.append(self._toolbox_widget)

        # Paned gives resizable split between canvas and right panel
        self._paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self._paned.set_hexpand(True)
        self._paned.set_vexpand(True)
        self._paned.set_position(900)
        self._paned.set_start_child(self._build_canvas_area())
        self._paned.set_end_child(self._build_right_panel())
        self._paned.set_resize_start_child(True)
        self._paned.set_resize_end_child(False)
        self._paned.set_shrink_start_child(False)
        self._paned.set_shrink_end_child(False)
        workspace.append(self._paned)

        root.append(workspace)

        root.append(self._build_statusbar())

    # ── HEADERBAR ────────────────────────────────────────────────────────────
    def _build_headerbar(self):
        header = Adw.HeaderBar()

        # Brand
        brand = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        mark = Gtk.Label(label="Pg")
        mark.add_css_class("pigment-logo-mark")
        name = Gtk.Label(label="Pigment")
        name.add_css_class("pigment-logo-name")
        ver = Gtk.Label(label='0.1 "Buzz"')
        ver.add_css_class("pigment-logo-version")
        brand.append(mark)
        brand.append(name)
        brand.append(ver)
        header.pack_start(brand)

        # Menu items inline
        for label, builder in [
            ("File",   self._build_file_menu),
            ("Edit",   self._build_edit_menu),
            ("Image",  self._build_image_menu),
            ("Layer",  self._build_layer_menu),
            ("Select", self._build_select_menu),
            ("Filter", self._build_filter_menu),
            ("View",   self._build_view_menu),
            ("Window", self._build_window_menu),
        ]:
            btn = Gtk.MenuButton(label=label)
            btn.add_css_class("pigment-menu-btn")
            btn.set_popover(builder())
            header.pack_start(btn)

        header.set_title_widget(Gtk.Box())  # hide default title
        return header

    # ── MENU BUILDERS ────────────────────────────────────────────────────────
    def _make_popover(self, items):
        """items: list of (label, callback) or None for separator"""
        pop = Gtk.Popover()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_margin_top(4); box.set_margin_bottom(4)
        box.set_margin_start(4); box.set_margin_end(4)
        for item in items:
            if item is None:
                sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
                sep.set_margin_top(3); sep.set_margin_bottom(3)
                box.append(sep)
            else:
                label, cb, *rest = item
                danger = rest[0] if rest else False
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                lbl = Gtk.Label(label=label, xalign=0)
                lbl.set_hexpand(True)
                row.append(lbl)
                if len(rest) > 1:
                    kbd = Gtk.Label(label=rest[1])
                    kbd.add_css_class("pigment-ob-label")
                    row.append(kbd)
                btn = Gtk.Button()
                btn.set_child(row)
                btn.add_css_class("flat")
                if danger:
                    btn.add_css_class("pigment-menu-danger")
                if cb:
                    btn.connect("clicked", lambda b, c=cb, p=pop: (p.popdown(), c()))
                box.append(btn)
        pop.set_child(box)
        return pop

    def _build_file_menu(self):
        return self._make_popover([
            ("New",       self._on_new_document,  False, "Ctrl+N"),
            ("Open…",     self._on_open_file,      False, "Ctrl+O"),
            None,
            ("Save",      self._on_save_file,      False, "Ctrl+S"),
            ("Save As…",  self._on_save_file,      False, "⇧Ctrl+S"),
            None,
            ("Export PNG…", self._on_save_file,    False),
            None,
            ("Quit",      self._on_quit,           True,  "Ctrl+Q"),
        ])

    def _build_edit_menu(self):
        return self._make_popover([
            ("Undo",  None, False, "Ctrl+Z"),
            ("Redo",  None, False, "⇧Ctrl+Z"),
        ])

    def _build_image_menu(self):
        return self._make_popover([
            ("Canvas Size…", None),
            ("Rotate 90° CW", None),
            ("Rotate 90° CCW", None),
            ("Flip Horizontal", None),
        ])

    def _build_layer_menu(self):
        return self._make_popover([
            ("New Layer",    None, False, "⇧Ctrl+N"),
            ("Duplicate",    None),
            ("Merge Down",   None, False, "Ctrl+E"),
            ("Flatten Image", None),
        ])

    def _build_select_menu(self):
        return self._make_popover([
            ("All",    None, False, "Ctrl+A"),
            ("Deselect", None, False, "Ctrl+D"),
            ("Invert", None, False, "⇧Ctrl+I"),
        ])

    def _build_filter_menu(self):
        return self._make_popover([
            ("Gaussian Blur…", None),
            ("Sharpen",        None),
            None,
            ("Levels…",        None),
            ("Curves…",        None),
        ])

    def _build_view_menu(self):
        return self._make_popover([
            ("Zoom In",     None, False, "Ctrl++"),
            ("Zoom Out",    None, False, "Ctrl+-"),
            ("Fit to Window", None, False, "Ctrl+0"),
            ("Actual Size", None, False, "Ctrl+1"),
            None,
            ("Rulers",      None),
            ("Grid",        None),
        ])

    def _build_window_menu(self):
        return self._make_popover([
            ("Toggle Panels",  self._toggle_panels),
            ("Toggle Toolbox", None),
            None,
            ("Dark Mode",  self._toggle_theme),
            ("Light Mode", self._toggle_theme),
        ])

    def _on_quit(self):
        self.get_application().quit()

    # ── OPTIONS BAR ──────────────────────────────────────────────────────────
    def _build_optionsbar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        bar.add_css_class("pigment-optionsbar")
        bar.set_margin_start(10); bar.set_margin_end(10)

        self._tool_chip = Gtk.Label(label="🖌  Brush")
        self._tool_chip.add_css_class("pigment-tool-chip")
        bar.append(self._tool_chip)
        bar.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        self._ob_entries = {}
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
            entry.connect("activate", self._on_ob_entry_changed, label)
            self._ob_entries[label] = entry
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

        spacer = Gtk.Box(); spacer.set_hexpand(True)
        bar.append(spacer)

        self._zoom_label = Gtk.Label(label="–")
        self._zoom_label.add_css_class("pigment-ob-label")
        zoom_out = Gtk.Button(label="−"); zoom_out.add_css_class("flat")
        zoom_out.connect("clicked", lambda _: self._canvas.zoom_out())
        zoom_in = Gtk.Button(label="+"); zoom_in.add_css_class("flat")
        zoom_in.connect("clicked", lambda _: self._canvas.zoom_in())
        fit_btn = Gtk.Button(label="Fit"); fit_btn.add_css_class("flat")
        fit_btn.connect("clicked", lambda _: self._canvas.zoom_fit())
        bar.append(zoom_out)
        bar.append(self._zoom_label)
        bar.append(zoom_in)
        bar.append(fit_btn)
        return bar

    # ── TAB BAR ──────────────────────────────────────────────────────────────
    def _build_tabbar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        bar.add_css_class("pigment-tabbar")
        bar.set_margin_start(8)
        self._tab_bar = bar
        return bar

    # ── TOOLBOX ──────────────────────────────────────────────────────────────
    def _build_toolbox(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer.add_css_class("pigment-toolbox")
        outer.set_size_request(82, -1)

        # Column switcher
        col_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        col_row.set_halign(Gtk.Align.CENTER)
        col_row.set_margin_top(4); col_row.set_margin_bottom(4)
        self._col_buttons = {}
        self._toolbox_cols = 3
        for n in [1, 2, 3, 4]:
            cb = Gtk.Button(label=str(n))
            cb.add_css_class("pigment-tool-btn")
            cb.set_size_request(18, 18)
            cb.connect("clicked", self._on_toolbox_cols, n)
            self._col_buttons[n] = cb
            col_row.append(cb)
        self._col_buttons[3].add_css_class("pigment-tool-active")
        outer.append(col_row)

        # Tool grid
        self._tool_grid = Gtk.Grid()
        self._tool_grid.set_row_spacing(2)
        self._tool_grid.set_column_spacing(2)
        grid = self._tool_grid

        tools = [
            ("⊹","Move (V)","move"),
            ("⬚","Marquee (M)","marquee"),
            ("⌖","Lasso (L)","lasso"),
            ("✦","Magic Wand (W)","wand"),
            ("⌗","Crop (C)","crop"),
            ("⧉","Slice (K)","slice"),
            ("✚","Healing Brush (J)","heal"),
            ("🖌","Brush (B)","brush"),
            ("⎘","Clone Stamp (S)","clone"),
            ("◻","Eraser (E)","eraser"),
            ("▦","Gradient (G)","gradient"),
            ("⬡","Paint Bucket","bucket"),
            ("◎","Blur/Sharpen (R)","blur"),
            ("◑","Dodge/Burn (O)","dodge"),
            ("✒","Pen (P)","pen"),
            ("T","Type (T)","type"),
            ("▭","Shape (U)","shape"),
            ("✥","Hand (H)","hand"),
            ("⊕","Zoom (Z)","zoom"),
        ]

        self._tool_buttons = {}
        self._active_tool_id = None
        cols = 3
        for i, (icon, tooltip, tool_id) in enumerate(tools):
            btn = Gtk.Button(label=icon)
            btn.set_tooltip_text(tooltip)
            btn.add_css_class("pigment-tool-btn")
            btn.connect("clicked", self._on_tool_clicked, tool_id)
            self._tool_buttons[tool_id] = btn
            grid.attach(btn, i % cols, i // cols, 1, 1)

        self._tools_list = tools
        outer.append(self._tool_grid)
        self._set_active_tool("brush")

        # FG/BG swatches
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.set_margin_top(6)
        outer.append(sep)

        swatch_area = Gtk.Fixed()
        swatch_area.set_size_request(54, 44)
        swatch_area.set_margin_top(4)
        swatch_area.set_halign(Gtk.Align.CENTER)

        # BG swatch (white, behind)
        self._bg_swatch = Gtk.DrawingArea()
        self._bg_swatch.set_size_request(28, 28)
        self._bg_swatch.set_draw_func(self._draw_bg_swatch)
        swatch_area.put(self._bg_swatch, 18, 14)

        # FG swatch (black, front)
        self._fg_swatch = Gtk.DrawingArea()
        self._fg_swatch.set_size_request(28, 28)
        self._fg_swatch.set_draw_func(self._draw_fg_swatch)
        swatch_area.put(self._fg_swatch, 4, 2)

        # Reset and swap labels
        reset_btn = Gtk.Button(label="↺")
        reset_btn.add_css_class("flat")
        reset_btn.add_css_class("pigment-ob-label")
        reset_btn.set_size_request(16, 16)
        reset_btn.connect("clicked", self._reset_colors)
        swatch_area.put(reset_btn, 0, 28)

        swap_btn = Gtk.Button(label="⇄")
        swap_btn.add_css_class("flat")
        swap_btn.add_css_class("pigment-ob-label")
        swap_btn.set_size_request(16, 16)
        swap_btn.connect("clicked", self._swap_colors)
        swatch_area.put(swap_btn, 36, 0)

        outer.append(swatch_area)

        return outer

    # ── CANVAS AREA ──────────────────────────────────────────────────────────
    def _build_canvas_area(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.set_hexpand(True); box.set_vexpand(True)

        canvas_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        canvas_box.set_hexpand(True); canvas_box.set_vexpand(True)
        canvas_box.add_css_class("pigment-canvas-bg")

        self._canvas = PigmentCanvas()
        self._canvas.on_zoom_changed = self._on_zoom_changed
        canvas_box.append(self._canvas)
        box.append(canvas_box)

        self._panel_toggle_strip = Gtk.Button(label="⟨")
        self._panel_toggle_strip.add_css_class("flat")
        self._panel_toggle_strip.add_css_class("pigment-ob-label")
        self._panel_toggle_strip.set_valign(Gtk.Align.CENTER)
        self._panel_toggle_strip.connect("clicked", self._toggle_panels)
        self._panel_toggle_strip.set_visible(False)
        box.append(self._panel_toggle_strip)

        return box

    # ── RIGHT PANEL ──────────────────────────────────────────────────────────
    def _build_right_panel(self):
        self._right_panel_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._right_panel_box.add_css_class("pigment-panels")
        self._right_panel_box.set_size_request(256, -1)

        # Panel titlebar
        title_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        title_row.add_css_class("pigment-panel-titlebar")
        title_row.set_margin_start(10); title_row.set_margin_end(10)
        title_lbl = Gtk.Label(label="Panels")
        title_lbl.add_css_class("pigment-panel-title")
        title_lbl.set_hexpand(True); title_lbl.set_xalign(0)
        hide_btn = Gtk.Button(label="⟩")
        hide_btn.add_css_class("pigment-panel-hide-btn")
        hide_btn.connect("clicked", self._toggle_panels)
        title_row.append(title_lbl)
        title_row.append(hide_btn)
        self._right_panel_box.append(title_row)

        # Scrollable accordion body
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        acc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        acc_box.append(self._build_accordion("Navigator", self._build_navigator_body()))
        acc_box.append(self._build_accordion("Color",     self._build_color_body()))
        acc_box.append(self._build_accordion("History",   self._build_history_body()))
        acc_box.append(self._build_accordion("Layers",    self._build_layers_body()))
        scroll.set_child(acc_box)
        self._right_panel_box.append(scroll)

        return self._right_panel_box

    def _build_accordion(self, title, body_widget):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        outer.append(sep)

        # Header button
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header_box.set_margin_start(12); header_box.set_margin_end(12)
        arrow = Gtk.Label(label="▶")
        arrow.add_css_class("pigment-ob-label")
        lbl = Gtk.Label(label=title)
        lbl.add_css_class("pigment-panel-title")
        lbl.set_xalign(0); lbl.set_hexpand(True)
        header_box.append(arrow)
        header_box.append(lbl)

        header_btn = Gtk.Button()
        header_btn.set_child(header_box)
        header_btn.add_css_class("flat")
        header_btn.add_css_class("pigment-acc-header")

        # Body revealer
        rev = Gtk.Revealer()
        rev.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        rev.set_reveal_child(True)
        body_wrapper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        body_wrapper.add_css_class("pigment-acc-body")
        body_wrapper.append(body_widget)
        rev.set_child(body_wrapper)

        def on_toggle(_btn, revealer=rev, arr=arrow):
            open_ = revealer.get_reveal_child()
            revealer.set_reveal_child(not open_)
            arr.set_label("▶" if open_ else "▼")

        header_btn.connect("clicked", on_toggle)

        outer.append(header_btn)
        outer.append(rev)
        return outer

    # ── ACCORDION BODIES ─────────────────────────────────────────────────────

    def _build_navigator_body(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        self._nav_thumb = Gtk.DrawingArea()
        self._nav_thumb.set_size_request(-1, 86)
        self._nav_thumb.add_css_class("pigment-nav-thumb")
        self._nav_thumb.set_draw_func(self._draw_nav_thumb)
        box.append(self._nav_thumb)

        zoom_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        zoom_row.append(Gtk.Label(label="−"))
        self._nav_slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 5, 3200, 1)
        self._nav_slider.set_value(100)
        self._nav_slider.set_hexpand(True)
        self._nav_slider.set_draw_value(False)
        self._nav_slider.connect("value-changed", self._on_nav_slider)
        zoom_row.append(self._nav_slider)
        zoom_row.append(Gtk.Label(label="+"))
        self._nav_zoom_label = Gtk.Label(label="100%")
        self._nav_zoom_label.add_css_class("pigment-ob-label")
        zoom_row.append(self._nav_zoom_label)
        box.append(zoom_row)
        return box

    def _build_color_body(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        self._color_swatch = Gtk.DrawingArea()
        self._color_swatch.set_size_request(-1, 34)
        self._color_swatch.add_css_class("pigment-color-swatch")
        self._color_swatch.set_draw_func(self._draw_color_swatch)
        box.append(self._color_swatch)

        for ch, idx in [("R", 0), ("G", 1), ("B", 2)]:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            lbl = Gtk.Label(label=ch)
            lbl.add_css_class("pigment-ob-label")
            lbl.set_size_request(12, -1)
            sl = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 255, 1)
            sl.set_value(0); sl.set_hexpand(True); sl.set_draw_value(False)
            sl.connect("value-changed", self._on_rgb_slider, idx)
            self._rgb_sliders[idx] = sl
            val_lbl = Gtk.Label(label="0")
            val_lbl.add_css_class("pigment-ob-label")
            val_lbl.set_size_request(28, -1)
            self._rgb_value_labels[idx] = val_lbl
            row.append(lbl); row.append(sl); row.append(val_lbl)
            box.append(row)

        hex_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hex_row.append(Gtk.Label(label="#"))
        self._hex_entry = Gtk.Entry()
        self._hex_entry.set_text("000000")
        self._hex_entry.set_width_chars(7)
        self._hex_entry.set_max_length(6)
        self._hex_entry.connect("activate", self._on_hex_entry)
        hex_row.append(self._hex_entry)
        box.append(hex_row)
        return box

    def _build_history_body(self):
        self._history_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        placeholder = Gtk.Label(label="No history yet")
        placeholder.add_css_class("pigment-ob-label")
        self._history_list.append(placeholder)
        return self._history_list

    def _build_layers_body(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        blend_strings = Gtk.StringList.new(["Normal","Multiply","Screen","Overlay"])
        blend_drop = Gtk.DropDown(model=blend_strings)
        blend_drop.set_hexpand(True)
        top_row.append(blend_drop)
        box.append(top_row)

        self._layers_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.append(self._layers_list)

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        for label in ["+ New", "⊕ Dup", "🗑"]:
            btn = Gtk.Button(label=label)
            btn.add_css_class("flat")
            btn.set_hexpand(True)
            actions.append(btn)
        box.append(actions)
        return box

    # ── STATUS BAR ───────────────────────────────────────────────────────────
    def _build_statusbar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        bar.add_css_class("pigment-statusbar")
        bar.set_margin_start(12); bar.set_margin_end(12)

        self._status_doc  = Gtk.Label(label='Pigment 0.1 "Buzz"')
        self._status_info = Gtk.Label(label="Python 3.13 · GTK 4.18")
        self._status_coord = Gtk.Label(label="No document open")
        for w in [self._status_doc, self._status_info, self._status_coord]:
            w.add_css_class("pigment-status-label")
            bar.append(w)
            bar.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        spacer = Gtk.Box(); spacer.set_hexpand(True)
        bar.append(spacer)

        accent = Gtk.Label(label='Pigment 0.1 "Buzz"')
        accent.add_css_class("pigment-status-accent")
        bar.append(accent)
        return bar

    # ── DOCUMENT ─────────────────────────────────────────────────────────────
    def _on_new_document(self):
        dialog = Adw.MessageDialog(transient_for=self, heading="New Document",
                                   body="Enter canvas dimensions:")
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("create", "Create")
        dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)

        grid = Gtk.Grid(column_spacing=8, row_spacing=6)
        grid.set_margin_top(8)
        grid.attach(Gtk.Label(label="Width",  xalign=0), 0, 0, 1, 1)
        grid.attach(Gtk.Label(label="Height", xalign=0), 0, 1, 1, 1)
        w_entry = Gtk.Entry(); w_entry.set_text("1920"); w_entry.set_width_chars(8)
        h_entry = Gtk.Entry(); h_entry.set_text("1080"); h_entry.set_width_chars(8)
        grid.attach(w_entry, 1, 0, 1, 1); grid.attach(h_entry, 1, 1, 1, 1)
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

    def _create_document(self, width, height):
        doc = Document(width, height, name="Untitled")
        self._documents.append(doc)
        self._active_doc = doc

        tab_btn = Gtk.Button(label=f"{doc.name}  ×")
        tab_btn.add_css_class("flat")
        tab_btn.add_css_class("pigment-tab-btn")
        tab_btn.connect("clicked", self._on_tab_clicked, doc, tab_btn)
        self._tab_bar.append(tab_btn)
        self._set_active_tab(tab_btn)

        self._canvas.set_document(doc)
        self._status_doc.set_text(f"{doc.name} — {width}×{height} px")
        self._status_info.set_text("RGB 8-bit")
        self._zoom_label.set_text(f"{self._canvas.zoom_percent:.1f}%")

    # ── FILE I/O ──────────────────────────────────────────────────────────────
    def _on_save_file(self):
        if not self._active_doc:
            return
        dialog = Gtk.FileDialog.new()
        dialog.set_title("Save as PNG")
        dialog.set_initial_name(f"{self._active_doc.name}.png")
        png_filter = Gtk.FileFilter()
        png_filter.set_name("PNG images")
        png_filter.add_mime_type("image/png")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(png_filter)
        dialog.set_filters(filters)
        dialog.save(self, None, self._on_save_response)

    def _on_save_response(self, dialog, result):
        try:
            file = dialog.save_finish(result)
        except Exception:
            return
        if not file:
            return
        path = file.get_path()
        if not path.endswith(".png"):
            path += ".png"
        from PIL import Image
        pixels = self._active_doc.pixels
        img = Image.fromarray(pixels[:, :, :3], "RGB")
        img.save(path)
        self._active_doc.name = path.split("/")[-1].replace(".png", "")
        self._active_doc.modified = False
        self._status_doc.set_text(f"{self._active_doc.name} — saved")

    def _on_open_file(self):
        dialog = Gtk.FileDialog.new()
        dialog.set_title("Open image")
        png_filter = Gtk.FileFilter()
        png_filter.set_name("PNG images")
        png_filter.add_mime_type("image/png")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(png_filter)
        dialog.set_filters(filters)
        dialog.open(self, None, self._on_open_response)

    def _on_open_response(self, dialog, result):
        try:
            file = dialog.open_finish(result)
        except Exception:
            return
        if not file:
            return
        path = file.get_path()
        from PIL import Image
        import numpy as np
        img = Image.open(path).convert("RGBA")
        arr = np.array(img, dtype=np.uint8)
        name = path.split("/")[-1].replace(".png", "")
        doc = Document(arr.shape[1], arr.shape[0], name=name)
        doc.pixels = arr
        self._documents.append(doc)
        self._active_doc = doc
        tab_btn = Gtk.Button(label=f"{doc.name}  ×")
        tab_btn.add_css_class("flat")
        tab_btn.add_css_class("pigment-tab-btn")
        tab_btn.connect("clicked", self._on_tab_clicked, doc, tab_btn)
        self._tab_bar.append(tab_btn)
        self._set_active_tab(tab_btn)
        self._canvas.set_document(doc)
        self._status_doc.set_text(f"{doc.name} — {doc.width}×{doc.height} px")
        self._status_info.set_text("RGB 8-bit")
        self._zoom_label.set_text(f"{self._canvas.zoom_percent:.1f}%")

    # ── NAVIGATOR ────────────────────────────────────────────────────────────
    def _draw_nav_thumb(self, area, cr, width, height):
        import cairo
        # Dark background
        cr.set_source_rgb(0.18, 0.18, 0.18)
        cr.paint()

        if not self._active_doc:
            return

        doc = self._active_doc
        pixels = doc.pixels

        # Build a Cairo surface from the pixel buffer
        import numpy as np
        h, w = pixels.shape[:2]
        bgra = np.zeros((h, w, 4), dtype=np.uint8)
        bgra[:, :, 0] = pixels[:, :, 2]  # B
        bgra[:, :, 1] = pixels[:, :, 1]  # G
        bgra[:, :, 2] = pixels[:, :, 0]  # R
        bgra[:, :, 3] = pixels[:, :, 3]  # A

        stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, w)
        flat = bgra.tobytes()
        surf = cairo.ImageSurface.create_for_data(
            bytearray(flat), cairo.FORMAT_ARGB32, w, h, stride
        )

        scale = min(width / w, height / h) * 0.95
        ox = (width  - w * scale) / 2
        oy = (height - h * scale) / 2

        cr.save()
        cr.translate(ox, oy)
        cr.scale(scale, scale)
        cr.set_source_surface(surf, 0, 0)
        cr.paint()
        cr.restore()

        # Viewport indicator
        if hasattr(self._canvas, '_offset_x'):
            zoom = self._canvas._zoom
            vw = self._canvas.get_width()
            vh = self._canvas.get_height()
            ox2 = self._canvas._offset_x
            oy2 = self._canvas._offset_y
            vp_x = ox + (-ox2 / zoom) * scale
            vp_y = oy + (-oy2 / zoom) * scale
            vp_w = (vw / zoom) * scale
            vp_h = (vh / zoom) * scale
            cr.set_source_rgba(0.49, 0.36, 0.75, 0.9)
            cr.set_line_width(1.5)
            cr.rectangle(vp_x, vp_y, vp_w, vp_h)
            cr.stroke()

    def _on_zoom_changed(self, zoom):
        pct = zoom * 100
        self._zoom_label.set_text(f"{pct:.1f}%")
        self._nav_zoom_label.set_text(f"{pct:.1f}%")
        self._nav_slider.handler_block_by_func(self._on_nav_slider)
        self._nav_slider.set_value(pct)
        self._nav_slider.handler_unblock_by_func(self._on_nav_slider)
        self._nav_thumb.queue_draw()

    def _on_nav_slider(self, slider):
        self._canvas._set_zoom(slider.get_value() / 100.0, center=True)

    # ── COLOR ────────────────────────────────────────────────────────────────
    def _draw_color_swatch(self, area, cr, width, height):
        r, g, b = [v / 255.0 for v in self._color_rgb]
        cr.set_source_rgb(r, g, b)
        cr.paint()
        cr.set_source_rgba(0, 0, 0, 0.15)
        cr.set_line_width(1)
        cr.rectangle(0, 0, width, height)
        cr.stroke()

    def _on_rgb_slider(self, slider, idx):
        val = int(slider.get_value())
        self._color_rgb[idx] = val
        self._rgb_value_labels[idx].set_text(str(val))
        self._sync_color()

    def _on_hex_entry(self, entry):
        text = entry.get_text().strip().lstrip("#")
        if len(text) == 6:
            try:
                r, g, b = int(text[0:2],16), int(text[2:4],16), int(text[4:6],16)
                self._color_rgb = [r, g, b]
                for idx, val in enumerate([r, g, b]):
                    self._rgb_sliders[idx].handler_block_by_func(self._on_rgb_slider)
                    self._rgb_sliders[idx].set_value(val)
                    self._rgb_value_labels[idx].set_text(str(val))
                    self._rgb_sliders[idx].handler_unblock_by_func(self._on_rgb_slider)
                self._sync_color()
            except ValueError:
                pass

    def _sync_color(self):
        r, g, b = self._color_rgb
        self._canvas._brush_color = (r, g, b)
        self._color_swatch.queue_draw()
        self._hex_entry.set_text(f"{r:02x}{g:02x}{b:02x}")
        if hasattr(self, '_fg_swatch'):
            self._fg_swatch.queue_draw()

    # ── TOOLS ────────────────────────────────────────────────────────────────
    def _on_toolbox_cols(self, btn, cols):
        self._toolbox_cols = cols
        for n, b in self._col_buttons.items():
            b.remove_css_class("pigment-tool-active")
        self._col_buttons[cols].add_css_class("pigment-tool-active")

        # Rebuild grid
        # Remove all children
        child = self._tool_grid.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self._tool_grid.remove(child)
            child = nxt

        # Re-attach tool buttons
        for i, (icon, tooltip, tool_id) in enumerate(self._tools_list):
            btn_w = self._tool_buttons[tool_id]
            self._tool_grid.attach(btn_w, i % cols, i // cols, 1, 1)

        # Resize toolbox
        width = cols * 28 + (cols + 1) * 2 + 10
        self._toolbox_widget.set_size_request(width, -1)

    def _draw_fg_swatch(self, area, cr, width, height):
        r, g, b = [v / 255.0 for v in self._color_rgb]
        # Checkerboard for transparency hint
        cr.set_source_rgb(0.88, 0.88, 0.88)
        cr.paint()
        cr.set_source_rgb(r, g, b)
        cr.paint()
        cr.set_source_rgba(0, 0, 0, 0.4)
        cr.set_line_width(1)
        cr.rectangle(0.5, 0.5, width - 1, height - 1)
        cr.stroke()

    def _draw_bg_swatch(self, area, cr, width, height):
        r, g, b = [v / 255.0 for v in self._bg_color_rgb]
        cr.set_source_rgb(r, g, b)
        cr.paint()
        cr.set_source_rgba(0, 0, 0, 0.25)
        cr.set_line_width(1)
        cr.rectangle(0.5, 0.5, width - 1, height - 1)
        cr.stroke()

    def _reset_colors(self, *_):
        self._color_rgb = [0, 0, 0]
        self._bg_color_rgb = [255, 255, 255]
        self._apply_fg_color()
        self._fg_swatch.queue_draw()
        self._bg_swatch.queue_draw()

    def _swap_colors(self, *_):
        self._color_rgb, self._bg_color_rgb = self._bg_color_rgb, self._color_rgb
        self._apply_fg_color()
        self._fg_swatch.queue_draw()
        self._bg_swatch.queue_draw()

    def _apply_fg_color(self):
        r, g, b = self._color_rgb
        self._canvas._brush_color = (r, g, b)
        for idx, val in enumerate([r, g, b]):
            self._rgb_sliders[idx].handler_block_by_func(self._on_rgb_slider)
            self._rgb_sliders[idx].set_value(val)
            self._rgb_value_labels[idx].set_text(str(val))
            self._rgb_sliders[idx].handler_unblock_by_func(self._on_rgb_slider)
        self._color_swatch.queue_draw()
        self._hex_entry.set_text(f"{r:02x}{g:02x}{b:02x}")
        if hasattr(self, '_fg_swatch'):
            self._fg_swatch.queue_draw()

    def _on_tool_clicked(self, btn, tool_id):
        self._set_active_tool(tool_id)

    def _set_active_tool(self, tool_id):
        if self._active_tool_id and self._active_tool_id in self._tool_buttons:
            self._tool_buttons[self._active_tool_id].remove_css_class("pigment-tool-active")
        self._active_tool_id = tool_id
        if tool_id in self._tool_buttons:
            self._tool_buttons[tool_id].add_css_class("pigment-tool-active")

    # ── OB ENTRIES ───────────────────────────────────────────────────────────
    def _on_tab_clicked(self, btn, doc, tab_btn):
        self._active_doc = doc
        self._canvas.set_document(doc)
        self._set_active_tab(tab_btn)
        self._status_doc.set_text(f"{doc.name} — {doc.width}×{doc.height} px")
        self._status_info.set_text("RGB 8-bit")
        self._zoom_label.set_text(f"{self._canvas.zoom_percent:.1f}%")

    def _set_active_tab(self, active_btn):
        child = self._tab_bar.get_first_child()
        while child:
            child.remove_css_class("pigment-tab-btn-active")
            child = child.get_next_sibling()
        active_btn.add_css_class("pigment-tab-btn-active")

    def _on_ob_entry_changed(self, entry, label):
        text = entry.get_text().replace("%", "").strip()
        try:
            val = float(text)
        except ValueError:
            return
        if label == "Size":
            self._canvas._brush_radius = val / 2.0
        elif label == "Opacity":
            self._canvas._brush_opacity = min(1.0, val / 100.0)

    # ── PANEL TOGGLE ─────────────────────────────────────────────────────────
    def _toggle_panels(self, *_):
        self._panel_visible = not self._panel_visible
        self._right_panel_box.set_visible(self._panel_visible)
        self._panel_toggle_strip.set_visible(not self._panel_visible)

    # ── THEME ────────────────────────────────────────────────────────────────
    def _toggle_theme(self, *_):
        manager = Adw.StyleManager.get_default()
        if manager.get_color_scheme() == Adw.ColorScheme.FORCE_DARK:
            manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        else:
            manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
