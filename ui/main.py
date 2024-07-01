from textual import app
from textual import widgets

import core
from .modules import ModulesScreen
from .settings import SettingsScreen


class Main(app.App):
    BINDINGS = [
        ("escape", "app.quit", "exit"),
        ("m", "push_screen('ModulesScreen')", "Modules"),
        #("s", "push_screen('SettingsScreen')", "Settings"),
    ]
    TITLE = "Liza brain"

    def compose(self) -> app.ComposeResult:
        """Create child widgets for the app."""
        yield widgets.Header()
        yield widgets.Label(f"Ver.: {core.v}")
        yield widgets.Footer()

    def on_mount(self) -> None:
        self.install_screen(ModulesScreen(), name="ModulesScreen")
        self.install_screen(SettingsScreen(), name="SettingsScreen")


if __name__ == "__main__":
    app = Main()
    app.run()
