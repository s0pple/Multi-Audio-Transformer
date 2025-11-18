# Mod## Audio Recording Features

### ✅ **Currently Working**
- **Microphone Recording**: Records from selected microphone device
- **Audio Device Selection**: Choose from available microphones
- **Audio Source Selection**: Choose microphone only, system only, or both
- **Error Handling**: Automatic fallback to default device on errors

### ⚠️ **System Audio Recording (Loopback)**
**What is Loopback Recording?**
- Loopback recording captures audio that's playing through your speakers/headphones
- This allows recording system sounds, music, videos, etc.
- Requires special Windows APIs (WASAPI) for accessing audio output

**Current Status:**
- Device selection is implemented (you can choose which speakers to record from)
- Actual loopback recording is not yet implemented
- Shows informative messages about what's needed
- Framework is ready for future implementation

### 🔧 **Audio Troubleshooting**
The app includes built-in troubleshooting tools:
- **Error Detection**: Identifies common audio issues
- **Automatic Fallback**: Tries default device when selected device fails
- **Troubleshooting Guide**: Built-in help for common problems
- **Device Testing**: Test different audio configurationsr Project Context

## Mission Overview
Create a simple program that can be started with a short command. The program opens a small popup on the right side of the screen where the user can choose a mode (e.g., what work they are doing). Based on the selected mode, it connects to designated folder paths for uploading and storing data.

## Key Features
- **Mode Selection**: GUI popup with radio buttons for different modes (user-customizable)
- **Mode Management**: Add, edit, and delete custom modes
- **Folder Connections**: Each mode can have separate recording and sharing folder paths
- **Audio Recording**: Records from selected microphone when a mode is active
- **Audio Source Selection**: Choose what to record (microphone only, system audio only, or both)
- **Audio Settings**: Allow user to choose default microphone and system audio, with options to change later
- **Recording Control**: When switching to Neutral mode, stop recording and save as a single MP3 file in the recording folder
- **Persistence**: Save settings, custom modes, and folder paths in JSON file

## Technical Implementation
- **Language**: Python
- **GUI**: Tkinter for the popup interface
- **Audio**: PyAudio for recording, PyDub for MP3 conversion
- **File Structure**:
  - `mode_recorder.py`: Main script
  - `settings.json`: User settings and folder paths
  - `context.md`: This file for long-term memory
  - `plan.md`: Task checklist and progress tracking

## User Workflow
1. Run the program with a short command
2. **Customize modes**: Click "Manage Modes" to add, edit, or delete modes
3. **Set folder paths**: For each mode, set both recording folder (where MP3s are saved) and sharing folder (for data sharing)
4. **Configure audio sources**: Click "Audio Sources" to choose what to record (microphone, system audio, or both)
5. **Choose microphone**: Click "Select Microphone" to pick your preferred input device
6. **Start recording**: Select a mode - recording begins immediately based on your audio source preferences
7. **Stop recording**: Switch to "Neutral" mode - the recording saves as an MP3 in the mode's recording folder
8. **Share data**: Use the sharing folder for uploading/connecting data related to that mode

## Future Enhancements
- Better system audio recording (WASAPI loopback mode implementation)
- Mixed audio recording (simultaneous microphone + system audio)
- Audio quality settings (sample rate, bit depth)
- Real-time audio monitoring
- Recording pause/resume functionality
- Data upload integration

## Notes
- Program positions itself on the right side of the screen
- Uses virtual environment for dependencies
- Recordings are saved as MP3 files with mode name and incremental number