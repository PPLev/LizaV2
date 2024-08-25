import os.path
from dataclasses import dataclass
from typing import List
import yaml

from event import Event


@dataclass
class Connection:
    name: str
    senders: List[str]
    before_ext: List[str]
    purposes: List[str]
    post_ext: List[str]
    acceptors: List[str]

    @staticmethod
    def load(filename: str) -> List['Connection']:
        if not os.path.isfile(filename):
            return []

        with open(filename, 'r') as file:
            data = yaml.safe_load(file)

        connections = []

        for rule in data["rules"]:
            connections.append(
                Connection(
                    name=rule,
                    **data["rules"][rule]
                )
            )

        for addition in data["includes"]:
            connections.extend(Connection.load(addition))

        return connections

    def check_event(self, event: Event) -> bool:
        event_connection_allowed = False

        is_event_purposed = hasattr(event, "purpose")
        exec_purpose = bool(len(self.purposes))

        if exec_purpose and is_event_purposed:
            if event.purpose in self.purposes:
                event_connection_allowed = True

        if not exec_purpose:
            event_connection_allowed = True

        return event_connection_allowed


if __name__ == '__main__':
    connections = Connection.load('connections/connections.yml')