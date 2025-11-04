import sys
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ChangeHandler(FileSystemEventHandler):
    """Restarts the script when a .py file is modified."""
    def __init__(self):
        self.process = None
        self.start_process()

    def start_process(self):
        """Starts the main application script as a subprocess."""
        if self.process:
            self.process.kill()
            self.process.wait()
        
        print("🚀 Starting reki agent...")
        # Use the same Python executable that's running this script
        python_executable = sys.executable
        self.process = subprocess.Popen([python_executable, "reki/main.py"])

    def on_modified(self, event):
        """Called when a file is modified."""
        if event.src_path.endswith(".py"):
            print(f"🐍 Change detected in {event.src_path}. Reloading...")
            self.start_process()

if __name__ == "__main__":
    path = "."  # Watch the current directory
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    
    print("👀 Watching for file changes... Press Ctrl+C to stop.")
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process:
            event_handler.process.kill()
            event_handler.process.wait()
    observer.join()
    print("👋 Watcher stopped. Goodbye!")
