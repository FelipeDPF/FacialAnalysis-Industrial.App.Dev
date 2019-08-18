from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter import Toplevel
import tkinter.scrolledtext as tkst
import cv2
import PIL.Image
import PIL.ImageTk
import time
import dlib
from imutils import face_utils
from scipy.spatial import distance as dist
from timeit import default_timer as timer
import numpy as np
from keras.models import load_model
from statistics import mode
from utils.datasets import get_labels
from utils.inference import detect_faces
from utils.inference import draw_text
from utils.inference import draw_bounding_box
from utils.inference import apply_offsets
from utils.inference import load_detection_model
from utils.preprocessor import preprocess_input
import tensorflow as tf
from prettytable import PrettyTable
import tkinter as tk
import os

#global var
is_recording = False
is_closing = False
out = None
out_file_name = "output.avi"

# table for emotion facial detection
emotionTable = PrettyTable()
emotionTable.field_names = ["Date and Time", "Emotion"]

# table for dlib facial detection
dlibTable = PrettyTable()
dlibTable.field_names = ["Date and Time", "Left Eye ratio", "Right eye ratio", "Eyes state"]

emotion_model_path = './models/emotion_model.hdf5'
emotion_labels = get_labels('fer2013')
# hyper-parameters for bounding boxes shape
frame_window = 10
emotion_offsets = (20, 40)
# loading models
face_cascade = cv2.CascadeClassifier(
    './models/haarcascade_frontalface_default.xml')

# starting lists for calculating modes
emotion_window = []

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")


