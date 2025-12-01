#!/usr/bin/env python3
"""
Development wrapper for trading scheduler with auto-reload
Uses watchdog to monitor file changes and restart scheduler
"""
import sys
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class SchedulerReloader(FileSystemEventHandler):
    """Handle file changes and restart scheduler"""
    
    def __init__(self):
        self.process = None
        self.restart_scheduler()
    
    def on_modified(self, event):
        """Called when a file is modified"""
        if event.is_directory:
            return
        
        # Only restart for Python files, config files, and prompts
        if event.src_path.endswith(('.py', '.yaml', '.txt', '.yml')):
            print(f"\n🔄 Change detected: {event.src_path}")
            print("Restarting scheduler...\n")
            self.restart_scheduler()
    
    def restart_scheduler(self):
        """Kill old process and start new one"""
        if self.process:
            print("Stopping old scheduler process...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        
        print("Starting scheduler...")
        self.process = subprocess.Popen(
            [sys.executable, "trading_scheduler.py"],
            cwd=Path(__file__).parent
        )

def main():
    """Main watchdog loop"""
    print("=" * 80)
    print("🔧 DEVELOPMENT MODE - Auto-reload enabled")
    print("=" * 80)
    print("\nWatching for changes in:")
    print("  - tools/")
    print("  - reki/")
    print("  - trading_scheduler.py")
    print("  - trading_config.yaml")
    print("\nPress Ctrl+C to stop\n")
    print("=" * 80 + "\n")
    
    # Create event handler and observer
    event_handler = SchedulerReloader()
    observer = Observer()
    
    # Watch the main directory and subdirectories
    root_path = Path(__file__).parent
    observer.schedule(event_handler, str(root_path / "tools"), recursive=True)
    observer.schedule(event_handler, str(root_path / "reki"), recursive=True)
    observer.schedule(event_handler, str(root_path), recursive=False)
    
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping development server...")
        if event_handler.process:
            event_handler.process.terminate()
            event_handler.process.wait()
        observer.stop()
    
    observer.join()
    print("Development server stopped.")

if __name__ == "__main__":
    main()
