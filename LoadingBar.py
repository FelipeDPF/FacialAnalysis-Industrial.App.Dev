from tkinter import *
from PIL import Image, ImageTk
import ttk

class DemoSplashScreen:
    def __init__(self, parent):
        self.parent = parent

        self.aturSplash()
        self.aturWindow()

    def aturSplash(self):
        self.gambar = Image.open("Green.png")
        self.imgSplash = ImageTk.PhotoImage(self.gambar)

    def aturWindow(self):
        lebar, tinggi = self.gambar.size

        setengahLebar = (self.parent.winfo_screenwidth()-lebar)//2
        setengahTinggi = (self.parent.winfo_screenheight()-tinggi)//2

        self.parent.geometry("%ix%i+%i+%i"%(lebar, tinggi, setengahLebar, setengahTinggi))

        Label(self.parent, image = self.imgSplash).pack()

if __name__ == "__main__":
    root = Tk()

    root.overrideredirect(True)
    progressbar = ttk.Progressbar(orient=HORIZONTAL, length=10000, mode='determinate')
    progressbar.pack(side="bottom")
    app = DemoSplashScreen(root)
    progressbar.start()

    root.after(9300, root.destroy)
    root.mainloop()