class App:
    """
    This class is used
    for processing the video stream and
    using the dlib to analise each incoming frame.
    Attributes
    ----------
    emotions_text : model
        used to display the emotions on the text box
    dlib_text : graph
       used to display the dlib results on the text box
    Methods
    -------
    __init__(self, window, window_title, video_source=0)
        Author: Nicolas Daigle
        Description: Initialize the program and loads the GUI
    setEmotionResults(self, emotion, emotion_probability)
        Author: Ahmad Kaafi
        Description: Used to retrieve  the current emotion from Emotioncapture
    setdlibResults(self, leftAspectRatio, rightAspectRatio, blinks)
        Author: Ahmad Kaafi
        Description: Used to retrieve  the aspect ratios and the state of the eyes(Opened/closed)
    getEmotionResults(self)
        Author: Ahmad Kaafi
        Description: Returns the current emotion state, used to display the results
    getDlibResults(self)
        Author: Ahmad Kaafi
        Description: Returns the current aspect ratios and the state of the eyes(Opened/closed), used to display the results
    aboutPanel(self, *args)
        Author: Nicolas Daigle
        Description: Creates a popup message box for application about info
    closeApplication(self)
        Author: Nicolas Daigle
        Description: Any form of closing the application will call this function and check if video recording is on or not.
    saveFilePopup(self, *args)
        Author: Nicolas Daigle
        Description: Create an initializes a popup window for save file menu bar functionality
    saveEmotionInfo(self, *args):
        Author: Felipe de Paula
        Description: Save emotions data results into csv file using pretty table
    saveDlibInfo(self, *args):
        Author: Felipe de Paula
        Description: Save dlib data results into csv file using pretty table
    setNormal(self, *args)
        Author: Jacob Jewell, Nicolas Daigle
        Description: Use the standard video capture with no processing
    setDlib(self, *args)
        Author: Jacob Jewell, Nicolas Daigle
        Description: Sets the camera to process each frame though the shape predictor
    setEmotion(self, *args)
        Author: Jacob Jewell, Nicolas Daigle
        Description: Sets the camera to process each frame though the emotion predictor
    update(self)
        Author: Jacob Jewell
        Description: Updates the live data (Camera output, text boxes)
    record(self)
        Author :- Aman Multani & Maryam Awan
        Description:- record the live feed from the webcam for storeg purpose
    stop_recording(self)
        Author :- Aman Multani & Maryam Awan
        Description :- To the stop the recording of gthe live feed and
        popups the option for saving the recorded feed
    openfile (self)
        Author :- Aman Multani & Maryam Awan
        Description:- To re-run the recorded live feed from webcam
    detect_color(self)
        Author :- Aman Multani & Maryam Awan
        Description:- To detect the color of the object/human
        or anything infront of the webcam
    """
    emotions_text = ""
    dlib_text = ""

    def __init__(self, window, window_title, video_source=0):
        self.window = window
        self.window.protocol("WM_DELETE_WINDOW", self.closeApplication)
        self.window.title(window_title)
        self.window.iconbitmap(r'Asset_10.ico')
        # self.window.geometry("1075x569")
        self.window.configure(background="#716D6B")
        self.window.resizable(False, False)
        self.video_source = video_source

        ### These StringVar are tied to the entry boxes and hold whatever value is in them.
        # TODO Take these values and store at the top of the table on save
        self.examineeName = StringVar()
        self.examineeName.set("")
        self.examinerName = StringVar()
        self.examinerName.set("")
        self.case = StringVar()
        self.case.set("")

        # initialize menubar to main window
        menuBar = Menu(window)
        # initialize filemenu, exit command and add to menubar
        fileMenu = Menu(menuBar, tearoff=0)
        fileMenu.add_command(label="Open", command=self.openFile,accelerator="Ctrl+O") 
        fileMenu.add_command(label="Save Data", accelerator="Ctrl+S",command=self.saveFilePopup)  
        self.window.bind("<Control-o>", self.openFile)
        self.window.bind("<Control-s>", self.saveFilePopup)

        fileMenu.add_separator()
        fileMenu.add_command(label="Record Video", command=self.record,accelerator="Ctrl+R")  
        fileMenu.add_command(label="Stop Recording", command=self.stop_recording, accelerator="Ctrl+T")
        self.window.bind("<Control-r>", lambda e: self.record())
        self.window.bind("<Control-t>", lambda e: self.stop_recording())

        fileMenu.add_separator()
        fileMenu.add_command(label="Exit", command=self.closeApplication, accelerator="Ctrl+Q")
        self.window.bind("<Control-q>", lambda e: self.closeApplication())
        menuBar.add_cascade(label="File", menu=fileMenu)

        # initialize viewmenu
        viewMenu = Menu(menuBar, tearoff=0)
        # initialize changeView submenu to viewmenu
        changeView = Menu(viewMenu, tearoff=0)
        changeView.add_command(label="Normal View", command=self.setNormal, accelerator="Ctrl+F")
        self.window.bind("<Control-f>", self.setNormal)
        changeView.add_command(label="Facial Analysis", command=self.setDlib, accelerator="Ctrl+G")
        self.window.bind("<Control-g>", self.setDlib)
        changeView.add_command(label="Emotion Detector", command=self.setEmotion, accelerator="Ctrl+H")
        self.window.bind("<Control-h>", self.setEmotion)
        # Add submenu to viewmenu
        viewMenu.add_cascade(label="Change View", menu=changeView)
        viewMenu.add_command(label="Detect Color", command=self.detect_color, accelerator="Ctrl+D")
        self.window.bind("<Control-d>", lambda e: self.detect_color())
        menuBar.add_cascade(label="View", menu=viewMenu)

        # initialize help menu
        helpMenu = Menu(menuBar, tearoff=0)
        helpMenu.add_command(label="About", command=self.aboutPanel, accelerator="Ctrl+I")
        self.window.bind("<Control-i>", self.aboutPanel)
        menuBar.add_cascade(label="Help", menu=helpMenu)

        window.config(menu=menuBar)
        self.vid = MyVideoCapture(self.video_source)

        # Text box frame
        self.dialogFrame = Frame(window, borderwidth=1, relief="sunken", background="#716D6B")
        self.dialogFrame.grid(row=1, column=1, rowspan=2, sticky=N+S+W, padx=(2, 2), pady=(8, 8))
        self.topDataDisplay = tkst.ScrolledText(self.dialogFrame, wrap=NONE, borderwidth=1, width=50, height=15.5,state="normal", font='System 10 bold')
        self.topDataDisplay.grid(row=0, column=0, sticky=NSEW, pady=(0, 2))
        self.botDataDisplay = tkst.ScrolledText(self.dialogFrame, wrap=NONE, borderwidth=1, width=50, height=15.4,state="normal", font='System 10 bold')
        self.botDataDisplay.grid(row=2, column=0, sticky=NSEW, pady=(2, 0))

        # Middle Frame/Save/Record Buttons
        self.midFrame = Frame(self.dialogFrame, borderwidth=1, relief="ridge", width=50, height=50,background="#ABA6A4")
        self.midFrame.grid(row=1, column=0, sticky=NSEW)

        self.btn_saveEmotion = Button(self.midFrame, text="Save Emotion Data\u2BA5", width=15,command=self.saveEmotionInfo)
        self.btn_saveEmotion.configure(background="white", foreground="black")
        self.btn_saveEmotion.pack(side=LEFT, padx=(20, 0), pady=(10, 10))

        self.btn_saveDlib = Button(self.midFrame, text="Save Facial Data\u2BA7", width=15, command=self.saveDlibInfo)
        self.btn_saveDlib.configure(background="white", foreground="black")
        self.btn_saveDlib.pack(side=RIGHT, padx=(0, 20), pady=(10, 10))

        self.recordImage = PhotoImage(file='rsz_asset_5.png')
        self.btn_recordVideo = Button(self.midFrame, image=self.recordImage, width=25, height=25, command=self.record)
        self.btn_recordVideo.configure(background="#ABA6A4", foreground="black")
        self.btn_recordVideo.pack(side=RIGHT, padx=(0, 60), pady=(10, 10))

        # north frame/metadata input
        self.northFrame = Frame(window, borderwidth=1, relief="ridge", width=1075, background="#ABA6A4")
        self.northFrame.grid(row=0, column=0, columnspan=2, sticky=N+E+W, pady=(8, 0))

        # examinee, examiner and case input form
        self.examineeLabel = Label(self.northFrame, text="Examinee's Name:", background="#ABA6A4").pack(side=LEFT,padx=(50, 10))
        self.examineeNameBox = Entry(self.northFrame, textvariable=self.examineeName, width=30).pack(side=LEFT,padx=(0, 0),pady=(10, 10))

        self.examinerLabel = Label(self.northFrame, text="Examiner's Name:", background="#ABA6A4").pack(side=LEFT,padx=(65, 10))
        self.examinerNameBox = Entry(self.northFrame, textvariable=self.examinerName, width=30).pack(side=LEFT,padx=(0, 0),pady=(10, 10))

        self.caseLabel = Label(self.northFrame, text="Case:", background="#ABA6A4").pack(side=LEFT, padx=(75, 10))
        self.caseBox = Entry(self.northFrame, textvariable=self.case, width=30).pack(side=LEFT, padx=(0, 50),pady=(10, 10))

        # south frame/button panel
        self.southFrame = Frame(window, borderwidth=1, relief="ridge", width=1075, background="#ABA6A4")
        self.southFrame.grid(row=2, column=0, columnspan=2, sticky=NSEW, padx=(2, 427), pady=(0, 8))

        self.btn_dlib = Button(self.southFrame, text="Facial Analysis", width=20, command=self.setDlib)
        self.btn_dlib.configure(background="white", foreground="black")
        self.btn_dlib.pack(side=LEFT, padx=(50, 0), pady=(10, 10))

        self.btn_emotion = Button(self.southFrame, text="Emotion Detector", width=20, command=self.setEmotion)
        self.btn_emotion.configure(background="white", foreground="black")
        self.btn_emotion.pack(side=RIGHT, padx=(0, 50), pady=(10, 10))

        self.btn_normal = Button(self.southFrame, text="Normal Mode", width=20, command=self.setNormal)
        self.btn_normal.configure(background="#7EB4D4", foreground="black")
        self.btn_normal.pack(side=RIGHT, padx=(0, 45), pady=(10, 10))

        # VideoStream canvas
        self.canvas = Canvas(width=self.vid.width, height=self.vid.height)
        self.canvas.grid(row=1, column=0, sticky=N+E+W, padx=(2, 2), pady=(8, 0))

        self.delay = 3
        self.update()

        self.window.mainloop()

    def setEmotionResults(self, emotion, emotion_probability):
        # Add table for emotions detector
        emotionTable.add_row([time.strftime("%a, %d %b %Y %H:%M:%S"), emotion])

        # Display emotion detected info
        App.emotions_text = "\t\tEmotion Predictor\n\n" + time.strftime(
            "%a, %d %b %Y %H:%M:%S") + "\n\nList of emotions : \n\n\t- HAPPY \n\t- SAD \n\t- ANGRY \n\t- NEUTRAL \n\t- SURPRISE \n\t- FEAR\n" + "\nCurrently predicting " + emotion.upper() + \
                            " with a " + \
                            "{0:.2f}".format(emotion_probability * 100) + "% accuracy"

    def setdlibResults(self, leftAspectRatio, rightAspectRatio, blinks, *args):
        # Add table for data analysis
        dlibTable.add_row([time.strftime("%a, %d %b %Y %H:%M:%S"), "{0:.5f}".format(leftAspectRatio),"{0:.5f}".format(rightAspectRatio), blinks])

        # Display dlib detected info
        App.dlib_text = "\t\tDeep Learning\n\n" + time.strftime(
            "%a, %d %b %Y %H:%M:%S") + "\n\nDetecting Blinks : " + blinks + "\n\nLeft Eye Aspect Ratio : " + "{0:.5f}".format(leftAspectRatio) + "\n\nRight Eye Aspect Ratio : " + "{0:.5f}".format(rightAspectRatio)

    def getEmotionResults(self):
        return App.emotions_text

    def getDlibResults(self):
        return App.dlib_text

    def aboutPanel(self, *args):
        # Spacing in string is for formatting
        messagebox.showinfo("About", "This is an AI Facial Analysis application\n           Developed for CST8354\n\tby team Green Bit")

    def closeApplication(self):
        global is_closing
        is_closing = True
        if is_recording == True:
            self.stop_recording()
        else:
            self.window.destroy()

    def saveFilePopup(self, *args):
        # Create and Initialize Popup Window
        saveWindow = Toplevel()
        saveWindow.geometry("300x150")
        saveWindow.config(background="#FFFFFF")
        self.window.iconbitmap(r'Asset_10.ico')
        saveWindow.resizable(False, False)
        saveWindow.title("Save File")

        # Popup message
        message = Label(saveWindow, text="Choose which data to save?")
        msgFont = ('times', 14, 'normal')
        message.config(font=msgFont, background="#FFFFFF", height=5, width=30)
        message.grid(row=0, column=0, rowspan=2, columnspan=2, sticky=NSEW)

        # Frame for buttons
        buttonFrame = Frame(saveWindow, borderwidth=0, background="#ABA6A4")
        buttonFrame.grid(row=2, column=0, columnspan=2, sticky=S + E + W, pady=(0, 0))
        emotionBtn = Button(buttonFrame, text="Emotion Data", command=self.saveEmotionInfo, background="#FFFFFF").pack(
            side=LEFT, padx=(50, 0), pady=(7, 7))
        dlibBtn = Button(buttonFrame, text="Facial Data", command=self.saveDlibInfo, background="#FFFFFF").pack(
            side=RIGHT, padx=(0, 50), pady=(7, 7))

    def saveEmotionInfo(self, *args):
        print(emotionTable.get_string(
            title="Examinee's: " + self.examineeName.get() + ", Examiner's: " + self.examinerName.get() + ", Case: " + self.case.get()))
        with open('emotionTable.csv', 'w') as w:
            w.write(str(emotionTable.get_string(title="Examinee's: " + self.examineeName.get() + ", Examiner's: " + self.examinerName.get() + ", Case: " + self.case.get())))

    def saveDlibInfo(self, *args):
        print(dlibTable.get_string(
            title="Examinee's: " + self.examineeName.get() + ", Examiner's: " + self.examinerName.get() + ", Case: " + self.case.get()))
        with open('dlibTable.csv', 'w') as w:
            w.write(str(dlibTable.get_string(title="Examinee's: " + self.examineeName.get() + ", Examiner's: " + self.examinerName.get() + ", Case: " + self.case.get())))

    def setNormal(self, *args):
        self.btn_dlib.configure(background='white', foreground='black')
        self.btn_emotion.configure(background='white', foreground='black')
        self.btn_normal.configure(background='#7EB4D4', foreground='black')
        self.vid = MyVideoCapture(self.video_source)

    def setDlib(self, *args):
        self.btn_normal.configure(background='white', foreground='black')
        self.btn_emotion.configure(background='white', foreground='black')
        self.btn_dlib.configure(background='#7EB4D4', foreground='black')
        self.vid = FacialCapture(self.video_source)

    def setEmotion(self, *args):
        self.btn_normal.configure(background='white', foreground='black')
        self.btn_dlib.configure(background='white', foreground='black')
        self.btn_emotion.configure(background='#7EB4D4', foreground='black')
        self.vid = emotionCapture(self.video_source)

    def update(self):
        # Get a frame from the video source
        ret, frame = self.vid.get_frame()
        if ret:
            self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            self.canvas.create_image(0, 0, image=self.photo, anchor=NW)
            recOnLabel = self.canvas.create_text(10, 10, anchor=NW, text="REC", fill="#FF0000", font="Times 16 bold", state=HIDDEN)
            if is_recording == True:
                self.canvas.itemconfig(recOnLabel, state="normal")
            else:
                self.canvas.itemconfig(recOnLabel, state="hidden")          

            self.topDataDisplay.delete("1.0", END)
            self.topDataDisplay.insert(INSERT, self.getEmotionResults())
            self.botDataDisplay.delete("1.0", END)
            self.botDataDisplay.insert(INSERT, self.getDlibResults())
        self.window.after(self.delay, self.update)

    def record(self):
        # Author :- Aman Multani and Maryam Awan
        # Description :- we are using the global varible for the boolean expression
        #                to set the is_recording for true while the button is not clicked
        global is_recording
        global out
        # for the Recording off
        if is_recording == True:
            self.stop_recording()
            return

        frame_width = int(cv2.VideoCapture(self.video_source).get(3))
        frame_height = int(cv2.VideoCapture(self.video_source).get(4))

        # Define the codec and create VideoWriter object.The output is stored in 'output.avi' file.
        out = cv2.VideoWriter(out_file_name, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 25,(frame_width, frame_height))
        out.set(cv2.CAP_PROP_POS_AVI_RATIO, 1)
        is_recording = True
        # self.setEmotion()

    def stop_recording(self):
        # Author :- Aman Multani and Maryam Awan

        global is_recording
        global is_closing
        global out
        if is_recording == True:
            MsgBox = tk.messagebox.askquestion('Save Recording', 'Are you sure you want to save the recording?', icon='info')
            out.release()
            if MsgBox == 'no':
                os.remove(out_file_name)
            is_recording = False

        if is_closing == True:
            self.window.destroy()


    # to open the video
    def openFile(self, *args):
        # author :- Aman Multani and Maryam Awan

        Tk().withdraw()
        filename = filedialog.askopenfilename()
        print(filename)
        cap = cv2.VideoCapture(filename)
        while cap.isOpened():
            ret, frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            cv2.imshow('frame', gray)
            if cv2.waitKey(35) & 0xFF == ord('q'):
              cv2.destroyAllWindows()
              cap.release()
     

    #   def __del__(self):
    #   self.stop_recording()

    def detect_color(self):
        # Author :- Aman Multani and Maryam Awan
        # Description:- we first defind the range of different color for just
        #               test pupose we are using here Red, yellow and blue
        #               then we track the object from its height and the weight and
        #                using the FONT_HERSHEY_SIMPLEX we detect the color from the given range.
        global is_recording
        global out

        # capturing video through webcam
        out = cv2.VideoCapture(0)

        while True:
            _, img = out.read()

            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            # definig the range of red color
            red_lower = np.array([136, 87, 111], np.uint8)
            red_upper = np.array([186, 255, 255], np.uint8)

            # defining the Range of Blue color
            blue_lower = np.array([99, 115, 150], np.uint8)
            blue_upper = np.array([110, 255, 255], np.uint8)

            # defining the Range of yellow color
            yellow_lower = np.array([22, 60, 200], np.uint8)
            yellow_upper = np.array([60, 255, 255], np.uint8)

            red = cv2.inRange(hsv, red_lower, red_upper)
            blue = cv2.inRange(hsv, blue_lower, blue_upper)
            yellow = cv2.inRange(hsv, yellow_lower, yellow_upper)

            # Morphological transformation, Dilation
            kernal = np.ones((5, 5), "uint8")

            red = cv2.dilate(red, kernal)
            res = cv2.bitwise_and(img, img, mask=red)

            blue = cv2.dilate(blue, kernal)
            res1 = cv2.bitwise_and(img, img, mask=blue)

            yellow = cv2.dilate(yellow, kernal)
            res2 = cv2.bitwise_and(img, img, mask=yellow)

            # Tracking the Red Color
            (contours,hierarchy) = cv2.findContours(red, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            for pic, contour in enumerate(contours):
                area = cv2.contourArea(contour)
                if area > 300:
                    x, y, w, h = cv2.boundingRect(contour)
                    img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    cv2.putText(img, "red color", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255))

            # Tracking the Blue Color
            (contours,hierarchy) = cv2.findContours(blue, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            for pic, contour in enumerate(contours):
                area = cv2.contourArea(contour)
                if area > 300:
                    x, y, w, h = cv2.boundingRect(contour)
                    img = cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    cv2.putText(img, "blue color", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0))

            # Tracking the yellow Color
            (contours,hierarchy) = cv2.findContours(yellow, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            for pic, contour in enumerate(contours):
                area = cv2.contourArea(contour)
                if area > 300:
                    x, y, w, h = cv2.boundingRect(contour)
                    img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(img, "yellow  color", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0))

            cv2.imshow("Color Tracking", img)
            is_recording = True
            if cv2.waitKey(10) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                out.release()
                break


