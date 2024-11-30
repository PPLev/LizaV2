from textual import screen, widgets, app


class SettingsScreen(screen.Screen):
    BINDINGS = [("escape", "app.pop_screen", "back")]
    TITLE = "Settings"

    def compose(self) -> app.ComposeResult:
        yield widgets.Header()

        yield widgets.Static(" Windows ", id="title")
        yield widgets.Static("Press any key to continue [blink]_[/]", id="any-key")

        yield widgets.Footer()