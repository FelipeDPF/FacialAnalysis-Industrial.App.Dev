from tkinter import *
from PIL import Image, ImageTk
from tkinter import ttk

class AnimatedGIF(Label, object):
    """ 
    Author :- Maryum Awan 
    Description:- This is a splash screen which appears on the front while the gui in loading.
                - It uses ttk Progress bar control for this.
                - It shows splash screen in the centre of the screen  
                - We gather the height , wigth and the center point of the Screen 
                - using the geometry function the ceneter of the screen is determined 
    Attributes
    ----------
 

    Methods
    -------
    __init__(self, master, path)
        Description: This function is called to initialize
    getWidth(self)
        Author: Maryam
        Description: This function is called to return image width
    getHeight(self)
        Author: Maryam
        Desctiption: This function is called to return image height
    """
    
    def __init__(self, master, path, forever=True):
        self._master = master
        self._loc = 0
        self._forever = forever #flag that indicate whether animation reapeat permanently or only one time.

        self._is_running = False #flag that indicate current status (animating or not)

        im = Image.open(path) #load image of path
        self._frames = []
        i = 0
        try:
            while True:
                photoframe = ImageTk.PhotoImage(im.copy().convert('RGBA')) #load frames of image
                self._frames.append(photoframe)

                i += 1
                im.seek(i)
        except EOFError:
            pass

        self._last_index = len(self._frames) - 1
        self._image_width, self._image_height = im.size #setting image size into local variables

        try:
            self._delay = im.info['duration']
        except:
            self._delay = 100 #if can't get it, set delay to 100(ms)

        self._callback_id = None

        super(AnimatedGIF, self).__init__(master, image=self._frames[0])

    def getWidth(self):
        return self._image_width #return image width

    def getHeight(self):
        return self._image_height #return image height

root = Tk()
l = AnimatedGIF(root, "Green.PNG") #create image object that contains "Green.PNG"
l.pack()

ws = root.winfo_screenwidth() #get screen width
hs = root.winfo_screenheight() #get screen height
w = l.getWidth() #get splash image width
h = l.getHeight() #get splash image height
x = (ws / 2) - (w / 2) #get xPos for showing splash in center of screen
y = (hs / 2) - (h / 2) #get yPos for showing splash in center of screen

root.geometry('%dx%d+%d+%d' % (w, h+30, x, y)) #Set splash geometry to center of screen
root.overrideredirect(True)

progressbar = ttk.Progressbar(root, orient=HORIZONTAL, length=8000, mode='determinate') #Create progressbar that has 8000ms countdown length.
progressbar.pack(side="bottom") #Attach progressbar under splash image
progressbar.start() #Start discounting of progressbar 

root.after(15000, root.destroy) #Exit app after 15000ms
root.attributes('-topmost', 'true') #set window to topmost window so that no window can hide it.
root.overrideredirect(True)

root.mainloop()
