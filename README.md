# Pigment

A professional image editor for Linux — built with Python, GTK 4, and Libadwaita.

**Current version:** 0.1 "Buzz"

---

## Philosophy

Pigment aims to be a first-class image editor for the GNOME desktop. It takes
inspiration from Photoshop's feature set and workflow, but is designed to look
and feel like a native GNOME application. It is not a GIMP replacement — it is
its own thing.

---

## Version Roadmap

| Version | Codename | Focus |
|---------|----------|-------|
| 0.1     | Buzz     | Core foundation — canvas, brush, colour picker, file I/O, GNOME UI ✅ |
| 0.2     | Rex      | Layer system — blend modes, opacity, reorder, merge |
| 0.3     | Bo       | Filters & adjustments — Levels, Curves, Gaussian Blur, Hue/Sat |
| 0.5     | Hamm     | Selections & masks — marquee, lasso, magic wand, layer masks |
| 0.7     | Slinky   | Text tool, shape tool, vector basics |
| 0.9     | Woody    | **.pig** native format, **XCF** import/export |
| 1.0     | Woody    | Stable release — full feature polish, performance pass |

---

## File Formats

### .pig — Pigment Native Format
Pigment's own open format, designed for full fidelity save/load of everything
the app supports. Implemented as a ZIP archive:

```
myfile.pig
├── manifest.json       ← format version, canvas size, colour profile
├── metadata.json       ← layer stack: names, blend modes, opacity, visibility
└── layers/
    ├── 0.png           ← each layer as a flat RGBA PNG
    ├── 1.png
    └── ...
```

Goals: human-inspectable, easy to implement, extensible, recoverable.

### .xcf — GIMP Native Format
XCF is an open, well-documented format. Pigment will support XCF import and
export to ensure full interoperability with GIMP, which is important for the
Linux creative community.

### PNG / JPEG
Flat export to PNG and JPEG is supported from day one (Phase 5+).

### PSD — Future Plugin
Adobe Photoshop format support is intentionally out of scope for the core app.
PSD support may be introduced later as an optional plugin, keeping the core
clean and the dependency footprint small.

---

## Phase Detail

### ✅ Phase 1 — Window Shell
- Adw.ApplicationWindow, GNOME CSD headerbar
- Toolbox (3-column, 1–4 column switcher)
- Right panel (Navigator / Color / History / Layers accordion)
- CSS warm-light theme, purple accent (#7c5cbf)
- Dark mode toggle via Window menu

### ✅ Phase 2 — Cairo Canvas
- PigmentCanvas drawing area with NumPy RGBA pixel buffer
- Checkerboard transparency pattern
- Zoom (mouse wheel, +/− keys) and pan (spacebar + drag)
- Fit-to-window, New Document dialog

### ✅ Phase 3 — Brush Painting
- Soft round brush with radius, opacity, flow
- NumPy-based paint_circle and paint_stroke on pixel buffer
- Coordinate conversion from widget space to canvas space

### ✅ Phase 4 — Colour Picker
- RGB sliders wired to brush colour
- Hex entry with bidirectional sync
- Live colour swatch preview

### ✅ Phase 5 — File I/O
- Save PNG via Gtk.FileDialog + Pillow
- Open PNG → new document tab

### ✅ Phase 6 — GNOME UI Polish
- Single CSD headerbar with inline PS-style menus
- Resizable canvas/panel split via Gtk.Paned
- GNOME-style document tabs with switching
- Accordion right panel (Navigator, Color, History, Layers)
- Toolbox column switcher (1/2/3/4 columns)
- Panel hide/show with canvas-edge restore button

### 🔜 Phase 7 — Layer System (0.2 Rex)
- Multiple layers per document
- Layer reorder (drag), rename, visibility toggle
- Blend modes: Normal, Multiply, Screen, Overlay, Soft Light
- Layer opacity
- Flatten image

### 🔜 Phase 8 — Filters & Adjustments (0.3 Bo)
- Gaussian Blur
- Levels (black/white/gamma point)
- Curves (RGB channel curves)
- Hue / Saturation / Brightness
- Sharpen

### 🔜 Phase 9 — Native Formats (0.9 Woody)
- **.pig** save and load (full layer fidelity)
- **.xcf** import and export (GIMP interoperability)

---

## Tech Stack

| Library       | Purpose                          |
|---------------|----------------------------------|
| Python 3.13   | Core language                    |
| GTK 4         | UI toolkit                       |
| Libadwaita 1  | GNOME design system              |
| PyGObject     | Python GTK bindings              |
| Cairo         | Canvas rendering                 |
| NumPy         | Pixel buffer operations          |
| Pillow        | PNG/JPEG encode-decode           |

---

## Running

```bash
source ~/.venvs/pigment/bin/activate
cd ~/Projects/pigment
./run.sh
```

---

## Contributing

Pigment is GPL v3. Contributions welcome.
Where code is adapted from other GPL v3 projects (e.g. GIMP), the original
source is noted in comments.

---

## License

GNU General Public License v3.0 — see LICENSE file.
