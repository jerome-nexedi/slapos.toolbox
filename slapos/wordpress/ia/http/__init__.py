##############################################################################
#
# Copyright (c) 2010 Vifib SARL and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
import argparse
from datetime import datetime
import httplib
import math
import json
import os
import urllib
import urllib2
import urlparse
import uuid
from collections import deque
from hashlib import sha512
import time
import socket

import atomize
import feedparser
from flask import Flask
from flask import abort
from flask import request
from flask import make_response
from sqlalchemy import desc
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from slapos.wordpress.ia.http.data import Base, Component, Entry, Config, Peer

app = Flask(__name__)
app.config.from_envvar('CONFIG')
DATABASE_PATH = app.config['DATABASE_PATH']
if not os.path.exists(DATABASE_PATH):
  open(DATABASE_PATH, 'w').close() # Just a touch
engine = create_engine('sqlite:///%s' % os.path.abspath(DATABASE_PATH))
Base.metadata.create_all(engine)

Session = sessionmaker()
Session.configure(bind=engine)

N_FEED_ENTRY_DEFAULT = 50
N_FEED_ENTRY_MAX = 500



def get_session_id(session):
  id_config = session.query(Config).filter(Config.id == 'id').first()
  if id_config is None:
    app_id = uuid.uuid4().urn
    session.add(Config(id='id', value=app_id))
    session.commit()
  else:
    app_id = id_config.value
  return app_id


def get_master(session):
  app_id = get_session_id(session)
  candidate_list = session.query(Peer).filter(Peer.id > app_id)\
                                      .order_by(desc(Peer.id))
  for candidate in candidate_list:
    try:
      candidate_id = uuid.UUID(candidate.id)
      id_url = urlparse.urljoin(candidate.url, 'id')
      read_id = uuid.UUID(urllib2.urlopen(id_url).read())
      if candidate_id == read_id:
        return candidate
    except SystemExit:
      raise
    except:
      pass

  return None # Master is me



@app.route('/getPeers')
def get_peers():
  result = make_response(json.dumps(app.config.get('PEERS', [])))
  result.headers['Content-Type'] = 'application/json'
  return result



@app.route('/refreshMesh')
def refresh_mesh():
  global app
  session = Session()

  session.query(Peer).delete()

  seen = deque([uuid.UUID(get_session_id(session))])
  to_see = deque(app.config.get('PEERS', []))

  while to_see:
    url = to_see.pop()
    try:
      id_url = urlparse.urljoin(url, 'id')
      id_ = uuid.UUID(urllib2.urlopen(id_url).read())
      if id_ not in seen:
        session.add(Peer(id=id_.urn, url=url))

        peers_list_url = urlparse.urljoin(url, 'getPeers')
        peers_url = [str(s) for s in json.loads(urllib2.urlopen(peers_list_url).read())]
        to_see.extend(peers_url)
        seen.append(id_)
    except SystemExit:
      pass
    except:
      pass

  session.commit()

  return '', httplib.NO_CONTENT



@app.route("/master/vote")
def vote_for_master():
  global app
  session = Session()

  master = get_master(session)
  if master is not None:
    id_ = uuid.UUID(master.id).urn
  else:
    id_ = get_session_id(session)

  response = make_response(id_)
  response.headers['Content-Type'] = 'text/plain'

  return response



@app.route("/master/get")
def get_master_url():
  global app
  session = Session()

  master_id = session.query(Config).filter(Config.id == 'master').first()
  if master_id is None:
    abort(httplib.NOT_FOUND)

  master = session.query(Peer).filter(Peer.id == master_id.value).first()
  if master is None:
    return '', httplib.NO_CONTENT
  else:
    response = make_response(master.url)
    response.headers['Content-Type'] = 'text/plain'
    return response



@app.route("/master/suggest", methods=['POST'])
def sugget_master():
  global app
  session = Session()

  try:
    suggested_master = uuid.UUID(request.form['master'])
  except ValueError:
    abort(httplib.BAD_REQUEST)

  master = get_master(session)
  if master is None:
    master = uuid.UUID(get_session_id(session))
  else:
    master = uuid.UUID(master.id)

  if master != suggested_master:
    abort(httplib.CONFLICT)
  else:
    master_query = session.query(Config).filter(Config.id == 'master')
    if master_query.count() > 1:
      master_query.delete()
    session.add(Config(id='master', value=master.urn))
    session.commit()

  return '', httplib.NO_CONTENT



