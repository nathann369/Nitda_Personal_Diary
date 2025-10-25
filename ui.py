# ui.py
# -----------------------------------------
# Handles GUI for Personal Diary App (Unified Save Button)
# -----------------------------------------

import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
from tkcalendar import Calendar
from diary import Diary, Entry
from storage import StorageManager
from utils import parse_date, hash_password, verify_password
from errors import DiaryLockedError, EntryNotFoundError


class DiaryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Diary")
        self.root.configure(bg="#333333")

        self.storage = StorageManager()
        self.diary = Diary()
        self.diary.entries = self.storage.load()

        # Initialize password on first run
        self._init_password()

        # -------------------------------
        # UI Layout Setup
        # -------------------------------
        self.left = tk.Frame(root, padx=10, pady=10, bg="#333333")
        self.left.pack(side=tk.LEFT, fill=tk.Y)

        self.right = tk.Frame(root, padx=10, pady=10, bg="#333333")
        self.right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # -------------------------------
        # Left Sidebar (Calendar + List)
        # -------------------------------
        try:
            self.cal = Calendar(self.left)
        except TypeError:
            self.cal = Calendar(self.left)
        self.cal.pack(pady=5)

        tk.Button(self.left, text="View by Date", command=self.view_by_date).pack(pady=5)

        self.listbox = tk.Listbox(self.left, width=30, height=15)
        self.listbox.pack(pady=10)
        self.listbox.bind("<<ListboxSelect>>", self.view_entry)

        # -------------------------------
        # Right Pane (Editor + Search)
        # -------------------------------
        tk.Label(self.right, text="Title:", fg="white", bg="#333333").pack(anchor="w")
        self.title_entry = tk.Entry(self.right, width=50)
        self.title_entry.pack(anchor="w")

        tk.Label(self.right, text="Content:", fg="white", bg="#333333").pack(anchor="w")
        self.content_text = scrolledtext.ScrolledText(self.right, width=60, height=15, bg="#979696", fg="white")
        self.content_text.pack(fill=tk.BOTH, expand=True)

        # Search box
        tk.Label(self.right, text="Search:", fg="white", bg="#333333").pack(anchor="w")
        self.search_box = tk.Entry(self.right, width=20)
        self.search_box.pack(anchor="w", pady=5)

        # -------------------------------
        # Unified Controls
        # -------------------------------
        control_frame = tk.Frame(self.right, bg="#333333")
        control_frame.pack(pady=10)

        tk.Button(control_frame, text="Search", command=self.search_entries).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Save Entry", command=self.save_entry).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Delete", command=self.delete_entry).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Lock", command=self.lock_diary).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Unlock", command=self.unlock_diary).pack(side=tk.LEFT, padx=5)

        # Lock status indicator
        self.lock_status = tk.Label(self.right, text="🔓 Unlocked", fg="green", bg="#333333", font=("Arial", 10, "bold"))
        self.lock_status.pack(anchor="e")

        self.refresh_list()

    # -------------------------------
    # Password Setup
    # -------------------------------
    def _init_password(self):
        """Set up or verify password."""
        try:
            with open("password.txt", "r") as f:
                stored_hash = f.read().strip()
        except FileNotFoundError:
            pw = simpledialog.askstring("Set Password", "Create a password for your diary:", show="*")
            if not pw:
                pw = "1234"
            with open("password.txt", "w") as f:
                f.write(hash_password(pw))
            stored_hash = hash_password(pw)
        self.diary.password_hash = stored_hash

    # -------------------------------
    # Core Functions
    # -------------------------------
    def refresh_list(self, entries=None):
        """Refresh the Listbox with diary entries."""
        self.listbox.delete(0, tk.END)
        for e in (entries or self.diary.entries):
            self.listbox.insert(tk.END, f"{e.date} - {e.title}")

    def save_entry(self):
        """Add or update an entry using a single Save button."""
        title = self.title_entry.get().strip()
        content = self.content_text.get("1.0", tk.END).strip()

        if not title or not content:
            messagebox.showwarning("Error", "Both title and content are required.")
            return

        try:
            # Check if entry already exists
            existing = next((e for e in self.diary.entries if e.title == title), None)
            if existing:
                self.diary.edit_entry(title, content)
                messagebox.showinfo("Updated", f"Entry '{title}' updated successfully.")
            else:
                self.diary.add_entry(Entry(title, content))
                messagebox.showinfo("Added", f"New entry '{title}' added successfully.")

            # Clear fields after saving
            self.title_entry.delete(0, tk.END)
            self.content_text.delete("1.0", tk.END)

            self.refresh_list()
            self.storage.save(self.diary.entries)

        except DiaryLockedError as e:
            messagebox.showerror("Locked", str(e))

    def delete_entry(self):
        """Delete a selected diary entry."""
        try:
            index = self.listbox.curselection()[0]
            title = self.diary.entries[index].title
            self.diary.delete_entry(title)
            self.refresh_list()
            self.storage.save(self.diary.entries)
            messagebox.showinfo("Deleted", f"Entry '{title}' deleted successfully.")
        except (DiaryLockedError, IndexError, EntryNotFoundError) as e:
            messagebox.showerror("Error", str(e))

    def view_entry(self, event):
        """Display selected entry details only if diary is unlocked."""
        try:
            index = self.listbox.curselection()[0]
            entry = self.diary.entries[index]

            # If diary is locked, prevent viewing content
            if self.diary.locked:
                self.title_entry.delete(0, tk.END)
                self.content_text.delete("1.0", tk.END)
                messagebox.showwarning("Locked", "Diary is locked. Unlock to view entry details.")
                return

            # Display entry content normally
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, entry.title)
            self.content_text.delete("1.0", tk.END)
            self.content_text.insert(tk.END, entry.content)

        except IndexError:
            pass
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def view_by_date(self):
        """Filter entries by selected calendar date."""
        date_selected = self.cal.get_date()
        results = [e for e in self.diary.entries if e.date.startswith(date_selected)]
        self.refresh_list(results)

    def search_entries(self):
        """Search entries by keyword or date range."""
        keyword = self.search_box.get().strip()
        start = simpledialog.askstring("Start Date", "Enter start date (YYYY-MM-DD):")
        end = simpledialog.askstring("End Date", "Enter end date (YYYY-MM-DD):")
        try:
            s = parse_date(start) if start else None
            e = parse_date(end) if end else None
            results = self.diary.search(keyword, s, e)
            self.refresh_list(results)
        except ValueError as err:
            messagebox.showerror("Error", str(err))

    # -------------------------------
    # Lock & Unlock
    # -------------------------------
    def lock_diary(self):
        """Lock the diary."""
        self.diary.lock()
        self.lock_status.config(text="🔒 Locked", fg="red")
        messagebox.showinfo("Locked", "Diary is now locked.")

    def unlock_diary(self):
        """Unlock the diary with password."""
        password = simpledialog.askstring("Unlock", "Enter your diary password:", show="*")
        if self.diary.unlock(password, lambda p: verify_password(self.diary.password_hash, p)):
            self.lock_status.config(text="🔓 Unlocked", fg="green")
            messagebox.showinfo("Unlocked", "Diary unlocked successfully!")
        else:
            messagebox.showerror("Error", "Incorrect password.")


# -------------------------------
# Entry Point
# -------------------------------
def start_ui():
    root = tk.Tk()
    app = DiaryApp(root)
    root.mainloop()


# if __name__ == "__main__":
#     start_ui()
