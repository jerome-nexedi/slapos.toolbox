from datetime import datetime
import csv
import feedparser
import socket
import json
import time
import math
import httplib # To avoid magic numbers
import argparse
import os
from hashlib import sha512

from atomize import Entry
from atomize import Feed
from atomize import Content
from flask import Flask
from flask import abort
from flask import request
app = Flask(__name__)

@app.route('/get/<feed>')
def get_feed(feed):
  global app

  feedpath = os.path.join(app.config['FEEDS'], feed)
  if not os.path.exists(feedpath):
    abort(httplib.NOT_FOUND)

  # XXX: Add a way to specify a title
  feed_title = 'Untitled'
  feed_guid = request.url
  # XXX: Add a way to specify an author
  feed_author = 'No author'

  entries = []
  feed_updated = 0
  with open(feedpath, 'r') as feed_file:
    reader = csv.reader(feed_file)
    for row in reader:
      timestamp, title, content, guid = row

      timestamp = int(timestamp)
      # Keep the maximum timestamp without
      # looping once more.
      if timestamp > feed_updated:
        feed_updated = timestamp

      entries.append(Entry(title=title,
                           guid=guid,
                           updated=datetime.fromtimestamp(timestamp),
                           content=Content(content, content_type='html'),
                          ))
  feed = Feed(title=feed_title,
              updated=datetime.fromtimestamp(feed_updated),
              guid=feed_guid,
              author=feed_author,
              entries=entries,
              self_link=request.url)

  return (feed.feed_string(),
          httplib.OK,
          {'Content-Type': 'application/atom+xml'}
         )

@app.route('/notify', methods=['POST'])
def notify():
  global app

  try:
    feed = feedparser.parse(request.data)
  except ValueError:
    abort(httplib.BAD_REQUEST)

  if feed.bozo: # Malformed XML
    abort(httplib.BAD_REQUEST)

  try:
    callback_filepath = os.path.join(app.config['CALLBACKS'],
                                     sha512(str(feed.feed.id)).hexdigest())
    if not os.path.exists(callback_filepath):
      abort(httplib.NOT_FOUND)
  except AttributeError:
    abort(httplib.BAD_REQUEST)

  with open(callback_filepath, 'r') as callback_file:
    callback = callback_file.read()


  timestamp = int(math.floor(time.mktime(feed.feed.updated_parsed)))

  equeue_request = json.dumps(dict(
    command=callback,
    timestamp=timestamp,
  ))

  equeue_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
  equeue_socket.connect(app.config['EQUEUE_SOCKET'])
  equeue_socket.send(equeue_request)
  result = equeue_socket.recv(len(callback))
  equeue_socket.close()

  if result != callback:
    abort(httplib.INTERNAL_SERVER_ERROR)

  return '', httplib.NO_CONTENT

def main():
  global app
  parser = argparse.ArgumentParser(description="Atom server")
  parser.add_argument('-c', '--callbacks', nargs=1, required=True,
                      help="Callback directory.")
  parser.add_argument('-f', '--feeds', nargs=1, required=True,
                      help="Feeds directory")
  parser.add_argument('-s', '--equeue-socket', dest='equeue_socket',
                      nargs=1, required=True, help="EQUEUE Server socket")
  parser.add_argument('host', metavar='hostname', default='0.0.0.0', nargs='?')
  parser.add_argument('port', metavar='port', type=int, default=8080, nargs='?')
  args = parser.parse_args()

  app.config.update(FEEDS=args.feeds[0],
                    CALLBACKS=args.callbacks[0],
                    EQUEUE_SOCKET=args.equeue_socket[0])
  app.run(host=args.host, port=args.port)

if __name__ == '__main__':
  main()
