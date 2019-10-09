name = "paperpython"

import os, sys, socket
import wsgi_pb2
def main():
  ''' message Config {
        string ip = 1;
        uint32 port = 2;
        bool isIPv6 = 3; '''
  socket_setting = wsgi_pb2.Config()
  socket_setting.ParseFromString(sys.stdin.buffer.read())

  af = socket.AF_INET6 if socket_setting.isIPv6 else socket.AF_INET

  soc = socket.socket(af, socket.SOCK_STREAM)
  soc.connect((socket_setting.ip, socket_setting.port))

  soc.send(b'\x06')

if __name__ == '__main__':
  # bootUp()
  main()
