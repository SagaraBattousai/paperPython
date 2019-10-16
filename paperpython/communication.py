import os, sys, socket, selectors, concurrent.futures
from . import wsgi_pb2, wsgiImporter#, wsgi

def bootUp():
  socket_setting = wsgi_pb2.Config()
  socket_setting.ParseFromString(sys.stdin.buffer.read())
  return ServerSocket(socket_setting)
  
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

    self.pool = concurrent.futures.ProcessPoolExecutor(self.numWorkers)



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
    self.sel.register(self.soc, selectors.EVENT_READ, self.handle)

  def run(self):
    events = self.sel.select()
    for key, mask in events:
      callback = key.data
      callback(key.fileobj, mask)

  #Use pool once sure about when write is ready
  def handle(self, sock, event):
      if event == selectors.EVENT_READ:
          self.handleRequests()
      else:
          self.serveRequests()

  def handleRequests(self):
      self.soc.recv(2)
      self.run_with_cgi()

  def serveRequests(self):
      self.soc.send(b'wr')

  def __del__(self):
      self.pool.shutdown()
  

  def unicode_to_wsgi(self, u):
      # Convert an environment variable to a WSGI "bytes-as-unicode" string
      return u.encode(self.enc, self.esc).decode('iso-8859-1')
  
  def wsgi_to_bytes(self, s):
      return s.encode('iso-8859-1')
  
  def run_with_cgi(self):
      environ = {k: self.unicode_to_wsgi(v) for k,v in os.environ.items()}
      environ['wsgi.input']        = sys.stdin.buffer
      environ['wsgi.errors']       = sys.stderr
      environ['wsgi.version']      = (1, 0)
      environ['wsgi.multithread']  = False
      environ['wsgi.multiprocess'] = True
      environ['wsgi.run_once']     = True
  
      ############################
      environ['PATH_INFO'] = "/"
      environ['SERVER_NAME'] = "tmp"
      environ['SERVER_PORT'] = "8080"
      environ['REQUEST_METHOD'] = "GET"
  
      if environ.get('HTTPS', 'off') in ('on', '1'):
          environ['wsgi.url_scheme'] = 'https'
      else:
          environ['wsgi.url_scheme'] = 'http'
  
      headers_set = []
      headers_sent = []
  
      def write(data):
          out = sys.stdout.buffer
  
          if not headers_set:
               raise AssertionError("write() before start_response()")
  
          elif not headers_sent:
               # Before the first output, send the stored headers
               status, response_headers = headers_sent[:] = headers_set
               out.write(self.wsgi_to_bytes('Status: %s\r\n' % status))
               for header in response_headers:
                   out.write(self.wsgi_to_bytes('%s: %s\r\n' % header))
               out.write(self.wsgi_to_bytes('\r\n'))
  
          out.write(data)
          out.flush()
  
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
  
      result = self.application(environ, start_response)
      try:
          for data in result:
              if data:    # don't send headers until body appears
                  write(data)
          if not headers_sent:
              write('')   # send headers now if body was empty
      finally:
          if hasattr(result, 'close'):
              result.close()


class RequestServer:
    pass

