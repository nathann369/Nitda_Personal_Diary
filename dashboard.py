# dashboard.py
# Main CustomTkinter dashboard. Run with: python dashboard.py <username>
import sys
import os
import customtkinter as ctk
from tkinter import messagebox, simpledialog, filedialog
from tkcalendar import Calendar
from fpdf import FPDF
from storage import load_entries, save_entries, ensure_user_file
from utils import parse_date, encrypt_text, decrypt_text
from auth import _load_users, verify_password  # verify_password is in auth.py

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")


def user_arg_or_exit():
    if len(sys.argv) < 2:
        print("Usage: python dashboard.py <username>")
        sys.exit(1)
    return sys.argv[1]


class Dashboard(ctk.CTk):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.title(f"Diary — {username}")
        self.geometry("1000x650")

        ensure_user_file(self.username)
        # load raw entries list (entries are dicts)
        self.entries = load_entries(self.username)

        # UI layout
        self.left_frame = ctk.CTkFrame(self, width=280, corner_radius=12)
        self.left_frame.pack(side="left", fill="y", padx=12, pady=12)

        self.right_frame = ctk.CTkFrame(self, corner_radius=12)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=12, pady=12)

        # Left: calendar + buttons
        self.cal = Calendar(self.left_frame, selectmode="day", date_pattern="yyyy-mm-dd")
        self.cal.pack(pady=(10, 8))

        ctk.CTkButton(self.left_frame, text="Add Entry", command=self.open_add_popup).pack(fill="x", padx=10, pady=6)
        ctk.CTkButton(self.left_frame, text="Edit Entry", command=self.open_edit_popup).pack(fill="x", padx=10, pady=6)
        ctk.CTkButton(self.left_frame, text="Delete Entry", command=self.delete_selected).pack(fill="x", padx=10, pady=6)
        ctk.CTkButton(self.left_frame, text="Lock/Unlock", command=self.lock_toggle_selected).pack(fill="x", padx=10, pady=6)
        ctk.CTkButton(self.left_frame, text="Export (PDF)", command=self.export_selected).pack(fill="x", padx=10, pady=6)
        # ctk.CTkButton(self.left_frame, text="View All Notes", command=self.refresh_list).pack(fill="x", padx=10, pady=6)

        # Right top: search center + refresh + logout
        topbar = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        topbar.pack(fill="x", pady=(4, 8))

        self.search_entry = ctk.CTkEntry(topbar, placeholder_text="Search keyword or YYYY-MM-DD", width=400)
        self.search_entry.pack(pady=6, side="left", padx=(120, 6))
        ctk.CTkButton(topbar, text="Search", command=self.search).pack(side="left", padx=6)
        ctk.CTkButton(topbar, text="Refresh", command=self.refresh_list, fg_color="blue").pack(side="left", padx=6)

        ctk.CTkButton(topbar, text="Logout", command=self.logout, fg_color="red").pack(side="right", padx=10)

        # Entries list (scrollable)
        self.list_container = ctk.CTkScrollableFrame(self.right_frame, height=300, corner_radius=8)
        self.list_container.pack(fill="x", padx=10, pady=6)

        # selected entry display area
        self.display_title = ctk.CTkLabel(self.right_frame, text="", font=("Helvetica", 16, "bold"))
        self.display_title.pack(anchor="w", padx=10, pady=(12, 4))
        self.display_date = ctk.CTkLabel(self.right_frame, text="", font=("Helvetica", 10))
        self.display_date.pack(anchor="w", padx=10)
        self.display_content = ctk.CTkTextbox(self.right_frame, height=200, corner_radius=8)
        self.display_content.pack(fill="both", expand=True, padx=10, pady=8)

        # internals
        # entries are stored as dicts with keys: title, content (plain or encrypted blob), date, locked (bool)
        self.selected_index = None
        self.refresh_list()

    # ---------------- storage helpers ----------------
    def persist(self):
        save_entries(self.username, self.entries)

    # ---------------- UI actions ----------------
    def refresh_list(self, _=None):
        # clear list_container children
        for w in self.list_container.winfo_children():
            w.destroy()

        for i, e in enumerate(self.entries):
            locked = e.get("locked", False)
            title = e.get("title", "")
            date = e.get("date", "")
            icon = "🔒 " if locked else ""
            text = f"{icon}{title} — {date}"
            btn = ctk.CTkButton(self.list_container, text=text, anchor="w",
                                command=lambda idx=i: self.select_entry(idx), fg_color=("#d0e8e2" if not locked else "#ffdede"))
            btn.pack(fill="x", pady=4, padx=6)

        # clear displayed content
        self.clear_display()

    def select_entry(self, idx):
        self.selected_index = idx
        entry = self.entries[idx]
        locked = entry.get("locked", False)
        self.display_title.configure(text=entry.get("title", ""))
        self.display_date.configure(text=entry.get("date", ""))
        self.display_content.configure(state="normal")
        self.display_content.delete("1.0", "end")
        if locked:
            self.display_content.insert("1.0", "(Locked) Unlock to view content.")
        else:
            # content may be plain string or encrypted blob (if locked before)
            content = entry.get("content", "")
            if isinstance(content, dict) and content.get("token"):
                # encrypted blob stored but not locked flag? decrypt required
                self.display_content.insert("1.0", "(Encrypted content)")
            else:
                self.display_content.insert("1.0", content)
        self.display_content.configure(state="disabled")

    def clear_display(self):
        self.selected_index = None
        self.display_title.configure(text="")
        self.display_date.configure(text="")
        self.display_content.configure(state="normal")
        self.display_content.delete("1.0", "end")
        self.display_content.configure(state="disabled")

    # ---------------- Add / Edit popups ----------------
    def open_add_popup(self):
        self._open_editor_popup(mode="add")

    def open_edit_popup(self):
        if self.selected_index is None:
            messagebox.showwarning("Select", "Choose an entry to edit.")
            return
        # if the selected is locked, block edit
        if self.entries[self.selected_index].get("locked"):
            messagebox.showwarning("Locked", "Unlock entry before editing.")
            return
        self._open_editor_popup(mode="edit", index=self.selected_index)

    def _open_editor_popup(self, mode="add", index=None):
        popup = ctk.CTkToplevel(self)
        popup.title("Add Entry" if mode == "add" else "Edit Entry")
        popup.geometry("600x450")
        popup.grab_set()
        popup.focus_force()

        title_entry = ctk.CTkEntry(popup, placeholder_text="Title", width=520)
        title_entry.pack(pady=(12, 8))
        text_box = ctk.CTkTextbox(popup, width=560, height=300, corner_radius=8)
        text_box.pack(pady=6)

        if mode == "edit" and index is not None:
            entry = self.entries[index]
            title_entry.insert(0, entry.get("title", ""))
            # if encrypted, cannot edit (should not happen because open_edit_popup blocked locked)
            text_box.insert("1.0", entry.get("content", ""))

        def do_save():
            title = title_entry.get().strip()
            content = text_box.get("1.0", "end").strip()
            if not title or not content:
                messagebox.showwarning("Missing", "Fill title and content.")
                return
            now = self._today()
            if mode == "add":
                self.entries.insert(0, {"title": title, "content": content, "date": now, "locked": False})
            else:
                self.entries[index]["title"] = title
                self.entries[index]["content"] = content
                self.entries[index]["date"] = now
            self.persist()
            self.refresh_list()
            popup.destroy()

        save_text = "Save" if mode == "add" else "Save Changes"
        ctk.CTkButton(popup, text=save_text, command=do_save).pack(pady=8)

    # ---------------- Delete ----------------
    def delete_selected(self):
        if self.selected_index is None:
            messagebox.showwarning("Select", "Choose an entry to delete.")
            return
        e = self.entries[self.selected_index]
        if e.get("locked"):
            messagebox.showwarning("Locked", "Unlock before deleting.")
            return
        if messagebox.askyesno("Confirm", f"Delete '{e.get('title')}'?"):
            self.entries.pop(self.selected_index)
            self.persist()
            self.refresh_list()

    # ---------------- Lock / Unlock ----------------
    def lock_toggle_selected(self):
        if self.selected_index is None:
            messagebox.showwarning("Select", "Choose an entry to lock/unlock.")
            return
        entry = self.entries[self.selected_index]
        if entry.get("locked"):
            # unlock flow: ask for user's password to derive key and decrypt
            pwd = simpledialog.askstring("Unlock", "Enter your account password:", show="*")
            if not pwd:
                return
            try:
                # attempt decrypt using provided password
                blob = entry.get("content")
                decrypted = decrypt_text(pwd, blob)
                entry["content"] = decrypted
                entry["locked"] = False
                self.persist()
                self.refresh_list()
                messagebox.showinfo("Unlocked", "Entry unlocked.")
            except Exception as exc:
                messagebox.showerror("Error", "Failed to unlock. Wrong password or corrupted data.")
        else:
            # lock flow: ask for password to derive key
            pwd = simpledialog.askstring("Lock", "Enter your account password to lock entry:", show="*")
            if not pwd:
                return
            try:
                encrypted = encrypt_text(pwd, entry.get("content", ""))
                entry["content"] = encrypted
                entry["locked"] = True
                self.persist()
                self.refresh_list()
                self.clear_display()
                messagebox.showinfo("Locked", "Entry locked and encrypted.")
            except Exception as exc:
                messagebox.showerror("Error", f"Failed to lock: {exc}")

    # ---------------- Search ----------------
    def search(self):
        query = self.search_entry.get().strip()
        if not query:
            self.refresh_list()
            return
        results = []
        # date range e.g., 2025-01-01 to 2025-01-31
        if "to" in query:
            parts = query.split("to")
            try:
                s = parse_date(parts[0].strip())
                e = parse_date(parts[1].strip())
                for ent in self.entries:
                    if s <= ent.get("date", "") <= e:
                        results.append(ent)
            except Exception:
                messagebox.showerror("Error", "Invalid date range. Use YYYY-MM-DD to YYYY-MM-DD")
                return
        else:
            # keyword search in title or content (content may be encrypted blob; skip encrypted ones)
            for ent in self.entries:
                title = ent.get("title", "")
                content = ent.get("content", "")
                if isinstance(content, dict):
                    # encrypted — cannot search inside unless unlocked
                    if query.lower() in title.lower():
                        results.append(ent)
                else:
                    if query.lower() in title.lower() or query.lower() in content.lower():
                        results.append(ent)
        # show results (note: results are entries dicts)
        for w in self.list_container.winfo_children():
            w.destroy()
        for i, ent in enumerate(results):
            locked = ent.get("locked", False)
            icon = "🔒 " if locked else ""
            btn = ctk.CTkButton(self.list_container, text=f"{icon}{ent.get('title')} — {ent.get('date')}",
                                anchor="w", command=lambda idx=i: None)
            btn.pack(fill="x", pady=4, padx=6)
        # clear display area
        self.clear_display()

    # ---------------- Export ----------------
    def export_selected(self):
        if self.selected_index is None:
            messagebox.showwarning("Select", "Choose an entry to export.")
            return
        entry = self.entries[self.selected_index]
        if entry.get("locked"):
            messagebox.showwarning("Locked", "Unlock before exporting.")
            return
        # ask for file location
        default_name = f"{entry.get('title','entry').replace(' ', '_')}.pdf"
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=default_name,
                                            filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, entry.get("title", ""), ln=True, align="C")
        pdf.ln(4)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 8, entry.get("content", ""))
        pdf.output(path)
        messagebox.showinfo("Exported", f"Saved PDF to:\n{path}")

    # ---------------- Logout ----------------
    def logout(self):
        if messagebox.askyesno("Logout", "Bye bye! Logout now?"):
            # restart login.py as new process
            python = sys.executable
            self.destroy()
            os.execv(python, [python, "login.py"])

    # ---------------- Utils ----------------
    def _today(self):
        from datetime import date
        return date.today().strftime("%Y-%m-%d")


if __name__ == "__main__":
    username = user_arg_or_exit()
    app = Dashboard(username)
    app.mainloop()
