# diary.py
# -----------------------------------------
# Handles core diary logic and entry model
# -----------------------------------------

from datetime import datetime
from tkinter import messagebox
from errors import DiaryLockedError, EntryNotFoundError
from pdf_exporter import export_entry_to_pdf


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

    def download_pdf(self):
        """Download the selected diary entry as a PDF."""
        try:
            index = self.listbox.curselection()[0]
            entry = self.diary.entries[index]

            if entry.locked:
                messagebox.showwarning("Locked", "You cannot download a locked entry.")
                return

            file_name = export_entry_to_pdf(entry)
            messagebox.showinfo("Success", f"Entry exported as '{file_name}' successfully!")

        except IndexError:
            messagebox.showwarning("Error", "Please select an entry to export.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")

    def search(self, keyword):
        """Search entries by keyword in title or content (case-insensitive)."""
        keyword = keyword.lower().strip()
        results = []
        for e in self.entries:
        # Use attributes instead of dictionary keys
            if keyword in e.title.lower() or keyword in e.content.lower():
                results.append({
                    "date": e.date,
                    "title": e.title,
                    "content": e.content
                 })
        return results

    def _find_entry(self, title):
        for e in self.entries:
            if e.title == title:
                return e
        raise EntryNotFoundError(f"Entry '{title}' not found.")
    

    
