import json

from textual import screen, widgets, app, on, containers
from module_manager import ModuleManager, Module

module_manager = ModuleManager()
module_manager.init_modules()


class OptionsEdit(widgets.Static):
    def compose(self) -> app.ComposeResult:
        self.text_area = widgets.TextArea(text="Модуль не выбран", language="json", disabled=True, show_line_numbers=True)
        self.turn_on_swich = widgets.Switch(value=False, disabled=True, animate=False)
        self.turn_on_label = widgets.Label("\nАктивен\n")
        self.version_label = widgets.TextArea(text="Вер. \n", disabled=True)

        self.text_area.styles.width = "3fr"

        with containers.Horizontal(id="plugin_container"):
            with containers.Vertical(id="ver_switch") as left_menu:
                left_menu.styles.width = "1fr"
                yield self.version_label
                with containers.Horizontal(id="turn_on_swich") as swicher:
                    swicher.styles.height = "3fr"
                    yield self.turn_on_label
                    yield self.turn_on_swich
            yield self.text_area

    def from_option(self, option_name):
        self.opened_file_name = f"modules/{option_name}/settings.json"
        with open(self.opened_file_name, "r", encoding="utf-8") as file:
            file_content = file.read()
        plugin_data: dict = json.loads(file_content)
        ver = plugin_data.pop("version")
        is_active = plugin_data.pop("is_active")

        self.version_label.text = f"Версия: {ver}\n"
        self.turn_on_swich.disabled = False
        self.turn_on_swich.value = is_active

        self.text_area.disabled = False
        self.text_area.text = json.dumps(plugin_data["config"], indent=2, ensure_ascii=False)
        self.update()

    def action_save(self):
        with open(self.opened_file_name, "r", encoding="utf-8") as file:
            file_data: dict = json.load(file)

        new_data = {
            "is_active": self.turn_on_swich.value,
            "config": json.loads(self.text_area.text)
        }

        file_data.update(new_data)

        with open(self.opened_file_name, "w", encoding="utf-8") as file:
            json.dump(file_data, file, indent=2, ensure_ascii=False)



class ModulesScreen(screen.Screen):
    BINDINGS = [("escape", "app.pop_screen", "back")]
    TITLE = "Modules"

    def compose(self) -> app.ComposeResult:
        yield widgets.Header()
        yield widgets.Footer()

        yield widgets.Select(
            [(f"{module.name} - {module.version}", module.name) for module in module_manager.modules.values()],
            prompt="Выберите модуль"
        )
        self.option_layout = OptionsEdit("OptionsEdit", classes="box")
        yield self.option_layout

    @on(widgets.Select.Changed)
    def select_changed(self, event: widgets.Select.Changed) -> None:
        self.option_layout.from_option(str(event.value))

    def action_save(self):
        self.option_layout.action_save()