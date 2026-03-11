# Cairo-backed canvas — the main drawing surface for Pigment
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib
import cairo
import numpy as np
from pigment.core.document import Document

# Checkerboard tile size in pixels
CHECKER_SIZE = 12
# Zoom limits
ZOOM_MIN = 0.05   # 5%
ZOOM_MAX = 32.0   # 3200%
ZOOM_STEPS = [
    0.0625, 0.083, 0.125, 0.167, 0.25, 0.333, 0.5,
    0.667, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0,
    16.0, 24.0, 32.0,
]


class PigmentCanvas(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.document: Document | None = None

        # Viewport state
        self._zoom     = 1.0
        self._offset_x = 0.0
        self._offset_y = 0.0

        # Pan state
        self._panning      = False
        self._pan_origin_x = 0.0
        self._pan_origin_y = 0.0
        self._space_held   = False

        # Cached checkerboard pattern (rebuilt when zoom changes)
        self._checker_surface = None
        self._checker_zoom    = -1.0

        # Cairo surface cache of the document pixels
        self._doc_surface: cairo.ImageSurface | None = None
        self._doc_dirty = True

        # Notify callback — called when zoom changes so window can update label
        self.on_zoom_changed = None

        # Brush state — updated by window when options bar changes
        self._brush_radius  = 9.5
        self._brush_color   = (0, 0, 0)
        self._brush_opacity = 0.85
        self._last_paint_x  = 0.0
        self._last_paint_y  = 0.0
        self._painting      = False

        # Drawing setup
        self.set_draw_func(self._draw)
        self.set_focusable(True)
        self.set_can_focus(True)
        self.set_hexpand(True)
        self.set_vexpand(True)

        # Mouse scroll → zoom
        scroll = Gtk.EventControllerScroll.new(
            Gtk.EventControllerScrollFlags.BOTH_AXES
        )
        scroll.connect("scroll", self._on_scroll)
        self.add_controller(scroll)

        # Mouse drag → pan or paint
        drag = Gtk.GestureDrag.new()
        drag.connect("drag-begin",  self._on_drag_begin)
        drag.connect("drag-update", self._on_drag_update)
        drag.connect("drag-end",    self._on_drag_end)
        self.add_controller(drag)

        # Keyboard → spacebar pan + zoom shortcuts
        key = Gtk.EventControllerKey.new()
        key.connect("key-pressed",  self._on_key_pressed)
        key.connect("key-released", self._on_key_released)
        self.add_controller(key)

        # Cursors
        self._cursor_default = Gdk.Cursor.new_from_name("crosshair")
        self._cursor_pan     = Gdk.Cursor.new_from_name("grab")
        self._cursor_panning = Gdk.Cursor.new_from_name("grabbing")
        self.set_cursor(self._cursor_default)

    # ── PUBLIC API ───────────────────────────────────────────────────────────

    def set_document(self, doc: Document):
        """Attach a document and fit it to the viewport."""
        self.document  = doc
        self._doc_dirty = True
        self._fit_to_window()

    def mark_dirty(self):
        """Call after any pixel change to trigger a redraw."""
        self._doc_dirty = True
        self.queue_draw()

    def zoom_in(self):
        self._step_zoom(1)

    def zoom_out(self):
        self._step_zoom(-1)

    def zoom_fit(self):
        self._fit_to_window()

    def zoom_actual(self):
        self._set_zoom(1.0, center=True)

    @property
    def zoom_percent(self):
        return self._zoom * 100.0

    # ── DRAWING ──────────────────────────────────────────────────────────────

    def _draw(self, area, cr: cairo.Context, width: int, height: int):
        cr.set_source_rgb(0.78, 0.77, 0.74)
        cr.paint()

        if self.document is None:
            self._draw_no_document(cr, width, height)
            return

        cr.save()
        cr.translate(self._offset_x, self._offset_y)
        cr.scale(self._zoom, self._zoom)

        self._draw_checker(cr)
        self._draw_document(cr)

        # Thin border around document
        cr.set_source_rgba(0, 0, 0, 0.25)
        cr.set_line_width(1.0 / self._zoom)
        cr.rectangle(0, 0, self.document.width, self.document.height)
        cr.stroke()

        cr.restore()

    def _draw_no_document(self, cr, width, height):
        cr.set_source_rgba(0, 0, 0, 0.25)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(14)
        msg = "File → New  or  File → Open"
        ext = cr.text_extents(msg)
        cr.move_to(width / 2 - ext.width / 2, height / 2)
        cr.show_text(msg)

    def _draw_checker(self, cr: cairo.Context):
        if not self.document:
            return
        if self._checker_zoom != self._zoom:
            self._checker_surface = self._make_checker_pattern()
            self._checker_zoom    = self._zoom
        pattern = cairo.SurfacePattern(self._checker_surface)
        pattern.set_extend(cairo.Extend.REPEAT)
        cr.set_source(pattern)
        cr.rectangle(0, 0, self.document.width, self.document.height)
        cr.fill()

    def _make_checker_pattern(self) -> cairo.ImageSurface:
        tile  = CHECKER_SIZE
        surf  = cairo.ImageSurface(cairo.FORMAT_RGB24, tile * 2, tile * 2)
        ctx   = cairo.Context(surf)
        light, dark = 0.93, 0.78
        for row in range(2):
            for col in range(2):
                c = light if (row + col) % 2 == 0 else dark
                ctx.set_source_rgb(c, c, c)
                ctx.rectangle(col * tile, row * tile, tile, tile)
                ctx.fill()
        return surf

    def _draw_document(self, cr: cairo.Context):
        if not self.document:
            return
        if self._doc_dirty or self._doc_surface is None:
            self._doc_surface = self._numpy_to_cairo(self.document.pixels)
            self._doc_dirty   = False
        cr.set_source_surface(self._doc_surface, 0, 0)
        cr.get_source().set_filter(
            cairo.Filter.NEAREST if self._zoom >= 2.0 else cairo.Filter.BILINEAR
        )
        cr.rectangle(0, 0, self.document.width, self.document.height)
        cr.fill()

    def _numpy_to_cairo(self, pixels: np.ndarray) -> cairo.ImageSurface:
        """Convert RGBA NumPy array to a Cairo ARGB32 surface."""
        h, w = pixels.shape[:2]
        bgra  = np.ascontiguousarray(pixels[:, :, [2, 1, 0, 3]])
        surf  = cairo.ImageSurface.create_for_data(
            bgra, cairo.FORMAT_ARGB32, w, h
        )
        # Keep a reference so the buffer isn't GC'd while the surface is alive
        self._bgra_refs = getattr(self, '_bgra_refs', [])
        self._bgra_refs.append(bgra)
        if len(self._bgra_refs) > 4:
            self._bgra_refs.pop(0)
        return surf

    # ── ZOOM ─────────────────────────────────────────────────────────────────

    def _step_zoom(self, direction: int):
        current = self._zoom
        if direction > 0:
            candidates = [z for z in ZOOM_STEPS if z > current * 1.001]
            new_zoom   = candidates[0] if candidates else ZOOM_MAX
        else:
            candidates = [z for z in ZOOM_STEPS if z < current * 0.999]
            new_zoom   = candidates[-1] if candidates else ZOOM_MIN
        self._set_zoom(new_zoom, center=True)

    def _set_zoom(self, new_zoom: float, center=False,
                  anchor_wx=None, anchor_wy=None):
        new_zoom = max(ZOOM_MIN, min(ZOOM_MAX, new_zoom))
        if anchor_wx is not None and anchor_wy is not None:
            cx = (anchor_wx - self._offset_x) / self._zoom
            cy = (anchor_wy - self._offset_y) / self._zoom
            self._zoom     = new_zoom
            self._offset_x = anchor_wx - cx * self._zoom
            self._offset_y = anchor_wy - cy * self._zoom
        elif center:
            w  = self.get_width()
            h  = self.get_height()
            cx = (w / 2 - self._offset_x) / self._zoom
            cy = (h / 2 - self._offset_y) / self._zoom
            self._zoom     = new_zoom
            self._offset_x = w / 2 - cx * self._zoom
            self._offset_y = h / 2 - cy * self._zoom
        else:
            self._zoom = new_zoom

        self._checker_zoom = -1.0
        if self.on_zoom_changed:
            self.on_zoom_changed(self._zoom)
        self.queue_draw()

    def _fit_to_window(self):
        if not self.document:
            return
        GLib.idle_add(self._fit_delayed)

    def _fit_delayed(self):
        if not self.document:
            return
        w, h = self.get_width(), self.get_height()
        if w <= 0 or h <= 0:
            GLib.idle_add(self._fit_delayed)
            return
        pad    = 40
        zoom   = min((w - pad * 2) / self.document.width,
                     (h - pad * 2) / self.document.height,
                     1.0)
        self._zoom     = max(ZOOM_MIN, zoom)
        self._offset_x = (w - self.document.width  * self._zoom) / 2
        self._offset_y = (h - self.document.height * self._zoom) / 2
        self._checker_zoom = -1.0
        if self.on_zoom_changed:
            self.on_zoom_changed(self._zoom)
        self.queue_draw()

    # ── SCROLL → ZOOM ────────────────────────────────────────────────────────

    def _on_scroll(self, controller, dx, dy):
        wx     = self.get_width()  / 2
        wy     = self.get_height() / 2
        factor = 1.1 if dy < 0 else (1.0 / 1.1)
        self._set_zoom(self._zoom * factor, anchor_wx=wx, anchor_wy=wy)
        return True

    # ── KEYBOARD ─────────────────────────────────────────────────────────────

    def _on_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_space and not self._space_held:
            self._space_held = True
            self.set_cursor(self._cursor_pan)
        elif keyval in (Gdk.KEY_plus, Gdk.KEY_equal):
            self.zoom_in()
        elif keyval == Gdk.KEY_minus:
            self.zoom_out()
        elif keyval == Gdk.KEY_0:
            self.zoom_fit()
        elif keyval == Gdk.KEY_1:
            self.zoom_actual()
        return False

    def _on_key_released(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_space:
            self._space_held = False
            self._panning    = False
            self.set_cursor(self._cursor_default)
        return False

    # ── DRAG → PAN or PAINT ──────────────────────────────────────────────────

    def _on_drag_begin(self, gesture, start_x, start_y):
        self.grab_focus()
        if self._space_held:
            self._panning      = True
            self._pan_origin_x = self._offset_x
            self._pan_origin_y = self._offset_y
            self.set_cursor(self._cursor_panning)
        else:
            self._painting = True
            self._start_paint(start_x, start_y)

    def _on_drag_update(self, gesture, offset_x, offset_y):
        if self._panning:
            self._offset_x = self._pan_origin_x + offset_x
            self._offset_y = self._pan_origin_y + offset_y
            self.queue_draw()
        elif self._painting:
            _ok, sx, sy = gesture.get_start_point()
            self._continue_paint(sx + offset_x, sy + offset_y)

    def _on_drag_end(self, gesture, offset_x, offset_y):
        if self._panning:
            self._panning = False
            self.set_cursor(
                self._cursor_pan if self._space_held else self._cursor_default
            )
        self._painting = False

    # ── BRUSH PAINTING ───────────────────────────────────────────────────────

    def _start_paint(self, x: float, y: float):
        self._last_paint_x, self._last_paint_y = self._widget_to_canvas(x, y)
        self._paint_dab(self._last_paint_x, self._last_paint_y)

    def _continue_paint(self, x: float, y: float):
        cx, cy = self._widget_to_canvas(x, y)
        if self.document:
            self.document.paint_stroke(
                self._last_paint_x, self._last_paint_y,
                cx, cy,
                self._brush_radius,
                self._brush_color,
                self._brush_opacity,
            )
            self.mark_dirty()
        self._last_paint_x, self._last_paint_y = cx, cy

    def _paint_dab(self, cx: float, cy: float):
        if self.document:
            self.document.paint_circle(
                cx, cy,
                self._brush_radius,
                self._brush_color,
                self._brush_opacity,
            )
            self.mark_dirty()

    def _widget_to_canvas(self, wx: float, wy: float):
        """Convert widget pixel coordinates to canvas document coordinates."""
        return (wx - self._offset_x) / self._zoom, \
               (wy - self._offset_y) / self._zoom
