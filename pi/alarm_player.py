import os
import subprocess
import sys
import time
import wave

BASE_DIR = os.path.expanduser("~/SafeStepAI")
AUDIO_DIR = os.path.join(BASE_DIR, "warning_audio")
TRIGGER_PATH = os.path.join(BASE_DIR, "trigger")
POLL_SEC = 0.2

# The one sound file that is played for every alarm.
ALARM_FILE = "alert.wav"

# Silence between the end of one playback and the start of the next.
GAP_SEC = 3.0


def wav_seconds(path):
    try:
        with wave.open(path) as w:
            return w.getnframes() / w.getframerate()
    except Exception:
        return None


def get_mtime():
    try:
        return os.stat(TRIGGER_PATH).st_mtime_ns
    except FileNotFoundError:
        return None


def play(path):
    """Start playing the file. Returns the process, or None on failure."""
    try:
        return subprocess.Popen(["aplay", "-q", path])
    except OSError as e:
        print(f"Cannot start aplay ({type(e).__name__})")
        return None


def main():
    path = os.path.join(AUDIO_DIR, ALARM_FILE)
    if not os.path.isfile(path):
        print(f"Sound file not found: {path}")
        sys.exit(1)

    sec = wav_seconds(path)
    if sec is None:
        print(f"Cannot read as WAV: {path}")
        sys.exit(1)
    print(f"Sound file: {ALARM_FILE} ({sec:.1f} sec), gap {GAP_SEC:.1f} sec")

    if "--test" in sys.argv:
        proc = play(path)
        if proc is not None:
            proc.wait()
        return

    # Create the trigger file as the current user, so that it can be touched later.
    os.makedirs(os.path.dirname(TRIGGER_PATH), exist_ok=True)
    with open(TRIGGER_PATH, "a"):
        pass

    last_mtime = get_mtime()
    proc = None
    pending = False        # a detection is waiting to be played
    next_allowed = 0.0     # no playback may start before this time (monotonic)
    print(f"Alarm player started. Watching {TRIGGER_PATH}")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            mtime = get_mtime()
            if mtime is not None and mtime != last_mtime:
                last_mtime = mtime
                if pending:
                    print("Trigger detected. Already waiting to play.")
                elif proc is not None or time.monotonic() < next_allowed:
                    print("Trigger detected. Will play after the current sound.")
                else:
                    print("Trigger detected.")
                # Many detections during playback are merged into one more playback.
                pending = True

            if proc is not None and proc.poll() is not None:
                # The playback has just finished: start the gap.
                proc = None
                next_allowed = time.monotonic() + GAP_SEC

            if pending and proc is None and time.monotonic() >= next_allowed:
                pending = False
                print("Playing sound.")
                proc = play(path)
                if proc is None:
                    next_allowed = time.monotonic() + GAP_SEC

            time.sleep(POLL_SEC)
    except KeyboardInterrupt:
        print("Stopped.")
        if proc is not None and proc.poll() is None:
            proc.terminate()


if __name__ == "__main__":
    main()