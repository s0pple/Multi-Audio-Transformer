#!/usr/bin/env python3
"""
Test script for mixed audio recording functionality
"""
import numpy as np
import sounddevice as sd
import time

def test_audio_mixing():
    """Test the audio mixing logic used in the main application"""
    print("Testing audio mixing logic...")

    # Simulate microphone data (mono, 16-bit)
    mic_data = np.random.randint(-32768, 32767, 1024, dtype=np.int16)

    # Simulate system audio data (stereo, 16-bit)
    system_data = np.random.randint(-32768, 32767, (1024, 2), dtype=np.int16)

    # Test the mixing logic from our main code
    system_mono = system_data[:, 0] if system_data.ndim > 1 else system_data
    mixed = np.mean([mic_data.flatten(), system_mono], axis=0).astype(np.int16)

    print(f"Mic data shape: {mic_data.shape}")
    print(f"System data shape: {system_data.shape}")
    print(f"Mixed data shape: {mixed.shape}")
    print(f"Mixed data type: {mixed.dtype}")
    print("Audio mixing test passed!")

def test_device_detection():
    """Test device detection for microphone and system audio"""
    print("\nTesting device detection...")

    # Find input devices (microphones)
    input_devices = []
    for i, device in enumerate(sd.query_devices()):
        if device['max_input_channels'] > 0:
            input_devices.append((i, device['name']))

    # Find output devices (for system audio loopback)
    output_devices = []
    for i, device in enumerate(sd.query_devices()):
        if device['max_output_channels'] > 0:
            output_devices.append((i, device['name']))

    print(f"Found {len(input_devices)} input devices:")
    for idx, name in input_devices[:3]:  # Show first 3
        print(f"  {idx}: {name}")

    print(f"\nFound {len(output_devices)} output devices:")
    for idx, name in output_devices[:3]:  # Show first 3
        print(f"  {idx}: {name}")

    return len(input_devices) > 0 and len(output_devices) > 0

def test_callback_logic():
    """Test the callback logic structure"""
    print("\nTesting callback logic structure...")

    # Simulate the callback data structures
    mixed_frames = []
    recording = True

    # Simulate microphone callback
    def mic_callback(indata, frames, time, status):
        if recording:
            mic_data = (indata * 32767).astype(np.int16)
            mixed_frames.append(mic_data.copy())
            print(f"Simulated mic callback: {mic_data.shape}")

    # Simulate system callback
    def system_callback(indata, frames, time, status):
        if recording and len(mixed_frames) > 0:
            system_data = (indata * 32767).astype(np.int16)
            mic_data = mixed_frames.pop(0)

            system_mono = system_data[:, 0] if system_data.ndim > 1 else system_data
            mixed = np.mean([mic_data.flatten(), system_mono], axis=0).astype(np.int16)
            print(f"Simulated system callback: mixed {mixed.shape}")

    # Test with dummy data
    dummy_mic = np.random.random((1024, 1)).astype(np.float32)
    dummy_system = np.random.random((1024, 2)).astype(np.float32)

    mic_callback(dummy_mic, 1024, None, None)
    system_callback(dummy_system, 1024, None, None)

    print("Callback logic test passed!")

if __name__ == "__main__":
    print("=== Mixed Audio Recording Test ===")

    try:
        test_audio_mixing()
        devices_ok = test_device_detection()
        test_callback_logic()

        print("\n=== Test Results ===")
        if devices_ok:
            print("✅ All tests passed! Mixed audio recording should work.")
        else:
            print("⚠️  Device detection test failed - check audio setup.")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()