class MyVideoCapture:
    """
    This class is used for processing the basic video stream.
    Attributes
    ----------
    none
    Methods
    -------
    __init__(self)
        Author: Jacob Jewell
        Description: Initalises the class to use the default camera (source: 0)
    get_frame(self)
        Author: Jacob Jewell
        Description: returns the live frame from the video feed
    __del__(self)
        Author: Jacob Jewell
        Description: release the video feed for proper termination
    """

    def __init__(self, video_source=0):
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)
        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def get_frame(self):
        global out
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                # Write the frame into the file 'output.avi'
                if is_recording:
                    out.write(frame)

                # Return a boolean success flag and the current frame converted to BGR
                return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            else:
                return (ret, None)
        else:
            return (ret, None)

    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()


class FacialCapture(App):
    """
    This class is used for processing the video stream and
    using the dlib to analise each incoming frame.
    Attributes
    ----------
    none
    Methods
    -------
    __init__(self)
        Author: Jacob Jewell
        Description: Initalises the class to use the default camera (source: 0)
    eye_aspect_ratio(self, eye):
        Author: Ahmad Kaafi
        Description: Compute the euclidean distances between the two sets of vertical eye landmarks (x, y)-coordinates
    get_frame(self):
        Author: Jacob Jewell, Ahmad Kaafi
        Description: returns the live frame from the video feed processes through the shape predictor
    __del__(self)
        Author: Jacob Jewell
        Description: release the video feed for proper termination
    """

    def __init__(self, video_source=0):
        self.video = cv2.VideoCapture(video_source)
        if not self.video.isOpened():
            raise ValueError("Unable to open video source", video_source)
        # Get video source width and height
        self.width = self.video.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.video.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def eye_aspect_ratio(self, eye):
        # compute the euclidean distances between the two sets of
        # vertical eye landmarks (x, y)-coordinates
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])

        # compute the euclidean distance between the horizontal
        # eye landmark (x, y)-coordinates
        C = dist.euclidean(eye[0], eye[3])

        # compute the eye aspect ratio
        ear = (A + B) / (2.0 * C)

        # return the eye aspect ratio
        return ear

    def get_frame(self):
        global out
        EYE_AR_THRESH = 0.17

        if self.video.isOpened():
            ret, image = self.video.read()
            if ret:
                # Write the frame into the file 'output.avi'
                if is_recording:
                    out.write(image)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            rects = detector(gray, 0)  # detect faces in the grayscale frame
            (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
            (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

            for rect in rects:

                shape = predictor(gray, rect)
                shape = face_utils.shape_to_np(shape)

                #################################################################
                ############### Checking if eyes are closed/open ################
                #################################################################
                # grab the indexes of the facial landmarks for the left and
                # right eye, mouth respectively
                leftEye = shape[lStart:lEnd]
                rightEye = shape[rStart:rEnd]
                leftEAR = FacialCapture.eye_aspect_ratio(self, leftEye)
                rightEAR = FacialCapture.eye_aspect_ratio(self, rightEye)

                # loop over the (x, y)-coordinates for the facial landmarks
                for (x, y) in shape:
                    cv2.circle(image, (x, y), 1, (0, 255, 0), -1)
                    ear = (rightEAR + leftEAR) / 2

                    leftEyeHull = cv2.convexHull(leftEye)
                    rightEyeHull = cv2.convexHull(rightEye)
                    cv2.drawContours(image, [leftEyeHull], -1, (0, 255, 0), 1)
                    cv2.drawContours(image, [rightEyeHull], -1, (0, 255, 0), 1)
                    # check to see if the eye aspect ratio is below the blink
                    # threshold, and if so, increment the blink frame counter
                    if ear < EYE_AR_THRESH:
                        blink = "Eyes closed"
                    # otherwise, the eye aspect ratio is not below the blink
                    # threshold
                    else:
                        blink = "Eyes open"

                    # loop over the (x, y)-coordinates for the facial landmarks
                    App.setdlibResults(self, leftEAR, rightEAR, blink)

            if ret:
                return (ret, cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            else:
                return (ret, None)
        else:
            return (ret, None)

    def __del__(self):
        if self.video.isOpened():
            self.video.release()


class emotionCapture(App):
    """
    This class is used for processing the video stream and
    using the emotion classifier to analise each incoming frame
    to predict a person's live emotion.
    Attributes
    ----------
    emotion_classifier : model
        a classifier containing the loaded model of the emotion model
    graph : graph
        used to get the graph
    emotion_target_size : shape
        used to get the input model shapes for inference
    Methods
    -------
    __init__(self)
        Author: Jacob Jewell
        Description: Initalises the class to use the default camera (source: 0)
    get_frame(self)
        Author: Jacob Jewell, Maryum
        Description: returns the live frame from the video feed processes through the emotion predictor
    __del__(self)
        Author: Jacob Jewell
        Description: release the video feed for proper termination
    """

    emotion_classifier = load_model(emotion_model_path)
    graph = tf.get_default_graph()
    emotion_target_size = emotion_classifier.input_shape[1:3]

    def __init__(self, video_source=0):
        global out
        self.video = cv2.VideoCapture(video_source)
        if not self.video.isOpened():
            raise ValueError("Unable to open video source", video_source)
        # Get video source width and height

    def get_frame(self):
        global out
        if self.video.isOpened():
            ret, image = self.video.read()

            if ret:
                # Write the frame into the file 'output.avi'
                if is_recording:
                    out.write(image)

            # Default resolutions of the frame are obtained.The default resolutions are system dependent.
            # We convert the resolutions from float to integer.

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            # determine the facial landmarks for the face region, then
            # convert the facial landmark (x, y)-coordinates to a NumPy
            # array
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30),
                                                  flags=cv2.CASCADE_SCALE_IMAGE)
            emotion_text = 'NEUTRAL'
            for face_coordinates in faces:
                x1, x2, y1, y2 = apply_offsets(
                    face_coordinates, emotion_offsets)
                gray_face = gray[y1:y2, x1:x2]
                try:
                    gray_face = cv2.resize(gray_face, self.emotion_target_size)
                except:
                    continue
                gray_face = preprocess_input(gray_face, True)
                gray_face = np.expand_dims(gray_face, 0)
                gray_face = np.expand_dims(gray_face, -1)
                with self.graph.as_default():
                    emotion_prediction = self.emotion_classifier.predict(
                        gray_face)
                    emotion_probability = np.max(emotion_prediction)
                    emotion_label_arg = np.argmax(emotion_prediction)
                    emotion_text = emotion_labels[emotion_label_arg]
                    emotion_window.append(emotion_text)
                    if len(emotion_window) > frame_window:
                        emotion_window.pop(0)
                try:
                    emotion_mode = mode(emotion_window)
                except:
                    continue

                if emotion_text == "ANGRY":
                    color = emotion_probability * np.asarray((255, 0, 0))
                elif emotion_text == "SAD":
                    color = emotion_probability * np.asarray((0, 0, 255))
                elif emotion_text == "HAPPY":
                    color = emotion_probability * np.asarray((255, 255, 0))
                elif emotion_text == "SURPRISE":
                    color = emotion_probability * np.asarray((0, 255, 255))
                else:
                    color = emotion_probability * np.asarray((0, 255, 0))

                App.setEmotionResults(self, emotion_text, emotion_probability)
                color = color.astype(int)
                color = color.tolist()

                draw_bounding_box(face_coordinates, rgb_image, color)
                draw_text(face_coordinates, rgb_image, emotion_mode,
                          color, 0, -45, 1, 1)

            bgr_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)
            data_emotion = np.concatenate((image, bgr_image), axis=1)

            if ret:
                return (ret, cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB))
            else:
                return (ret, None)
        else:
            return (ret, None)

    def __del__(self):
        if self.video.isOpened():
            self.video.release()


# Create a window and pass it to the Application object
App(Tk(), "GreenBit - Facial Analysis")
# root.protocol('WM_DELETE_WINDOW', callback)
