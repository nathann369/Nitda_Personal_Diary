# diary.py
# -----------------------------------------
# Handles core diary logic and entry model
# -----------------------------------------

from datetime import datetime
from errors import DiaryLockedError, EntryNotFoundError


class Entry:
    def __init__(self, title, content, date=None, locked=False):
        self.title = title
        self.content = content
        self.date = date or datetime.now().strftime("%Y-%m-%d")
        self.locked = locked  # Each entry can be locked individually

    def lock(self):
        self.locked = True

    def unlock(self):
        self.locked = False


class Diary:
    def __init__(self):
        self.entries = []

    def add_entry(self, entry):
        self.entries.append(entry)

    def edit_entry(self, title, new_content):
        entry = self._find_entry(title)
        if entry.locked:
            raise DiaryLockedError(f"Entry '{title}' is locked and cannot be edited.")
        entry.content = new_content

    def delete_entry(self, title):
        entry = self._find_entry(title)
        if entry.locked:
            raise DiaryLockedError(f"Entry '{title}' is locked and cannot be deleted.")
        self.entries.remove(entry)

    def search(self, keyword=None):
        results = self.entries
        if keyword:
            results = [e for e in results if keyword.lower() in e.title.lower() or keyword.lower() in e.content.lower()]
        
        return results

    def _find_entry(self, title):
        for e in self.entries:
            if e.title == title:
                return e
        raise EntryNotFoundError(f"Entry '{title}' not found.")
