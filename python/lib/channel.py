from typing import List

from lib.client import Client


class Channel:
    name: str = None
    password: str = None
    admins: List[Client] = []
    users: List[Client] = []

    def __init__(self, name: str, password: str = None):
        self.name = name
        self.password = password