@app.route("/master")
def selected_master():
  global app
  session = Session()
  master = session.query(Config).filter(Config.id == 'master').first()
  if master is None:
    return '', httplib.NO_CONTENT

  response = make_response(master)
  response.headers['Content-Type'] = 'plain/text'
  return response



@app.route("/log/<title>", methods=['POST'])
def post_log_entry(title):
  global app
  session = Session()

  component = session.query(Component).filter(Component.title == title)\
                                      .first()
  if component is None:
    component = Component(title=title)
    session.add(component)

  session.add(Entry(
    component=component,
    datetime=datetime.now(),
    title=urllib.unquote(request.query_string),
    content=request.data
  ))

  session.commit()

  return '', httplib.NO_CONTENT



@app.route("/log/<title>", methods=['GET'])
def get_log_entries(title):
  global app
  session = Session()

  component = session.query(Component).filter(Component.title == title)\
                                      .first()
  if component is None:
    abort(httplib.NOT_FOUND)

  min_date = request.args.get('min-date')
  max_date = request.args.get('max-date')
  try:
    if min_date is not None:
      min_date = datetime.fromtimestamp(float(min_date))
    if max_date is not None:
      max_date = datetime.fromtimestamp(float(max_date))
    if min_date > max_date:
      raise ValueError
    number = int(request.args.get('n', N_FEED_ENTRY_DEFAULT))
  except ValueError:
    abort(httplib.BAD_REQUEST)

  if number > N_FEED_ENTRY_MAX:
    abort(httplib.REQUEST_ENTITY_TOO_LARGE)

  pattern = request.args.get('pattern', None)

  entries = session.query(Entry).filter(Entry.component_id == component.id)
  if min_date is not None:
    entries = entries.filter(Entry.datetime > min_date)
  if max_date is not None:
    entries = entries.filter(Entry.datetime < max_date)
  if pattern is not None:
    entries = entries.filter(Entry.content.like(pattern))
  entries = entries.order_by(desc(Entry.datetime))
  entries = entries.limit(number)

  feed_entries = []
  feed_updated = datetime.fromtimestamp(0)
  for entry in entries:
    kwargs = {}
    if entry.content is not None:
      kwargs['content'] = atomize.Content(entry.content, content_type='html')
    feed_entries.append(atomize.Entry(
      title=entry.title,
      guid=urlparse.urljoin(request.url, '/%d/%d' % (entry.component.id, entry.id)),
      updated=entry.datetime,
      author=entry.component.title,
      **kwargs
    ))
    feed_updated = max(feed_updated, entry.datetime)

  feed = atomize.Feed(
    title=component.title,
    updated=feed_updated,
    guid=request.base_url,
    self_link=request.url,
    entries=feed_entries,
    author=component.title,
  )
  return feed.feed_string()


@app.route('/notify', methods=['POST'])
def notify():
  global app

  if request.form['hub.mode'] != 'publish':
    abort(httplib.BAD_REQUEST)

  # Just the latest entry
  url = urlparse.urljoin(request.form['hub.url'], '?n=1')
  feed = feedparser.parse(url)
  timestamp = int(math.floor(time.mktime(feed.feed.updated_parsed)))

  callback_filename = os.path.join(app.config['CALLBACKS_DIRECTORY'],
                                   sha512(feed.feed.id).hexdigest())
  if not os.path.exists(callback_filename):
    abort(httplib.NOT_FOUND)
  with open(callback_filename, 'r') as callback_file:
    callback = callback_file.read()

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


@app.route('/id')
def get_id():
  session = Session()

  app_id = get_session_id(session)

  response = make_response(app_id)
  response.headers['Content-Type'] = 'text/plain'

  return response



def main():
  global app
  parser = argparse.ArgumentParser(description="Wordpress Log Server")
  parser.add_argument('-d', '--debug', action='store_const',
                      const=True, default=False,
                      help="enable debug mode for development.")
  parser.add_argument('--host', metavar='HOSTNAME', default='0.0.0.0',
                      required=False, help="specify hostname to bind on.",
                      type=str)
  parser.add_argument('--port', metavar='PORT', type=int, default=8080,
                      help="specify port to bind on.")
  args = parser.parse_args()
  app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
  main()
