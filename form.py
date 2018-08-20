# Author : Mr.Nontachai  Yoothai

import sys, os
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import cv2
import numpy as np
import requests, json

qtCreatorFile = "/home/pea/TestGUI/main.ui"  # Enter file here.

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


class Capture():
    def __init__(self):
        self.capturing = False
        self.c = cv2.VideoCapture(0)
        self.frame = None

    def startCapture(self):
        print "pressed start"
        # self.MyApp.Live.start(500)
        # self.MyApp.Live.start(500)
        self.capturing = True
        cap = self.c
        while self.capturing:
            ret, frame = cap.read()
            # cv2.imshow("Capture", frame)
            cv2.waitKey(5)
            self.frame = frame
            cv2.imwrite('/tmp/live.png', cv2.resize(frame, (431, 281)), [cv2.IMWRITE_PNG_COMPRESSION, 9])
        cv2.destroyAllWindows()

    def endCapture(self):
        print "pressed End"
        os.system('rm -rf /tmp/live.png')
        self.capturing = False
        self.c.release()

    def quitCapture(self):
        print "pressed Quit"
        cap = self.c
        cv2.destroyAllWindows()
        cap.release()
        QtCore.QCoreApplication.quit()


class MyApp(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        # schedule.every(10).seconds.do(check_status)
        self.config = json.load(open("./config.json", 'r'))
        self.capture = Capture()
        self.fileDiag = QFileDialog()
        self.img_path = None
        self.thread_2 = self.v2_sl.value()
        self.thread_1 = self.v1_sl.value()
        # self.tableWidget.setColumnCount(3)
        # self.tableWidget.resizeColumnsToContents()
        # self.tableWidget.resizeRowsToContents()

        self.start_cam_btn.clicked.connect(self.capture.startCapture)
        self.stop_cam_btn.clicked.connect(self.capture.endCapture)
        self.snap_btn.clicked.connect(self.snap_handler)
        self.edge_btn.clicked.connect(self.edge_handler)
        self.exit_btn.clicked.connect(exit_handler)
        self.pick_btn.clicked.connect(self.get_file)
        self.detect_btn.clicked.connect(self.detect_api)
        self.detect_btn.setDisabled(True)
        self.v1_sl.valueChanged.connect(self.v1_changed)
        self.v2_sl.valueChanged.connect(self.v2_changed)

        self.measure_btn.clicked.connect(self.measure)
        self.count_btn.clicked.connect(self.count)

        self.circle_radio.toggled.connect(lambda: self.btnstate(self.circle_radio))
        self.unknow_radio.toggled.connect(lambda: self.btnstate(self.unknow_radio))
        self.object_type = None

        self.label.setAutoFillBackground(True)
        self.label.setText("Wait for Connection ..")
        self.label.setStyleSheet('color: blue')

        self.Timer = QTimer()
        self.Timer.timeout.connect(self.check_status)
        self.Timer.start(5000)

        self.Live = QTimer()
        self.Live.timeout.connect(self.update_live)
        self.Live.start(500)
        # os.system('rm -rf /tmp/live.png')
        # self.Live.stop()

    def update_live(self):
        try:
            if os.path.exists('/tmp/live.png'):

                image = QtGui.QImage(QtGui.QImageReader("/tmp/live.png").read())
                self.live_lb.setPixmap(QtGui.QPixmap(image))
                self.live_lb.show()
            else:

                image = QtGui.QImage(QtGui.QImageReader("./output/template.png").read())
                self.live_lb.setPixmap(QtGui.QPixmap(image))
                self.live_lb.show()

        except Exception as Err:
            pass

    def check_status(self):
        try:
            res = requests.get('http://www.google.com')
            if res.status_code == 200:
                # print res.status_code
                self.label.setText("STATUS : CONNECTED")
                self.label.setStyleSheet('color: green')
            else:
                # print res.status_code
                self.label.setText("STATUS : DISCONNECTED")
                self.label.setStyleSheet('color: red')


        except Exception as Err:
            self.label.setText("STATUS : DISCONNECTED")
            self.label.setStyleSheet('color: red')
            pass

    def rest_call(self, img):
        print("Prediction")

        url = self.config.get("Url")
        body = img
        headers = self.config.get("Header")

        response = requests.request("POST", url, data=body, headers=headers)
        print(response.status_code)
        print('Debug')
        # TODO : Utilize Response Here.
        result = json.loads(response.content)
        predictions = result.get('predictions')  # prediction is a List of Dict.
        # Try to drop less prob.
        output = []
        for pred in predictions:
            if int(pred.get('probability')*100) >= 85:
                output.append(pred)
        # Try to count object that found in images
        tmp = []
        for tag in output:
            tmp.append(tag.get('tagName'))
        found = set(tmp)  # Now known how many type of found.
        detect = {}
        box =[]
        for f in found:
            box = []
            for i in output:
                if f == i.get('tagName'):
                    box.append(i.get('boundingBox'))
            detect.update({f: box})
            del box

        self.plotBox(detect)
        self.update_table(detect)

    def update_table(self, info): # TODO : Argent Require

        horHeaders = ['Device-Type', 'UNIT']

        ind = 0
        # self.tableWidget.resizeColumnsToContents()
        # self.tableWidget.resizeRowsToContents()
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setRowCount(len(info.keys()))
        self.tableWidget.setColumnWidth(0, 400)
        self.tableWidget.setColumnWidth(1, 142)


        for k, v in info.items():
            KeyItem = QTableWidgetItem(k)
            ValItem = QTableWidgetItem(str(len(v)))
            self.tableWidget.setItem(ind, 0, KeyItem)
            self.tableWidget.setItem(ind, 1, ValItem)
            ind += 1
        self.tableWidget.setHorizontalHeaderLabels(horHeaders)

        #for numRow in range(len(info.keys())):
        #     for key, val in info.items():
        #         newitem = QTableWidgetItem(key)
        #         self.tableWidget.setItem(0, 1, newitem)
        #         newitem = QTableWidgetItem(len(val))
        #         self.tableWidget.setItem(1, 1, newitem)

    def plotBox(self, info):
        frame = cv2.imread(str(self.img_path))
        for item in info.keys():
            print("Found : Number of {0} = {1}".format(item, len(info.get(item))))
            for box in info.get(item):

                x1 = int(320*box.get('left'))
                y1 = int(240*box.get('top'))
                x2 = x1 + int(320*box.get('width'))
                y2 = y1 + int(240*box.get('height'))

                cv2.rectangle(frame, (x1,y1), (x2,y2), (0, 128, 250), 2)
            cv2.imwrite('./output/result.png', frame)
            image = QtGui.QImage(QtGui.QImageReader("./output/result.png").read())
            self.result_lb.setPixmap(QtGui.QPixmap(image))
            self.result_lb.show()

    def detect_api(self):
        print("Detect by API")
        self.rest_call(open(str(self.img_path), 'rb').read())  # Call Function rest_call by passing BinaryByte of Image

    def btnstate(self, b):  # For handle State of Radio Button Selected
        # TODO : remove print()
        if b.text() == "Circle":
            if b.isChecked():
                print b.text() + " is selected"
                self.object_type = "Circle"

        if b.text() == "Unknow":
            if b.isChecked():
                print b.text() + " is selected"
                self.object_type = "Unknow"
                self.detect_btn.setEnabled(True)

    def measure(self):
        print("Measurement Process")
        # TODO : Function for Measurement things.

    def count(self):  # Function to Handle when Count Button Clicked
        print("Count Object Process")
        oriimg = cv2.imread(str(self.img_path))
        if oriimg.shape[-1] == 3:  # color image
            b, g, r = cv2.split(oriimg)  # get b,g,r
            rgb_img = cv2.merge([r, g, b])  # switch it to rgb
            gray_img = cv2.cvtColor(oriimg, cv2.COLOR_BGR2GRAY)
        else:
            gray_img = oriimg

        gray_img = cv2.medianBlur(gray_img, 7)
        frame = cv2.Canny(gray_img, float(self.thread_1), float(self.thread_2))
        # frame = cv2.bitwise_not(frame)  # For Invert bit on B/W

        if self.object_type == "Circle":
            print("Counting Circle")
            # This Prosedure for Count Circle
            circles = cv2.HoughCircles(frame, cv2.cv.CV_HOUGH_GRADIENT, dp=2 , minDist= 50, param1= 4, param2=20,
                                       minRadius= 20, maxRadius=50)

            circles = np.uint16(np.around(circles))

            for i in circles[0, :]:
                # draw the outer circle
                cv2.circle(oriimg, (i[0], i[1]), i[2], (128, 255, 0), 2)
                # draw the center of the circle
                cv2.circle(oriimg, (i[0], i[1]), 2, (0, 128, 255), 2)
            cv2.imwrite('./output/result.png', oriimg)
            image = QtGui.QImage(QtGui.QImageReader("./output/result.png").read())
            self.result_lb.setPixmap(QtGui.QPixmap(image))
            self.result_lb.show()

        elif self.object_type == "Unknow":
            print("Counting Unknow")
            # TODO : Add Function Detect By API

    def v1_changed(self, position):  #  Function for handle value on scroll bar changed.
        self.thread_1 = position
        self.edge_handler()

    def v2_changed(self, position):
        self.thread_2 = position
        self.edge_handler()

    def get_file(self):  # Function Handle on OpenDialog Button.

        self.fileDiag.setFileMode(QFileDialog.AnyFile)
        # self.fileDiag.setFilter("Image files (*.png,*.jpg)")
        filenames = QStringList()
        if self.fileDiag.exec_():  # Check File Dialog Choosing
            filenames = self.fileDiag.selectedFiles()
            tmp = cv2.imread(str(filenames[0]))
            tmp = cv2.resize(tmp, (320, 240))
            cv2.imwrite(str(filenames[0]), tmp)  # Open Resize and Replace file
            img = QtGui.QImage(QtGui.QImageReader(filenames[0]).read())
            self.origin_lb.setPixmap(QtGui.QPixmap(img))
            self.origin_lb.show()
            self.img_path = filenames[0]

    def snap_handler(self): # Capture Function
        print("Button Clicked")
        resize = cv2.resize(self.capture.frame, (320, 240))
        cv2.imwrite('./output/snap.png', resize)
        self.img_path = './output/snap.png'
        self.capture.capturing = False
        cv2.destroyAllWindows()
        self.capture.c.release()
        image = QtGui.QImage(QtGui.QImageReader("./output/snap.png").read())
        self.origin_lb.setPixmap(QtGui.QPixmap(image))
        self.origin_lb.show()

    def edge_handler(self):  # Function for edge detection.
        os.system('rm -rf ./output/edge.png')
        frame = cv2.imread(str(self.img_path), 0)
        edge = cv2.Canny(frame, float(self.thread_1), float(self.thread_2))
        cv2.imwrite('./output/edge.png', edge)
        Image = QtGui.QImage(QtGui.QImageReader("./output/edge.png").read())
        self.process_lb.setPixmap(QtGui.QPixmap(Image))
        self.process_lb.show()


# Static Method for Handle Exit Task.
def exit_handler():
    print("Terminate by User !!!")
    exit()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
