# login.py
# Login / Signup UI. On successful login it launches dashboard.py <username>
import os
import subprocess
import sys
import customtkinter as ctk
from tkinter import messagebox
from auth import signup, login
from storage import ensure_user_file

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")  # friendly teal-ish


class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Diary — Login / Sign Up")
        self.geometry("480x420")
        self.resizable(False, False)

        container = ctk.CTkFrame(self, corner_radius=12)
        container.pack(padx=20, pady=20, fill="both", expand=True)

        title = ctk.CTkLabel(container, text="Personal Diary", font=("Helvetica", 20, "bold"))
        title.pack(pady=(10, 10))

        self.tabview = ctk.CTkTabview(container, width=380, height=220)
        self.tabview.pack(pady=10)
        self.login_tab = self.tabview.add("Login")
        self.signup_tab = self.tabview.add("Sign Up")

        # Login tab
        self.login_user = ctk.CTkEntry(self.login_tab, placeholder_text="Username")
        self.login_user.pack(pady=8)
        self.login_pass = ctk.CTkEntry(self.login_tab, placeholder_text="Password", show="*")
        self.login_pass.pack(pady=8)
        ctk.CTkButton(self.login_tab, text="Login", command=self.handle_login).pack(pady=12)

        # Signup tab
        self.su_user = ctk.CTkEntry(self.signup_tab, placeholder_text="Choose a username")
        self.su_user.pack(pady=8)
        self.su_pass = ctk.CTkEntry(self.signup_tab, placeholder_text="Create a password", show="*")
        self.su_pass.pack(pady=8)
        self.su_pass2 = ctk.CTkEntry(self.signup_tab, placeholder_text="Confirm password", show="*")
        self.su_pass2.pack(pady=8)
        ctk.CTkButton(self.signup_tab, text="Sign Up", command=self.handle_signup).pack(pady=12)

        # Mode switch
        # self.mode_switch = ctk.CTkSwitch(container, text="Dark Mode", command=self.toggle_mode)
        # self.mode_switch.pack(pady=(10, 0))

    def toggle_mode(self):
        mode = "dark" if self.mode_switch.get() else "light"
        ctk.set_appearance_mode(mode)

    def handle_signup(self):
        user = self.su_user.get().strip()
        password = self.su_pass.get().strip()
        confirm_password = self.su_pass2.get().strip()
        if not user or not password or not confirm_password:
            messagebox.showwarning("Missing", "Fill all fields.")
            return
        if password != confirm_password:
            messagebox.showerror("Mismatch", "Passwords do not match.")
            return
        ok, msg = signup(user, password)
        if ok:
            ensure_user_file(user)
            # messagebox.showinfo("Success", msg)
            # Optionally switch to login tab
            self.tabview.set("Login")
        else:
            messagebox.showerror("Error", msg)

    def handle_login(self):
        user = self.login_user.get().strip()
        password = self.login_pass.get().strip()
        if not user or not password:
            messagebox.showwarning("Missing", "Fill all fields.")
            return
        ok, msg = login(user, password)
        if ok:
            ensure_user_file(user)
            # messagebox.showinfo("Welcome", msg)
            # Launch dashboard as new process, pass username
            python = sys.executable
            # close window first
            self.destroy()
            # Launch dashboard script (dashboard.py) with username arg
            subprocess.Popen([python, "dashboard.py", user])
        else:
            messagebox.showerror("Error", msg)


if __name__ == "__main__":
    app = LoginWindow()
    app.mainloop()
