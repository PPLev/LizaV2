from nlu import NLU


class Module:
    def __init__(self, name):
        self.intents = {}
        self.name = ""
        self.version = ""

    def get_settings(self):
        pass

    def update_settings(self, key, value):
        pass

    def run_intent(self):
        pass

class ModuleManager:
    def __init__(self):
        self.nlu: NLU = None

    def list(self):
        pass

    def init_modules(self):
        pass
