from PyQt5.QtCore import *

from PyQt5.QtGui import *

from PyQt5.QtWidgets import *

from server import *
import sys

#serverInstance = Server()

#task publish widget:shows after task publish button clicked
class TaskPublishSubWidget(QWidget):
    def __init__(self):
        super(TaskPublishSubWidget,self).__init__()
        self.setWindowTitle("添加任务")
        self.resize(640,640)

###major tab windows positioning on the right side
#this one is used for resource usage of compute nodes
class ResourceUsageTab(QWidget):
    def __init__(self):
        super(ResourceUsageTab,self).__init__()

#this one presents all submitted tasks since program started
class TaskListTab(QWidget):
    def __init__(self):
        super(TaskListTab,self).__init__()

#this one shows all running log printed by console
class ServerLogTab(QWidget):
    def __init__(self):
        super(ServerLogTab,self).__init__()
        self.logTestView = QTextEdit()
        self.logTestView.setReadOnly(True)

        self.mainLayout = QHBoxLayout()
        self.mainLayout.addWidget(self.logTestView)

        self.setLayout(self.mainLayout)


#main window of this program
class ServerWindow(QWidget):
    def __init__(self):
        super(ServerWindow, self).__init__()
        self.setWindowTitle("服务端")
        self.resize(1024,768)

        #Server instance
        self.serverInstance = Server()

        #Buttons
        self.connectButton = QPushButton("启动服务端")
        self.connectButton.setFixedSize(150,75)
        self.taskPublishButton = QPushButton("发布任务")
        self.taskPublishButton.setFixedSize(150,75)
        self.modifyButton = QPushButton("设置")
        self.modifyButton.setFixedSize(150,75)
        self.closeButton = QPushButton("关闭服务端")
        self.closeButton.setFixedSize(150,75)

        self.buttonLayout = QVBoxLayout()
        self.buttonLayout.addWidget(self.connectButton)
        self.buttonLayout.addWidget(self.taskPublishButton)
        self.buttonLayout.addWidget(self.modifyButton)
        self.buttonLayout.addWidget(self.closeButton)

        #tabs
        self.resourceUsageTab = ResourceUsageTab()
        self.taskListTab = TaskListTab()
        self.serverLogTab = ServerLogTab()

        self.tabWidget = QTabWidget()
        self.tabWidget.addTab(self.resourceUsageTab,"资源监视")
        self.tabWidget.addTab(self.taskListTab,"任务列表")
        self.tabWidget.addTab(self.serverLogTab,"系统日志")

        self.taskPublishSubWidget = None
        self.isConnected = False

        self.mainLayout = QGridLayout()
        self.mainLayout.addLayout(self.buttonLayout,0,0,1,1)
        self.mainLayout.addWidget(self.tabWidget,0,1,1,1)
        self.mainLayout.setColumnStretch(0,1)
        self.mainLayout.setColumnStretch(1,3)

        self.setLayout(self.mainLayout)

        self.setupSlotConnections()

    def setupSlotConnections(self):
        self.connectButton.clicked.connect(self.startServerSlot)
        self.taskPublishButton.clicked.connect(self.taskPublishSlot)
        self.closeButton.clicked.connect(self.closeClientSlot)

    #Overload close event to shut down server instance
    def closeEvent(self, event):
        if self.isConnected == True:
            self.serverInstance.close_server()
            del self.serverInstance

        event.accept()

    @pyqtSlot()
    def startServerSlot(self):
        if self.isConnected == False:
            ret = self.serverInstance.start_server()
            if ret == True:
                # self.infoShowPanel.append("Server Start!")
                self.serverLogTab.logTestView.append("Server Start!")
                self.isConnected = True
                self.connectButton.setEnabled(False)

    @pyqtSlot()
    def taskPublishSlot(self):
        if self.taskPublishSubWidget == None:
            self.taskPublishSubWidget = TaskPublishSubWidget()

        self.taskPublishSubWidget.show()

    @pyqtSlot()
    def closeClientSlot(self):
        if self.isConnected == True:
            ret = self.serverInstance.close_server()
            del self.serverInstance
            self.serverInstance = Server()
            if ret == True:
                info_message = QMessageBox(QMessageBox.Information, "信息", "服务端已关闭", QMessageBox.Ok)
                info_message.exec_()
                # self.close()
                self.serverLogTab.logTestView.append("Server Closed!")
                self.connectButton.setEnabled(True)
                self.isConnected = False


app = QApplication(sys.argv)
demo = ServerWindow()
demo.show()
app.exec_()