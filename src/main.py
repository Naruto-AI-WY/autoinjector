import sys
import os
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow

def main():
    print("Starting application...")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print(f"PYTHONPATH: {sys.path}")
    
    app = QApplication(sys.argv)
    print("Created QApplication")
    
    window = MainWindow()
    print("Created MainWindow")
    
    window.show()
    print("Showing window")
    
    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())
