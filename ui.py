# ui.py
# -----------------------------------------
# Handles GUI for Personal Diary App
# -----------------------------------------
from pdf_exporter import export_entry_to_pdf
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
        self.root.geometry("900x600")
        self.root.configure(bg="#333333")  # Dark background

        self.storage = StorageManager()
        self.diary = Diary()
        self.diary.entries = self.storage.load()

        self._init_password()

        # -------------------------------
        # UI Layout
        # -------------------------------
        self.left = tk.Frame(root, padx=10, pady=10, bg="#333333")
        self.left.pack(side=tk.LEFT, fill=tk.Y)

        self.right = tk.Frame(root, padx=10, pady=10, bg="#333333")
        self.right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)


        # ---------- Left Side (Calendar + Search) ----------
        self.left = tk.Frame(root, bg="#333333", width=300)
        self.left.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(self.left, text="Calendar", bg="#333333", fg="white", font=("Arial", 12, "bold")).pack(pady=5)
        self.cal = Calendar(self.left, date_pattern="yyyy-mm-dd")
        self.cal.pack(pady=5)
       # Search Box
        # Search Box 
        tk.Label(self.left, text="Search", bg="#333333", fg="white", font=("Arial", 12, "bold")).pack(pady=5)

        self.search_box = tk.Entry(self.left, width=30)
        self.search_box.pack(pady=5)

        def search_entries():
            """Search entries by keyword."""
            keyword = self.search_box.get().strip()
            if not keyword:
                messagebox.showinfo("Results", "Please enter a keyword.")
                return

            # Call the Diary class's search() method from diary.py
            results = self.diary.search(keyword)

            if results:
                text = "\n\n".join([f"{r['date']} - {r['title']}\n{r['content']}" for r in results])
                messagebox.showinfo("Results", text)
            else:
                messagebox.showinfo("Results", "No entries found.")

        tk.Button(self.left, text="Search", command=search_entries, font=("Arial", 10, "bold")).pack(pady=5)


        # Results List
        self.listbox = tk.Listbox(self.left, width=40, height=15)
        self.listbox.pack(pady=10)
        self.listbox.bind("<<ListboxSelect>>", self.view_entry)

        # Right Pane
        tk.Label(self.right, text="Title:", bg="#333333", fg="white", font=("Arial", 12, "bold")).pack(anchor="w")
        self.title_entry = tk.Entry(self.right, width=50)
        self.title_entry.pack(anchor="w")

        tk.Label(self.right, text="Content:", bg="#333333", fg="white", font=("Arial", 12, "bold")).pack(anchor="w")
        self.content_text = scrolledtext.ScrolledText(self.right, height=15, width=70)
        self.content_text.pack(fill=tk.BOTH, expand=True)

       

        # ---------- Buttons ----------
        btn_frame = tk.Frame(self.right, bg="#2b2b2b")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Save Entry", command=self.save_entry, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete", command=self.delete_entry, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Lock/Unlock", command=self.toggle_lock, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Download PDF", command=self.download_pdf, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        

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
    # Helper Functions
    # -------------------------------
    def clear_fields(self):
        """Clear the title and content fields."""
        self.title_entry.delete(0, tk.END)
        self.content_text.delete("1.0", tk.END)

    def refresh_list(self, entries=None):
        """Refresh the entry list with per-entry lock icons."""
        self.listbox.delete(0, tk.END)
        for e in (entries or self.diary.entries):
            lock_icon = "🔒 " if e.locked else ""
            self.listbox.insert(tk.END, f"{lock_icon}{e.date} - {e.title}")


    # -------------------------------
    # Diary Actions
    # -------------------------------
    def save_entry(self):
        """Add or update an entry with one button."""
        title = self.title_entry.get().strip()
        content = self.content_text.get("1.0", tk.END).strip()

        if not title or not content:
            messagebox.showwarning("Error", "Both title and content required.")
            return

        try:
            # Check if entry with same title exists
            existing = next((e for e in self.diary.entries if e.title == title), None)
            if existing:
                self.diary.edit_entry(title, content)
                messagebox.showinfo("Updated", "Entry updated successfully.")
            else:
                self.diary.add_entry(Entry(title, content))
                messagebox.showinfo("Added", "New entry added.")
            self.storage.save(self.diary.entries)
            self.refresh_list()
            self.clear_fields()
        except DiaryLockedError:
            messagebox.showerror("Locked", "Cannot modify entries while diary is locked.")

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

    def delete_entry(self):
        """Delete the selected entry."""
        try:
            index = self.listbox.curselection()[0]
            title = self.diary.entries[index].title
            self.diary.delete_entry(title)
            self.storage.save(self.diary.entries)
            self.refresh_list()
            self.clear_fields()
            messagebox.showinfo("Deleted", "Entry removed successfully.")
        except (DiaryLockedError, IndexError, EntryNotFoundError) as e:
            messagebox.showerror("Error", str(e))

    def view_entry(self, event):
        """Display entry in editor pane if not locked."""
        try:
            index = self.listbox.curselection()[0]
            e = self.diary.entries[index]
            if e.locked:
                self.clear_fields()
                messagebox.showwarning("Locked", f"'{e.title}' is locked.")
                return
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, e.title)
            self.content_text.delete("1.0", tk.END)
            self.content_text.insert(tk.END, e.content)
        except IndexError:
            pass


    def view_by_date(self):
        date_selected = self.cal.get_date()
        results = [e for e in self.diary.entries if e.date.startswith(date_selected)]
        self.refresh_list(results)

    def search_entries(self):
        """Search by keyword or date range."""
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
    # Lock / Unlock
    # -------------------------------
  
    # def lock_diary(self):
    #     """Lock the selected entry."""
    #     try:
    #         index = self.listbox.curselection()[0]
    #         entry = self.diary.entries[index]
    #         entry.lock()
    #         self.refresh_list()
    #         messagebox.showinfo("Locked", f"'{entry.title}' has been locked.")
    #     except IndexError:
    #         messagebox.showwarning("Error", "Please select an entry to lock.")

    # def unlock_diary(self):
    #     """Unlock the selected entry with password verification."""
    #     try:
    #         index = self.listbox.curselection()[0]
    #         entry = self.diary.entries[index]
    #         password = simpledialog.askstring("Unlock Entry", "Enter your diary password:", show="*")
    #         if not password:
    #             return
    #         if verify_password(self.diary.password_hash, password):
    #             entry.unlock()
    #             self.refresh_list()
    #             messagebox.showinfo("Unlocked", f"'{entry.title}' has been unlocked.")
    #         else:
    #             messagebox.showerror("Error", "Incorrect password.")
    #     except IndexError:
    #         messagebox.showwarning("Error", "Please select an entry to unlock.")

    def toggle_lock(self):
        """
        Toggle lock/unlock for the selected diary entry.
        - Lock instantly with no password.
        - Unlock requires password verification.
        """
        try:
            index = self.listbox.curselection()[0]
            entry = self.diary.entries[index]

            # 🔒 If entry is currently locked → ask for password to unlock
            if entry.locked:
                password = simpledialog.askstring(
                    "Unlock Entry", "Enter your diary password:", show="*"
                )
                if not password:
                    return  # user canceled
                if verify_password(self.diary.password_hash, password):
                    entry.unlock()
                    self.refresh_list()
                    messagebox.showinfo("Unlocked", f"'{entry.title}' has been unlocked.")
                else:
                    messagebox.showerror("Error", "Incorrect password. Entry remains locked.")

            # 🔓 If entry is unlocked → lock instantly
            else:
                entry.lock()
                self.refresh_list()
                messagebox.showinfo("Locked", f"'{entry.title}' has been locked.")

        except IndexError:
            messagebox.showwarning("Error", "Please select an entry to lock or unlock.")


def start_ui():
    root = tk.Tk()
    app = DiaryApp(root)
    root.mainloop()
