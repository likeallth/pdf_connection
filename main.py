import tkinter as tk
from gui import PDFConnectionApp

def main():
    root = tk.Tk()
    app = PDFConnectionApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
