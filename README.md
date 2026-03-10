# Pigment 0.1 "Buzz"

A professional image editor for Linux, built with Python 3.13, GTK 4 and Cairo.
Inspired by classic desktop image editing workflows.

## Status
- [x] Phase 1 — Main window shell (HeaderBar, toolbox, panels, statusbar)
- [ ] Phase 2 — Cairo canvas with zoom and pan
- [ ] Phase 3 — Document model and single layer
- [ ] Phase 4 — Tool switching and Marquee selection
- [ ] Phase 5 — Brush engine
- [ ] Phase 6 — Full layer system
- [ ] Phase 7 — Filters and adjustments
- [ ] Phase 8 — PSD file I/O

## Running
```bash
source ~/.venvs/pigment/bin/activate
cd ~/Projects/pigment
PYTHONPATH=src python3 -m pigment.main
```

## Stack
- Python 3.13
- GTK 4.18 + Adwaita 1.7 via PyGObject
- Cairo 1.27 (canvas rendering)
- NumPy 2.2 (pixel buffers)
- psd-tools 1.14 (PSD I/O)
