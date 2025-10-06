import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import pyaudio
import wave
import threading
import os
import json
import numpy as np
from pydub import AudioSegment
import sounddevice as sd
from packaging import version

# Version requirements
REQUIRED_VERSIONS = {
    'sounddevice': '0.5.2',  # Minimum version
    'soundcard': '0.4.5',    # Minimum version
    'pyaudio': '0.2.11'      # Minimum version
}

# Feature version requirements
LOOPBACK_MIN_VERSION = '0.6.0'  # sounddevice version needed for native loopback

def check_dependency_versions():
    """Check versions of audio dependencies and return status messages.
    
    Returns:
        list: List of (component, status, message) tuples where status is
              'ok', 'warning', or 'error'
    """
    results = []
    
    # Check sounddevice
    try:
        sd_ver = sd.__version__
        if version.parse(sd_ver) < version.parse(REQUIRED_VERSIONS['sounddevice']):
            results.append(('sounddevice', 'error', 
                f'Version {sd_ver} is below minimum {REQUIRED_VERSIONS["sounddevice"]}'))
        elif version.parse(sd_ver) < version.parse(LOOPBACK_MIN_VERSION):
            results.append(('sounddevice', 'warning',
                f'Version {sd_ver} lacks native loopback support (needs {LOOPBACK_MIN_VERSION}+)'))
        else:
            results.append(('sounddevice', 'ok',
                f'Version {sd_ver} installed'))
    except Exception as e:
        results.append(('sounddevice', 'error', f'Not properly installed: {str(e)}'))
    
    # Check soundcard
    try:
        import soundcard as sc
        HAS_SOUNDCARD = True
        sc_ver = sc.__version__
        if version.parse(sc_ver) < version.parse(REQUIRED_VERSIONS['soundcard']):
            results.append(('soundcard', 'warning',
                f'Version {sc_ver} is below recommended {REQUIRED_VERSIONS["soundcard"]}'))
        else:
            results.append(('soundcard', 'ok',
                f'Version {sc_ver} installed'))
    except ImportError:
        HAS_SOUNDCARD = False
        results.append(('soundcard', 'warning',
            'Not installed. System audio recording limited'))
    except Exception as e:
        HAS_SOUNDCARD = False
        results.append(('soundcard', 'error', f'Error loading: {str(e)}'))
    
    # Check pyaudio
    try:
        import pyaudio
        pa_ver = pyaudio.__version__
        if version.parse(pa_ver) < version.parse(REQUIRED_VERSIONS['pyaudio']):
            results.append(('pyaudio', 'warning',
                f'Version {pa_ver} is below recommended {REQUIRED_VERSIONS["pyaudio"]}'))
        else:
            results.append(('pyaudio', 'ok',
                f'Version {pa_ver} installed'))
    except Exception as e:
        results.append(('pyaudio', 'error', f'Not properly installed: {str(e)}'))
    
    return results

# Initialize version info
VERSION_STATUS = check_dependency_versions()

try:
    import soundcard as sc
    HAS_SOUNDCARD = True
except ImportError:
    HAS_SOUNDCARD = False

