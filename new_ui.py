# ui.py
# -----------------------------------------
# Modern Personal Diary App (CustomTkinter)
# -----------------------------------------
import customtkinter as ctk
from tkinter import messagebox, simpledialog, filedialog
from tkcalendar import Calendar
from fpdf import FPDF
from diary import Diary, Entry
from storage import StorageManager
from utils import parse_date, hash_password, verify_password
from errors import DiaryLockedError, EntryNotFoundError


class DiaryApp:
    def __init__(self, root):
        # -----------------------------------------
        # App setup and theme
        # -----------------------------------------
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = root
        self.root.title("Modern Personal Diary")
        self.root.geometry("950x600")

        # Data and storage
        self.storage = StorageManager()
        self.diary = Diary()
        self.diary.entries = self.storage.load()
        self._init_password()

        # -----------------------------------------
        # Layout setup
        # -----------------------------------------
        self.left_frame = ctk.CTkFrame(self.root, width=280, corner_radius=15, fg_color="#2b2b2b")
        self.left_frame.pack(side="left", fill="y", padx=10, pady=10)

        self.right_frame = ctk.CTkFrame(self.root, corner_radius=15, fg_color="#333333")
        self.right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # -----------------------------------------
        # Calendar & Entries list
        # -----------------------------------------
        self.cal = Calendar(self.left_frame, selectmode="day", date_pattern="yyyy-mm-dd")
        self.cal.pack(pady=10)

        ctk.CTkButton(self.left_frame, text="View by Date", command=self.view_by_date).pack(pady=5)

        self.listbox = ctk.CTkTextbox(self.left_frame, width=260, height=250, corner_radius=10)
        self.listbox.pack(pady=10)
        self.listbox.bind("<ButtonRelease-1>", self.view_entry)

        # -----------------------------------------
        # Right pane - Editor
        # -----------------------------------------
        ctk.CTkLabel(self.right_frame, text="Title:").pack(anchor="w", padx=10, pady=(10, 0))
        self.title_entry = ctk.CTkEntry(self.right_frame, width=400)
        self.title_entry.pack(anchor="w", padx=10)

        ctk.CTkLabel(self.right_frame, text="Content:").pack(anchor="w", padx=10, pady=(10, 0))
        self.content_text = ctk.CTkTextbox(self.right_frame, width=600, height=300, corner_radius=10)
        self.content_text.pack(padx=10, pady=5, fill="both", expand=True)

        # -----------------------------------------
        # Controls
        # -----------------------------------------
        control_frame = ctk.CTkFrame(self.right_frame, fg_color="#3a3a3a", corner_radius=10)
        control_frame.pack(fill="x", pady=10, padx=10)

        self.search_box = ctk.CTkEntry(control_frame, placeholder_text="Search by keyword...")
        self.search_box.pack(side="left", padx=5, pady=5)

        ctk.CTkButton(control_frame, text="Search", command=self.search_entries).pack(side="left", padx=5)
        ctk.CTkButton(control_frame, text="Save Entry", command=self.save_entry).pack(side="left", padx=5)
        ctk.CTkButton(control_frame, text="Delete", command=self.delete_entry).pack(side="left", padx=5)
        ctk.CTkButton(control_frame, text="Lock/Unlock", command=self.toggle_lock).pack(side="left", padx=5)
        ctk.CTkButton(control_frame, text="Download PDF", command=self.download_pdf).pack(side="left", padx=5)

        # Load initial entries
        self.refresh_list()

    # -----------------------------------------
    # Password setup
    # -----------------------------------------
    def _init_password(self):
        """Initialize or set up diary password."""
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

    # -----------------------------------------
    # Core functions
    # -----------------------------------------
    def refresh_list(self, entries=None):
        """Display all diary entries with lock icons."""
        self.listbox.delete("1.0", "end")
        for e in (entries or self.diary.entries):
            icon = "🔒" if e.locked else "🔓"
            self.listbox.insert("end", f"{icon} {e.date} - {e.title}\n")

    def save_entry(self):
        """Add or update an entry."""
        title = self.title_entry.get().strip()
        content = self.content_text.get("1.0", "end").strip()
        if not title or not content:
            messagebox.showwarning("Warning", "Title and content cannot be empty.")
            return
        try:
            existing = next((x for x in self.diary.entries if x.title == title), None)
            if existing:
                existing.content = content
            else:
                self.diary.add_entry(Entry(title, content))
            self.storage.save(self.diary.entries)
            self.refresh_list()
            self.clear_fields()
            messagebox.showinfo("Saved", "Entry saved successfully.")
        except DiaryLockedError as e:
            messagebox.showerror("Locked", str(e))

    def delete_entry(self):
        """Delete selected entry."""
        try:
            index = int(self.listbox.index("@0,0").split('.')[0]) - 1
            entry = self.diary.entries[index]
            self.diary.delete_entry(entry.title)
            self.storage.save(self.diary.entries)
            self.refresh_list()
            self.clear_fields()
            messagebox.showinfo("Deleted", f"'{entry.title}' deleted.")
        except Exception:
            messagebox.showwarning("Error", "Please select an entry to delete.")

    def view_entry(self, event=None):
        """Show entry details when selected."""
        try:
            index = int(self.listbox.index("@0,0").split('.')[0]) - 1
            entry = self.diary.entries[index]
            if entry.locked:
                self.title_entry.delete(0, "end")
                self.content_text.delete("1.0", "end")
                messagebox.showinfo("Locked", f"'{entry.title}' is locked 🔒.")
            else:
                self.title_entry.delete(0, "end")
                self.title_entry.insert(0, entry.title)
                self.content_text.delete("1.0", "end")
                self.content_text.insert("end", entry.content)
        except Exception:
            pass

    def view_by_date(self):
        """Filter entries by selected date."""
        date_selected = self.cal.get_date()
        results = [e for e in self.diary.entries if e.date == date_selected]
        self.refresh_list(results)

    def search_entries(self):
        """Search entries by keyword or date range."""
        keyword = self.search_box.get().strip().lower()
        start = simpledialog.askstring("Start Date", "Enter start date (YYYY-MM-DD):")
        end = simpledialog.askstring("End Date", "Enter end date (YYYY-MM-DD):")
        try:
            s = parse_date(start) if start else None
            e = parse_date(end) if end else None
            results = self.diary.search(keyword, s, e)
            self.refresh_list(results)
        except ValueError as err:
            messagebox.showerror("Error", str(err))

    # -----------------------------------------
    # Lock / Unlock toggle
    # -----------------------------------------
    def toggle_lock(self):
        """Toggle between lock/unlock for selected entry."""
        try:
            index = int(self.listbox.index("@0,0").split('.')[0]) - 1
            entry = self.diary.entries[index]
            if entry.locked:
                password = simpledialog.askstring("Unlock Entry", "Enter password:", show="*")
                if verify_password(self.diary.password_hash, password):
                    entry.unlock()
                    messagebox.showinfo("Unlocked", f"'{entry.title}' is now unlocked.")
                else:
                    messagebox.showerror("Error", "Incorrect password.")
            else:
                entry.lock()
                messagebox.showinfo("Locked", f"'{entry.title}' is now locked.")
            self.storage.save(self.diary.entries)
            self.refresh_list()
        except IndexError:
            messagebox.showwarning("Error", "Please select an entry.")

    # -----------------------------------------
    # PDF download
    # -----------------------------------------
    def download_pdf(self):
        """Download current entry as PDF locally."""
        title = self.title_entry.get().strip()
        content = self.content_text.get("1.0", "end").strip()
        if not title or not content:
            messagebox.showwarning("Warning", "No entry selected or content empty.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")], title="Save PDF As"
        )
        if not file_path:
            return

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, txt=title, ln=True, align="C")
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=content)
        pdf.output(file_path)

        messagebox.showinfo("Download", f"PDF saved to:\n{file_path}")

    # -----------------------------------------
    # Helpers
    # -----------------------------------------
    def clear_fields(self):
        """Clear text fields after actions."""
        self.title_entry.delete(0, "end")
        self.content_text.delete("1.0", "end")


def start_new_ui():
    root = ctk.CTk()
    DiaryApp(root)
    root.mainloop()

