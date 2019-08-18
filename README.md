# GreenBit
Here is the source code for our Facial Recognition program.


Road Map
  - the facial landmarks
  - blink counter
  - eye aspect ratio
  - mouth aspect ratio(Version 0.6)
  - eye tracker (Version 0.7)
  - Determine which way a person is looking (Version 0.7)
  - Write the table to a file (Version 0.7)
  - Eye timer to see how long eyes are closed (Version 0.8)
  - Display if eyes are opened or closed (Version 0.8) 
  
Version 1.0
  - Application UI
  - Dlib Facial landmark analysis
  - Emotion Detection 
  - Save data to cvs file
  - Record the Live feed and re-run it later 
  - Detect the color 

# Instructions to run this code (as a developer) 
### 1.1 -> Follow the instruction
   https://www.learnopencv.com/install-opencv-3-and-dlib-on-windows-python-only/
### 1.2 -> When you get to setp 3.2, after the first 2 commands, install cmake (pip install cmake), then use this command to install dlib: 
  conda install -c conda-forge dlib
### 2.0 -> Turn on the virtual environment (using anaconda):
  activate opencv-env
### 3.0 -> Install the required Libraries:
  - pip install numpy scipy matplotlib scikit-learn jupyter
  - pip install opencv-contrib-python
  - conda install -c conda-forge dlib
  - pip uninstall numpy
  - pip install -U numpy
  - pip install tensorflow
  - pip install opencv-python
  - pip install pillow
  - pip install pandas
  - pip install matplotlib
  - pip install h5py
  - pip install keras
  - pip install imutils
  - pip install PTable
### 4.0 -> Command to run the Application:  
  python start.py
## Required data file can be found here:
https://github.com/AKSHAYUBHAT/TensorFace/blob/master/openface/models/dlib/shape_predictor_68_face_landmarks.dat