class ModeRecorder:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Mode Recorder")
        self.root.geometry("300x400")
        self.root.attributes("-topmost", True)
        
        # Position on right side
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"+{screen_width-320}+100")
        
        self.current_mode = "Neutral"
        self.recording = False
        self.audio_frames = []
        self.audio = pyaudio.PyAudio()  # Initialize PyAudio here
        self.stream = None
        
        # Settings
        self.settings_file = "settings.json"
        self.load_settings()
        
        self.create_widgets()

    # ---------------- Utility: loopback microphone via soundcard -----------------
    def check_system_audio_support(self):
        """Check if system audio recording is supported with current configuration.
        
        Returns:
            tuple: (bool, str) - (is_supported, message)
            is_supported: True if system audio recording should work
            message: Description of support status and any required actions
        """
        if not HAS_SOUNDCARD:
            return False, "System audio recording requires the soundcard library.\nInstall it with: pip install soundcard"
            
        try:
            import sounddevice
            sd_version = sounddevice.__version__
            if not sd_version >= "0.6.0":
                return False, f"System audio recording requires sounddevice 0.6.0+\nCurrent version: {sd_version}\nUpdate with: pip install --upgrade sounddevice"
        except Exception:
            pass  # sounddevice check is optional
            
        try:
            lb_mic = self.get_loopback_microphone()
            if lb_mic:
                return True, "System audio recording supported (soundcard loopback available)"
            return False, "No loopback capture device found.\nTry enabling stereo mix or installing a virtual audio cable."
        except Exception as e:
            return False, f"Error checking loopback support: {str(e)}"
    
    def get_loopback_microphone(self):
        """Return a loopback microphone device (system playback) if available.

        Uses soundcard.get_microphone with include_loopback=True which exposes
        the system output as an input-like capture source.
        """
        if not HAS_SOUNDCARD:
            return None
        try:
            # Try default speaker loopback name enumeration
            loopbacks = [m for m in sc.all_microphones(include_loopback=True) if m.is_loopback]
            if loopbacks:
                return loopbacks[0]
            # Fallback: try default speaker by name
            default_spk = sc.default_speaker()
            if default_spk:
                # Some systems expose a loopback microphone with similar name
                for m in sc.all_microphones(include_loopback=True):
                    if default_spk.name.split('(')[0].strip() in m.name and m.is_loopback:
                        return m
            return None
        except Exception:
            return None
        
    def create_widgets(self):
        # Mode selection
        ttk.Label(self.root, text="Select Mode:").pack(pady=10)
        self.mode_var = tk.StringVar(value=self.current_mode)
        self.mode_frame = ttk.Frame(self.root)
        self.mode_frame.pack(fill=tk.X, padx=20)
        self.update_mode_radios()
        
        # Manage Modes button
        ttk.Button(self.root, text="Manage Modes", command=self.manage_modes).pack(pady=5)
        
        # Folder selection buttons
        ttk.Label(self.root, text="Folder Paths:").pack(pady=10)
        self.folder_frame = ttk.Frame(self.root)
        self.folder_frame.pack(fill=tk.X, padx=20)
        self.update_folder_buttons()
        
        # Audio settings
        ttk.Label(self.root, text="Audio Settings:").pack(pady=10)
        ttk.Button(self.root, text="Select Microphone", command=self.select_microphone).pack(pady=5)
        ttk.Button(self.root, text="Select System Audio", command=self.select_system_audio).pack(pady=5)
        ttk.Button(self.root, text="Audio Sources", command=self.select_audio_sources).pack(pady=5)
        ttk.Button(self.root, text="Troubleshoot Audio", command=self.troubleshoot_audio).pack(pady=5)
        
        # Status area with icon
        status_frame = ttk.Frame(self.root)
        status_frame.pack(pady=10, fill=tk.X, padx=10)
        
        self.status_icon = ttk.Label(status_frame, text="✓", font=("Arial", 12))
        self.status_icon.pack(side=tk.LEFT, padx=(0, 5))
        
        status_text_frame = ttk.Frame(status_frame)
        status_text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.status_label = ttk.Label(status_text_frame, text="Status: Neutral")
        self.status_label.pack(fill=tk.X)
        
        self.status_detail = ttk.Label(status_text_frame, text="", 
                                     font=("Arial", 8), wraplength=250)
        self.status_detail.pack(fill=tk.X)
        
    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
            else:
                self.settings = {
                    "microphone_index": 0,
                    "system_audio_index": 0,
                    "audio_sources": {
                        "microphone": True,
                        "system": False
                    },
                    "modes": {
                        "Work": {"recording_folder": "", "sharing_folder": ""},
                        "Meeting": {"recording_folder": "", "sharing_folder": ""},
                        "Study": {"recording_folder": "", "sharing_folder": ""}
                    }
                }            # Ensure all required keys exist
            if "modes" not in self.settings:
                self.settings["modes"] = {
                    "Work": {"recording_folder": "", "sharing_folder": ""},
                    "Meeting": {"recording_folder": "", "sharing_folder": ""},
                    "Study": {"recording_folder": "", "sharing_folder": ""}
                }
            if "microphone_index" not in self.settings:
                self.settings["microphone_index"] = 0
            if "system_audio_index" not in self.settings:
                self.settings["system_audio_index"] = 0
            if "audio_sources" not in self.settings:
                self.settings["audio_sources"] = {
                    "microphone": True,
                    "system": False
                }
            
            # Extract modes from settings
            self.modes = list(self.settings["modes"].keys()) + ["Neutral"]
            self.folder_paths = self.settings["modes"]
            
        except (json.JSONDecodeError, KeyError) as e:
            # If settings file is corrupted, reset to defaults
            print(f"Settings file corrupted, resetting to defaults: {e}")
            self.settings = {
                "microphone_index": 0,
                "system_audio_index": 0,
                "audio_sources": {
                    "microphone": True,
                    "system": False
                },
                "modes": {
                    "Work": {"recording_folder": "", "sharing_folder": ""},
                    "Meeting": {"recording_folder": "", "sharing_folder": ""},
                    "Study": {"recording_folder": "", "sharing_folder": ""}
                }
            }
            self.modes = list(self.settings["modes"].keys()) + ["Neutral"]
            self.folder_paths = self.settings["modes"]
            self.save_settings()
    
    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f)
    
    def update_mode_radios(self):
        # Clear existing radios
        for widget in self.mode_frame.winfo_children():
            widget.destroy()
        
        # Create new radios
        for mode in self.modes:
            ttk.Radiobutton(self.mode_frame, text=mode, variable=self.mode_var, value=mode, command=self.on_mode_change).pack(anchor=tk.W)
    
    def update_folder_buttons(self):
        # Clear existing buttons
        for widget in self.folder_frame.winfo_children():
            widget.destroy()
        
        # Create new buttons for each mode (excluding Neutral)
        for mode in self.modes[:-1]:
            mode_frame = ttk.Frame(self.folder_frame)
            mode_frame.pack(fill=tk.X, pady=2)
            ttk.Label(mode_frame, text=f"{mode}:").pack(side=tk.LEFT)
            
            button_frame = ttk.Frame(mode_frame)
            button_frame.pack(side=tk.RIGHT)
            ttk.Button(button_frame, text="Recording", command=lambda m=mode: self.select_folder(m, "recording")).pack(side=tk.LEFT, padx=2)
            ttk.Button(button_frame, text="Sharing", command=lambda m=mode: self.select_folder(m, "sharing")).pack(side=tk.LEFT, padx=2)
    
    def manage_modes(self):
        self.manage_window = tk.Toplevel(self.root)
        self.manage_window.title("Manage Modes")
        self.manage_window.geometry("400x300")
        
        # Listbox for modes
        ttk.Label(self.manage_window, text="Current Modes:").pack(pady=5)
        self.mode_listbox = tk.Listbox(self.manage_window, height=8)
        self.mode_listbox.pack(fill=tk.X, padx=20, pady=5)
        
        # Populate listbox with current modes (excluding Neutral)
        self.refresh_mode_listbox()
        
        # Buttons
        button_frame = ttk.Frame(self.manage_window)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Add Mode", command=self.add_mode).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Edit Mode", command=self.edit_mode).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Mode", command=self.delete_mode).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self.manage_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def refresh_mode_listbox(self):
        # Clear and repopulate the listbox
        self.mode_listbox.delete(0, tk.END)
        for mode in self.modes[:-1]:  # Exclude Neutral
            self.mode_listbox.insert(tk.END, mode)
    
    def select_folder(self, mode, folder_type):
        folder = filedialog.askdirectory(title=f"Select {folder_type} folder for {mode}")
        if folder:
            self.folder_paths[mode][f"{folder_type}_folder"] = folder
            self.save_settings()
            messagebox.showinfo("Success", f"{folder_type.capitalize()} folder for {mode} set to {folder}")
    
    def add_mode(self):
        name = tk.simpledialog.askstring("Add Mode", "Enter mode name:")
        if name and name not in self.modes:
            try:
                self.settings["modes"][name] = {"recording_folder": "", "sharing_folder": ""}
                self.modes.insert(-1, name)  # Insert before Neutral
                self.folder_paths[name] = {"recording_folder": "", "sharing_folder": ""}
                self.save_settings()
                self.update_mode_radios()
                self.update_folder_buttons()
                self.mode_listbox.insert(tk.END, name)
                messagebox.showinfo("Success", f"Mode '{name}' added")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add mode: {str(e)}")
    
    def edit_mode(self):
        selection = self.mode_listbox.curselection()
        if selection:
            old_name = self.mode_listbox.get(selection[0])
            new_name = tk.simpledialog.askstring("Edit Mode", "Enter new mode name:", initialvalue=old_name)
            if new_name and new_name != old_name and new_name not in self.modes:
                try:
                    # Update settings
                    if old_name in self.settings["modes"]:
                        self.settings["modes"][new_name] = self.settings["modes"].pop(old_name)
                    else:
                        # If not in settings, create it
                        self.settings["modes"][new_name] = {"recording_folder": "", "sharing_folder": ""}
                    
                    # Update folder_paths (ensure it's in sync)
                    if old_name in self.folder_paths:
                        self.folder_paths[new_name] = self.folder_paths.pop(old_name)
                    else:
                        self.folder_paths[new_name] = {"recording_folder": "", "sharing_folder": ""}
                    
                    # Update modes list
                    idx = self.modes.index(old_name)
                    self.modes[idx] = new_name
                    
                    self.save_settings()
                    self.update_mode_radios()
                    self.update_folder_buttons()
                    self.mode_listbox.delete(selection[0])
                    self.mode_listbox.insert(selection[0], new_name)
                    messagebox.showinfo("Success", f"Mode renamed to '{new_name}'")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to edit mode: {str(e)}")
    
    def delete_mode(self):
        selection = self.mode_listbox.curselection()
        if selection:
            mode_name = self.mode_listbox.get(selection[0])
            if messagebox.askyesno("Confirm Delete", f"Delete mode '{mode_name}'?"):
                try:
                    # Remove from settings
                    if mode_name in self.settings["modes"]:
                        del self.settings["modes"][mode_name]
                    if mode_name in self.folder_paths:
                        del self.folder_paths[mode_name]
                    
                    # Remove from modes list
                    if mode_name in self.modes:
                        self.modes.remove(mode_name)
                    
                    self.save_settings()
                    self.update_mode_radios()
                    self.update_folder_buttons()
                    self.mode_listbox.delete(selection[0])
                    messagebox.showinfo("Success", f"Mode '{mode_name}' deleted")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete mode: {str(e)}")
    
    def select_microphone(self):
        devices = []
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info.get('maxInputChannels') > 0:
                devices.append((i, info.get('name')))
        
        if devices:
            self.mic_window = tk.Toplevel(self.root)
            self.mic_window.title("Select Microphone")
            self.mic_window.geometry("300x200")
            
            ttk.Label(self.mic_window, text="Choose Microphone:").pack(pady=10)
            self.mic_var = tk.StringVar()
            for idx, name in devices:
                ttk.Radiobutton(self.mic_window, text=name, variable=self.mic_var, value=str(idx)).pack(anchor=tk.W, padx=20)
            
            ttk.Button(self.mic_window, text="OK", command=self.set_microphone).pack(pady=10)
        else:
            messagebox.showerror("Error", "No microphones found")
    
    def set_microphone(self):
        self.settings["microphone_index"] = int(self.mic_var.get())
        self.save_settings()
        self.mic_window.destroy()
        messagebox.showinfo("Success", "Microphone selected")
    
    def select_system_audio(self):
        # Check if system audio is supported first
        is_supported, support_msg = self.check_system_audio_support()
        
        # Get available output devices (speakers/headphones)
        output_devices = []
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            # Look for devices with output channels (speakers/headphones)
            if info.get('maxOutputChannels') > 0:
                output_devices.append((i, info.get('name')))
        
        if output_devices:
            self.sys_window = tk.Toplevel(self.root)
            self.sys_window.title("Select System Audio Output")
            self.sys_window.geometry("400x300")
            
            # Show system audio support status first
            status_frame = ttk.Frame(self.sys_window)
            status_frame.pack(fill=tk.X, padx=10, pady=5)
            status_color = "green" if is_supported else "red"
            ttk.Label(status_frame, text="System Audio Status:", font=("Arial", 9, "bold")).pack()
            ttk.Label(status_frame, text=support_msg, foreground=status_color, wraplength=350).pack(pady=5)
            
            if not is_supported:
                ttk.Label(status_frame, text="Select an output device anyway if you plan to add loopback capability later.",
                         font=("Arial", 8), wraplength=350).pack(pady=5)
                ttk.Button(status_frame, text="Show Solutions", 
                          command=self.troubleshoot_audio).pack(pady=5)
            
            # Device selection
            ttk.Label(self.sys_window, text="Choose output device to record from:", font=("Arial", 9, "bold")).pack(pady=10)
            device_frame = ttk.Frame(self.sys_window)
            device_frame.pack(fill=tk.X, padx=20)
            
            # Add scrollbar for device list
            scroll_frame = ttk.Frame(device_frame)
            scroll_frame.pack(fill=tk.BOTH, expand=True)
            scrollbar = ttk.Scrollbar(scroll_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            canvas = tk.Canvas(scroll_frame, yscrollcommand=scrollbar.set)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=canvas.yview)
            device_list = ttk.Frame(canvas)
            canvas.create_window((0, 0), window=device_list, anchor='nw')
            
            self.sys_var = tk.StringVar()
            for idx, name in output_devices:
                ttk.Radiobutton(device_list, text=name, variable=self.sys_var, 
                              value=str(idx)).pack(anchor=tk.W, pady=2)
            
            # Configure scroll region
            device_list.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
            
            # Buttons
            button_frame = ttk.Frame(self.sys_window)
            button_frame.pack(pady=15)
            ttk.Button(button_frame, text="Select", command=self.set_system_audio).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=self.sys_window.destroy).pack(side=tk.LEFT, padx=5)
        else:
            messagebox.showerror("Error", "No output devices found")
    
    def set_system_audio(self):
        selected_index = int(self.sys_var.get())
        self.settings["system_audio_index"] = selected_index
        
        # Get device name for confirmation
        device_info = self.audio.get_device_info_by_index(selected_index)
        device_name = device_info.get('name')
        
        # Check system audio support
        is_supported, support_msg = self.check_system_audio_support()
        
        self.save_settings()
        self.sys_window.destroy()
        
        if is_supported:
            messagebox.showinfo("Success", 
                f"System audio output set to: {device_name}\n\n"
                "System audio recording is supported and ready to use.")
        else:
            messagebox.showwarning("Limited Support", 
                f"System audio output set to: {device_name}\n\n"
                "Warning: {support_msg}\n\n"
                "Recording will fall back to microphone only until this is resolved.\n"
                "Click 'Troubleshoot Audio' for solutions.")
    
    def select_audio_sources(self):
        self.audio_window = tk.Toplevel(self.root)
        self.audio_window.title("Select Audio Sources")
        self.audio_window.geometry("300x200")
        
        ttk.Label(self.audio_window, text="Choose what to record:").pack(pady=10)
        
        # Checkboxes for audio sources
        self.mic_check = tk.BooleanVar(value=self.settings["audio_sources"].get("microphone", True))
        self.system_check = tk.BooleanVar(value=self.settings["audio_sources"].get("system", False))
        
        ttk.Checkbutton(self.audio_window, text="Microphone", variable=self.mic_check).pack(anchor=tk.W, padx=20)
        ttk.Checkbutton(self.audio_window, text="System Audio", variable=self.system_check).pack(anchor=tk.W, padx=20)
        
        ttk.Button(self.audio_window, text="Save", command=self.save_audio_sources).pack(pady=10)
    
    def save_audio_sources(self):
        self.settings["audio_sources"]["microphone"] = self.mic_check.get()
        self.settings["audio_sources"]["system"] = self.system_check.get()
        self.save_settings()
        self.audio_window.destroy()
        messagebox.showinfo("Success", "Audio sources updated")
    
    def update_status(self, status_text, detail_text="", status_type="info"):
        """Update the status display with an icon and optional detail text.
        
        Args:
            status_text: Main status message
            detail_text: Optional details or guidance
            status_type: One of "info" (blue ℹ), "success" (green ✓), 
                        "warning" (yellow ⚠), or "error" (red ✕)
        """
        icons = {
            "info": ("ℹ", "blue"),
            "success": ("✓", "green"),
            "warning": ("⚠", "orange"),
            "error": ("✕", "red")
        }
        icon, color = icons.get(status_type, icons["info"])
        
        self.status_icon.config(text=icon, foreground=color)
        self.status_label.config(text=status_text)
        self.status_detail.config(text=detail_text)
        
        # Force GUI update
        self.root.update_idletasks()

    def on_mode_change(self):
        new_mode = self.mode_var.get()
        self.current_mode = new_mode
        
        if new_mode == "Neutral":
            if self.recording:
                self.stop_recording()
            self.update_status(
                f"Status: {new_mode}", 
                "Recording stopped. Select a mode to start recording.",
                "info"
            )
        else:
            if not self.recording:
                # Check audio support before starting
                is_supported, support_msg = self.check_system_audio_support()
                sources = []
                if self.settings["audio_sources"].get("microphone", True):
                    sources.append("microphone")
                if self.settings["audio_sources"].get("system", False):
                    if is_supported:
                        sources.append("system audio")
                    else:
                        detail = f"System audio not available:\n{support_msg}"
                        self.update_status(
                            f"Status: {new_mode}", 
                            detail,
                            "warning"
                        )
                        
                if sources:
                    self.update_status(
                        f"Status: {new_mode}", 
                        f"Recording from: {', '.join(sources)}",
                        "success"
                    )
                    self.start_recording()
                else:
                    self.update_status(
                        f"Status: {new_mode}",
                        "No audio sources selected.\nEnable sources in Audio Sources menu.",
                        "error"
                    )
    
    def start_recording(self):
        self.recording = True
        self.audio_frames = []
        
        # Get audio source preferences
        mic_enabled = self.settings["audio_sources"].get("microphone", True)
        system_enabled = self.settings["audio_sources"].get("system", False)
        
        try:
            if mic_enabled and not system_enabled:
                # Record microphone only (use existing PyAudio method)
                self.audio = pyaudio.PyAudio()
                mic_index = self.settings.get("microphone_index", 0)
                self.stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=44100, 
                                            input=True, input_device_index=mic_index,
                                            frames_per_buffer=1024)
                threading.Thread(target=self.record_audio).start()
                self.update_status(
                    "Recording Active", 
                    "Recording from microphone",
                    "success"
                )
                
            elif system_enabled and not mic_enabled:
                # Record system audio only
                self.record_system_audio_only()
                
            elif mic_enabled and system_enabled:
                # Record both microphone and system audio simultaneously
                self.record_mixed_audio()
                
            else:
                self.update_status(
                    "Recording Failed", 
                    "No audio sources selected.\nEnable sources in Audio Sources menu.",
                    "error"
                )
                messagebox.showerror("Error", "No audio sources selected")
                self.recording = False
                return
            
        except OSError as e:
            self.recording = False
            error_msg = f"Audio device error: {str(e)}\n\n"
            
            if "Errno -9999" in str(e):
                error_msg += "This usually means:\n"
                error_msg += "• Audio device is busy (close other audio apps)\n"
                error_msg += "• Audio device settings changed\n"
                error_msg += "• Try selecting a different microphone\n\n"
                error_msg += "Would you like to try with the default device?"
                
                if messagebox.askyesno("Audio Device Error", error_msg):
                    self.try_default_device()
                else:
                    messagebox.showinfo("Recording Cancelled", "Recording was cancelled due to audio device issues.")
            else:
                messagebox.showerror("Audio Error", f"Failed to start recording:\n{str(e)}")
                
        except Exception as e:
            self.recording = False
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred:\n{str(e)}")
    
    def record_system_audio_only(self):
        """Record system audio using WASAPI loopback"""
        try:
            # Prefer soundcard if available for system audio capture
            if HAS_SOUNDCARD:
                self.record_system_audio_soundcard()
                return
            # Get the system audio device index
            system_device_index = self.settings.get("system_audio_index", None)
            
            if system_device_index is None:
                messagebox.showerror("Error", "No system audio device selected")
                self.recording = False
                return
            
            # Check if the device has input channels
            device_info = sd.query_devices()[system_device_index]
            if device_info['max_input_channels'] == 0:
                messagebox.showerror("System Audio Not Supported", 
                    f"The selected device '{device_info['name']}' is an output device (speakers/headphones).\n\n"
                    "System audio recording requires loopback functionality, which is not supported in sounddevice 0.5.2.\n\n"
                    "To record system audio, you need:\n"
                    "• soundcard library installed (now supported) OR\n"
                    "• sounddevice version 0.6.0+ (when released with loopback) OR\n"
                    "• Use external screen recording software\n\n"
                    "Install soundcard with: pip install soundcard\n\n"
                    "Falling back to microphone recording.")
                self.start_microphone_recording()
                return
            
            # Use sounddevice for WASAPI loopback
            def callback(indata, frames, time, status):
                if status:
                    print(f"Audio callback status: {status}")
                if self.recording:
                    # Convert to the format expected by our audio processing
                    audio_data = (indata * 32767).astype(np.int16).tobytes()
                    self.audio_frames.append(audio_data)
            
            # Start recording with WASAPI loopback
            with sd.InputStream(device=system_device_index, channels=device_info['max_input_channels'], 
                              samplerate=44100, callback=callback, dtype='float32'):
                while self.recording:
                    sd.sleep(100)
                    
        except Exception as e:
            self.recording = False
            error_msg = str(e)
            
            # Check if this is a loopback-related error or channel error
            if "use_loopback" in error_msg or "loopback" in error_msg.lower():
                messagebox.showerror("System Audio Not Supported", 
                    "System audio recording (loopback) is not supported in the current version of sounddevice.\n\n"
                    "This feature requires sounddevice version 0.6.0 or later.\n\n"
                    "Falling back to microphone recording only.\n\n"
                    "To enable system audio recording, please update sounddevice:\n"
                    "pip install --upgrade sounddevice")
                # Fallback to microphone
                self.start_microphone_recording()
            elif "invalid number of channels" in error_msg.lower() or "paerrorcode -9998" in error_msg.lower():
                messagebox.showerror("Invalid Audio Device", 
                    "The selected system audio device doesn't support input recording.\n\n"
                    "This usually means you selected speakers/headphones instead of a microphone.\n\n"
                    "System audio recording requires loopback functionality which is not available in sounddevice 0.5.2.\n\n"
                    "Falling back to microphone recording only.")
                # Fallback to microphone
                self.start_microphone_recording()
            else:
                messagebox.showerror("System Audio Error", 
                    f"Failed to record system audio:\n{error_msg}\n\n"
                    "Falling back to microphone recording.")
                # Fallback to microphone
                self.start_microphone_recording()
    
    def record_mixed_audio(self):
        """Record both microphone and system audio simultaneously and mix them"""
        try:
            # Prefer soundcard if available
            if HAS_SOUNDCARD:
                self.record_mixed_audio_soundcard()
                return
            mic_index = self.settings.get("microphone_index", 0)
            system_device_index = self.settings.get("system_audio_index", None)
            
            if system_device_index is None:
                messagebox.showwarning("Mixed Audio Warning", 
                    "No system audio device selected.\nRecording microphone only.")
                self.start_microphone_recording()
                return
            
            # Check if the system audio device has input channels
            device_info = sd.query_devices()[system_device_index]
            if device_info['max_input_channels'] == 0:
                messagebox.showerror("Mixed Audio Not Supported", 
                    f"The selected system audio device '{device_info['name']}' is an output device.\n\n"
                    "System audio recording requires loopback functionality, which is not supported in sounddevice 0.5.2.\n\n"
                    "To record system audio, you need:\n"
                    "• soundcard library installed (now supported) OR\n"
                    "• sounddevice version 0.6.0+ (future loopback) OR\n"
                    "• Use external screen recording software\n\n"
                    "Install soundcard with: pip install soundcard\n\n"
                    "Falling back to microphone recording only.")
                self.start_microphone_recording()
                return
            
            # Use sounddevice for both streams
            mixed_frames = []
            
            def mic_callback(indata, frames, time, status):
                if self.recording:
                    # Store microphone data
                    mic_data = (indata * 32767).astype(np.int16)
                    mixed_frames.append(mic_data.copy())
            
            def system_callback(indata, frames, time, status):
                if self.recording and len(mixed_frames) > 0:
                    try:
                        # Mix with system audio
                        system_data = (indata * 32767).astype(np.int16)
                        mic_data = mixed_frames.pop(0)
                        
                        # Simple mixing - average the two channels
                        # Take left channel of system audio for mono mixing
                        system_mono = system_data[:, 0] if system_data.ndim > 1 else system_data
                        mixed = np.mean([mic_data.flatten(), system_mono], axis=0).astype(np.int16)
                        self.audio_frames.append(mixed.tobytes())
                    except IndexError:
                        # If no mic data available, just use system audio
                        system_mono = system_data[:, 0] if system_data.ndim > 1 else system_data
                        self.audio_frames.append(system_mono.tobytes())
            
            # Start both streams
            mic_stream = sd.InputStream(device=mic_index, channels=1, samplerate=44100, 
                                      callback=mic_callback, dtype='float32')
            system_stream = sd.InputStream(device=system_device_index, 
                                         channels=device_info['max_input_channels'], 
                                         samplerate=44100, callback=system_callback, dtype='float32')
            
            with mic_stream, system_stream:
                messagebox.showinfo("Mixed Audio Recording", 
                    "Recording both microphone and system audio!\n"
                    "Switch to Neutral mode to stop and save.")
                while self.recording:
                    sd.sleep(100)
                    
        except Exception as e:
            self.recording = False
            error_msg = str(e)
            
            # Check if this is a loopback-related error or channel error
            if "use_loopback" in error_msg or "loopback" in error_msg.lower():
                messagebox.showerror("Mixed Audio Not Supported", 
                    "Mixed audio recording (microphone + system) is not supported in the current version of sounddevice.\n\n"
                    "This feature requires sounddevice version 0.6.0 or later for loopback recording.\n\n"
                    "Falling back to microphone recording only.\n\n"
                    "To enable mixed audio recording, please update sounddevice:\n"
                    "pip install --upgrade sounddevice")
                # Fallback to microphone
                self.start_microphone_recording()
            elif "invalid number of channels" in error_msg.lower() or "paerrorcode -9998" in error_msg.lower():
                messagebox.showerror("Invalid Audio Device", 
                    "The selected system audio device doesn't support input recording.\n\n"
                    "This usually means you selected speakers/headphones instead of a microphone.\n\n"
                    "System audio recording requires loopback functionality which is not available in sounddevice 0.5.2.\n\n"
                    "Falling back to microphone recording only.")
                # Fallback to microphone
                self.start_microphone_recording()
            else:
                messagebox.showerror("Mixed Audio Error", 
                    f"Failed to record mixed audio:\n{error_msg}\n\n"
                    "Falling back to microphone recording.")
                # Fallback to microphone
                self.start_microphone_recording()
    
    def start_microphone_recording(self):
        """Fallback method for microphone recording"""
        try:
            self.update_status(
                "Starting Microphone", 
                "Initializing audio stream...",
                "info"
            )
            
            self.audio = pyaudio.PyAudio()
            mic_index = self.settings.get("microphone_index", 0)
            
            # Get device info for status message
            try:
                device_info = self.audio.get_device_info_by_index(mic_index)
                device_name = device_info.get('name', 'Default Device')
            except:
                device_name = 'Default Device'
            
            self.stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=44100, 
                                        input=True, input_device_index=mic_index,
                                        frames_per_buffer=1024)
            threading.Thread(target=self.record_audio).start()
            
            self.update_status(
                "Recording Active", 
                f"Recording from: {device_name}",
                "success"
            )
        except Exception as e:
            self.recording = False
            error_msg = str(e)
            
            if "Invalid number of channels" in error_msg:
                detail = (
                    "Selected device doesn't support recording.\n"
                    "Try selecting a different microphone in Audio Settings."
                )
            elif "Device Unavailable" in error_msg:
                detail = (
                    "Microphone is not available:\n"
                    "1. Check if it's plugged in\n"
                    "2. Enable it in Windows settings\n"
                    "3. Close other apps using it"
                )
            else:
                detail = f"Recording failed: {error_msg}"
            
            self.update_status(
                "Microphone Error",
                detail,
                "error"
            )
            messagebox.showerror("Microphone Error", f"Failed to start microphone recording:\n{detail}")
    
    def try_default_device(self):
        """Try recording with the system default audio input device"""
        try:
            # Reset to default device
            self.settings["microphone_index"] = 0
            self.settings["system_audio_index"] = 0
            self.save_settings()
            
            # Show version status if there are warnings
            warnings = [r for r in VERSION_STATUS if r[1] in ('warning', 'error')]
            if warnings:
                detail = "Audio Component Status:\n" + "\n".join(
                    f"• {w[0]}: {w[2]}" for w in warnings
                )
                messagebox.showwarning("Audio Component Warning", detail)
            
            # Try recording
            self.recording = False  # Ensure clean start
            if self.current_mode != "Neutral":
                self.start_recording()
            
        except Exception as e:
            messagebox.showerror("Error", 
                f"Failed to start recording with default device:\n{str(e)}")

    def troubleshoot_audio(self):
        """Help troubleshoot audio issues"""
        troubleshoot_window = tk.Toplevel(self.root)
        troubleshoot_window.title("Audio Troubleshooting")
        troubleshoot_window.geometry("500x400")
        
        # Create a notebook for tabbed interface
        notebook = ttk.Notebook(troubleshoot_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Tips tab
        tips_frame = ttk.Frame(notebook)
        notebook.add(tips_frame, text="Common Issues")
        
        ttk.Label(tips_frame, text="Common Audio Issues & Solutions:", 
                 font=("Arial", 10, "bold")).pack(pady=10)
        
        tips_text = tk.Text(tips_frame, height=12, wrap=tk.WORD)
        tips_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tips = """
Common Audio Issues & Solutions:

1. "Unanticipated host error" (-9999):
   • Close other audio applications (Zoom, browsers, etc.)
   • Restart your computer
   • Check Windows audio settings

2. "No microphones found":
   • Check if microphone is plugged in
   • Enable microphone in Windows settings
   • Test microphone in Windows Sound control panel

3. Audio device busy:
   • Close applications using audio
   • Try different audio device
   • Restart audio services

4. System audio not working:
   • Loopback recording requires sounddevice 0.6.0+
   • Current version: 0.5.2 (no loopback support)
   • Output devices (speakers) can't be used as input
   • Update with: pip install --upgrade sounddevice
   • Use screen recording software for system audio

5. "Invalid number of channels" error:
   • Selected output device instead of input device
   • Speakers/headphones can't record audio input
   • Choose a microphone device for system audio
   • Or use external recording software

Quick Fix: Try the default audio device
"""
        tips_text.insert(tk.END, tips)
        tips_text.config(state=tk.DISABLED)
        
        # System Status tab
        status_frame = ttk.Frame(notebook)
        notebook.add(status_frame, text="System Status")
        
        ttk.Label(status_frame, text="Audio Component Status:", 
                 font=("Arial", 10, "bold")).pack(pady=10)
        
        # Component status display
        for component, status, message in VERSION_STATUS:
            component_frame = ttk.Frame(status_frame)
            component_frame.pack(fill=tk.X, padx=10, pady=2)
            
            # Status icon
            if status == 'ok':
                icon = "✓"
                color = "green"
            elif status == 'warning':
                icon = "⚠"
                color = "orange"
            else:  # error
                icon = "✕"
                color = "red"
            
            ttk.Label(component_frame, text=icon, 
                     foreground=color).pack(side=tk.LEFT, padx=(0,5))
            ttk.Label(component_frame, text=component + ":",
                     font=("Arial", 9, "bold")).pack(side=tk.LEFT)
            ttk.Label(component_frame, text=message,
                     wraplength=350).pack(side=tk.LEFT, padx=5)
        
        # Actions
        action_frame = ttk.Frame(troubleshoot_window)
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(action_frame, text="Try Default Device", 
                  command=lambda: [troubleshoot_window.destroy(), 
                                 self.try_default_device()]).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Close", 
                  command=troubleshoot_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def get_error_message(self, context, error_text):
        """Get a user-friendly error message with solutions based on context and error.
        
        Args:
            context: The operation context ('microphone', 'system', 'mixed', etc.)
            error_text: The raw error message text
        
        Returns:
            tuple: (brief_msg, detailed_msg) - Brief and detailed error messages
        """
        error_lookup = {
            'microphone': {
                'Invalid number of channels': (
                    "Invalid Microphone Settings",
                    "The selected microphone doesn't support the required format:\n\n"
                    "1. Try selecting a different microphone\n"
                    "2. Check Windows sound settings\n"
                    "3. Update audio drivers"
                ),
                'Device Unavailable': (
                    "Microphone Unavailable",
                    "The microphone cannot be accessed:\n\n"
                    "1. Check if it's properly connected\n"
                    "2. Enable it in Windows Privacy Settings\n"
                    "3. Close other applications using it\n"
                    "4. Try unplugging and reconnecting"
                ),
                'Unanticipated host error': (
                    "Audio System Error",
                    "Windows audio system error (-9999):\n\n"
                    "1. Close other audio applications\n"
                    "2. Check Windows audio settings\n"
                    "3. Restart the computer\n"
                    "4. Try updating audio drivers"
                )
            },
            'system': {
                'No loopback': (
                    "System Audio Unavailable",
                    "Cannot capture system audio:\n\n"
                    "1. Enable 'Stereo Mix' if available\n"
                    "2. Install a virtual audio cable\n"
                    "3. Update to sounddevice 0.6.0+\n"
                    "4. Use screen recording software"
                ),
                'channels': (
                    "Audio Format Error",
                    "Invalid audio format:\n\n"
                    "1. Try different channel settings\n"
                    "2. Select a different output device\n"
                    "3. Update audio drivers"
                )
            },
            'mixed': {
                'sync': (
                    "Audio Sync Error",
                    "Failed to sync microphone and system audio:\n\n"
                    "1. Try reducing system load\n"
                    "2. Close other audio applications\n"
                    "3. Use simpler recording mode"
                ),
            }
        }
        
        # Look for known error patterns
        for pattern, (brief, detailed) in error_lookup.get(context, {}).items():
            if pattern.lower() in error_text.lower():
                return brief, detailed
        
        # Generic messages if no match
        generic_messages = {
            'microphone': (
                "Microphone Error",
                f"Failed to use microphone:\n\n{error_text}\n\n"
                "1. Check if microphone is connected\n"
                "2. Try selecting a different device\n"
                "3. Check Windows sound settings"
            ),
            'system': (
                "System Audio Error",
                f"Failed to capture system audio:\n\n{error_text}\n\n"
                "1. Try updating audio drivers\n"
                "2. Check Windows sound settings\n"
                "3. Use alternative recording software"
            ),
            'mixed': (
                "Mixed Audio Error",
                f"Failed to record both sources:\n\n{error_text}\n\n"
                "1. Try recording from one source\n"
                "2. Check individual audio settings\n"
                "3. Use alternative recording method"
            )
        }
        
        return generic_messages.get(context, ("Error", f"Operation failed:\n\n{error_text}"))

    def record_audio(self):
        while self.recording:
            try:
                data = self.stream.read(1024)
                self.audio_frames.append(data)
            except Exception as e:
                if self.recording:
                    brief, detailed = self.get_error_message('microphone', str(e))
                    self.update_status(brief, detailed, "error")
                    messagebox.showerror(brief, detailed)
                    self.recording = False
                break

    # ---------------- Soundcard (loopback) Implementations -----------------
    def record_system_audio_soundcard(self):
        """Capture system playback using soundcard (loopback) in a background thread."""
        # Validate system audio support first
        is_supported, support_msg = self.check_system_audio_support()
        if not is_supported:
            messagebox.showerror("System Audio Not Available", 
                "System audio recording is not available:\n\n"
                f"{support_msg}\n\n"
                "Recording will use microphone only.\n"
                "Click 'Troubleshoot Audio' for help enabling system audio.")
            self.recording = False
            self.start_microphone_recording()
            return

        try:
            loopback_mic = self.get_loopback_microphone()
            if not loopback_mic:
                raise RuntimeError(
                    "No loopback device found. To enable system audio recording:\n\n"
                    "1. Enable 'Stereo Mix' in Windows Sound settings\n"
                    "2. Install a virtual audio cable\n"
                    "3. Check if your audio driver supports loopback"
                )
            samplerate = 44100
            blocksize = 1024

            def loop():
                try:
                    # Try stereo first, fallback to mono
                    channel_errors = []
                    for ch in (2, 1):
                        try:
                            with loopback_mic.recorder(samplerate=samplerate, channels=ch) as rec:
                                messagebox.showinfo("System Audio Active", 
                                    f"Successfully capturing system audio ({ch} channels)\n"
                                    "Switch to Neutral mode to stop and save.")
                                while self.recording:
                                    data = rec.record(numframes=blocksize)
                                    if data.ndim > 1:
                                        data_mono = data.mean(axis=1)
                                    else:
                                        data_mono = data
                                    pcm16 = (np.clip(data_mono, -1.0, 1.0) * 32767).astype(np.int16)
                                    self.audio_frames.append(pcm16.tobytes())
                                return
                        except Exception as ch_error:
                            channel_errors.append(f"{ch} channels: {str(ch_error)}")
                            continue
                    
                    # If both channel attempts failed
                    if self.recording:
                        error_details = "\n".join(channel_errors)
                        raise RuntimeError(
                            f"Failed to open loopback recorder:\n{error_details}\n\n"
                            "Try selecting a different audio device or check driver settings."
                        )
                except Exception as inner_e:
                    if self.recording:
                        messagebox.showerror("System Audio Error", 
                            f"Loopback capture failed:\n{str(inner_e)}\n\n"
                            "Recording will use microphone only.\n"
                            "Click 'Troubleshoot Audio' for help.")
                        self.recording = False
                        self.start_microphone_recording()
            
            threading.Thread(target=loop, daemon=True).start()
        
        except Exception as e:
            self.recording = False
            messagebox.showerror("System Audio Error", 
                f"Soundcard loopback failed to start:\n{str(e)}\n\n"
                "Recording will use microphone only.\n"
                "Click 'Troubleshoot Audio' for help.")
            self.start_microphone_recording()

    def record_mixed_audio_soundcard(self):
        """Capture microphone (PyAudio) and system playback (soundcard) and mix to mono."""
        # Validate system audio support first
        is_supported, support_msg = self.check_system_audio_support()
        if not is_supported:
            messagebox.showerror("Mixed Audio Limited", 
                "System audio recording is not available:\n\n"
                f"{support_msg}\n\n"
                "Recording will use microphone only.\n"
                "Click 'Troubleshoot Audio' for help enabling system audio.")
            self.recording = False
            self.start_microphone_recording()
            return

        try:
            samplerate = 44100
            blocksize = 1024
            
            # Open microphone stream first
            try:
                self.audio = pyaudio.PyAudio()
                mic_index = self.settings.get("microphone_index", 0)
                mic_stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=samplerate,
                                          input=True, input_device_index=mic_index,
                                          frames_per_buffer=blocksize)
            except Exception as mic_error:
                raise RuntimeError(
                    f"Failed to open microphone (check if it's plugged in/enabled):\n{str(mic_error)}\n\n"
                    "1. Check if microphone is connected\n"
                    "2. Enable microphone in Windows settings\n"
                    "3. Try selecting a different microphone device"
                )
            
            # Get loopback device
            loopback_mic = self.get_loopback_microphone()
            if not loopback_mic:
                raise RuntimeError(
                    "No loopback device found. To enable system audio recording:\n\n"
                    "1. Enable 'Stereo Mix' in Windows Sound settings\n"
                    "2. Install a virtual audio cable\n"
                    "3. Check if your audio driver supports loopback"
                )

            def loop():
                try:
                    # Try stereo then mono for system audio
                    channel_errors = []
                    for ch in (2, 1):
                        try:
                            with loopback_mic.recorder(samplerate=samplerate, channels=ch) as rec:
                                messagebox.showinfo("Mixed Audio Active", 
                                    f"Successfully capturing microphone + system audio ({ch} ch)\n"
                                    "Switch to Neutral mode to stop and save.")
                                while self.recording:
                                    # Read and process microphone
                                    try:
                                        mic_data = mic_stream.read(blocksize)
                                        mic_np = np.frombuffer(mic_data, dtype=np.int16).astype(np.int32)
                                    except Exception as mic_err:
                                        raise RuntimeError(f"Microphone error: {str(mic_err)}")
                                    
                                    # Read and process system audio
                                    try:
                                        sys_data = rec.record(numframes=blocksize)
                                        if sys_data.ndim > 1:
                                            sys_mono = sys_data.mean(axis=1)
                                        else:
                                            sys_mono = sys_data
                                        sys_np = (np.clip(sys_mono, -1.0, 1.0) * 32767).astype(np.int16).astype(np.int32)
                                    except Exception as sys_err:
                                        raise RuntimeError(f"System audio error: {str(sys_err)}")
                                    
                                    # Mix the streams
                                    try:
                                        length = min(len(mic_np), len(sys_np))
                                        mixed = mic_np[:length] + sys_np[:length]
                                        mixed = np.clip(mixed, -32768, 32767).astype(np.int16)
                                        self.audio_frames.append(mixed.tobytes())
                                    except Exception as mix_err:
                                        raise RuntimeError(f"Error mixing audio streams: {str(mix_err)}")
                                return
                        except Exception as ch_error:
                            channel_errors.append(f"{ch} channels: {str(ch_error)}")
                            continue
                    
                    # If both channel attempts failed
                    if self.recording:
                        error_details = "\n".join(channel_errors)
                        raise RuntimeError(
                            f"Failed to open loopback recorder:\n{error_details}\n\n"
                            "Try selecting a different audio device or check driver settings."
                        )
                except Exception as inner_e:
                    if self.recording:
                        messagebox.showerror("Mixed Audio Error", 
                            f"Mixed audio capture failed:\n{str(inner_e)}\n\n"
                            "Recording will use microphone only.\n"
                            "Click 'Troubleshoot Audio' for help.")
                        self.recording = False
                        self.start_microphone_recording()
                finally:
                    if mic_stream:
                        mic_stream.stop_stream()
                        mic_stream.close()
            
            threading.Thread(target=loop, daemon=True).start()
        
        except Exception as e:
            self.recording = False
            messagebox.showerror("Mixed Audio Error", 
                f"Mixed audio capture failed to start:\n{str(e)}\n\n"
                "Recording will use microphone only.\n"
                "Click 'Troubleshoot Audio' for help.")
            self.start_microphone_recording()
    
    def stop_recording(self):
        self.recording = False
        
        self.update_status(
            "Stopping Recording", 
            "Closing audio streams...",
            "info"
        )
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()
        
        # Save as MP3
        if self.audio_frames:
            self.update_status(
                "Saving Recording", 
                "Converting and saving audio file...",
                "info"
            )
            
            mode_paths = self.folder_paths.get(self.current_mode, {})
            folder = mode_paths.get("recording_folder", "")
            if not folder:
                folder = os.getcwd()
            filename = os.path.join(folder, f"{self.current_mode}_{len(os.listdir(folder))}.mp3")
            
            try:
                self.save_as_mp3(filename)
                self.update_status(
                    "Recording Saved",
                    f"Saved to: {filename}",
                    "success"
                )
            except Exception as e:
                self.update_status(
                    "Save Failed",
                    f"Error saving recording: {str(e)}",
                    "error"
                )
        else:
            self.update_status(
                "Recording Stopped",
                "No audio data was recorded",
                "warning"
            )
    
    def save_as_mp3(self, filename):
        # Convert to WAV first
        wav_filename = filename.replace('.mp3', '.wav')
        wf = wave.open(wav_filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(b''.join(self.audio_frames))
        wf.close()
        
        # Convert to MP3
        audio = AudioSegment.from_wav(wav_filename)
        audio.export(filename, format="mp3")
        os.remove(wav_filename)
        messagebox.showinfo("Saved", f"Recording saved as {filename}")

if __name__ == "__main__":
    app = ModeRecorder()
    app.root.mainloop()