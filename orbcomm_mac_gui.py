#!/usr/bin/env python3
"""
ORBCOMM Email Parser - macOS Native GUI Version
Optimized for Mac M4 with IDE integration
"""

import csv
import platform
import re
import subprocess
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk


class ORBCOMMParserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ORBCOMM Email Parser - macOS")
        self.root.geometry("1200x800")

        # Set macOS-specific styling
        if platform.system() == "Darwin":
            self.root.configure(bg="#f0f0f0")
            try:
                # Enable full keyboard access for better macOS integration
                self.root.tk.call("tk", "scaling", 1.5)
            except Exception:
                pass

        self.parsed_data = []
        self.setup_ui()

        # Bind common Mac shortcuts
        self.root.bind("<Command-v>", lambda e: self.paste_from_clipboard())
        self.root.bind("<Command-s>", lambda e: self.save_to_csv())
        self.root.bind("<Command-e>", lambda e: self.export_to_excel())
        self.root.bind("<Command-n>", lambda e: self.clear_all())

    def setup_ui(self):
        # Create menu bar (Mac-style)
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.clear_all, accelerator="⌘N")
        file_menu.add_command(
            label="Open Email File...", command=self.load_email_file, accelerator="⌘O"
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Save as CSV", command=self.save_to_csv, accelerator="⌘S"
        )
        file_menu.add_command(
            label="Export to Excel", command=self.export_to_excel, accelerator="⌘E"
        )
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.root.quit, accelerator="⌘Q")

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(
            label="Paste", command=self.paste_from_clipboard, accelerator="⌘V"
        )
        edit_menu.add_command(label="Clear All", command=self.clear_all)
        edit_menu.add_command(
            label="Copy Results", command=self.copy_results, accelerator="⌘C"
        )

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(
            label="Process Multiple Files", command=self.batch_process
        )
        tools_menu.add_command(label="Open in VS Code", command=self.open_in_vscode)
        tools_menu.add_command(label="Copy to Numbers", command=self.copy_to_numbers)

        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        main_frame.rowconfigure(4, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="🛰️ ORBCOMM Service Notification Parser",
            font=("SF Pro Display", 18, "bold"),
        )
        title_label.grid(row=0, column=0, pady=(0, 10), sticky=tk.W)

        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Email Input", padding="10")
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(0, weight=1)

        # Subject line input
        ttk.Label(input_frame, text="Subject Line (optional):").grid(
            row=0, column=0, sticky=tk.W
        )
        self.subject_entry = ttk.Entry(input_frame, width=80)
        self.subject_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 10))

        # Email body input
        ttk.Label(input_frame, text="Email Body:").grid(row=2, column=0, sticky=tk.W)
        self.email_text = scrolledtext.ScrolledText(
            input_frame, height=10, wrap=tk.WORD, font=("SF Mono", 11)
        )
        self.email_text.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, pady=10)

        # Styled buttons
        self.parse_btn = ttk.Button(
            button_frame, text="🔍 Parse Email", command=self.parse_email, width=15
        )
        self.parse_btn.grid(row=0, column=0, padx=5)

        ttk.Button(
            button_frame,
            text="📋 Paste from Clipboard",
            command=self.paste_from_clipboard,
            width=20,
        ).grid(row=0, column=1, padx=5)

        ttk.Button(
            button_frame, text="📝 Load Sample", command=self.load_sample, width=15
        ).grid(row=0, column=2, padx=5)

        ttk.Button(
            button_frame, text="🗑️ Clear All", command=self.clear_all, width=15
        ).grid(row=0, column=3, padx=5)

        # Results section
        results_frame = ttk.LabelFrame(main_frame, text="Parsed Results", padding="10")
        results_frame.grid(
            row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10)
        )
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        # Results treeview
        columns = (
            "Reference",
            "Date",
            "Platform",
            "Event",
            "Status",
            "Scheduled",
            "Duration",
            "Services",
        )
        self.tree = ttk.Treeview(
            results_frame, columns=columns, show="headings", height=10
        )

        # Define headings
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        # Scrollbars
        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(results_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # Export buttons
        export_frame = ttk.Frame(main_frame)
        export_frame.grid(row=4, column=0, pady=10)

        ttk.Button(
            export_frame, text="💾 Save as CSV", command=self.save_to_csv, width=15
        ).grid(row=0, column=0, padx=5)

        ttk.Button(
            export_frame, text="📊 Copy for Excel", command=self.copy_for_excel, width=15
        ).grid(row=0, column=1, padx=5)

        ttk.Button(
            export_frame,
            text="📈 Open in Numbers",
            command=self.copy_to_numbers,
            width=15,
        ).grid(row=0, column=2, padx=5)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(
            main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        status_bar.grid(row=5, column=0, sticky=(tk.W, tk.E))

    def parse_email(self):
        subject = self.subject_entry.get().strip()
        body = self.email_text.get(1.0, tk.END).strip()

        if not body:
            messagebox.showwarning(
                "No Input", "Please paste or type email content first!"
            )
            return

        # Split by --- for multiple emails
        emails = body.split("---")

        for email_text in emails:
            if email_text.strip():
                parsed = self.parse_notification_text(email_text.strip(), subject)
                self.parsed_data.append(parsed)
                self.add_to_tree(parsed)

        self.status_var.set(f"Parsed {len(self.parsed_data)} notification(s)")
        messagebox.showinfo(
            "Success", f"Successfully parsed {len(emails)} notification(s)!"
        )

    def parse_notification_text(self, text, subject):  # noqa: C901
        """Parse ORBCOMM notification text."""
        result = {
            "reference_number": "",
            "date_received": datetime.now().strftime("%Y-%m-%d"),
            "platform": "",
            "event_type": "",
            "status": "Open",
            "scheduled_date": "",
            "scheduled_time": "",
            "duration": "",
            "affected_services": "",
            "summary": "",
        }

        # Parse subject
        if subject:
            ref_match = re.search(r"([A-Z]-\d{6})", subject)
            if ref_match:
                result["reference_number"] = ref_match.group(1)

            if "resolved" in subject.lower():
                result["status"] = "Resolved"
            elif "continuing" in subject.lower():
                result["status"] = "Continuing"

            if "IDP" in subject:
                result["platform"] = "IDP"
            elif "OGx" in subject or "OGX" in subject:
                result["platform"] = "OGx"

        # Parse body
        lines = text.split("\n")
        summary_text = ""

        for line in lines:
            line = line.strip()
            if line.lower().startswith("platform:"):
                result["platform"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("event:"):
                result["event_type"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("summary:"):
                summary_text = line.split(":", 1)[1].strip()

        result["summary"] = summary_text[:200]  # Truncate for display

        # Extract dates and duration
        date_match = re.search(r"(\w+\s+\d{1,2}(?:st|nd|rd|th)?)", summary_text)
        if date_match:
            result["scheduled_date"] = date_match.group(1)

        time_match = re.search(r"(\d{1,2}:\d{2}\s*(?:UTC|GMT|EST|PST)?)", summary_text)
        if time_match:
            result["scheduled_time"] = time_match.group(1)

        duration_match = re.search(
            r"(?:last|duration)\s+(\d+)\s+(hour|minute)s?", summary_text, re.I
        )
        if duration_match:
            result[
                "duration"
            ] = f"{duration_match.group(1)} {duration_match.group(2)}(s)"

        # Extract services
        services = []
        service_keywords = [
            "Partner-Support",
            "VAPP",
            "OGWS",
            "Gateway",
            "API",
            "Portal",
        ]
        for keyword in service_keywords:
            if keyword.lower() in summary_text.lower():
                services.append(keyword)
        result["affected_services"] = ", ".join(services)

        return result

    def add_to_tree(self, data):
        """Add parsed data to the treeview."""
        values = (
            data["reference_number"],
            data["date_received"],
            data["platform"],
            data["event_type"],
            data["status"],
            f"{data['scheduled_date']} {data['scheduled_time']}".strip(),
            data["duration"],
            data["affected_services"],
        )
        self.tree.insert("", tk.END, values=values)

    def paste_from_clipboard(self):
        """Paste from clipboard into email text area."""
        try:
            clipboard_text = self.root.clipboard_get()
            self.email_text.delete(1.0, tk.END)
            self.email_text.insert(1.0, clipboard_text)
            self.status_var.set("Pasted from clipboard")
        except tk.TclError:
            messagebox.showerror("Error", "Could not paste from clipboard")

    def clear_all(self):
        """Clear all inputs and results."""
        self.subject_entry.delete(0, tk.END)
        self.email_text.delete(1.0, tk.END)
        self.tree.delete(*self.tree.get_children())
        self.parsed_data = []
        self.status_var.set("Cleared all data")

    def load_sample(self):
        """Load sample data."""
        sample_subject = (
            "ORBCOMM Service Notification: IDP-Maintenance (Reference#: M-003147)-Open"
        )
        sample_body = """Platform: IDP
Event: Maintenance
Summary: Dear ORBCOMM Partner, We will be conducting scheduled maintenance of the Partner-Support page and VAPP interface on November 5th at 15:00 UTC. The maintenance window is expected to last 1 hour."""  # noqa: E501

        self.subject_entry.delete(0, tk.END)
        self.subject_entry.insert(0, sample_subject)
        self.email_text.delete(1.0, tk.END)
        self.email_text.insert(1.0, sample_body)
        self.status_var.set("Sample data loaded")

    def save_to_csv(self):
        """Save parsed data to CSV file."""
        if not self.parsed_data:
            messagebox.showwarning("No Data", "No data to save!")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"orbcomm_notifications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )

        if filename:
            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = list(self.parsed_data[0].keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.parsed_data)

            self.status_var.set(f"Saved to {Path(filename).name}")
            messagebox.showinfo("Success", f"Data saved to {filename}")

            # Offer to open in Finder
            if messagebox.askyesno(
                "Open File", "Do you want to reveal the file in Finder?"
            ):
                subprocess.run(["open", "-R", filename])

    def copy_for_excel(self):
        """Copy data in tab-delimited format for Excel."""
        if not self.parsed_data:
            messagebox.showwarning("No Data", "No data to copy!")
            return

        # Create tab-delimited text
        headers = list(self.parsed_data[0].keys())
        lines = ["\t".join(headers)]

        for data in self.parsed_data:
            lines.append("\t".join(str(data[h]) for h in headers))

        text = "\n".join(lines)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

        self.status_var.set("Data copied to clipboard (Excel format)")
        messagebox.showinfo("Success", "Data copied! You can now paste it into Excel.")

    def copy_results(self):
        """Copy selected results."""
        self.copy_for_excel()

    def copy_to_numbers(self):
        """Export and open in Numbers app."""
        if not self.parsed_data:
            messagebox.showwarning("No Data", "No data to export!")
            return

        # Save temporary CSV
        temp_file = f"/tmp/orbcomm_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        with open(temp_file, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = list(self.parsed_data[0].keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.parsed_data)

        # Open in Numbers
        subprocess.run(["open", "-a", "Numbers", temp_file])
        self.status_var.set("Opened in Numbers")

    def open_in_vscode(self):
        """Open the CSV in VS Code."""
        if not self.parsed_data:
            messagebox.showwarning("No Data", "No data to open!")
            return

        # Save temporary CSV
        temp_file = f"/tmp/orbcomm_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        with open(temp_file, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = list(self.parsed_data[0].keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.parsed_data)

        # Try to open in VS Code
        try:
            subprocess.run(["code", temp_file])
            self.status_var.set("Opened in VS Code")
        except (FileNotFoundError, subprocess.SubprocessError):
            messagebox.showerror(
                "Error", "Could not open VS Code. Is it installed and in PATH?"
            )

    def load_email_file(self):
        """Load email from file."""
        filename = filedialog.askopenfilename(
            filetypes=[
                ("Text files", "*.txt"),
                ("Email files", "*.eml"),
                ("All files", "*.*"),
            ]
        )

        if filename:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()

            self.email_text.delete(1.0, tk.END)
            self.email_text.insert(1.0, content)
            self.status_var.set(f"Loaded {Path(filename).name}")

    def batch_process(self):
        """Process multiple email files."""
        filenames = filedialog.askopenfilenames(
            filetypes=[
                ("Text files", "*.txt"),
                ("Email files", "*.eml"),
                ("All files", "*.*"),
            ]
        )

        if filenames:
            for filename in filenames:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()

                # Try to extract subject from filename or first line
                subject = Path(filename).stem
                parsed = self.parse_notification_text(content, subject)
                self.parsed_data.append(parsed)
                self.add_to_tree(parsed)

            self.status_var.set(f"Processed {len(filenames)} files")
            messagebox.showinfo("Success", f"Processed {len(filenames)} files!")


def main():
    # Check if running on macOS
    if platform.system() != "Darwin":
        print("Warning: This GUI is optimized for macOS but will run on other systems.")

    root = tk.Tk()

    # Set macOS-specific options
    if platform.system() == "Darwin":
        try:
            # Make the app more Mac-like
            root.tk.call("tk::mac::standardAboutPanel")
            root.createcommand("tk::mac::ShowPreferences", lambda: print("Preferences"))
        except Exception:
            pass

    _app = ORBCOMMParserApp(root)  # noqa: F841
    root.mainloop()


if __name__ == "__main__":
    main()
