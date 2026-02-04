import os
import subprocess
import sys
import time
import json
import requests
import threading
import tkinter as tk
from tkinter import scrolledtext, font
import queue
import base64

class ModernUpdateUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("UGauto - Application Launcher")
        self.root.geometry("800x400")
        
        # Configure window
        self.root.configure(bg='#ffffff')
        self.root.resizable(True, True)
        self.root.minsize(600, 300)
        
        # Message queue for thread-safe UI updates
        self.message_queue = queue.Queue()
        
        # Fonts
        self.title_font = font.Font(family="Segoe UI", size=20, weight="bold")
        self.subtitle_font = font.Font(family="Segoe UI", size=9)
        self.log_font = font.Font(family="Consolas", size=9)
        self.button_font = font.Font(family="Segoe UI", size=10, weight="normal")
        self.status_font = font.Font(family="Segoe UI", size=8)
        
        # Colors
        self.colors = {
            'primary': '#2563eb',
            'primary_dark': '#1d4ed8',
            'primary_light': '#3b82f6',
            'secondary': '#64748b',
            'success': '#10b981',
            'warning': '#f59e0b',
            'error': '#ef4444',
            'background': '#ffffff',
            'surface': '#f8fafc',
            'border': '#e2e8f0',
            'text_primary': '#1e293b',
            'text_secondary': '#64748b',
            'text_light': '#94a3b8',
            'log_background': '#0f172a',
            'log_text': '#e2e8f0'
        }
        
        # Flag to track if log is visible
        self.log_visible = False
        self.app_started = False
        
        # Set up UI
        self.setup_ui()
        
        # Start checking messages from queue
        self.root.after(100, self.check_queue)
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_simple_logo_canvas(self):
        """Create a simple logo using tkinter Canvas (no external dependencies)"""
        canvas = tk.Canvas(width=140, height=40, bg='red', 
                          highlightthickness=0, bd=0)
        
        # Blue background with gradient effect
        for i in range(40):
            color_intensity = int(17 + (100 - 17) * i / 40)
            color = f'#{color_intensity:02x}65ae'
            canvas.create_line(0, i, 40, i, fill=color)
        
        # White U shape
        canvas.create_arc(10, 10, 30, 30, start=180, extent=180, 
                         outline='white', width=2, style='arc')
        canvas.create_line(10, 20, 10, 25, fill='white', width=2)
        canvas.create_line(30, 20, 30, 25, fill='white', width=2)
        canvas.create_line(10, 25, 30, 25, fill='white', width=2)
        
        # Red circle in center
        canvas.create_oval(18, 18, 22, 22, fill='#fe0000', outline='')
        
        # White cross inside red circle
        canvas.create_line(18, 20, 22, 20, fill='white', width=1)
        canvas.create_line(20, 18, 20, 22, fill='white', width=1)
        
        # Outer border
        canvas.create_rectangle(2, 2, 38, 38, outline='#1e40af', width=1)
        
        return canvas
    
    def create_text_logo(self):
        """Create a text-based logo as fallback"""
        frame = tk.Frame(width=40, height=40, bg=self.colors['primary'])
        frame.pack_propagate(False)
        
        # Create stylized UG text
        logo_text = tk.Label(frame, text="UG", 
                           font=("Segoe UI", 16, "bold"), 
                           fg='white', bg=self.colors['primary'])
        logo_text.pack(expand=True)
        
        return frame
    
    def create_logo_widget(self, parent):
        """Create logo widget for the header"""
        try:
            # Try canvas-based logo first
            return self.create_simple_logo_canvas()
        except Exception as e:
            print(f"Canvas logo failed: {e}")
            # Fallback to text logo
            return self.create_text_logo()
    
    def setup_ui(self):
        # Main container with padding
        main_container = tk.Frame(self.root, bg=self.colors['background'], padx=15, pady=15)
        main_container.pack(fill='both', expand=True)
        
        # Header Section
        header_frame = tk.Frame(main_container, bg=self.colors['background'])
        header_frame.pack(fill='x', pady=(0, 15))
        
        # Logo and Title
        title_container = tk.Frame(header_frame, bg=self.colors['background'])
        title_container.pack(fill='x')
        
        # Add logo
        logo_widget = self.create_logo_widget(title_container)
        logo_widget.pack(side='left', padx=(0, 12))
        
        title_text = tk.Label(title_container, text="UGauto Launcher", 
                            font=self.title_font, fg=self.colors['text_primary'], 
                            bg=self.colors['background'])
        title_text.pack(side='left')
        
        # Version badge
        version_badge = tk.Label(title_container, text="v1.0.0", 
                               font=self.subtitle_font, fg='white', 
                               bg=self.colors['primary_light'], padx=6, pady=1)
        version_badge.pack(side='left', padx=(8, 0))
        
        # Subtitle
        subtitle_label = tk.Label(header_frame, text="Smart application updater and launcher", 
                                font=self.subtitle_font, fg=self.colors['text_secondary'], 
                                bg=self.colors['background'])
        subtitle_label.pack(fill='x', pady=(3, 0))
        
        # Progress Section
        progress_frame = tk.Frame(main_container, bg=self.colors['background'])
        progress_frame.pack(fill='x', pady=(0, 15))
        
        # Progress labels
        progress_header = tk.Frame(progress_frame, bg=self.colors['background'])
        progress_header.pack(fill='x')
        
        progress_title = tk.Label(progress_header, text="Update Progress", 
                                font=("Segoe UI", 10, "bold"), fg=self.colors['text_primary'], 
                                bg=self.colors['background'])
        progress_title.pack(side='left')
        
        self.status_text = tk.Label(progress_header, text="Initializing...", 
                                  font=self.status_font, fg=self.colors['text_secondary'], 
                                  bg=self.colors['background'])
        self.status_text.pack(side='right')
        
        # Custom progress bar
        progress_container = tk.Frame(progress_frame, height=6, bg=self.colors['border'])
        progress_container.pack(fill='x', pady=(6, 0))
        progress_container.pack_propagate(False)
        
        self.progress_bar = tk.Frame(progress_container, bg=self.colors['primary'], width=0)
        self.progress_bar.pack(side='left', fill='y')
        
        # Minimal Log Section (collapsible)
        self.log_container = tk.Frame(main_container, bg=self.colors['surface'], 
                                     relief='flat', bd=1)
        
        # Log header with toggle button
        log_header = tk.Frame(self.log_container, bg=self.colors['surface'], height=30)
        log_header.pack(fill='x')
        log_header.pack_propagate(False)
        
        # Toggle button for log
        self.toggle_btn = tk.Button(log_header, text="▼ Show Log", 
                                  command=self.toggle_log,
                                  font=self.button_font,
                                  bg='white',
                                  fg=self.colors['primary'],
                                  activebackground=self.colors['primary_light'],
                                  activeforeground='white',
                                  relief='flat',
                                  bd=1,
                                  highlightthickness=0,
                                  padx=10,
                                  pady=2)
        self.toggle_btn.pack(side='left', padx=10)
        
        # Action buttons in log header (only shown when log is visible)
        self.log_action_frame = tk.Frame(log_header, bg=self.colors['surface'])
        
        # Clear log button
        self.clear_btn = tk.Button(self.log_action_frame, text="Clear", 
                                 command=self.clear_log,
                                 font=self.button_font,
                                 bg='white',
                                 fg=self.colors['primary'],
                                 activebackground=self.colors['primary_light'],
                                 activeforeground='white',
                                 relief='flat',
                                 bd=1,
                                 highlightthickness=0,
                                 padx=8,
                                 pady=2)
        self.clear_btn.pack(side='left', padx=2)
        
        # Copy log button
        self.copy_btn = tk.Button(self.log_action_frame, text="Copy", 
                                command=self.copy_log,
                                font=self.button_font,
                                bg='white',
                                fg=self.colors['primary'],
                                activebackground=self.colors['primary_light'],
                                activeforeground='white',
                                relief='flat',
                                bd=1,
                                highlightthickness=0,
                                padx=8,
                                pady=2)
        self.copy_btn.pack(side='left', padx=2)
        
        # Log text area (initially hidden)
        log_inner = tk.Frame(self.log_container, bg=self.colors['log_background'])
        
        self.log_text = scrolledtext.ScrolledText(
            log_inner,
            height=8,
            width=80,
            bg=self.colors['log_background'],
            fg=self.colors['log_text'],
            font=self.log_font,
            insertbackground=self.colors['log_text'],
            wrap='word',
            relief='flat',
            bd=0,
            padx=12,
            pady=10
        )
        self.log_text.pack(fill='both', expand=True, padx=0, pady=0)
        
        # Configure tags for different message types
        self.log_text.tag_config("timestamp", foreground=self.colors['text_light'])
        self.log_text.tag_config("info", foreground='#93c5fd')
        self.log_text.tag_config("success", foreground=self.colors['success'])
        self.log_text.tag_config("warning", foreground=self.colors['warning'])
        self.log_text.tag_config("error", foreground='#fca5a5')
        self.log_text.tag_config("system", foreground='#cbd5e1')
        
        # Show log header only initially
        self.log_container.pack(fill='x', pady=(0, 15))
        
        # Quick status display (visible when log is hidden)
        self.quick_status_frame = tk.Frame(main_container, bg=self.colors['surface'], 
                                          height=60, relief='flat', bd=1)
        self.quick_status_frame.pack(fill='x', pady=(0, 15))
        self.quick_status_frame.pack_propagate(False)
        
        self.quick_status_label = tk.Label(self.quick_status_frame, 
                                         text="Initializing...", 
                                         font=("Segoe UI", 9),
                                         fg=self.colors['text_primary'],
                                         bg=self.colors['surface'],
                                         wraplength=700,
                                         justify='left')
        self.quick_status_label.pack(anchor='w', padx=15, pady=10)
        
        # Footer Section
        footer_frame = tk.Frame(main_container, bg=self.colors['background'], height=60)
        footer_frame.pack(fill='x', side='bottom')
        footer_frame.pack_propagate(False)
        
        # Left footer - Stats
        stats_frame = tk.Frame(footer_frame, bg=self.colors['background'], height=50)
        stats_frame.pack(side='left', fill='y')
        stats_frame.pack_propagate(False)
        
        self.stats_label = tk.Label(stats_frame, text="Ready", 
                                  font=self.status_font, fg=self.colors['text_secondary'], 
                                  bg=self.colors['background'])
        self.stats_label.pack(anchor='w', pady=15)
        
        # Right footer - Control buttons
        self.button_frame = tk.Frame(footer_frame, bg=self.colors['background'], height=50)
        self.button_frame.pack(side='right', fill='y')
        self.button_frame.pack_propagate(False)
        
        # Create buttons
        self.restart_btn = self.create_button("🔄 Restart", self.restart_updater)
        self.manual_btn = self.create_button("📂 Folder", self.open_app_folder)
        self.exit_btn = self.create_button("✕ Exit", self.root.quit, is_secondary=True)
        
        # Initialize progress
        self.update_progress(0)
        
    def create_button(self, text, command, is_secondary=False):
        """Create a modern styled button with proper sizing"""
        if is_secondary:
            bg_color = 'white'
            fg_color = self.colors['text_secondary']
            hover_color = self.colors['surface']
            border_color = self.colors['border']
        else:
            bg_color = self.colors['primary']
            fg_color = 'white'
            hover_color = self.colors['primary_dark']
            border_color = self.colors['primary_dark']
        
        btn = tk.Button(
            self.button_frame,
            text=text,
            command=command,
            font=self.button_font,
            bg=bg_color,
            fg=fg_color,
            activebackground=hover_color,
            activeforeground=fg_color if is_secondary else 'white',
            relief='flat',
            bd=1,
            highlightthickness=0,
            padx=20,
            pady=8,
            cursor='hand2',
            height=1
        )
        
        # Add hover effect
        def on_enter(e):
            if is_secondary:
                btn['bg'] = hover_color
                btn['bd'] = 1
                btn['relief'] = 'solid'
            else:
                btn['bg'] = hover_color
                btn['bd'] = 1
                btn['relief'] = 'solid'
            
        def on_leave(e):
            if is_secondary:
                btn['bg'] = bg_color
                btn['bd'] = 1
                btn['relief'] = 'flat'
            else:
                btn['bg'] = bg_color
                btn['bd'] = 1
                btn['relief'] = 'flat'
            
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    def toggle_log(self):
        """Toggle log visibility"""
        if self.log_visible:
            # Hide log
            for widget in self.log_container.winfo_children():
                if widget != self.log_container.winfo_children()[0]:  # Keep header
                    widget.pack_forget()
            self.toggle_btn.config(text="▼ Show Log")
            self.log_action_frame.pack_forget()
            self.quick_status_frame.pack(fill='x', pady=(0, 15))
            self.root.geometry("800x400")  # Smaller size
        else:
            # Show log
            log_inner = self.log_container.winfo_children()[1] if len(self.log_container.winfo_children()) > 1 else None
            if log_inner:
                log_inner.pack(fill='both', expand=True, padx=1, pady=(0, 1))
            self.toggle_btn.config(text="▲ Hide Log")
            self.log_action_frame.pack(side='right', padx=10)
            self.quick_status_frame.pack_forget()
            self.root.geometry("800x550")  # Larger size to show log
        
        self.log_visible = not self.log_visible
        self.root.update_idletasks()
    
    def update_progress(self, percentage):
        """Update the progress bar width"""
        container_width = self.progress_bar.master.winfo_width()
        if container_width > 1:
            width = int(container_width * (percentage / 100))
            self.progress_bar.config(width=width)
    
    def log_message(self, message, message_type="info"):
        """Add message to log text area"""
        timestamp = time.strftime("%H:%M:%S")
        
        # Queue the message for thread-safe update
        self.message_queue.put((timestamp, message, message_type))
        
        # Update quick status with last important message
        if message_type in ["success", "error", "warning"]:
            self.quick_status_label.config(text=message[:100] + "..." if len(message) > 100 else message)
    
    def check_queue(self):
        """Check for new messages in queue and update UI"""
        try:
            while True:
                timestamp, message, msg_type = self.message_queue.get_nowait()
                
                # Insert timestamp
                self.log_text.insert('end', f"[{timestamp}] ", "timestamp")
                
                # Insert message with appropriate tag
                self.log_text.insert('end', f"{message}\n", msg_type)
                
                # Update status text with last message
                self.status_text.config(text=message[:50] + "..." if len(message) > 50 else message)
                
                # Auto-scroll
                self.log_text.see('end')
                
                # Update progress based on message type
                if msg_type == "success":
                    # Increment progress slightly for success messages
                    current_width = self.progress_bar.winfo_width()
                    container_width = self.progress_bar.master.winfo_width()
                    if container_width > 0:
                        current_percent = (current_width / container_width) * 100
                        if current_percent < 90:
                            self.update_progress(current_percent + 2)
                
        except queue.Empty:
            pass
        
        # Check again after 100ms
        self.root.after(100, self.check_queue)
    
    def clear_log(self):
        """Clear the log text area"""
        self.log_text.delete(1.0, 'end')
        self.log_message("Log cleared", "system")
    
    def copy_log(self):
        """Copy log content to clipboard"""
        log_content = self.log_text.get(1.0, 'end-1c')
        self.root.clipboard_clear()
        self.root.clipboard_append(log_content)
        self.log_message("Log copied to clipboard", "success")
    
    def show_buttons(self):
        """Show control buttons in footer with proper spacing"""
        # Clear any existing buttons
        for widget in self.button_frame.winfo_children():
            widget.pack_forget()
        
        # Pack buttons with proper spacing
        self.restart_btn.pack(side='right', padx=(8, 0), pady=10)
        self.manual_btn.pack(side='right', padx=(8, 0), pady=10)
        self.exit_btn.pack(side='right', pady=10)
        
        # Make sure button frame is visible
        self.button_frame.pack(side='right', fill='y')
        
        # Update the UI
        self.root.update_idletasks()
    
    def close_launcher(self):
        """Close the launcher completely"""
        self.root.quit()
        self.root.destroy()
    
    def hide_ui(self):
        """Hide the UI to system tray"""
        if self.app_started:
            self.root.withdraw()  # Hide window
    
    def show_ui(self):
        """Show the UI again"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def restart_updater(self):
        """Restart the updater"""
        self.log_message("Restarting updater...", "system")
        self.root.destroy()
        os.execl(sys.executable, sys.executable, *sys.argv)
    
    def open_app_folder(self):
        """Open application folder"""
        target_path = "C:/Documents/ChatUgautodetal" if os.name == 'nt' else os.path.expanduser("~/Documents/ChatUgautodetal")
        try:
            if os.name == 'nt':  # Windows
                os.startfile(target_path)
            else:  # Linux/Mac
                subprocess.run(['xdg-open', target_path])
            self.log_message(f"Opened folder: {target_path}", "success")
        except Exception as e:
            self.log_message(f"Error opening folder: {e}", "error")
    
    def on_closing(self):
        """Handle window closing"""
        if self.app_started:
            self.hide_ui()
        else:
            self.root.quit()
    
    def start(self):
        """Start the UI main loop"""
        self.update_progress(10)
        self.root.mainloop()

# ... (keep all other functions the same as before: get_version_from_api, download_with_gdown,
# get_final_filename, check_file_exists, start_application, run_updater, main, etc.)

def get_version_from_api(ui):
    """Get current version, file_id and output_file from local API"""
    api_url = "https://ugauto-back-version.vercel.app/version"
    
    try:
        ui.log_message(f"Checking version from API: {api_url}", "info")
        ui.update_progress(20)
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                ui.log_message("API response successful", "success")
                ui.update_progress(30)
                return {
                    "file_id": data.get("file_id", ""),
                    "output_file": data.get("output_file", ""),
                    "data": data.get("data", {})
                }
            else:
                ui.log_message(f"API returned non-success status: {data.get('status')}", "warning")
        else:
            ui.log_message(f"API request failed with status code: {response.status_code}", "error")
            
    except requests.exceptions.ConnectionError:
        ui.log_message("Cannot connect to API server.", "error")
    except requests.exceptions.Timeout:
        ui.log_message("API request timed out.", "warning")
    except requests.exceptions.RequestException as e:
        ui.log_message(f"API request error: {e}", "error")
    except json.JSONDecodeError:
        ui.log_message("Invalid JSON response from API.", "error")
    
    # Return default values if API fails
    ui.log_message("Using default values...", "warning")
    return {
        "file_id": "",
        "output_file": "",
        "data": {}
    }

def download_with_gdown(file_id, output_file, ui):
    """Alternative download method using gdown for Google Drive files"""
    try:
        import gdown
    except ImportError:
        ui.log_message("Installing gdown package...", "info")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "gdown"], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            import gdown
            ui.log_message("gdown package installed successfully", "success")
        except Exception as e:
            ui.log_message(f"Error installing gdown: {e}", "error")
            return False
    
    url = f"https://drive.google.com/uc?id={file_id}"
    ui.log_message(f"Downloading from: {url}", "info")
    ui.update_progress(50)
    
    try:
        gdown.download(url, output_file, quiet=False)
        ui.update_progress(80)
        
        # Check if file was actually downloaded
        if os.path.exists(output_file):
            return True
        else:
            ui.log_message(f"Download completed but file not found: {output_file}", "error")
            return False
    except Exception as e:
        ui.log_message(f"Download failed: {e}", "error")
        return False

def get_final_filename(output_file, version):
    """Generate final filename: output_file + version + .exe"""
    if not output_file:
        return ""
    
    # Add .exe extension if not present
    if not output_file.lower().endswith('.exe'):
        base_name = output_file + ".exe"
    else:
        base_name = output_file
    
    if not version:
        return base_name
    
    # Create filename: base_name (without .exe) + _ + version + .exe
    base_without_ext = base_name[:-4]  # Remove .exe
    return f"{base_without_ext}_{version}.exe"

def check_file_exists(output_file, version, ui):
    """Check if the specific version file already exists"""
    target_filename = get_final_filename(output_file, version)
    
    if not target_filename:
        return None
    
    if os.path.exists(target_filename):
        ui.log_message(f"File already exists: {target_filename}", "info")
        file_size = os.path.getsize(target_filename)
        ui.log_message(f"File size: {file_size:,} bytes", "info")
        return target_filename
    
    # Also check for the base filename without version
    if version:
        base_filename = f"{output_file}.exe" if not output_file.lower().endswith('.exe') else output_file
        if os.path.exists(base_filename):
            ui.log_message(f"Found base file (without version): {base_filename}", "info")
            # Rename it to include version
            final_filename = get_final_filename(output_file, version)
            try:
                os.rename(base_filename, final_filename)
                ui.log_message(f"Renamed to: {final_filename}", "success")
                return final_filename
            except Exception as e:
                ui.log_message(f"Error renaming file: {e}", "warning")
                return base_filename
    
    return None

def start_application(filename, api_data, ui):
    """Start the application with optional API data"""
    if not filename or not os.path.exists(filename):
        ui.log_message(f"Cannot start application: File not found - {filename}", "error")
        return False, None
    
    ui.log_message(f"\nStarting {filename}...", "info")
    ui.update_progress(90)
    
    # Prepare environment with API data if available
    env = os.environ.copy()
    if api_data:
        # Pass API data as environment variables
        env['API_DATA'] = json.dumps(api_data)
        ui.log_message(f"Passing API data to application", "info")
    
    try:
        # Start the application with environment variables
        if os.name == 'nt':  # Windows
            process = subprocess.Popen([filename], shell=True, env=env)
        else:  # Linux/Mac
            process = subprocess.Popen([filename], env=env)
            
        ui.log_message(f"Application started successfully! (PID: {process.pid})", "success")
        ui.update_progress(95)
        
        # Wait a moment to ensure app is running
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            ui.log_message("✓ Application is running normally", "success")
            ui.update_progress(100)
            return True, process
        else:
            ui.log_message("✗ Application terminated immediately", "error")
            return False, None
    except Exception as e:
        ui.log_message(f"Error starting application: {e}", "error")
        ui.log_message(f"Try running it manually from: {os.path.abspath(filename)}", "info")
        return False, None

def run_updater(ui):
    """Main updater logic"""
    target_path = "C:/Documents/ChatUgautodetal" if os.name == 'nt' else os.path.expanduser("~/Documents/ChatUgautodetal")
    
    # Create and change directory
    try:
        os.makedirs(target_path, exist_ok=True)
        os.chdir(target_path)
        ui.log_message(f"Working directory: {os.getcwd()}", "info")
    except Exception as e:
        ui.log_message(f"Error setting up directory: {e}", "error")
        ui.show_buttons()
        return False, None
    
    # Step 1: Get version info from API
    api_info = get_version_from_api(ui)
    
    if not api_info["data"]:
        ui.log_message("No API data received. Please check your connection.", "error")
        ui.show_buttons()
        return False, None
    
    file_id = api_info["data"].get("file_id", "")
    output_file = api_info["data"].get("output_file", "")
    current_version = api_info["data"].get("version", "")
    api_data = api_info["data"]
    
    if not output_file:
        ui.log_message("Error: No output file specified in API response", "error")
        ui.show_buttons()
        return False, None
    
    ui.log_message("\nAPI Information:", "system")
    ui.log_message(f"  Output File: {output_file}", "info")
    ui.log_message(f"  Current Version: {current_version}", "info")
    ui.log_message(f"  File ID: {file_id}", "info")
    
    # Step 2: Check if we already have this exact version
    final_filename = get_final_filename(output_file, current_version)
    ui.log_message(f"\nTarget filename: {final_filename}", "info")
    
    existing_file = check_file_exists(output_file, current_version, ui)
    
    if existing_file:
        ui.log_message(f"\nFound existing file: {existing_file}", "info")
        
        # Check if it's the exact version we need
        if existing_file == final_filename:
            ui.log_message("✓ Exact version match found!", "success")
            success, process = start_application(existing_file, api_data, ui)
            if success:
                ui.log_message("✓ Application started successfully!", "success")
                return True, process
        else:
            ui.log_message(f"Different version found. Checking for updates...", "info")
    
    # Step 3: Download new version if needed
    ui.log_message(f"\nChecking for updates...", "system")
    
    if existing_file and not current_version:
        # No version info from API, just run existing file
        ui.log_message("No version info from API. Running existing file...", "warning")
        success, process = start_application(existing_file, api_data, ui)
        if success:
            ui.log_message("✓ Application started successfully!", "success")
            return True, process
        return False, None
    
    # Step 4: Download new version
    if not file_id:
        ui.log_message("Error: No file ID specified in API response", "error")
        if existing_file:
            ui.log_message("Starting existing file...", "info")
            success, process = start_application(existing_file, api_data, ui)
            if success:
                ui.log_message("✓ Application started successfully!", "success")
                return True, process
        ui.show_buttons()
        return False, None
    
    ui.log_message(f"\nDownloading new version...", "system")
    
    # Create temporary filename for download
    temp_filename = output_file if output_file.lower().endswith('.exe') else output_file + ".exe"
    
    # Check if we need to download
    download_needed = True
    if existing_file and current_version:
        download_needed = current_version not in existing_file
    
    ui.log_message(f"Download needed: {download_needed}", "info")
    
    if download_needed:
        try:
            download_success = download_with_gdown(file_id, temp_filename, ui)
        except Exception as e:
            ui.log_message(f"Gdown failed: {e}", "error")
            download_success = False
    else:
        download_success = True
        ui.log_message("Skipping download - latest version already exists", "success")
    
    if download_success:
        # Check which file to use
        if download_needed and os.path.exists(temp_filename):
            file_to_use = temp_filename
            ui.log_message(f"\n✓ Download successful: {temp_filename}", "success")
            try:
                file_size = os.path.getsize(temp_filename)
                ui.log_message(f"File size: {file_size:,} bytes", "info")
            except Exception as e:
                ui.log_message(f"Could not get file size: {e}", "warning")
            
            # Rename to final filename with version if version exists
            if current_version:
                final_filename = get_final_filename(output_file, current_version)
                try:
                    os.rename(temp_filename, final_filename)
                    ui.log_message(f"Renamed to: {final_filename}", "success")
                    file_to_use = final_filename
                except Exception as e:
                    ui.log_message(f"Error renaming file: {e}", "warning")
                    file_to_use = temp_filename
        else:
            # Use existing file
            file_to_use = existing_file if existing_file else final_filename
        
        # Save API data to a JSON file alongside the executable
        if api_data and file_to_use:
            data_filename = file_to_use.replace('.exe', '_data.json')
            try:
                with open(data_filename, 'w') as f:
                    json.dump(api_data, f, indent=2)
                ui.log_message(f"Saved API data to: {data_filename}", "info")
            except Exception as e:
                ui.log_message(f"Error saving API data: {e}", "warning")
        
        # Start the application
        ui.log_message("\nStarting application with API data...", "system")
        success, process = start_application(file_to_use, api_data, ui)
        if success:
            ui.log_message("✓ Application started successfully!", "success")
            return True, process
        
    else:
        ui.log_message("\n✗ Download failed.", "error")
        
        # Try to start existing file if download fails
        if existing_file:
            ui.log_message(f"Attempting to start existing file: {existing_file}", "info")
            success, process = start_application(existing_file, api_data, ui)
            if success:
                ui.log_message("✓ Application started successfully!", "success")
                return True, process
        else:
            ui.log_message("Please check your connection and try again.", "error")
            ui.show_buttons()
    
    return False, None

def main():
    # Create UI
    ui = ModernUpdateUI()
    
    # Install requests if not available
    def check_and_install_requests():
        try:
            import requests
            ui.log_message("Requests package already installed", "success")
        except ImportError:
            ui.log_message("Installing requests package...", "info")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"], 
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                ui.log_message("✓ Requests package installed successfully", "success")
            except Exception as e:
                ui.log_message(f"Error installing requests: {e}", "error")
    
    # Run requests check in separate thread
    requests_thread = threading.Thread(target=check_and_install_requests)
    requests_thread.daemon = True
    requests_thread.start()
    
    # Run updater in separate thread
    def run_updater_thread():
        time.sleep(1)  # Wait a bit for UI to initialize
        success, process = run_updater(ui)
        
        if success:
            # Log success
            ui.log_message("\n" + "="*60, "system")
            ui.log_message("✓ Chat application started successfully!", "success")
            ui.log_message("Closing launcher in 2 seconds...", "info")
            ui.log_message("="*60, "system")
            time.sleep(2)
            
            # Update stats label
            if process:
                ui.stats_label.config(text=f"App running (PID: {process.pid})")
            
            # Set flag and close launcher completely
            ui.app_started = True
            
            # Schedule the launcher to close after a brief delay
            ui.root.after(500, ui.close_launcher)
            
        else:
            ui.log_message("\n✗ Failed to start application", "error")
            ui.show_buttons()
            ui.stats_label.config(text="Failed to start")
    
    # Start updater thread
    updater_thread = threading.Thread(target=run_updater_thread)
    updater_thread.daemon = True
    updater_thread.start()
    
    # Start UI main loop
    ui.start()

if __name__ == "__main__":
    main()