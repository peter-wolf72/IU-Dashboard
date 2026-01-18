import tkinter as tk
from gui import DashboardGUI

def main():
    main_window = tk.Tk()
    dashboard_app = DashboardGUI(main_window)
    dashboard_app.pack(fill="both", expand=True)
    main_window.mainloop()    

if __name__ == "__main__":
    main()
