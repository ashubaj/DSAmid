"""
CSC200 - Data Structures & Algorithms
Solitaire (Klondike) - Main Project Entry Point

Usage:
    python main.py           # Launch Desktop Graphical Interface (Tkinter) [Default]
    python main.py --web     # Launch Responsive Web Interface (http://localhost:8080)
    python main.py --cli     # Launch Interactive Terminal (CLI) Interface
    python main.py --test    # Run Unit Test Verification Suite
"""

import sys
import os
import webbrowser
import threading
import time


def run_gui():
    import tkinter as tk
    from gui import SolitaireGUI
    root = tk.Tk()
    app = SolitaireGUI(root)
    root.mainloop()


def run_web(port=8080):
    from web_server import run_server
    url = f"http://localhost:{port}"
    print(f"==================================================")
    print(f"CSC200 Solitaire Web Server started!")
    print(f"Access the game at: {url}")
    print(f"Press Ctrl+C to stop the server.")
    print(f"==================================================")
    
    # Auto-open browser after 1 second
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        run_server(port)
    except KeyboardInterrupt:
        print("\nWeb server stopped.")


def run_cli():
    from cli import SolitaireCLI
    cli = SolitaireCLI()
    cli.run()


def run_tests():
    import unittest
    import test_solitaire
    suite = unittest.defaultTestLoader.loadTestsFromModule(test_solitaire)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


def main():
    if len(sys.argv) > 1:
        flag = sys.argv[1].lower()
        if flag in ['--web', '-w']:
            port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
            run_web(port)
            return
        elif flag in ['--cli', '-c']:
            run_cli()
            return
        elif flag in ['--test', '-t']:
            run_tests()
            return
        elif flag in ['--help', '-h']:
            print(__doc__)
            return

    # Default to GUI
    try:
        run_gui()
    except Exception as e:
        print(f"Unable to launch Tkinter GUI: {e}")
        print("Falling back to Web Interface...")
        run_web()


if __name__ == "__main__":
    main()
