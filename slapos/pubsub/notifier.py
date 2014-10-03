#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import csv
import httplib
import socket
import subprocess
import sys
import time
import traceback
import urllib2
import urlparse
import uuid


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
                      nargs='*', required=True,
                      help="Notification url")
  parser.add_argument('--executable', nargs=1, dest='executable',
                      help="Executable to wrap")
  parser.add_argument('--transaction-id', nargs=1, dest='transaction_id',
                      type=int, required=False,
                      help="Additional parameter for notification-url")

  args = parser.parse_args()

  try:
    content = subprocess.check_output(
        args.executable[0],
        stderr=subprocess.STDOUT
    )
    exit_code = 0
    content = ("OK</br><p>%s ran successfully</p>"
                  "<p>Output is: </p><pre>%s</pre>" % (
          args.executable[0],
          content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
      ))
  except subprocess.CalledProcessError as e:
    content = e.output
    exit_code = e.returncode
    content = ("FAILURE</br><p>%s Failed with returncode <em>%d</em>.</p>"
                  "<p>Output is: </p><pre>%s</pre>" % (
          args.executable[0],
          exit_code,
          content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
      ))

  print content


  with open(args.logfile[0], 'a') as file_:
    cvsfile = csv.writer(file_)
    cvsfile.writerow([
      int(time.time()),
      args.title[0],
      content,
      'slapos:%s' % uuid.uuid4(),
    ])

  if  exit_code != 0:
    sys.exit(exit_code)

  print 'Fetching %s feed...' % args.feed_url[0]

  feed = urllib2.urlopen(args.feed_url[0])
  body = feed.read()

  some_notification_failed = False
  for notif_url in args.notification_url:
    notification_url = urlparse.urlparse(notif_url)

    notification_port = notification_url.port
    if notification_port is None:
      notification_port = socket.getservbyname(notification_url.scheme)

    notification_path = notification_url.path
    if not notification_path.endswith('/'):
      notification_path += '/'

    transaction_id = args.transaction_id[0] if args.transaction_id else int(time.time()*1e6)
    notification_path += str(transaction_id)

    headers = {'Content-Type': feed.info().getheader('Content-Type')}
    try:
      notification = httplib.HTTPConnection(notification_url.hostname,
                                            notification_port)
      notification.request('POST', notification_path, body, headers)
      response = notification.getresponse()
      if not (200 <= response.status < 300):
        sys.stderr.write("The remote server at %s didn't send a successful reponse.\n" % notif_url)
        sys.stderr.write("Its response was %r\n" % response.reason)
        some_notification_failed = True
    except socket.error as exc:
      sys.stderr.write("Connection with remote server at %s failed:\n" % notif_url)
      sys.stderr.write(traceback.format_exc(exc))
      some_notification_failed = True

  if some_notification_failed:
    sys.exit(1)

if __name__ == '__main__':
  main()

