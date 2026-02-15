"""Login view with authentication options"""
import customtkinter as ctk
from ui.styles import ThemeManager, FONTS, RADIUS, SPACING
from ui.components.buttons import PrimaryButton, OutlineButton
from ui.components.inputs import StyledEntry, StyledLabel, FormField


class LoginView(ctk.CTkFrame):
    """Login screen with Google, Microsoft, SSO, and email options"""

    def __init__(self, parent, on_login_success=None):
        colors = ThemeManager.get_colors()
        super().__init__(parent, fg_color=colors["bg"], corner_radius=0)

        self.on_login_success = on_login_success
        self.show_email_form = False
        self.is_signup = False
        self.is_loading = False
        self.loading_provider = None

        self._build_ui()

    def _build_ui(self):
        """Build the login UI"""
        colors = ThemeManager.get_colors()

        # Center container
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Card
        self.card = ctk.CTkFrame(
            self.center_frame,
            fg_color=colors["card"],
            corner_radius=RADIUS["xl"],
            border_width=1,
            border_color=colors["border"],
            width=420,
        )
        self.card.pack(padx=SPACING["xl"], pady=SPACING["xl"])

        # Content container
        self.content = ctk.CTkFrame(self.card, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=SPACING["xl"], pady=SPACING["xl"])

        self._show_main_options()

    def _clear_content(self):
        """Clear all widgets from content frame"""
        for widget in self.content.winfo_children():
            widget.destroy()

    def _show_main_options(self):
        """Show main login options"""
        self._clear_content()
        colors = ThemeManager.get_colors()

        # Header
        StyledLabel(
            self.content,
            text="Personal Assistant",
            variant="heading_lg"
        ).pack(pady=(0, SPACING["xs"]))

        StyledLabel(
            self.content,
            text="Sign in to access your meetings, journal, and AI insights",
            variant="caption"
        ).pack(pady=(0, SPACING["xl"]))

        # Google button
        google_btn = OutlineButton(
            self.content,
            text="     Continue with Google",
            command=lambda: self._handle_provider_login("google"),
            height=44,
        )
        google_btn.pack(fill="x", pady=SPACING["xs"])

        # Microsoft button
        microsoft_btn = OutlineButton(
            self.content,
            text="     Continue with Microsoft",
            command=lambda: self._handle_provider_login("microsoft"),
            height=44,
        )
        microsoft_btn.pack(fill="x", pady=SPACING["xs"])

        # SSO button
        sso_btn = OutlineButton(
            self.content,
            text="     Continue with SSO",
            command=lambda: self._handle_provider_login("sso"),
            height=44,
        )
        sso_btn.pack(fill="x", pady=SPACING["xs"])

        # Divider
        divider_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        divider_frame.pack(fill="x", pady=SPACING["lg"])

        ctk.CTkFrame(
            divider_frame,
            height=1,
            fg_color=colors["border"]
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            divider_frame,
            text="  Or  ",
            font=FONTS["caption"],
            text_color=colors["text_muted"],
            fg_color=colors["card"]
        ).pack(side="left")

        ctk.CTkFrame(
            divider_frame,
            height=1,
            fg_color=colors["border"]
        ).pack(side="left", fill="x", expand=True)

        # Email button
        email_btn = OutlineButton(
            self.content,
            text="     Continue with Email",
            command=self._show_email_form,
            height=44,
        )
        email_btn.pack(fill="x", pady=SPACING["xs"])

        # Terms
        StyledLabel(
            self.content,
            text="By continuing, you agree to our Terms of Service and Privacy Policy",
            variant="caption"
        ).pack(pady=(SPACING["lg"], 0))

    def _show_email_form(self):
        """Show email/password login form"""
        self._clear_content()
        colors = ThemeManager.get_colors()

        # Header
        StyledLabel(
            self.content,
            text="Sign Up" if self.is_signup else "Sign In",
            variant="heading_lg"
        ).pack(pady=(0, SPACING["xl"]))

        # Email field
        self.email_field = FormField(
            self.content,
            label="Email",
            placeholder="you@example.com",
            input_type="text"
        )
        self.email_field.pack(fill="x", pady=SPACING["sm"])

        # Password field
        self.password_field = FormField(
            self.content,
            label="Password",
            placeholder="Enter your password",
            input_type="password"
        )
        self.password_field.pack(fill="x", pady=SPACING["sm"])

        # Submit button
        submit_text = "Create Account" if self.is_signup else "Sign In"
        self.submit_btn = PrimaryButton(
            self.content,
            text=submit_text,
            command=self._handle_email_login,
            height=44,
        )
        self.submit_btn.pack(fill="x", pady=(SPACING["md"], SPACING["sm"]))

        # Toggle signup/signin
        toggle_text = "Already have an account? Sign in" if self.is_signup else "Don't have an account? Sign up"
        toggle_btn = ctk.CTkButton(
            self.content,
            text=toggle_text,
            fg_color="transparent",
            hover_color=colors["secondary"],
            text_color=colors["accent"],
            font=FONTS["caption"],
            command=self._toggle_signup
        )
        toggle_btn.pack(pady=SPACING["xs"])

        # Back button
        back_btn = ctk.CTkButton(
            self.content,
            text="← Back to all sign in options",
            fg_color="transparent",
            hover_color=colors["secondary"],
            text_color=colors["text_muted"],
            font=FONTS["caption"],
            command=self._show_main_options
        )
        back_btn.pack(pady=SPACING["sm"])

        # Terms
        StyledLabel(
            self.content,
            text="By continuing, you agree to our Terms of Service and Privacy Policy",
            variant="caption"
        ).pack(pady=(SPACING["md"], 0))

    def _show_loading_screen(self, provider):
        """Show loading screen during authentication"""
        self._clear_content()
        colors = ThemeManager.get_colors()

        provider_names = {
            "google": "Google",
            "microsoft": "Microsoft",
            "sso": "SSO",
            "email": "Email"
        }
        provider_name = provider_names.get(provider, provider)

        # Loading spinner (using text animation)
        self.loading_label = ctk.CTkLabel(
            self.content,
            text="⟳",
            font=("Arial", 48),
            text_color=colors["accent"]
        )
        self.loading_label.pack(pady=SPACING["xl"])

        # Animate the spinner
        self._animate_spinner()

        StyledLabel(
            self.content,
            text="Signing you in...",
            variant="heading_sm"
        ).pack(pady=SPACING["sm"])

        StyledLabel(
            self.content,
            text=f"Authenticating with {provider_name}",
            variant="caption"
        ).pack(pady=SPACING["xs"])

        # Status indicators
        status_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        status_frame.pack(pady=SPACING["xl"])

        steps = [
            ("🟢", "Verifying credentials"),
            ("🔵", "Establishing secure connection"),
            ("🟣", "Loading your workspace"),
        ]

        for dot, text in steps:
            step_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
            step_frame.pack(pady=SPACING["xs"])

            ctk.CTkLabel(
                step_frame,
                text=dot,
                font=FONTS["caption"],
            ).pack(side="left", padx=SPACING["xs"])

            ctk.CTkLabel(
                step_frame,
                text=text,
                font=FONTS["caption"],
                text_color=colors["text_muted"]
            ).pack(side="left")

    def _animate_spinner(self):
        """Animate the loading spinner"""
        if not self.is_loading:
            return

        if hasattr(self, 'loading_label') and self.loading_label.winfo_exists():
            current = self.loading_label.cget("text")
            frames = ["⟳", "↻", "⟳", "↺"]
            try:
                idx = frames.index(current)
                next_idx = (idx + 1) % len(frames)
            except ValueError:
                next_idx = 0

            self.loading_label.configure(text=frames[next_idx])
            self.after(200, self._animate_spinner)

    def _toggle_signup(self):
        """Toggle between signup and signin mode"""
        self.is_signup = not self.is_signup
        self._show_email_form()

    def _handle_provider_login(self, provider):
        """Handle OAuth provider login"""
        self.is_loading = True
        self.loading_provider = provider
        self._show_loading_screen(provider)

        # Simulate login delay
        self.after(2500, lambda: self._complete_login(provider))

    def _handle_email_login(self):
        """Handle email/password login"""
        email = self.email_field.get()
        password = self.password_field.input.get()

        if not email or not password:
            from ui.components.toast import ToastManager
            ToastManager.error("Please enter both email and password")
            return

        self.is_loading = True
        self.loading_provider = "email"
        self._show_loading_screen("email")

        # Simulate login delay
        self.after(2000, lambda: self._complete_login("email", email))

    def _complete_login(self, provider, email=None):
        """Complete the login process"""
        self.is_loading = False

        # Create session data
        session_data = {
            "provider": provider,
            "email": email or f"user@{provider}.com",
            "logged_in": True,
        }

        # Notify parent
        if self.on_login_success:
            self.on_login_success(session_data)


class LoadingSpinner(ctk.CTkFrame):
    """Animated loading spinner"""

    def __init__(self, parent, size=48, **kwargs):
        colors = ThemeManager.get_colors()
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.label = ctk.CTkLabel(
            self,
            text="⟳",
            font=("Arial", size),
            text_color=colors["accent"]
        )
        self.label.pack()

        self._animating = True
        self._animate()

    def _animate(self):
        if not self._animating:
            return

        current = self.label.cget("text")
        frames = ["⟳", "↻", "⟳", "↺"]
        try:
            idx = frames.index(current)
            next_idx = (idx + 1) % len(frames)
        except ValueError:
            next_idx = 0

        self.label.configure(text=frames[next_idx])
        self.after(150, self._animate)

    def stop(self):
        self._animating = False
