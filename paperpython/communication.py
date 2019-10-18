import os, sys, socket, selectors, multiprocessing # concurrent.futures
from . import wsgi_pb2, wsgiImporter#, wsgi

application = wsgiImporter.getWsgiApplication()

def bootUp():
  socket_setting = wsgi_pb2.Config()
  socket_setting.ParseFromString(sys.stdin.buffer.read())
  return ServerSocket(socket_setting)

def run_with_cgi(soc, mask):

  env = wsgi_pb2.Environ()
  env.ParseFromString(soc.recv(4096))

  environ = {}
  environ['REQUEST_METHOD']  = env.request_method
  environ['SCRIPT_NAME']     = env.script_name
  environ['PATH_INFO']       = env.path_info
  environ['QUERY_STRING']    = env.query_string
  environ['CONTENT_TYPE']    = env.content_type
  environ['CONTENT_LENGTH']  = env.content_length
  environ['SERVER_NAME']     = env.server_name
  environ['SERVER_PORT']     = env.server_port
  environ['SERVER_PROTOCOL'] = env.server_protocol

  #map<string, string> http_request_headers = 10;
  #Wsgi wsgi = 11;
  wsgi = env.wsgi
  environ['wsgi.version']      = (wsgi.version.major, wsgi.version.minor)
  environ['wsgi.url_scheme']   = wsgi.url_scheme
  # TODO: fix
  environ['wsgi.input']        = sys.stdin.buffer #need to fix
  environ['wsgi.errors']       = sys.stderr # wsgi. blah
  environ['wsgi.multithread']  = wsgi.multithreaded
  environ['wsgi.multiprocess'] = wsgi.multiprocess
  environ['wsgi.run_once']     = wsgi.run_once

  headers_set = []
  headers_sent = []

  def write(data):
    out = soc

    response = wsgi_pb2.Response()

    if not headers_set:
      raise AssertionError("write() before start_response()")

    elif not headers_sent:
      # Before the first output, send the stored headers
      status, response_headers = headers_sent[:] = headers_set
      response.header.status = 'Status: {}'.format(status)
      for header in response_headers:
        response.header.response_headers[header[0]] = header[1]

    response.body = data

    out.send(response.SerializeToString())

  def start_response(status, response_headers, exc_info=None):
    if exc_info:
      try:
        if headers_sent:
          # Re-raise original exception if headers sent
          raise exc_info[1].with_traceback(exc_info[2])
      finally:
        exc_info = None     # avoid dangling circular ref
    elif headers_set:
      raise AssertionError("Headers already set!")

    headers_set[:] = [status, response_headers]

    # Note: error checking on the headers should happen here,
    # *after* the headers are set.  That way, if an error
    # occurs, start_response can only be re-called with
    # exc_info set.

    return write

  result = application(environ, start_response)
  try:
    for data in result:
      if data:    # don't send headers until body appears
        write(data)
    if not headers_sent:
      write('')   # send headers now if body was empty
  finally:
    if hasattr(result, 'close'):
      result.close()


class SocketConnectionError(Exception):
  pass


#Todo: Change name
class ServerSocket:

  ACK = b'\x06'

  #TODO: add separate read and write sockets
  def __init__(self, socket_setting):
    self.application = wsgiImporter.getWsgiApplication()
    self._setupSocket(socket_setting)
    self._handshake()
    self.soc.setblocking(False)

    self._setupSelector()

    self.enc, self.esc = sys.getfilesystemencoding(), 'surrogateescape'

  def _setupSocket(self, socket_setting):
    self.ip = socket_setting.ip
    self.port = socket_setting.port
    self.isIPv6 = socket_setting.isIPv6
    self.idChecksum = socket_setting.idChecksum
    self.numWorkers = socket_setting.numWorkers

    self.af = socket.AF_INET6 if self.isIPv6 else socket.AF_INET

    self.soc = socket.socket(self.af, socket.SOCK_STREAM)
    self.soc.connect((self.ip, self.port))

  def _handshake(self):
    self.soc.send(self.idChecksum.SerializeToString())
    ack = self.soc.recv(1)
    if ack != ServerSocket.ACK:
      raise SocketConnectionError

  def _setupSelector(self):
    self.sel = selectors.DefaultSelector()
    self.sel.register(self.soc, selectors.EVENT_READ, run_with_cgi)#self.handle)

  def run(self):

    events = self.sel.select()
    while True:
      events = self.sel.select()
      for key, mask in events:
        callback = key.data
        callback(key.fileobj, mask)

  #Use pool once sure about when write is ready
  # def handle(self, sock, event):

  def __del__(self):
    pass
    # self.pool.shutdown()
    # self.pool.close()

  def unicode_to_wsgi(self, u):
    # Convert an environment variable to a WSGI "bytes-as-unicode" string
      return u.encode(self.enc, self.esc).decode('iso-8859-1')

  def wsgi_to_bytes(self, s):
    return s.encode('iso-8859-1')



class RequestServer:
  pass

