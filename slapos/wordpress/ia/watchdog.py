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
from collections import deque
import time
import urlparse
import urllib
import httplib
import json
import uuid

class Connector(httplib.HTTPConnection):


  def __init__(self, url):
    self._url = urlparse.urlparse(url)
    hostname = self._url.hostname
    if ':' in hostname: # IPv6
      hostname = '[%s]' % hostname
    httplib.HTTPConnection.__init__(self, hostname,
                                    self._url.port)
    self._path_base = self._url.path
    self._peers = {}
    self._master_url = None


  def request(self, method, url, body=None, headers={}):
    url = urlparse.urljoin(self._url.path, url)
    return httplib.HTTPConnection.request(self, method, url, body, headers)


  def GET(self, url, params={}, headers={}):
    self.request('GET', urlparse.urljoin(url, urllib.urlencode(params)))
    return self.getresponse()


  def POST(self, url, data, headers={}):
    if isinstance(data, dict):
      _headers = headers.copy()
      _headers['Content-Type'] = 'application/x-www-form-urlencoded'
      _data = urllib.urlencode(data)
      self.request('POST', url, body=_data, headers=_headers)
    elif isinstance(data, basestring):
      self.request('POST', url, body=data, headers=headers)
    else:
      raise ValueError("data is neither a dict nor a string.")
    return self.getresponse()

  def geturl(self):
    return self._url.geturl()

  def __eq__(self, other):
    if not isinstance(other, Connector):
      raise ValueError, "Connector expected"
    return self._url.geturl() == other._url.geturl()


class Server(Connector):

  def gather_peers(self):
    self._peers = {}
    seen = deque()
    to_see = deque([Connector(self._url.geturl())])
    while to_see:
      try:
        connector = to_see.popleft()
        if connector not in seen:
          seen.append(connector)
          id_ = connector.GET('id').read()
          self.set_peer_id(id_, connector)
          to_see.extend([Connector(url)
                         for url in json.loads(self.GET('getPeers').read())])
      # Swallow everything except SIGTERM
      except SystemExit:
        raise
      except:
        pass


  @staticmethod
  def _convert_uuid(id_):
    if isinstance(id_, basestring):
      id_ = uuid.UUID(id_)
    if not isinstance(id_, uuid.UUID):
      raise ValueError("id should be an uuid")
    return id_


  def set_peer_id(self, id_, value):
    id_ = Server._convert_uuid(id_)
    self._peers[id_] = value


  def get_peer_id(self, id_):
    id_ = Server._convert_uuid(id_)
    if id_ not in self._peers:
      self.gather_peers()
    return self._peers[id_]


  def list_peers(self):
    return self._peers.values()

  def do_master_election(self):
    self.GET('refreshMesh')
    id_ = Server._convert_uuid(self.GET('master/vote').read())
    self.gather_peers()
    try:
      peer_list = self.list_peers()
      failed_list = []
      for peer in peer_list:
        response = peer.POST('master/suggest', {'master': id_.urn})
        if response.status == httplib.NO_CONTENT:
          pass
        else:
          failed_list.append(peer)
    except SystemExit:
      raise
    except:
      pass
    return self.get_peer_id(id_).geturl()


  def get_master(self):
    if self._master_url is None:
      get_master = self.GET('master/get')
      if get_master.status == httplib.NOT_FOUND:
        self._master_url = self.do_master_election()

      elif get_master.status == httplib.NO_CONTENT:
        self._master_url = self._url.geturl()

      else:
        try:
          self._master_url = get_master.read()
        except IndexError:
          self._master_url = self.do_master_election()
    else:
      try:
        Server._conver_uuid(Connector(self._master_url).GET('id').read())
      except SystemExit:
        raise
      except:
        self._master_url = None
        return self.get_master()
    return self._master_url

  def watch(self):
    print repr(self.get_master())



def main():

  parser = argparse.ArgumentParser(description="Wordpress Watch Dog")
  parser.add_argument('url', metavar='URL', nargs=1, help="Url of one node.")
  parser.add_argument('--frequency', '-f', type=int, help="Frequency of watchdog.",
                      default=60)
  args = parser.parse_args()

  server = Server(args.url[0])
  while True:
    time.sleep(args.frequency)
    server.watch()



if __name__ == '__main__':
  main()
