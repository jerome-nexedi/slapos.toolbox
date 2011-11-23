#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import subprocess
import os
import uuid
import csv
import time
import urllib2
from urlparse import urlparse
import httplib
import socket
import sys
import argparse

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('-l', '--log', nargs=1, required=True,
                      dest='logfile', metavar='logfile',
                      help="Logging file")
  parser.add_argument('-t', '--title', nargs=1, required=True,
                      help="Entry title.")
  parser.add_argument('-f', '--feed', nargs=1, required=True,
                      dest='feed_url', help="Url of the feed.")
  parser.add_argument('--notification-url', dest='notification_url',
                      nargs=1, required=True,
                      help="Notification url")
  parser.add_argument('executable', nargs=1,
                      help="Executable to wrap")

  args = parser.parse_args()

  with open(os.devnull) as devnull:
    command = subprocess.Popen(args.executable,
                               stdin=subprocess.PIPE,
                               stdout=devnull,
                               stderr=subprocess.PIPE,
                               close_fds=True)
    command.stdin.flush()
    command.stdin.close()

    if command.wait() != 0:
      content = ("<p>Failed with returncode <em>%d</em>.</p>"
                 "<p>Standard error output is :</p><pre>%s</pre>") % (
        command.poll(),
        command.stderr.read().replace('&', '&amp;')\
                             .replace('<', '&lt;')\
                             .replace('>', '&gt;'),
      )
    else:
      content = "<p>Everything went well.</p>"

  with open(args.logfile[0], 'a') as file_:
    cvsfile = csv.writer(file_)
    cvsfile.writerow([
      int(math.floor(time.time())), # Timestamp
      args.title[0],
      content,
      'slapos:%s' % uuid.uuid4(),
    ])

  feed = urllib2.urlopen(args.feed_url[0])

  notification_url = urlparse(args.notification_url[0])
  notification_port = notification_url.port
  if notification_port is None:
    notification_port = socket.getservbyname(notification_url.scheme)

  headers = {'Content-Type': feed.info().getheader('Content-Type')}
  notification = httplib.HTTPConnection(notification_url.hostname,
                                               notification_port)
  notification.request('POST', notification_url.path, feed.read(), headers)
  response = notification.getresponse()

  if 200 <= response.status < 300:
    return 0
  else:
    print >> sys.stderr, "The remote server didn't send a successfull reponse."
    print >> sys.stderr, "It's response was %r" % response.reason
    return 1

if __name__ == '__main__':
  main()
