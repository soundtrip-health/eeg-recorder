#!/usr/bin/env python3
"""
Simple Tone Timer Script
Announces elapsed time with audio tones at regular intervals
"""

import time
import sys
import numpy as np
import argparse
try:
    import sounddevice as sd
except ImportError:
    sd = None

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

def play_tone(tone_type='bright', duration=0.3, sample_rate=44100):
    """Generate and play a tone using sounddevice"""
    if sd is None:
        print("Warning: sounddevice not installed. Cannot play tones.")
        return
    
    if tone_type == 'bright':
        tone = generate_bright_tone(duration=duration, sample_rate=sample_rate)
    else:  # rough
        tone = generate_rough_tone(duration=duration, sample_rate=sample_rate)
    
    sd.play(tone, sample_rate)
    sd.wait()

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Timer with tone announcements')
    parser.add_argument('-d', '--tone-duration', type=float, default=0.3,
                        help='Duration of tones in seconds (default: 0.3)')
    parser.add_argument('-i', '--interval', type=int, default=60,
                        help='Play tone every N seconds for milestones (default: 60, 0 to disable)')
    parser.add_argument('-r', '--runtime', type=int, default=0,
                        help='Runtime in seconds (default: 0, 0 to run forever)')
    args = parser.parse_args()
    
    # Check if sounddevice is available
    if sd is None:
        print("Error: sounddevice package is required.")
        print("Install with: pip install sounddevice numpy")
        sys.exit(1)

    # Display settings
    print("Tone Timer Script")
    print(f"Interval: {args.interval} second(s)")
    print(f"Tone duration: {args.tone_duration}s")
    print(f"Runtime: {args.runtime} seconds")
    tone_type = "bright"

    print("\nPress Enter to start timing...")
    input()

    # Countdown 3-2-1 before starting the timer
    for i in range(3, 0, -1):
        play_tone('rough', args.tone_duration)
        print(i)
        time.sleep(1 - args.tone_duration)

    play_tone(tone_type, args.tone_duration)
    target_sec = args.interval

    # Record start time
    start_time = time.time()
    
    try:
        while True:
            elapsed_seconds = time.time() - start_time
            if args.runtime > 0 and elapsed_seconds >= args.runtime:
                print("Timer finished")
                break

            if elapsed_seconds >= target_sec:
                play_tone(tone_type, args.tone_duration)
                print(f"{elapsed_seconds:0.1f} seconds elapsed")
                tone_type = "rough" if tone_type == "bright" else "bright"
                target_sec += args.interval

            # Sleep briefly to avoid busy waiting
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nTimer stopped by user")

    print(f"{elapsed_seconds:0.1f} seconds total")
    for i in range(3, 0, -1):
        play_tone('rough', args.tone_duration * 0.7)  # Shorter rough tone for stop
        time.sleep(0.2)

if __name__ == "__main__":
    main()

