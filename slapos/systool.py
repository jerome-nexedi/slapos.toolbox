import sys
import os
import signal
def killpidfromfile():
  if len(sys.argv) != 3:
    raise ValueError('Invocation: %s <pidfile> <signal name>' % sys.argv[0])
  file = sys.argv[1]
  sig = getattr(signal, sys.argv[2], None)
  if sig is None:
    raise ValueError('Unknwon signal name %s' % sys.argv[2])
  pid = int(open(file).read())
  print 'Killing pid %s with signal %s' % (pid, sys.argv[2])
  os.kill(pid, sig)
