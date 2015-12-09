# coding: utf-8

import socket
import time
import threading
import json
import Queue

class Server(object):
    def __init__(self, addr="localhost", port=12345, max_user=10):
        self.addr = addr
        self.port = port
        self.max_user = max_user

        self.connections = []                                                   # 连接列表
        self.nickname = {}                                                      # 昵称字典
        self.data_queue = Queue.Queue()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.addr, self.port))

    def listen(self):
        """\
        监听是否有新连接建立
        """
        # self.sock.bind((self.addr, self.port))
        self.sock.listen(self.max_user)
        print "Listening at %s:%d"%(self.addr, self.port)
        while True:
            connection, address = self.sock.accept()
            print "Connection established with %s:%d"%address
            connection.settimeout(0.1)                                          # 设置超时时间
            self.connections.append(connection)

    def rm_conn(self, connection):
        """\
        中断连接，从连接列表中删除该连接
        """
        try:
            self.connections.remove(connection)                                     # 删除连接
        except ValueError:
            pass

        addr = connection.getpeername()
        nickname = self.nickname[addr]
        del self.nickname[addr]
        print u"Connection breakup with %s:%d"%addr

        data = {
            "type": "info",
            "time": time.time(),
            "msg": u"{name}@{ip}:{port} leave the room".format(
                                    name=nickname, ip=addr[0], port=addr[1])
        }
        for conn in self.connections:
            conn.send(json.dumps(data))

    def user_join(self, data, addr):
        """\
        通知其他用户，有新用户加入
        """
        nickname = data["nickname"]
        self.nickname[addr] = nickname
        payload = {
            "type": "info",
            "time": data["time"],
            "msg": u"{name}@{ip}:{port} join the room".format(
                                    name=nickname, ip=addr[0], port=addr[1])
        }
        for conn in self.connections:
            conn.send(json.dumps(payload))

    def update_msg(self):
        """\
        轮询所有连接，并将收到的消息加入队列
        """
        while True:
            for conn in self.connections:
                try:
                    data = json.loads(conn.recv(1024))
                except socket.timeout:
                    continue
                except socket.error, e:
                    if e.errno in (10053, 10054):                               # 有用户离开
                        self.rm_conn(conn)
                except ValueError:
                    pass
                else:
                    addr = conn.getpeername()
                    self.data_queue.put((addr, data, conn))

    def exec_message(self, data, addr):
        """\
        转发消息
        """
        payload = {
            "type": "message",
            "time": data["time"],
            "nickname": self.nickname[addr],
            "address": "%s:%d"%addr,            # "127.0.0.1:5000"
            "msg": data["msg"]
        }
        for conn in self.connections:
            conn.send(json.dumps(payload))


    def run(self):
        """\
        主程序
        """
        funclist = [self.listen, self.update_msg]
        thrlist = [threading.Thread(target=func) for func in funclist]
        map(lambda x: x.setDaemon(True), thrlist)
        map(lambda x: x.start(), thrlist)

        while True:
            addr, data, conn = self.data_queue.get()
            if data["action"] == "join":
                self.user_join(data, addr)

            elif data["action"] == "quit":
                self.rm_conn(conn)

            elif data["action"] == "send":
                self.exec_message(data, addr)


    def __del__(self):
        self.socket.close()


if __name__ == '__main__':
    server = Server(addr="0.0.0.0", port=12345)
    server.run()
