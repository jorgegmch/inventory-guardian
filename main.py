import ttkbootstrap as tb
from app import GuardianInventarioApp

if __name__ == "__main__":
    root = tb.Window(themename="darkly")
    app = GuardianInventarioApp(root)
    root.mainloop()