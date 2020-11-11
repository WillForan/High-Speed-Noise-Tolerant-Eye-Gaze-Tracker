#!/usr/bin/env python

import os
import sys
import cv2
import pathlib
import threading
import os, shutil
import numpy as np
from tracker import auto_tracker
from gtracker import g_auto_tracker
from Interface.user import MyWidget
from PyQt5.QtGui import QIcon, QPixmap
from video_construct import video_construct
from PyQt5 import uic, QtCore, QtGui, QtWidgets
from Interface.video_player import VideoPlayer
from plotting import auto_draw
import copy
from preProcess import preprocess

class main(QtWidgets.QMainWindow):
    def __init__(self, video = None, file = None):
        #Dictionary including index and picture for each
        super().__init__()
        self.width = 0
        self.height = 0
        self.wanted = None
        self.MyWidget = None
        self.collection = {}
        self.pic_collection = {}
        self.p_r_collection = {}
        self.Video = None   # Video for the patient
        self.File = None  # Data retrived by the machine
        self.f_rate = 60 #Should be presented in the file. Don't know if could be gotten using python
        #Factor that resize the image to make the program run faster
        self.size_factor = (4,4)
        self.cropping_factor_pupil = [[0,0],[0,0]] #(start_x, end_x, start_y, end_y)
        self.cropping_factor_glint = [[0,0],[0,0]]

        #Define all the thread values
        self.g_blur  = None
        self.H_count = None
        self.th_range_glint = None

        uic.loadUi('Interface/dum.ui', self)
        self.path = str(pathlib.Path(__file__).parent.absolute())+'/input/video.mp4'
        self.setWindowTitle('Pupil Tracking')
        self.Analyze.setEnabled(False)
        self.Generate.clicked.connect(self.generate)
        self.Analyze.clicked.connect(self.analyze)
        self.Pupil_click.setEnabled(False)
        self.Glint_click.setEnabled(False)
        self.Plotting.setEnabled(False)
        self.Pupil_chose.toggled.connect(self.circle_pupil)
        self.Glint_chose.toggled.connect(self.circle_glint)
        self.Pupil_chose.setEnabled(False)
        self.Glint_chose.setEnabled(False)
        self.Pupil_click.clicked.connect(self.store_pupil)
        self.Glint_click.clicked.connect(self.store_glint)
        self.Plotting.clicked.connect(self.plot_result)
        #Only for the initial run
        self.VideoText.setText('input/run1.mov')
        self.FileText.setText('input/10997_20180818_mri_1_view.csv')
        self.player = VideoPlayer(self, self.path)
        self.show()

    #The whole purpose of this function is to use multi-threading
    def tracking(self, ROI, parameters, p_glint):
        #Initialize the eye_tracker
        track = auto_tracker(self.Video, ROI, parameters, p_glint)
        track.set_events(self.File)
        track.run_tracker()

    def gtracking(self, ROI, CPI, parameters_glint):
        track = g_auto_tracker(self.Video, ROI, CPI, parameters_glint)
        track.set_events(self.File)
        track.run_tracker()

    def video_call(self):
        #Construct all thr available files to video to be displayed
        video_construct()
        self.player.setWindowTitle("Player")
        self.player.resize(600, 400)
        self.player.show()

    #Clear everything in a folder
    def clear_folder(self, path):
        folder = path
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

    def get_ROI(self, cropping_factor):
        #ROI is x, y, x displacement and y displacement
        #Cropping factor is x, y, x1, and y1
        return (cropping_factor[0][0],\
                cropping_factor[1][0],\
                cropping_factor[0][1] - cropping_factor[0][0],\
                cropping_factor[1][1] - cropping_factor[1][0]) 

    def get_center(self, ROI):
        return (ROI[0] + ROI[2]/2, ROI[1] + ROI[3]/2)

    def pupil_threshold(self, center, sf, CPI, parameters):
        pp = preprocess(center, sf, CPI, parameters['blur'], parameters['canny'])
        return pp.start()

    def glint_threshold(self, center, sf, CPI, parameters):
        pp = preprocess(center, sf, CPI, parameters['blur'], parameters['canny'])
        return pp.d_glint()

    def get_blur(self, sf, CPI, parameters, ROI_pupil, ROI_glint):
        bb = preprocess(None, sf, CPI, parameters['blur'], parameters['canny'])
        self.g_blur = bb.anal_blur(ROI_pupil, ROI_glint, self.Video)

    #This is for the count in Glint detection Hough Transform
    def get_count(self, sf, ROI, CPI, parameters):
        glint_CPI = copy.deepcopy(CPI)
        cc = preprocess(None, sf, glint_CPI, parameters['blur'], parameters['canny'])
        self.H_count = cc.g_count(ROI, glint_CPI, parameters, self.Video)

    def analyze(self):

        self.Analyze.setEnabled(False)
        self.Plotting.setEnabled(True)

        parameters_pupil = {'blur': (20, 20), 'canny': (40, 50)}
        parameters_glint = {'blur': (1, 1), 'canny': (40, 50), 'H_count': 8}

        #Cropping factor for KCF tracker
        ROI_pupil = self.get_ROI(self.cropping_factor_pupil)
        ROI_glint = self.get_ROI(self.cropping_factor_glint)
        #Cropping factor for pre-processing
        CPI_pupil = self.cropping_factor_pupil
        CPI_glint = self.cropping_factor_glint
        center_pupil = self.get_center(ROI_pupil)
        center_glint = self.get_center(ROI_glint)

        self.th_range_glint = self.glint_threshold(center_glint, 1, CPI_glint, parameters_glint) #In order to get previse result for glint, don't shrink it!!
        parameters_glint['threshold'] = self.th_range_glint
        #Propress the blurring factor
        t1 = threading.Thread(target = self.get_blur, args = (4, CPI_pupil, parameters_pupil, ROI_pupil, ROI_glint))
        #Should be after the threshold is gotten to get the count for Hough transform
        t2 = threading.Thread(target = self.get_count, args = (1, ROI_glint, CPI_glint, parameters_glint))

        #Run the thread
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        parameters_pupil['blur'] = self.g_blur
        print(self.g_blur)
        #Get the threshold based on blur
        th_range_pupil = self.pupil_threshold(center_pupil, 4, CPI_pupil, parameters_pupil) #4 is the shrinking factor
        #Add the perfect threshold value
        parameters_pupil['threshold'] = th_range_pupil 
        #Add the perfect H_count value
        parameters_glint['H_count'] = self.H_count

        #Parameters is stored as(blur, canny, threshold)

        t2 = threading.Thread(target=self.tracking, args=(ROI_pupil, parameters_pupil, ROI_glint))
        t3 = threading.Thread(target=self.gtracking, args=(ROI_glint, CPI_glint, parameters_glint))
        #Start the thread for final calculation
        t2.start()
        t3.start()

    #This function also calls another thread which saves all video generated images in the output file
    def generate(self):
        self.Analyze.setEnabled(True)
        self.Generate.setEnabled(False)
        self.Pupil_chose.setEnabled(True)
        self.Glint_chose.setEnabled(True)
        self.clear_folder("./output")  # TODO: DANGEROUS. maybe gui button or checkbox?
        self.clear_folder("./glint_output")
        self.clear_folder("./glint_testing")
        self.clear_folder("./testing")
        self.Video = self.VideoText.text()
        self.File = self.FileText.text()
        #Check validity
        if not os.path.exists(self.Video): #or not os.path.exists(File):
            print(f"Video file '{self.Video}' does not exist")
            return
        if not os.path.exists(self.File):
            print(f"Text file '{self.File}' does not exist")
            return

        # disable line editing once we've picked our files to avoid confusion
        self.VideoText.setEnabled(False)
        self.FileText.setEnabled(False)

        print('Start writing images to the file\n')
        print('start reading in files')

        #Create a thread to break down video into frames into out directory
        t1 = threading.Thread(target=self.to_frame, args=(self.Video, None))

        #Only run the thread when the file is empty
        if not os.path.exists('output'):
            os.makedirs('output')
        dirls = os.listdir('output')
            # t1.start()

        self.wanted = self.to_frame(self.Video)
        #Just to check for extreme cases, could be ignored for normal cases.
        if self.wanted != None:
            sample = self.pic_collection[self.wanted]
            #Saved because user.py actually need to read the picture to create the widget
            #Since the picture are all sized down by 4, it needed to be sized up here in order for the user to see
            # sample = cv2.resize(sample,(int(self.width)*self.size_factor[0], int(self.height)*self.size_factor[1]))
            cv2.imwrite('input/chosen_pic.png', sample)
        self.label_5.setText("Generating done, choose(Pupil/Glint)")

    def circle_pupil(self):
        #Fist clear every widgets in the layout
        for i in reversed(range(self.LayVideo.count())): 
            self.LayVideo.itemAt(i).widget().setParent(None)

        self.Pupil_click.setEnabled(True)
        self.Glint_click.setEnabled(False)
        self.MyWidget = MyWidget(self)
        self.LayVideo.addWidget(self.MyWidget)

    def circle_glint(self):
        #Fist clear every widgets in the layout
        for i in reversed(range(self.LayVideo.count())): 
            self.LayVideo.itemAt(i).widget().setParent(None)

        self.Pupil_click.setEnabled(False)
        self.Glint_click.setEnabled(True)
        self.MyWidget = MyWidget(self)
        self.LayVideo.addWidget(self.MyWidget)

    def store_pupil(self):
        self.Pupil_store.setText('Pupil: Stored')

        self.cropping_factor_pupil[0][0] = self.MyWidget.begin.x()
        self.cropping_factor_pupil[0][1] = self.MyWidget.end.x()
        self.cropping_factor_pupil[1][0] = self.MyWidget.begin.y()
        self.cropping_factor_pupil[1][1] = self.MyWidget.end.y()
        self.p_x.setText('x: '+ str(self.MyWidget.begin.x()))
        self.p_xl.setText('xl: '+ str(self.MyWidget.end.x()))
        self.p_y.setText('y: '+ str(self.MyWidget.begin.y()))
        self.p_yl.setText('yl: '+ str(self.MyWidget.end.y()))



    def store_glint(self):
        self.Glint_store.setText('Glint: Stored')

        self.cropping_factor_glint[0][0] = self.MyWidget.begin.x()
        self.cropping_factor_glint[0][1] = self.MyWidget.end.x()
        self.cropping_factor_glint[1][0] = self.MyWidget.begin.y()
        self.cropping_factor_glint[1][1] = self.MyWidget.end.y()
        self.g_x.setText('x: '+ str(self.MyWidget.begin.x()))
        self.g_xl.setText('xl: '+ str(self.MyWidget.end.x()))
        self.g_y.setText('y: '+ str(self.MyWidget.begin.y()))
        self.g_yl.setText('yl: '+ str(self.MyWidget.end.y()))


    def plot_result(self):
        #Plot glint
        ad = auto_draw()
        ad.read('data_output/pupil.csv')
        ad.draw_x('plotting/x_pupil.png')
        ad.draw_y('plotting/y_pupil.png')
        ad.draw_r('plotting/r_pupil.png')
        ad.draw_blink('plotting/blink_pupil.png')

        ag = auto_draw()
        ag.read('data_output/glint.csv')    
        ag.draw_x('plotting/x_glint.png')
        ag.draw_y('plotting/y_glint.png')
        ag.draw_r('plotting/r_glint.png')


    #This function is only for choosing the best open-eye picture
    #Maybe its a bit redundant, try to fix later
    def to_frame(self, video, limit = 300):
        maximum = 0
        wanted = 0
        #i counts the image sequence generated from the video file
        i = 0
        cap = cv2.VideoCapture(video)
        while(cap.isOpened()):
            ret, frame = cap.read()
            if ret == False:
                break
            #Need to figure out a way to downscale the image to make it run faster
            self.height = frame.shape[0]
            self.width = frame.shape[1]
            # frame = cv2.resize(frame,(int(self.width/self.size_factor[0]), int(self.height/self.size_factor[1])))
            if limit != None:
                #Test for the non-blinking image(Find image with the larggest dark space)
                if len(np.where(frame < 100)[0]) > maximum and i < limit:
                    maximum = len(np.where(frame < 100)[0])
                    wanted = i
                #Add a limit to it so it could run faster when testing
                #We need a perfect opened_eye to run machine learning program on to determine the parameters.
                if i > limit:
                    return wanted

                self.pic_collection[i] = frame
                if i % 25 == 0:
                    print("%d/%d(max) image scanned" % (i,limit))
            else: 
                cv2.imwrite('output/%015d.png'%i, frame)

            i+=1
        print('Thread 2 finished')
        return wanted

if __name__ == '__main__':
    #Later put into the user interface

    App = QtWidgets.QApplication([])
    WINDOW = main()
    sys.exit(App.exec_())
