import customtkinter as ctk
from tkinter import messagebox
from auth import signup, login
from dashboard import open_dashboard  # we'll create dashboard.py next

# --- Theme setup ---
ctk.set_appearance_mode("light")  # can switch to "dark"
ctk.set_default_color_theme("blue")

class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Personal Diary Login")
        self.geometry("500x400")
        self.resizable(False, False)

        # --- Frame container ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=20)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # --- Title ---
        self.title_label = ctk.CTkLabel(
            self.main_frame, text="📘 Personal Diary", font=("Helvetica", 22, "bold")
        )
        self.title_label.pack(pady=(20, 10))

        # --- Tabs for Login / Signup ---
        self.tabview = ctk.CTkTabview(self.main_frame, width=350, height=220)
        self.tabview.pack(pady=10)
        self.tab_login = self.tabview.add("Login")
        self.tab_signup = self.tabview.add("Signup")

        # --- LOGIN TAB ---
        self.username_login = ctk.CTkEntry(self.tab_login, placeholder_text="Username")
        self.username_login.pack(pady=10)
        self.password_login = ctk.CTkEntry(self.tab_login, placeholder_text="Password", show="*")
        self.password_login.pack(pady=10)
        self.login_button = ctk.CTkButton(self.tab_login, text="Login", command=self.handle_login)
        self.login_button.pack(pady=10)

        # --- SIGNUP TAB ---
        self.username_signup = ctk.CTkEntry(self.tab_signup, placeholder_text="Username")
        self.username_signup.pack(pady=10)
        self.password_signup = ctk.CTkEntry(self.tab_signup, placeholder_text="Password", show="*")
        self.password_signup.pack(pady=10)
        self.signup_button = ctk.CTkButton(self.tab_signup, text="Sign Up", command=self.handle_signup)
        self.signup_button.pack(pady=10)

        # --- Light/Dark mode toggle ---
        self.switch_var = ctk.StringVar(value="light")
        self.mode_switch = ctk.CTkSwitch(
            self.main_frame,
            text="🌞 / 🌙 Mode",
            variable=self.switch_var,
            onvalue="dark",
            offvalue="light",
            command=self.toggle_mode
        )
        self.mode_switch.pack(pady=15)

    # --- Handlers ---
    def handle_login(self):
        username = self.username_login.get().strip()
        password = self.password_login.get().strip()

        if not username or not password:
            messagebox.showwarning("Error", "Please fill in all fields.")
            return

        success, msg = login(username, password)
        if success:
            messagebox.showinfo("Success", msg)
            self.destroy()
            open_dashboard(username)  # move to dashboard
        else:
            messagebox.showerror("Error", msg)

    def handle_signup(self):
        username = self.username_signup.get().strip()
        password = self.password_signup.get().strip()

        if not username or not password:
            messagebox.showwarning("Error", "Please fill in all fields.")
            return

        success, msg = signup(username, password)
        if success:
            messagebox.showinfo("Success", msg)
        else:
            messagebox.showerror("Error", msg)

    def toggle_mode(self):
        mode = self.switch_var.get()
        ctk.set_appearance_mode(mode)

# --- Run app ---
if __name__ == "__main__":
    app = LoginApp()
    app.mainloop()
