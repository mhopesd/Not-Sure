"""Settings view with theme toggle and configuration options"""
import customtkinter as ctk
from ui.styles import ThemeManager, FONTS, RADIUS, SPACING
from ui.components.buttons import PrimaryButton, OutlineButton, DestructiveButton
from ui.components.inputs import StyledEntry, StyledLabel, StyledTextbox, PasswordEntry, FormField
from ui.components.badges import Badge
from secure_store import secure_store


class SettingsView(ctk.CTkFrame):
    """Settings panel with appearance, LLM configuration, and account options"""

    def __init__(self, parent, on_theme_change=None, on_logout=None, backend=None):
        colors = ThemeManager.get_colors()
        super().__init__(parent, fg_color=colors["bg"], corner_radius=0)

        self.on_theme_change = on_theme_change
        self.on_logout = on_logout
        self.backend = backend

        self._build_ui()

    def _build_ui(self):
        """Build the settings interface"""
        colors = ThemeManager.get_colors()

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SPACING["xl"], pady=(SPACING["xl"], SPACING["md"]))

        StyledLabel(
            header,
            text="Settings",
            variant="heading"
        ).pack(anchor="w")

        StyledLabel(
            header,
            text="Customize your experience and manage your account",
            variant="caption"
        ).pack(anchor="w", pady=(SPACING["xs"], 0))

        # Scrollable content
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=SPACING["xl"], pady=(0, SPACING["xl"]))

        # Appearance section
        self._create_appearance_section()

        # LLM Configuration section
        self._create_llm_section()

        # Calendar Integration section (placeholder)
        self._create_calendar_section()

        # Meeting Coach section
        self._create_coach_section()

        # About section
        self._create_about_section()

        # Account section
        self._create_account_section()

    def _create_section_card(self, title, subtitle=None):
        """Create a settings section card"""
        colors = ThemeManager.get_colors()

        card = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=colors["card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=colors["border"]
        )
        card.pack(fill="x", pady=SPACING["sm"])

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=SPACING["lg"], pady=SPACING["lg"])

        # Section title
        StyledLabel(
            content,
            text=title,
            variant="subheading"
        ).pack(anchor="w")

        if subtitle:
            StyledLabel(
                content,
                text=subtitle,
                variant="caption"
            ).pack(anchor="w", pady=(SPACING["xs"], 0))

        return content

    def _create_appearance_section(self):
        """Create appearance settings section"""
        colors = ThemeManager.get_colors()

        content = self._create_section_card(
            "Appearance",
            "Customize the look and feel of the application"
        )

        # Theme toggle row
        theme_row = ctk.CTkFrame(content, fg_color="transparent")
        theme_row.pack(fill="x", pady=(SPACING["md"], 0))

        StyledLabel(
            theme_row,
            text="Theme",
            variant="body_medium"
        ).pack(side="left")

        # Theme toggle buttons
        toggle_frame = ctk.CTkFrame(theme_row, fg_color="transparent")
        toggle_frame.pack(side="right")

        current_theme = ThemeManager.get_theme()

        self.light_btn = ctk.CTkButton(
            toggle_frame,
            text="Light",
            width=80,
            height=32,
            corner_radius=RADIUS["md"],
            fg_color=colors["primary"] if current_theme == "light" else "transparent",
            text_color=colors["primary_fg"] if current_theme == "light" else colors["text_secondary"],
            hover_color=colors["secondary"],
            border_width=1,
            border_color=colors["border"],
            font=FONTS["body_sm"],
            command=lambda: self._set_theme("light")
        )
        self.light_btn.pack(side="left", padx=(0, SPACING["xs"]))

        self.dark_btn = ctk.CTkButton(
            toggle_frame,
            text="Dark",
            width=80,
            height=32,
            corner_radius=RADIUS["md"],
            fg_color=colors["primary"] if current_theme == "dark" else "transparent",
            text_color=colors["primary_fg"] if current_theme == "dark" else colors["text_secondary"],
            hover_color=colors["secondary"],
            border_width=1,
            border_color=colors["border"],
            font=FONTS["body_sm"],
            command=lambda: self._set_theme("dark")
        )
        self.dark_btn.pack(side="left")

    def _create_llm_section(self):
        """Create LLM provider configuration section"""
        colors = ThemeManager.get_colors()

        content = self._create_section_card(
            "AI Provider",
            "Configure your AI model for meeting analysis and journal insights"
        )

        # Provider selection
        provider_row = ctk.CTkFrame(content, fg_color="transparent")
        provider_row.pack(fill="x", pady=(SPACING["md"], SPACING["sm"]))

        StyledLabel(
            provider_row,
            text="Provider",
            variant="label"
        ).pack(anchor="w", pady=(0, SPACING["xs"]))

        # Get current provider from backend if available
        current_provider = "Google Gemini"
        if self.backend:
            config = getattr(self.backend, 'config', None)
            if config:
                llm = config.get('Settings', 'llm_provider', fallback='gemini')
                provider_map = {
                    'gemini': 'Google Gemini',
                    'openai': 'OpenAI',
                    'anthropic': 'Anthropic Claude',
                    'ollama': 'Ollama (Local)'
                }
                current_provider = provider_map.get(llm, 'Google Gemini')

        self.provider_dropdown = ctk.CTkOptionMenu(
            provider_row,
            values=["Google Gemini", "OpenAI", "Anthropic Claude", "Ollama (Local)"],
            fg_color=colors["bg"],
            button_color=colors["secondary"],
            button_hover_color=colors["border"],
            dropdown_fg_color=colors["card"],
            dropdown_hover_color=colors["secondary"],
            text_color=colors["text_primary"],
            font=FONTS["body"],
            corner_radius=RADIUS["md"],
            width=250,
            height=40,
            command=self._on_provider_change
        )
        self.provider_dropdown.set(current_provider)
        self.provider_dropdown.pack(anchor="w")

        # API Key input
        api_key_frame = ctk.CTkFrame(content, fg_color="transparent")
        api_key_frame.pack(fill="x", pady=(SPACING["sm"], 0))

        StyledLabel(
            api_key_frame,
            text="API Key",
            variant="label"
        ).pack(anchor="w", pady=(0, SPACING["xs"]))

        key_input_row = ctk.CTkFrame(api_key_frame, fg_color="transparent")
        key_input_row.pack(fill="x")

        self.api_key_entry = PasswordEntry(
            key_input_row,
            placeholder="Enter your API key"
        )
        self.api_key_entry.pack(side="left", fill="x", expand=True, padx=(0, SPACING["sm"]))

        # Load existing key (masked) — check keychain first, then config
        has_key = False
        if secure_store.is_available and secure_store.get_api_key('gemini'):
            has_key = True
        elif self.backend:
            config = getattr(self.backend, 'config', None)
            if config:
                key = config.get('API', 'gemini_api_key', fallback='')
                has_key = bool(key)
        if has_key:
            self.api_key_entry.input.insert(0, "••••••••••••••••")

        save_key_btn = PrimaryButton(
            key_input_row,
            text="Save",
            command=self._save_api_key,
            width=80,
            height=40
        )
        save_key_btn.pack(side="right")

        # Status indicator
        self.api_status_frame = ctk.CTkFrame(api_key_frame, fg_color="transparent")
        self.api_status_frame.pack(anchor="w", pady=(SPACING["sm"], 0))

        self._update_api_status()

    def _create_calendar_section(self):
        """Create calendar integration section (placeholder)"""
        colors = ThemeManager.get_colors()

        content = self._create_section_card(
            "Calendar Integration",
            "Connect your calendar for automatic meeting scheduling"
        )

        # Coming soon badge
        coming_soon_row = ctk.CTkFrame(content, fg_color="transparent")
        coming_soon_row.pack(fill="x", pady=(SPACING["md"], 0))

        Badge(
            coming_soon_row,
            text="Coming Soon",
            variant="secondary"
        ).pack(side="left")

        StyledLabel(
            coming_soon_row,
            text="Google Calendar and Outlook integration coming in a future update",
            variant="caption"
        ).pack(side="left", padx=SPACING["md"])

    def _create_coach_section(self):
        """Create meeting coach configuration section"""
        colors = ThemeManager.get_colors()

        content = self._create_section_card(
            "Meeting Coach",
            "Configure live meeting coaching and company context feeds"
        )

        # Feed URLs
        feed_frame = ctk.CTkFrame(content, fg_color="transparent")
        feed_frame.pack(fill="x", pady=(SPACING["md"], SPACING["sm"]))

        StyledLabel(
            feed_frame,
            text="RSS Feed URLs (one per line)",
            variant="label"
        ).pack(anchor="w", pady=(0, SPACING["xs"]))

        self.feed_urls_textbox = StyledTextbox(
            feed_frame,
            height=80
        )
        self.feed_urls_textbox.pack(fill="x")

        # Load existing feed URLs
        if self.backend:
            config = getattr(self.backend, 'config', None)
            if config:
                urls = config.get('COACH', 'feed_urls', fallback='')
                if urls:
                    # Convert comma-separated to newline-separated for display
                    url_lines = "\n".join(u.strip() for u in urls.split(",") if u.strip())
                    self.feed_urls_textbox.insert("1.0", url_lines)

        # Intervals row
        intervals_frame = ctk.CTkFrame(content, fg_color="transparent")
        intervals_frame.pack(fill="x", pady=(0, SPACING["sm"]))

        # Feed refresh interval
        refresh_row = ctk.CTkFrame(intervals_frame, fg_color="transparent")
        refresh_row.pack(fill="x", pady=SPACING["xs"])

        StyledLabel(
            refresh_row,
            text="Feed Refresh Interval (hours)",
            variant="label"
        ).pack(side="left")

        self.feed_refresh_entry = StyledEntry(
            refresh_row,
            placeholder="4",
            width=80
        )
        self.feed_refresh_entry.pack(side="right")

        # Load existing value
        if self.backend:
            config = getattr(self.backend, 'config', None)
            if config:
                val = config.get('COACH', 'feed_refresh_hours', fallback='4')
                self.feed_refresh_entry.insert(0, val)

        # Coach analysis interval
        coach_row = ctk.CTkFrame(intervals_frame, fg_color="transparent")
        coach_row.pack(fill="x", pady=SPACING["xs"])

        StyledLabel(
            coach_row,
            text="Coach Analysis Interval (seconds)",
            variant="label"
        ).pack(side="left")

        self.coach_interval_entry = StyledEntry(
            coach_row,
            placeholder="30",
            width=80
        )
        self.coach_interval_entry.pack(side="right")

        # Load existing value
        if self.backend:
            config = getattr(self.backend, 'config', None)
            if config:
                val = config.get('COACH', 'coach_interval', fallback='30')
                self.coach_interval_entry.insert(0, val)

        # Save button
        save_frame = ctk.CTkFrame(content, fg_color="transparent")
        save_frame.pack(fill="x", pady=(SPACING["sm"], 0))

        PrimaryButton(
            save_frame,
            text="Save Coach Settings",
            command=self._save_coach_settings,
            width=160,
            height=40
        ).pack(anchor="w")

    def _save_coach_settings(self):
        """Save coach configuration"""
        if not self.backend:
            return

        # Get feed URLs (newline-separated → comma-separated for config)
        feed_text = self.feed_urls_textbox.get("1.0", "end").strip()
        feed_urls = ",".join(u.strip() for u in feed_text.split("\n") if u.strip())

        refresh_hours = self.feed_refresh_entry.get().strip() or "4"
        coach_interval = self.coach_interval_entry.get().strip() or "30"

        if not self.backend.config.has_section('COACH'):
            self.backend.config.add_section('COACH')

        self.backend.config.set('COACH', 'feed_urls', feed_urls)
        self.backend.config.set('COACH', 'feed_refresh_hours', refresh_hours)
        self.backend.config.set('COACH', 'coach_interval', coach_interval)

        # Save config file
        config_path = getattr(self.backend, 'config_path', 'audio_config.ini')
        try:
            with open(config_path, 'w') as f:
                self.backend.config.write(f)
            from ui.components.toast import ToastManager
            ToastManager.success("Coach settings saved!")
        except Exception as e:
            from ui.components.toast import ToastManager
            ToastManager.error(f"Failed to save: {e}")

    def _create_about_section(self):
        """Create about section"""
        colors = ThemeManager.get_colors()

        content = self._create_section_card(
            "About",
            "Personal Assistant App"
        )

        info_frame = ctk.CTkFrame(content, fg_color="transparent")
        info_frame.pack(fill="x", pady=(SPACING["md"], 0))

        # Version
        version_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        version_row.pack(fill="x", pady=SPACING["xs"])

        StyledLabel(
            version_row,
            text="Version",
            variant="body"
        ).pack(side="left")

        StyledLabel(
            version_row,
            text="1.0.0",
            variant="caption"
        ).pack(side="right")

        # Features
        features = [
            "Local audio transcription with Whisper",
            "AI-powered meeting summaries",
            "Journal with AI insights",
            "Privacy-focused design"
        ]

        StyledLabel(
            info_frame,
            text="Features",
            variant="body_medium"
        ).pack(anchor="w", pady=(SPACING["md"], SPACING["xs"]))

        for feature in features:
            feature_row = ctk.CTkFrame(info_frame, fg_color="transparent")
            feature_row.pack(fill="x", pady=2)

            ctk.CTkLabel(
                feature_row,
                text="•",
                font=FONTS["body"],
                text_color=colors["accent"]
            ).pack(side="left", padx=(0, SPACING["sm"]))

            StyledLabel(
                feature_row,
                text=feature,
                variant="caption"
            ).pack(side="left")

    def _create_account_section(self):
        """Create account section with logout"""
        colors = ThemeManager.get_colors()

        content = self._create_section_card(
            "Account",
            "Manage your account settings"
        )

        # User info (if logged in)
        if self.backend and self.backend.is_logged_in():
            user_info = self.backend.get_user_info()

            user_row = ctk.CTkFrame(content, fg_color="transparent")
            user_row.pack(fill="x", pady=(SPACING["md"], SPACING["sm"]))

            # Avatar placeholder
            avatar = ctk.CTkFrame(
                user_row,
                width=40,
                height=40,
                fg_color=colors["accent"],
                corner_radius=RADIUS["full"]
            )
            avatar.pack(side="left", padx=(0, SPACING["md"]))
            avatar.pack_propagate(False)

            initial = user_info.get("email", "U")[0].upper()
            ctk.CTkLabel(
                avatar,
                text=initial,
                font=FONTS["body_medium"],
                text_color="#ffffff"
            ).place(relx=0.5, rely=0.5, anchor="center")

            # User details
            details_frame = ctk.CTkFrame(user_row, fg_color="transparent")
            details_frame.pack(side="left", fill="x", expand=True)

            StyledLabel(
                details_frame,
                text=user_info.get("email", "User"),
                variant="body_medium"
            ).pack(anchor="w")

            provider = user_info.get("provider", "email").capitalize()
            StyledLabel(
                details_frame,
                text=f"Signed in with {provider}",
                variant="caption"
            ).pack(anchor="w")

        # Logout button
        logout_frame = ctk.CTkFrame(content, fg_color="transparent")
        logout_frame.pack(fill="x", pady=(SPACING["md"], 0))

        logout_btn = DestructiveButton(
            logout_frame,
            text="Sign Out",
            command=self._handle_logout,
            width=120,
            height=40
        )
        logout_btn.pack(anchor="w")

    def _set_theme(self, theme):
        """Set the application theme"""
        colors_before = ThemeManager.get_colors()
        ThemeManager.set_theme(theme)
        colors = ThemeManager.get_colors()

        # Update toggle buttons
        self.light_btn.configure(
            fg_color=colors["primary"] if theme == "light" else "transparent",
            text_color=colors["primary_fg"] if theme == "light" else colors["text_secondary"]
        )
        self.dark_btn.configure(
            fg_color=colors["primary"] if theme == "dark" else "transparent",
            text_color=colors["primary_fg"] if theme == "dark" else colors["text_secondary"]
        )

        # Notify parent to refresh entire UI
        if self.on_theme_change:
            self.on_theme_change(theme)

    def _on_provider_change(self, provider):
        """Handle provider dropdown change"""
        # Clear API key entry for new provider
        self.api_key_entry.input.delete(0, "end")
        self._update_api_status()

    def _save_api_key(self):
        """Save the API key to the OS keychain (or config file as fallback)"""
        key = self.api_key_entry.input.get().strip()

        if not key or key == "••••••••••••••••":
            from ui.components.toast import ToastManager
            ToastManager.warning("Please enter a valid API key")
            return

        provider = self.provider_dropdown.get()
        provider_map = {
            "Google Gemini": "gemini",
            "OpenAI": "openai",
            "Anthropic Claude": "anthropic",
            "Ollama (Local)": "ollama"
        }
        provider_key = provider_map.get(provider, "gemini")

        if self.backend:
            # Save API key to keychain (secure) — falls back to config if unavailable
            stored_securely = secure_store.set_api_key(provider_key, key)

            # Save non-secret settings to config file
            if not self.backend.config.has_section('Settings'):
                self.backend.config.add_section('Settings')
            self.backend.config.set('Settings', 'llm_provider', provider_key)

            # Only write key to INI as fallback if keychain is unavailable
            if not stored_securely:
                if not self.backend.config.has_section('API'):
                    self.backend.config.add_section('API')
                key_names = {
                    "gemini": "gemini_api_key",
                    "openai": "openai_api_key",
                    "anthropic": "anthropic_api_key"
                }
                key_name = key_names.get(provider_key, "gemini_api_key")
                self.backend.config.set('API', key_name, key)

            # Save config file (settings only, no secrets if keychain worked)
            config_path = self.backend.config_path if hasattr(self.backend, 'config_path') else 'audio_config.ini'
            with open(config_path, 'w') as f:
                self.backend.config.write(f)

            from ui.components.toast import ToastManager
            if stored_securely:
                ToastManager.success("API key saved securely to keychain!")
            else:
                ToastManager.success("API key saved (keychain unavailable, stored in config file)")

            # Mask the key
            self.api_key_entry.input.delete(0, "end")
            self.api_key_entry.input.insert(0, "••••••••••••••••")

        self._update_api_status()

    def _update_api_status(self):
        """Update the API configuration status indicator"""
        colors = ThemeManager.get_colors()

        # Clear existing status
        for widget in self.api_status_frame.winfo_children():
            widget.destroy()

        is_configured = False
        # Check keychain first, then config file
        if secure_store.is_available and secure_store.get_api_key('gemini'):
            is_configured = True
        elif self.backend:
            config = getattr(self.backend, 'config', None)
            if config:
                key = config.get('API', 'gemini_api_key', fallback='')
                is_configured = bool(key)

        if is_configured:
            ctk.CTkLabel(
                self.api_status_frame,
                text="✓",
                font=FONTS["body_medium"],
                text_color=colors["success"]
            ).pack(side="left", padx=(0, SPACING["xs"]))

            StyledLabel(
                self.api_status_frame,
                text="API key configured",
                variant="caption"
            ).pack(side="left")
        else:
            ctk.CTkLabel(
                self.api_status_frame,
                text="!",
                font=FONTS["body_medium"],
                text_color=colors["warning"]
            ).pack(side="left", padx=(0, SPACING["xs"]))

            StyledLabel(
                self.api_status_frame,
                text="No API key configured",
                variant="caption"
            ).pack(side="left")

    def _handle_logout(self):
        """Handle logout button click"""
        if self.backend:
            self.backend.logout()

        if self.on_logout:
            self.on_logout()

    def refresh(self):
        """Refresh the view"""
        # Rebuild UI to reflect any changes
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()
