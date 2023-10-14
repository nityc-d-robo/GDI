from PyQt5.QtWidgets import QApplication, QMainWindow, QSplitter, QTextEdit, QGraphicsView, QGraphicsScene ,QPushButton
from PyQt5.QtCore import QThread, pyqtSignal ,Qt , pyqtSlot
from PyQt5.QtGui import QPixmap, QImage


import sys
from cv_bridge import CvBridge


# ros2 
import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from std_msgs.msg import Bool



# terminal
import QTermWidget

RED = "background-color: red; color: white; font-size: 20px; width: 200px; height: 50px;"
GREEN = "background-color: green; color: white; font-size: 20px; width: 200px; height: 50px;"


class Terminal(QTermWidget.QTermWidget):
    def __init__(self, parent=None):
        super().__init__(0, parent)

        self.click_count = 0
        self.node_update = True

        self.setColorScheme('WhiteOnBlack')
        self.setShellProgram("/bin/bash")
        self.setArgs(["-i"])

        self.startShellProgram()

        self.sendText("cd \n")
        self.sendText("clear \n")

class RosThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        QThread.__init__(self)
        rclpy.init()
        self.node = rclpy.create_node('my_node')
        self.publisher = self.node.create_publisher(Bool, 'topic', 10)
        self.subscription = self.node.create_subscription(Image, '/image_raw', self.listener_callback, 10)
        self.bridge = CvBridge()

    def listener_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        height, width, _ = cv_image.shape
        bytes_per_line = 3 * width
        qimage = QImage(cv_image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(qimage)
        self.signal.emit({"pixmap":pixmap,"node_list":self.node.get_node_names()})

    def send_command(self,mode:bool):
        msg = Bool()
        msg.data = mode
        self.publisher.publish(msg)


    def run(self):
        rclpy.spin(self.node)

class Window(QMainWindow):

    click_count = 0
    # node_update = True
    def __init__(self):
        super().__init__()

        self.setGeometry(100, 100, 700, 700)
        self.setWindowTitle("Graphical D-Robo Interface")

        self.thread = RosThread()
        self.thread.signal.connect(self.thread_return)
        self.thread.start()

        self.create_splitter()

    def create_splitter(self):
        
        self.windows = {
            "upper" : QSplitter(),
                "upper_right" : QSplitter(),
                    "upper_right_upper" : QTextEdit(),
                    "upper_right_lower" :QPushButton('Balus', self),

                "upper_left"  : QGraphicsView(),

            "lower" : QSplitter(),
                "lower_right" : QTextEdit(),
                "lower_left"  : Terminal() # Use QGraphicsView for displaying image
        }

        # Create a button and set its style
        self.windows["upper_right_lower"].setStyleSheet("background-color: red; color: white; font-size: 20px; width: 200px; height: 50px;")
        self.windows["upper_right_lower"].clicked.connect(self.on_click)

        self.on_click()

        self.windows["upper"].addWidget(self.windows["upper_left"])
        self.windows["upper"].addWidget(self.windows["upper_right"])
        
        self.windows["upper_right"].setOrientation(Qt.Vertical)
        self.windows["upper_right"].addWidget(self.windows["upper_right_upper"])
        self.windows["upper_right"].addWidget(self.windows["upper_right_lower"])

        self.windows["lower"].addWidget(self.windows["lower_left"])
        self.windows["lower"].addWidget(self.windows["lower_right"])

        vsplitter = QSplitter()
        vsplitter.setOrientation(Qt.Vertical)

        vsplitter.addWidget(self.windows["upper"])
        vsplitter.addWidget(self.windows["lower"])

        self.setCentralWidget(vsplitter)

        self.windows["upper_right_upper"].focusInEvent = self.focusInEvent
        self.windows["upper_right_upper"].focusOutEvent = self.focusOutEvent

        self.scene = QGraphicsScene()
        self.windows["upper_left"].setScene(self.scene)

    def thread_return(self,data):
        self.image_management(data["pixmap"])
        self.node_list_management(data["node_list"])


    def image_management(self, pixmap):
        self.scene.clear()
        self.scene.addPixmap(pixmap)
        self.windows["upper_left"].fitInView(self.scene.sceneRect())
    
    def node_list_management(self, node_list):
        # if not self.node_update:
        #     return
        node_list = "\n".join(node_list)
        self.windows["upper_right_upper"].setText(node_list)

    

    # @pyqtSlot()
    # def focusInEvent(self, event):
    #     self.node_update = False
    #     return super(QTextEdit, self.windows["upper_right_upper"]).focusInEvent(event)

    # @pyqtSlot()
    # def focusOutEvent(self, event):
    #     self.node_update = True
    #     return super(QTextEdit, self.windows["upper_right_upper"]).focusOutEvent(event)
        
        
        
    
    def on_click(self):
        

        self.click_count += 1
        if self.click_count % 2 == 0:
            self.windows["upper_right_lower"].setStyleSheet(RED)
            self.windows["upper_right_lower"].setText('Restart')
            self.thread.send_command(True)

            
        else:
            self.windows["upper_right_lower"].setStyleSheet(GREEN)
            self.windows["upper_right_lower"].setText('Balus')
            self.thread.send_command(False)


if __name__ == "__main__":


    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
