import os, sys
# from importlib import util, machinery
import importlib

class ApplicationImportError(Exception):
    pass

def getWsgiApplication():
  wsgiEnv = os.getenv("WSGI_APP") 
  wsgiApp = "application.wsgi" if wsgiEnv is None else wsgiEnv
  _origional_suffixes = importlib.machinery.SOURCE_SUFFIXES.copy()
 
  try:
    wsgiAppPath = os.path.abspath(wsgiApp)
    importlib.machinery.SOURCE_SUFFIXES.append(".wsgi")
    module_name = "application"
    spec = importlib.util.spec_from_file_location(module_name, wsgiAppPath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    return module.application
  
  except:
    raise ApplicationImportError

  finally:
    importlib.machinery.SOURCE_SUFFIXES = _origional_suffixes

