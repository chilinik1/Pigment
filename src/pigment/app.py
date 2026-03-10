# Manages app startup, CSS theming, and window creation
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, Gdk
from pathlib import Path
from pigment.ui.window import PigmentWindow

class PigmentApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="com.pigment.editor",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self.connect("activate", self._on_activate)

    def _on_activate(self, app):
        self._load_css()
        win = PigmentWindow(application=app)
        win.present()

    def _load_css(self):
        # Load our flat light theme from the resources folder
        theme_path = Path(__file__).parent / "resources" / "themes" / "pigment-light.css"
        if not theme_path.exists():
            print(f"Warning: theme not found at {theme_path}")
            return
        provider = Gtk.CssProvider()
        provider.load_from_path(str(theme_path))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
