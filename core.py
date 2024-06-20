from module_manager import ModuleManager

v = "0.1"


class Core:
    def __init__(self, connection_config_path="modules/conections.json"):
        self.connection_config_path = connection_config_path
        self.queues = {}
        self.MM = ModuleManager()

    async def run(self):
        await self.MM.init_modules()

