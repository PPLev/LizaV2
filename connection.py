import asyncio
import os.path
from typing import List
import yaml

from event import Event
from module_manager import ModuleManager


class Extension:
    def __init__(self, target_func, **kwargs):
        self.target_func = target_func
        self.kwargs = kwargs

    async def apply(self, event: Event):
        if asyncio.iscoroutinefunction(self.target_func):
            applied_event = await self.target_func(event, **self.kwargs)
        else:
            applied_event = self.target_func(event, **self.kwargs)

        return applied_event


class IOPair:
    def __init__(self, destination, target):
        self.destination = destination
        self.target = target

    @staticmethod
    def load_file(filename: str) -> List['IOPair']:
        if not os.path.isfile(filename):
            return []

        with open(filename, 'r', encoding="utf-8") as file:
            data = yaml.safe_load(file)

        pairs = []

        if "io_pairs" in data:
            for destination, target in data["io_pairs"].items():
                pairs.append(
                    IOPair(
                        destination=destination,
                        target=target
                    )
                )

        if "includes" in data:
            for addition in data["includes"]:
                pairs.extend(IOPair.load_file(addition))

        return pairs


class Connection:
    name: str
    senders: List[str]
    before_ext: List[Extension]
    purposes: List[str]
    acceptors: List[str]

    def __init__(self, name, senders, before_ext, purposes, acceptors):
        self.name = name
        self.senders = senders
        self.before_ext = before_ext
        self.purposes = purposes
        self.acceptors = acceptors

    @staticmethod
    def load_file(filename: str) -> List['Connection']:
        if not os.path.isfile(filename):
            return []

        with open(filename, 'r', encoding="utf-8") as file:
            data = yaml.safe_load(file)

        connections = []

        if "rules" in data:
            for rule in data["rules"]:
                connections.append(
                    Connection(
                        name=rule,
                        **data["rules"][rule]
                    )
                )

        if "includes" in data:
            for addition in data["includes"]:
                connections.extend(Connection.load_file(addition))

        return connections

    def init_extensions(self, mm: ModuleManager):
        init_exts: List[Extension] = []
        for extension in self.before_ext:
            if isinstance(extension, str):
                init_exts.append(Extension(mm.extensions[extension]))
            if isinstance(extension, list) and len(extension) == 2:
                init_exts.append(Extension(mm.extensions[extension[0]], **extension[1]))

        self.before_ext = init_exts

    def check_event(self, event: Event) -> bool:
        event_connection_allowed = False

        exec_purpose = bool(len(self.purposes))

        if exec_purpose and event.purpose:
            if event.purpose in self.purposes:
                event_connection_allowed = True

        if not exec_purpose:
            event_connection_allowed = True

        return event_connection_allowed

    async def run_event(self, event: Event, mm: ModuleManager):
        if len(self.senders) and (event.from_module not in self.senders):
            return

        if not self.check_event(event):
            return

        for extension in self.before_ext:
            event = await extension.apply(event)

        for acceptor in self.acceptors:
            await mm.queues[acceptor].input.put(event.copy())


if __name__ == '__main__':
    connections = Connection.load_file('connections/connections.yml')
