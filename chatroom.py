# coding: utf-8

import sys
import time
import Queue
import threading
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from chatroomUI import Ui_MainWindow
from client import Client

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None, addr="localhost", port=12345, nickname="Stdio"):
        super(MainWindow,self).__init__(parent)

        self.setupUi(self)

        self.queue = Queue.Queue()
        self.client = Client(addr=addr, port=port,
                             nickname=nickname, queue=self.queue)
        self.addr = self.client.get_local_addr()
        self.addrs = "%s:%d"%self.addr

        # 启动监听线程
        thr = threading.Thread(target=self.client.receive_loop)
        thr.setDaemon(True)
        thr.start()
        

        # 建立时钟
        self.timer = QTimer(self.messageEdit)
        self.timer.timeout.connect(self.flush_message)
        self.timer.start(200)

        self.sendButton.clicked.connect(self.send)

    def send(self):
        message = unicode(self.sendEdit.text().toUtf8(), "utf-8", 'ignore').encode("utf-8")
        self.sendEdit.clear()
        self.client.send_message(message)

    def flush_message(self):
        try:
            while True:
                data = self.queue.get(block=False)
                if data["type"] == "message":
                    x = time.localtime(data["time"])
                    tstr = time.strftime('%H:%M:%S',x)

                    string = u"""
                    <p style="margin-top:3px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">
                    <span style="color:{color};">{nickname}@{addr} {time}</span>
                    </p>
                    <p style="margin-top:0px; margin-bottom:3px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">
                        &nbsp;&nbsp;{message}
                    </p>""".format( color="#008040" if data["address"]==self.addrs else "#0000ff",
                                    nickname=data["nickname"], 
                                    time=tstr,
                                    addr=data["address"],
                                    message=data["msg"])
                    self.messageEdit.append(string)

                else:
                    self.messageEdit.append(u"""
                    <p style="font-style:italic; margin-top:4px; margin-bottom:4px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">
                        {msg}
                    </p>""".format(msg=data["msg"]))
        except Queue.Empty:
            pass

    def __del__(self):
        self.timer.stop()
        del self.client


def main():
    addr = raw_input("Input the server's IP and port (127.0.0.1:12345 by default): ")
    if not addr:
        ip = "localhost"
        port = 12345
    else:
        ip, port = addr.split(":")
        port = int(port)

    nickname = raw_input("Input your nickname: ").decode("gbk").encode("utf-8")
    Program = QApplication(sys.argv)
    Window = MainWindow(nickname=nickname, addr=ip, port=port)
    Window.show()
    Program.exec_()

if __name__ == '__main__':
    main()

