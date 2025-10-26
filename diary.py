from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional
from errors import DiaryLockedError, EntryNotFoundError

@dataclass
class Entry:
    title: str
    content: str
    date: str
    locked: bool = False

    @classmethod
    def create(cls, title: str, content: str, date: Optional[str] = None):
        date = date or datetime.now().strftime('%Y-%m-%d')
        return cls(title=title, content=content, date=date, locked=False)

class Diary:
    def __init__(self):
        self.entries: List[Entry] = []

    def add(self, entry: Entry):
        self.entries.append(entry)

    def to_list_of_dicts(self):
        return [asdict(e) for e in self.entries]

    def load_from_list_of_dicts(self, data: list):
        self.entries = [Entry(**d) for d in data]
