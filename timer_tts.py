#!/usr/bin/env python3
"""
Simple TTS Timer Script
Announces elapsed time in minutes at regular intervals
Can use either TTS or tone sounds
"""

import time
import pyttsx3
import sys
import numpy as np
import argparse
try:
    import sounddevice as sd
except ImportError:
    sd = None

def announce_text(text):
    """Announce text using TTS"""
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def generate_bright_tone(duration=0.3, sample_rate=44100):
    """Generate a bright, pure tone using harmonic sine waves"""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Create a harmonic series with fundamental at 800 Hz
    fundamental = 800
    harmonics = [1.0, 0.5, 0.25, 0.125]  # Decreasing amplitudes
    tone = np.zeros_like(t)
    
    for i, amplitude in enumerate(harmonics):
        tone += amplitude * np.sin(2 * np.pi * fundamental * (i + 1) * t)
    
    # Normalize
    tone = tone / np.max(np.abs(tone))
    
    # Apply Hann window to avoid clicks/artifacts
    window = np.hanning(len(tone))
    tone = tone * window
    
    return tone

def generate_rough_tone(duration=0.3, sample_rate=44100):
    """Generate a rough, harsh tone with inharmonic partials"""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Mix of inharmonic frequencies to create roughness
    frequencies = [400, 537, 689, 823, 971]  # Non-harmonic relationship
    amplitudes = [1.0, 0.8, 0.6, 0.4, 0.3]
    
    tone = np.zeros_like(t)
    for freq, amp in zip(frequencies, amplitudes):
        tone += amp * np.sin(2 * np.pi * freq * t)
    
    # Add slight noise for extra roughness
    tone += 0.1 * np.random.randn(len(t))
    
    # Normalize
    tone = tone / np.max(np.abs(tone))
    
    # Apply Hann window to avoid clicks/artifacts
    window = np.hanning(len(tone))
    tone = tone * window
    
    return tone

def play_tone(tone, sample_rate=44100):
    """Play a tone using sounddevice"""
    if sd is None:
        print("Warning: sounddevice not installed. Cannot play tones.")
        return
    sd.play(tone, sample_rate)
    sd.wait()

def announce(text, mode='speech', tone_type='bright', tone_duration=0.3):
    """Announce using either speech or tones"""
    if mode == 'speech':
        announce_text(text)
    elif mode == 'tone':
        if tone_type == 'bright':
            tone = generate_bright_tone(duration=tone_duration)
        else:  # rough
            tone = generate_rough_tone(duration=tone_duration)
        play_tone(tone)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Timer with TTS or tone announcements')
    parser.add_argument('interval', type=float, nargs='?', default=1.0,
                        help='Interval in minutes between announcements (default: 1)')
    parser.add_argument('--mode', choices=['speech', 'tone'], default='speech',
                        help='Announcement mode: speech (TTS) or tone (default: speech)')
    parser.add_argument('--tone-type', choices=['bright', 'rough'], default='bright',
                        help='Type of tone: bright (harmonic) or rough (inharmonic) (default: bright)')
    parser.add_argument('--tone-duration', type=float, default=0.3,
                        help='Duration of tones in seconds (default: 0.3)')
    
    args = parser.parse_args()
    
    interval_minutes = args.interval
    mode = args.mode
    tone_type = args.tone_type
    tone_duration = args.tone_duration
    
    # Check if sounddevice is available when using tone mode
    if mode == 'tone' and sd is None:
        print("Error: sounddevice package is required for tone mode.")
        print("Install with: pip install sounddevice")
        sys.exit(1)

    # Announce script start
    print("Timer Script")
    print(f"Interval: {interval_minutes} minute(s)")
    print(f"Mode: {mode}")
    if mode == 'tone':
        print(f"Tone type: {tone_type}")
        print(f"Tone duration: {tone_duration}s")
    
    announce(f"Timer started. Press Enter to begin timing.", mode, tone_type, tone_duration)

    # Wait for user to press Enter
    input("Press Enter to start timing...")

    # Record start time
    start_time = time.time()

    announce("Timer started", mode, tone_type, tone_duration)

    try:
        elapsed_minutes = 0
        while True:
            # Calculate elapsed time
            elapsed_seconds = time.time() - start_time
            current_elapsed_minutes = int(elapsed_seconds / 60)

            # Announce if a new minute has passed
            if current_elapsed_minutes > elapsed_minutes:
                elapsed_minutes = current_elapsed_minutes
                announcement = f"{elapsed_minutes} minute{'s' if elapsed_minutes != 1 else ''} elapsed"
                print(announcement)
                
                # Use appropriate tone type: bright for normal intervals, rough for milestones
                current_tone_type = tone_type
                if mode == 'tone' and elapsed_minutes % 5 == 0 and elapsed_minutes > 0:
                    # Use rough tone for 5-minute intervals
                    current_tone_type = 'rough'
                
                announce(announcement, mode, current_tone_type, tone_duration)

            # Wait for the interval
            time.sleep(interval_minutes * 60)

    except KeyboardInterrupt:
        print("\nTimer stopped by user")
        announce("Timer stopped", mode, tone_type, tone_duration)

if __name__ == "__main__":
    main()

