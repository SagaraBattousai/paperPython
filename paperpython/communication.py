import os, sys, socket
from . import wsgi_pb2

def bootUp():
  socket_setting = wsgi_pb2.Config()
  socket_setting.ParseFromString(sys.stdin.buffer.read())
  return ServerSocket(socket_setting)
  
class SocketConnectionError(Exception):
    pass

#Todo: Change name
class ServerSocket:

  ACK = 0x06

  def __init__(self, socket_setting):
    self.ip = socket_setting.ip
    self.port = socket_setting.port
    self.isIPv6 = socket_setting.isIPv6
    self.idChecksum = socket_setting.idChecksum
    self.numWorkers = socket_setting.numWorkers

    self.af = socket.AF_INET6 if self.isIPv6 else socket.AF_INET

    self.soc = socket.socket(self.af, socket.SOCK_STREAM)
    self.soc.connect((self.ip, self.port))

    self.handshake()
    
  def handshake(self):
    self.soc.send(self.idChecksum.SerializeToString())
    ack = self.soc.recv(1)
    if ack != ACK:
      raise SocketConnectionError

