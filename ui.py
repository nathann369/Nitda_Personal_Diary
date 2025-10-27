import tkinter as tk
from tkinter import messagebox, simpledialog
from tkcalendar import Calendar
from diary import Diary, Entry
from storage import save_entries, load_entries
from pdf_exporter import export_entry_to_pdf
from security import verify_password

def ask_password_or_exit():
    pw = simpledialog.askstring('Diary Password', 'Enter diary password (first-time will create it):', show='*')
    if pw is None:
        return False, None
    ok = verify_password(pw)
    return ok, pw

class DiaryApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Diary - Simple')
        self.root.geometry('820x600')
        self.root.configure(bg='white')

        self.diary = Diary()
        data = load_entries()
        if data:
            self.diary.load_from_list_of_dicts(data)
        else:
            sample = Entry.create('Welcome', 'This is a sample note. Use Add New to create entries.', None)
            self.diary.add(sample)
            save_entries(self.diary.to_list_of_dicts())

        top = tk.Frame(root, bg='white')
        top.pack(pady=8)

        self.cal = Calendar(top, selectmode='day', date_pattern='yyyy-mm-dd')
        self.cal.pack(side=tk.LEFT, padx=8)
        self.cal.bind("<<CalendarSelected>>", lambda e: self.view_by_date())

        search_frame = tk.Frame(top, bg='white')
        search_frame.pack(side=tk.LEFT, padx=12)
        tk.Label(search_frame, text='Search Title:', bg='white').pack(anchor='w')
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(pady=4)
        tk.Button(search_frame, text='Search', width=12, command=self.search_by_title).pack()

        btns = tk.Frame(top, bg='white')
        btns.pack(side=tk.LEFT, padx=12)
        tk.Button(btns, text='Add New', width=14, command=self.add_new).pack(pady=3)
        tk.Button(btns, text='Edit Selected', width=14, command=self.edit_selected).pack(pady=3)
        tk.Button(btns, text='Delete Selected', width=14, command=self.delete_selected).pack(pady=3)
        tk.Button(btns, text='Lock/Unlock', width=14, command=self.toggle_lock).pack(pady=3)
        tk.Button(btns, text='Export PDF', width=14, command=self.export_pdf).pack(pady=3)
        tk.Button(btns, text='Show All', width=14, command=self.show_all).pack(pady=3)

        # self.listbox = tk.Listbox(root, width=110, height=22)
        # self.listbox.pack(pady=10)

                # Create main frame (split view)
        main_frame = tk.Frame(root, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Left: list of entries
        left_frame = tk.Frame(main_frame, bg='white')
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)

        self.listbox = tk.Listbox(left_frame, width=45, height=22)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y)
        self.listbox.bind("<<ListboxSelect>>", self.show_or_hide_details)

        scrollbar = tk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        # Right: details view
        self.details_frame = tk.Frame(main_frame, bg='#f8f8f8', relief=tk.SUNKEN, bd=1)
        self.details_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        self.details_visible = False
        self.current_detail_index = None

        # Inside the details frame
        self.details_title = tk.Label(self.details_frame, text='', font=('Arial', 14, 'bold'), bg='#f8f8f8', anchor='w', justify='left', wraplength=350)
        self.details_title.pack(anchor='w', pady=(10, 5), padx=10)

        self.details_content = tk.Text(self.details_frame, wrap='word', bg='#fdfdfd', width=60, height=22)
        self.details_content.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        self.details_content.config(state='disabled')

        # Initially hide the details view
        self.details_frame.pack_forget()


        self.refresh_list()


    def show_or_hide_details(self, event):
        try:
            index = self.listbox.curselection()[0]
        except IndexError:
            return

        # If the same entry is clicked again, hide the detail panel
        if self.details_visible and self.current_detail_index == index:
            self.details_frame.pack_forget()
            self.details_visible = False
            self.current_detail_index = None
            return

        entry = self.diary.entries[index]
        self.current_detail_index = index
        self.details_visible = True

        # Update the detail panel
        self.details_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        self.details_title.config(text=f"{entry.date} - {entry.title}")
        self.details_content.config(state='normal')
        self.details_content.delete('1.0', tk.END)
        if entry.locked:
            self.details_content.insert('1.0', '[Locked] Unlock to view content.')
        else:
            self.details_content.insert('1.0', entry.content)
        self.details_content.config(state='disabled')

    def refresh_list(self, entries=None):
        self.listbox.delete(0, tk.END)
        entries = entries if entries is not None else self.diary.entries
        for e in entries:
            icon = '🔒 ' if e.locked else ''
            self.listbox.insert(tk.END, f"{icon}{e.date} - {e.title}")

    def get_selected(self):
        try:
            idx = self.listbox.curselection()[0]
            return self.diary.entries[idx]
        except IndexError:
            messagebox.showwarning('No selection', 'Please select an entry first.')
            return None

    def add_new(self):
        win = tk.Toplevel(self.root)
        win.title('Add New Entry')
        win.geometry('500x450')

        tk.Label(win, text='Title:').pack(anchor='w', padx=8, pady=4)
        title = tk.Entry(win, width=60)
        title.pack(padx=8)

        tk.Label(win, text='Content:').pack(anchor='w', padx=8, pady=4)
        content = tk.Text(win, width=60, height=18)
        content.pack(padx=8)

        def save():
            t = title.get().strip()
            c = content.get('1.0', tk.END).strip()
            if not t or not c:
                messagebox.showwarning('Missing', 'Both title and content are required.')
                return
            entry = Entry.create(t, c, date=self.cal.get_date())
            self.diary.add(entry)
            save_entries(self.diary.to_list_of_dicts())
            self.refresh_list()
            win.destroy()
            messagebox.showinfo('Saved', 'Entry added successfully.')

        tk.Button(win, text='Save', command=save).pack(pady=8)

    def edit_selected(self):
        entry = self.get_selected()
        if not entry:
            return
        if entry.locked:
            messagebox.showwarning('Locked', 'Unlock required to edit')
            return
        win = tk.Toplevel(self.root)
        win.title('Edit Entry')
        win.geometry('500x450')

        tk.Label(win, text='Title:').pack(anchor='w', padx=8, pady=4)
        title = tk.Entry(win, width=60)
        title.insert(0, entry.title)
        title.pack(padx=8)

        tk.Label(win, text='Content:').pack(anchor='w', padx=8, pady=4)
        content = tk.Text(win, width=60, height=18)
        content.insert('1.0', entry.content)
        content.pack(padx=8)

        def save():
            entry.title = title.get().strip()
            entry.content = content.get('1.0', tk.END).strip()
            save_entries(self.diary.to_list_of_dicts())
            self.refresh_list()
            win.destroy()
            messagebox.showinfo('Updated', 'Entry updated successfully.')

        tk.Button(win, text='Save Changes', command=save).pack(pady=8)

    def delete_selected(self):
        entry = self.get_selected()
        if not entry:
            return
        if entry.locked:
            messagebox.showwarning('Locked', 'Unlock required to delete')
            return
        if messagebox.askyesno('Confirm', f"Delete '{entry.title}'?"):
            self.diary.entries.remove(entry)
            save_entries(self.diary.to_list_of_dicts())
            self.refresh_list()
            messagebox.showinfo('Deleted', 'Entry deleted.')

    def toggle_lock(self):
        entry = self.get_selected()
        if not entry:
            return
        if entry.locked:
            pw = simpledialog.askstring('Password', 'Enter diary password:', show='*')
            if pw is None:
                return
            if verify_password(pw):
                entry.locked = False
                save_entries(self.diary.to_list_of_dicts())
                self.refresh_list()
                messagebox.showinfo('Unlocked', 'Entry unlocked.')
            else:
                messagebox.showerror('Wrong', 'Incorrect password.')
        else:
            entry.locked = True
            save_entries(self.diary.to_list_of_dicts())
            self.refresh_list()
            messagebox.showinfo('Locked', 'Entry locked.')

    def export_pdf(self):
        entry = self.get_selected()
        if not entry:
            return
        if entry.locked:
            messagebox.showwarning('Locked', 'Unlock required to export')
            return
        try:
            filename = export_entry_to_pdf(entry)
            messagebox.showinfo('Exported', f'Saved to {filename}')
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def search_by_title(self):
        q = self.search_var.get().strip().lower()
        if not q:
            messagebox.showinfo('Search', 'Enter a title to search for.')
            return
        results = [e for e in self.diary.entries if q in e.title.lower()]
        if results:
            self.refresh_list(results)
        else:
            messagebox.showinfo('Search', 'No entries found with that title.')

    def view_by_date(self):
        selected = self.cal.get_date()
        filtered = [e for e in self.diary.entries if e.date == selected]
        self.refresh_list(filtered)

    def show_all(self):
        self.refresh_list()

def start_ui():
    root = tk.Tk()
    root.withdraw()  # hide while password prompt appears
    ok, pw = ask_password_or_exit()
    if not ok:
        return
    root.deiconify()
    app = DiaryApp(root)
    root.mainloop()
