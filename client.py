# coding: utf-8

import socket
import json
import time
import threading

class Client(object):
    def __init__(self, addr="127.0.0.1", port=12345, nickname=None, queue=None):
        self.addr = addr
        self.port = port
        self.run = True
        self.queue = queue
        self.nickname = nickname

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect()

        if not self.sock:
            return

    def connect(self, nickname=None):
        try:
            self.sock.connect((self.addr, self.port))
            self.sock.settimeout(3)
        except socket.error, e:
            if e.errno == 10061:
                print "Couldn't established connection with %s:%d"%(self.addr, self.port)
                return
            else:
                raise
        else:
            if self.nickname:
                pass
            elif nickname:
                self.nickname = nickname
            else:
                self.nickname = raw_input("Set your nickname: ").decode("GBK").encode("utf-8")                # 设置昵称

            self.sock.send(json.dumps({"action": "join",
                                    "time": time.time(),
                                    "nickname": self.nickname}))

    def receive_loop(self):
        """\
        监听线程，可以将收到的消息存入一个队列中
        """
        try:
            while self.run:
                try:
                    data = json.loads(self.sock.recv(1024))
                    if self.queue:
                        self.queue.put(data)                                    # 向队列中推送消息
                    else:
                        if data["type"] == "message":
                            x = time.localtime(data["time"])
                            tstr = time.strftime('%Y-%m-%d %H:%M:%S',x)


                            print u"{n}@{addr} {time}\n{msg}\n".format(n=data["nickname"],
                                addr=data["address"],
                                time=tstr,
                                msg=data["msg"])

                        elif data["type"] == "info":
                            print "INFO:", data["msg"]
                except KeyboardInterrupt:
                    self.run = False
                except socket.timeout:
                    pass

        except socket.error, e:
            if e.errno == 10053:
                self.run = False
                print "Server closed"

    def send_loop(self):
        try:
            while self.run:
                s = raw_input().decode("gbk").encode("utf-8")
                self.sock.send(json.dumps({"action": "send", 
                                            "time": time.time(),
                                            "msg": s}))

        except (EOFError, KeyboardInterrupt):
            self.sock.send(json.dumps({"action": "quit", "time": time.time()}))
            self.run = False

    def send_message(self, msg):
        """\
        发送消息
        """
        self.sock.send(json.dumps({"action": "send", 
                                    "time": time.time(),
                                    "msg": msg}))

    def main(self):
        """\
        主函数
        """
            
        funclist = [self.receive_loop, self.send_loop]
        thrlist = [threading.Thread(target=f)for f in funclist]
        map(lambda x: x.start(), thrlist)
        try:
            map(lambda x: x.join(), thrlist)
        except KeyboardInterrupt:
            pass

    def __del__(self):
        self.sock.close()


if __name__ == '__main__':
    client = Client(addr="localhost", port=12345)
    client.main()
