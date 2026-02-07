"""
finance_tracker/ui/tabs/ai_insights_tab.py

Tab for generating AI-driven insights from finance data.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from ...services.ai_insights_service import (
    AIConfig,
    build_chat_messages,
    build_insights_prompt,
    request_ai_insights,
)


class AIInsightsTab:
    def __init__(self, notebook, state):
        self.state = state

        main = ttk.Frame(notebook, padding="10")
        notebook.add(main, text="AI Insights")
        main.rowconfigure(1, weight=1)
        main.columnconfigure(0, weight=1)

        settings = ttk.LabelFrame(main, text="AI Settings", padding="10")
        settings.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        settings.columnconfigure(1, weight=1)

        ttk.Label(settings, text="Provider Preset:").grid(row=0, column=0, sticky="w", pady=5)
        self.provider_var = tk.StringVar(value="Google Gemini")
        self.provider_combo = ttk.Combobox(
            settings,
            textvariable=self.provider_var,
            state="readonly",
            values=["Google Gemini", "OpenAI-Compatible", "Groq"],
        )
        self.provider_combo.grid(row=0, column=1, sticky="ew", pady=5)
        self.provider_combo.bind("<<ComboboxSelected>>", self._apply_preset)

        ttk.Label(settings, text="Model:").grid(row=1, column=0, sticky="w", pady=5)
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(settings, textvariable=self.model_var, state="normal")
        self.model_combo.grid(row=1, column=1, sticky="ew", pady=5)

        ttk.Label(settings, text="API Key:").grid(row=2, column=0, sticky="w", pady=5)
        self.api_key_entry = ttk.Entry(settings, show="*")
        self.api_key_entry.grid(row=2, column=1, sticky="ew", pady=5)

        self.remember_key_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            settings,
            text="Remember API Key",
            variable=self.remember_key_var,
            command=self._persist_api_key,
        ).grid(row=3, column=1, sticky="w", pady=(0, 5))

        self._apply_preset()

        ttk.Button(main, text="Generate Insights", command=self.open_insights_window).grid(
            row=0, column=0, sticky="e", pady=(0, 10)
        )

        chat_frame = ttk.LabelFrame(main, text="Ask the AI", padding="10")
        chat_frame.grid(row=1, column=0, sticky="nsew")
        chat_frame.rowconfigure(0, weight=1)
        chat_frame.columnconfigure(0, weight=1)

        self.chat_text = tk.Text(chat_frame, wrap="word", height=10, font=("Arial", 10))
        self.chat_text.grid(row=0, column=0, sticky="nsew")
        chat_scroll = ttk.Scrollbar(chat_frame, orient="vertical", command=self.chat_text.yview)
        chat_scroll.grid(row=0, column=1, sticky="ns")
        self.chat_text.configure(yscrollcommand=chat_scroll.set)

        input_frame = ttk.Frame(chat_frame)
        input_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        input_frame.columnconfigure(0, weight=1)
        self.chat_entry = ttk.Entry(input_frame)
        self.chat_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ttk.Button(input_frame, text="Send", command=self.send_chat).grid(row=0, column=1, sticky="e")

        self.chat_history = []
        self.last_month = datetime.now().strftime("%Y-%m")
        self.last_months_back = 3

        self._load_saved_api_key()

    def _apply_preset(self, _event=None):
        preset = self.provider_var.get()
        if preset == "Google Gemini":
            self.model_combo["values"] = ["gemini-3-flash-preview", "gemini-2.5-flash"]
            if self.model_var.get() not in self.model_combo["values"]:
                self.model_var.set("gemini-3-flash-preview")
        elif preset == "Groq":
            self.model_combo["values"] = ["llama-3.1-70b-versatile"]
            if self.model_var.get() not in self.model_combo["values"]:
                self.model_var.set("llama-3.1-70b-versatile")
        else:
            self.model_combo["values"] = ["gpt-4o-mini"]
            if self.model_var.get() not in self.model_combo["values"]:
                self.model_var.set("gpt-4o-mini")

    def _load_saved_api_key(self):
        ai_settings = self.state.budget_settings.get("ai_settings", {})
        saved_key = ai_settings.get("api_key", "")
        if saved_key:
            self.api_key_entry.delete(0, tk.END)
            self.api_key_entry.insert(0, saved_key)
            self.remember_key_var.set(True)

    def _persist_api_key(self):
        ai_settings = self.state.budget_settings.setdefault("ai_settings", {})
        if self.remember_key_var.get():
            ai_settings["api_key"] = self.api_key_entry.get().strip()
        else:
            ai_settings["api_key"] = ""
        self.state.save()

    def _get_api_base_url(self):
        provider_key = self.provider_var.get()
        base_urls = {
            "Google Gemini": "https://generativelanguage.googleapis.com/v1beta",
            "OpenAI-Compatible": "https://api.openai.com/v1/chat/completions",
            "Groq": "https://api.groq.com/openai/v1/chat/completions",
        }
        return base_urls.get(provider_key, base_urls["OpenAI-Compatible"])

    def open_insights_window(self):
        win = tk.Toplevel(self.chat_entry)
        win.title("AI Insights Report")
        win.geometry("900x600")
        win.minsize(700, 500)
        win.bind('<Escape>', lambda e: win.destroy())

        options = ttk.Frame(win, padding=10)
        options.pack(fill="x")
        ttk.Label(options, text="End Month (YYYY-MM):").grid(row=0, column=0, sticky="w")
        month_entry = ttk.Entry(options, width=12)
        month_entry.insert(0, self.last_month)
        month_entry.grid(row=0, column=1, sticky="w", padx=(5, 20))

        ttk.Label(options, text="Months to Analyze:").grid(row=0, column=2, sticky="w")
        months_back_entry = ttk.Entry(options, width=6)
        months_back_entry.insert(0, str(self.last_months_back))
        months_back_entry.grid(row=0, column=3, sticky="w", padx=(5, 0))

        text_frame = ttk.Frame(win, padding=10)
        text_frame.pack(fill="both", expand=True)
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)
        report_text = tk.Text(text_frame, wrap="word", font=("Arial", 10))
        report_text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(text_frame, orient="vertical", command=report_text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        report_text.configure(yscrollcommand=scroll.set)

        def run_report():
            month_str = month_entry.get().strip()
            months_back_raw = months_back_entry.get().strip()
            model = self.model_var.get().strip()
            api_key = self.api_key_entry.get().strip()
            api_url = self._get_api_base_url()

            if not model or not api_key:
                messagebox.showerror("Missing Settings", "Please enter a model and API key.")
                return

            try:
                months_back = int(months_back_raw)
                if months_back <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid Input", "Months to analyze must be a positive integer.")
                return

            self.last_month = month_str or self.last_month
            self.last_months_back = months_back

            messages = build_insights_prompt(self.state, self.last_month, self.last_months_back)
            provider_key = self.provider_var.get()
            provider_map = {
                "Google Gemini": "google",
                "OpenAI-Compatible": "openai",
                "Groq": "groq",
            }
            config = AIConfig(
                provider=provider_map.get(provider_key, "openai"),
                api_base_url=api_url,
                api_key=api_key,
                model=model,
            )
            self._persist_api_key()

            try:
                insights = request_ai_insights(config, messages)
            except RuntimeError as exc:
                messagebox.showerror("AI Request Failed", str(exc))
                return

            report_text.delete("1.0", tk.END)
            report_text.insert("1.0", insights)

        ttk.Button(options, text="Generate Report", command=run_report).grid(
            row=0, column=4, sticky="e", padx=(15, 0)
        )

    def send_chat(self):
        user_message = self.chat_entry.get().strip()
        if not user_message:
            return

        api_url = self._get_api_base_url()
        model = self.model_var.get().strip()
        api_key = self.api_key_entry.get().strip()

        if not model or not api_key:
            messagebox.showerror("Missing Settings", "Please enter a model and API key.")
            return

        month_str = self.last_month
        months_back = self.last_months_back

        provider_key = self.provider_var.get()
        provider_map = {
            "Google Gemini": "google",
            "OpenAI-Compatible": "openai",
            "Groq": "groq",
        }
        config = AIConfig(
            provider=provider_map.get(provider_key, "openai"),
            api_base_url=api_url,
            api_key=api_key,
            model=model,
        )
        self._persist_api_key()

        messages = build_chat_messages(
            self.state,
            month_str,
            months_back,
            self.chat_history,
            user_message,
        )

        self.chat_history.append({"role": "user", "content": user_message})
        self._append_chat("You", user_message)
        self.chat_entry.delete(0, tk.END)

        try:
            response = request_ai_insights(config, messages)
        except RuntimeError as exc:
            messagebox.showerror("AI Request Failed", str(exc))
            return

        self.chat_history.append({"role": "assistant", "content": response})
        self._append_chat("AI", response)

    def _append_chat(self, sender, message):
        self.chat_text.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_text.see(tk.END)
