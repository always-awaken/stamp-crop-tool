# -*- coding: utf-8 -*-
import cv2  # Tested with opencv version 3.2.0
import os.path
import numpy as np
import argparse
import sys

from natsort import natsorted
from PyQt5 import QtCore, uic, QtGui
from PyQt5.QtWidgets import *
qtCreatorFile = "StampCropTool_qt5.ui"

# Control flags
DEBUG = True

# Constants
APP_NAME = 'StampCropTool'

Ui_MainWindow = uic.loadUiType(qtCreatorFile)[0]


class StampCropTool(QMainWindow, Ui_MainWindow):

    def __init__(self, debug=None):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon('static/icon.png'))

        # Init
        if debug:
            self.debug = True
        else:
            self.debug = False

        # Init progressBar
        self.img_view.mousePressEvent = self.__handle_click
        self.img_view.setMouseTracking(True) 

        self.img_view.mouseMoveEvent = self.__handle_move
		
		#set stampWidthBox and stampHeightBox
        self.stampHalfWidth = int(int(self.stampWidthBox.text())/2)
        self.stampHalfHeight = int(int(self.stampHeightBox.text())/2)
		
		# Connect handlers to signals from QLineEdit(s)
        self.stampWidthBox.textChanged.connect(self.__handle_stamp_width_box)
        self.stampHeightBox.textChanged.connect(self.__handle_stamp_height_box)
        
		
		# Connect handlers to signals from QPushButton(s)
        self.inFile.clicked.connect(self.get_input_file)
        self.outFile.clicked.connect(self.get_output_folder)
        self.nextBtn.clicked.connect(self.__handle_next_btn)
        self.previousBtn.clicked.connect(self.__handle_previous_btn)
		
        #Global variable
        self.eps = 0
        self.count = 0

    def __handle_next_btn(self, event):
        
        if self.currentImageIndex + 1 < len(self.imgList):
            self.currentImageIndex = self.currentImageIndex + 1
            self.currentImage = self.imgList[self.currentImageIndex]
            self.load_new_image()
        else:
            self._log('No more images in directory! Currently at image %d of %d' % (
                    self.currentImageIndex + 1, len(self.imgList)))
			
    def _log(self, text):
        self.logView.append(text)
    def __handle_stamp_width_box(self, event):
        self.stampHalfWidth = int(int(self.stampWidthBox.text())/2)
		
    def resizeEvent(self, event):
        if hasattr(self, 'cv_img'):
         self._log('image Load : %s' % self.currentImage)
         self.load_opencv_to_canvas()
        QMainWindow.resizeEvent(self, event)

    def __handle_stamp_height_box(self, event):
        self.stampHalfHeight = int(int(self.stampHeightBox.text())/2)
    def __handle_previous_btn(self, event):

        if self.currentImageIndex > 0:
            self.currentImageIndex = self.currentImageIndex - 1
            self.currentImage = self.imgList[self.currentImageIndex]
            self.load_new_image()
        else:
            self._log('No previous image! Currently at image %d of %d' % (
                    self.currentImageIndex + 1, len(self.imgList)))

    def __create_dir_if_not_exists(self, dir):
        if not os.path.exists(dir):
            os.makedirs(dir)

    def __saveStampImage(self, x_pos, y_pos):
        self.count = self.count + 1
        
        image_path = os.path.join(self.outputPath.toPlainText(), "")
        #print(image_path)
        self.__create_dir_if_not_exists(image_path)
        intStampWidth = int(self.stampWidthBox.text())
        intStampHeight = int(self.stampHeightBox.text())
        
        crop_img = self.original_img[y_pos:y_pos+intStampHeight, x_pos:x_pos+intStampWidth]
        if x_pos < 0 or y_pos < 0 or x_pos > self.original_img.shape[1] or y_pos > self.original_img.shape[0]:
            self._log("Out of range")
        #cv2.cvtColor(crop_img, cv2.COLOR_RGB2BGR)
        
        cv2.imwrite(os.path.join(image_path, self.outputPrefixTextBox.text()+str(self.count)+".jpg"), crop_img)
        self._log('image Save : ' + os.path.join(image_path, self.outputPrefixTextBox.text()+str(self.count)+".jpg"))

    def __handle_click(self, event):
        x = event.pos().x()
        y = event.pos().y()
        cv2.rectangle(self.cv_img, (x - self.stampHalfWidth, y - self.stampHalfHeight),(x + self.stampHalfWidth, y + self.stampHalfHeight), (0, 255, 0), 3)
        height, width, __ = self.cv_img.shape
        self.update_canvas(self.cv_img, height, width)
        self.__saveStampImage(x-self.stampHalfWidth ,y-self.stampHalfHeight)
        if self.settingNextAfterOneclickBox.isChecked():
            self.__handle_next_btn(event)
    def __handle_move(self, event):
        x = event.pos().x()
        y = event.pos().y()
        self.eps = self.eps + 1
        if self.eps >= 5 and hasattr(self, 'cv_img'):
            self.eps=0
            cv_buffer_img = self.cv_img.copy()
            cv2.rectangle(cv_buffer_img, (x - self.stampHalfWidth, y - self.stampHalfHeight),(x + self.stampHalfWidth, y + self.stampHalfHeight), (255, 0, 0), 3)
            height, width, __ = cv_buffer_img.shape
            self.update_canvas(cv_buffer_img, height, width)
    def update_canvas(self, img, height, width):
        if self.debug == True:
            print("update_canvas: height=%d,width=%d" % (height, width))
        bytesPerLine = 3 * width
        qImg = QtGui.QImage(img, width, height,
                      bytesPerLine, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap(qImg)
        self.img_view.setPixmap(pixmap)
        
        self.img_view.show()

    def read_filelist(self):
        img_path, img_name = os.path.split(self.currentImage)
        imgList = [os.path.join(dirpath, f)
                   for dirpath, dirnames, files in os.walk(img_path)
                   for f in files if f.endswith("jpg") or f.endswith("png")]
        #for Windows
        imgList = [img.replace('\\', '/') for img in imgList]
        
        self.outputPath.setText(img_path + '/output')
        self.imgList = natsorted(imgList)
        self.currentImageIndex = self.imgList.index(self.currentImage)
        

    def load_new_image(self):
        self.imageField.setText(self.currentImage)
        self._log('image Load : %s' % self.currentImage)
        self.load_opencv_to_canvas()

    def get_input_file(self):
        self.currentImage = QFileDialog.getOpenFileName(self, 'Open file','c:\\', "Image files (*.jpg *.png)")[0]
        self.load_new_image()
        self.read_filelist()

    def get_output_folder(self):
        self.outputFolder = str(QFileDialog.getExistingDirectory(
            self, "Select root output directory"))
        self.outputPath.setText(self.outputFolder)
    def YUV2RGB( yuv ):
        m = np.array([[ 1.0, 1.0, 1.0],[-0.000007154783816076815, -0.3441331386566162, 1.7720025777816772],[ 1.4019975662231445, -0.7141380310058594 , 0.00001542569043522235] ])
        rgb = np.dot(yuv,m)
        rgb[:,:,0]-=179.45477266423404
        rgb[:,:,1]+=135.45870971679688
        rgb[:,:,2]-=226.8183044444304
        return rgb
    def load_opencv_to_canvas(self):
        
        print("self.currentImgage %s" % self.currentImage)
        self.cv_img = cv2.imread(self.currentImage)
        self.original_img = self.cv_img.copy()
        try :
            self.cv_img = cv2.cvtColor(self.cv_img, cv2.COLOR_BGR2RGB).astype(np.uint8)
        except ValueError :
            self.cv_img = self.YUV2RGB(self.cv_img)
            print(ValueError)
        
        height, width, __ = self.cv_img.shape
        self.has_original_been_created = False
        self.segmentation_mask = np.zeros((height, width))
        
        self.update_canvas(self.cv_img, height, width)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', help="run in debug mode",
                        action="store_true")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    window = StampCropTool(args.debug)
    window.show()
    sys.exit(app.exec_())