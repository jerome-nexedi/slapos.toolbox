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
from collections import deque
import urlparse
import urllib
import httplib
import json
import uuid
import feedparser
import datetime
import math
import time

from slapos.slap import slap

def get_status(feed_content):
  feed = feedparser.parse(feed_content)

  error_amount = 0
  for entry in feed.entries:
    if 'FAIL' in entry.summary:
      error_amount += 1
    # XXX: Hard coding maximum error amount
    #      is 3.
    if error_amount >= 3:
      return False
  return True

def get_timestamp(minutes_ago):
  result = datetime.datetime.now()
  result -= datetime.timedelta(minutes=minutes_ago)
  return int(math.floor(time.mktime(result.timetuple())))



class Connector(httplib.HTTPConnection):

  def __init__(self, url):
    self._url = urlparse.urlparse(url)
    httplib.HTTPConnection.__init__(self, self._url.hostname,
                                    self._url.port)
    self._path_base = self._url.path
    self._peers = {}
    self._master_url = None

    self._computer_id = self.GET('info/computerId').read().strip()
    self._partition_id = self.GET('info/partitionId').read().strip()

  def request(self, method, url, body=None, headers={}):
    url = urlparse.urljoin(self._url.path, url)
    return httplib.HTTPConnection.request(self, method, url, body, headers)

  def GET(self, url, params={}, headers={}):
    self.connect()
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
      return NotImplemented
    return self._url.geturl() == other._url.geturl()

class Server(Connector):

  def __init__(self, url, software_release,
               master_url, key_file=None, cert_file=None):
    Connector.__init__(self, url)

    self._slapos_master_url = master_url
    self._key_file = key_file
    self._cert_file = cert_file
    self._software_release = software_release

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
                         for url in json.loads(connector.GET('getPeers').read())])
      except:
        pass

  @staticmethod
  def _convert_uuid(id_):
    if isinstance(id_, basestring):
      id_ = uuid.UUID(str(id_))
    if not isinstance(id_, uuid.UUID):
      raise ValueError("id should be an uuid")
    return id_


  def set_peer_id(self, id_, value):
    id_ = Server._convert_uuid(id_)
    type_ = None
    try:
      type_ = value.GET('info/type').read()
    except:
        pass
    else:
      to_set_none = deque()
      # Look for peer having same type (type should be unique)
      for peer_id, peer_data in self._peers.iteritems():
        peer_type = peer_data[0]
        if peer_type == type_:
          to_set_none.append(peer_id)
      # Set type None for those peers
      for peer_id in to_set_none:
        self._peers[peer_id] = (None, self._peers[peer_id][1],)
    self._peers[id_] = (type_, value,)


  def get_peer_id(self, id_):
    id_ = Server._convert_uuid(id_)
    if id_ not in self._peers:
      self.gather_peers()
    return self._peers[id_][1]

  def list_peers(self):
    return (p[1] for p in self._peers.values())

  def do_master_election(self):
    self.GET('refreshMesh').read()
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
    except:
      pass
    return self.get_peer_id(id_).geturl()


  def get_master(self):
    if self._master_url is None:
      get_master = self.GET('master/get')
      master_url = get_master.read()
      if get_master.status == httplib.NOT_FOUND:
        self._master_url = self.do_master_election()

      elif get_master.status == httplib.NO_CONTENT:
        self._master_url = self._url.geturl()

      else:
        self._master_url = master_url
    else:
      try:
        Server._conver_uuid(Connector(self._master_url).GET('id').read())
      except:
        self._master_url = None
        return self.get_master()
    return self._master_url

  def think(self, threshold):
    """Main function of watchdog behavior.
    """
    self.gather_peers()
    for peer in self.list_peers():
      try:
        log_list_request = peer.GET('logList')
        if log_list_request.status == httplib.NOT_FOUND:
          log_list_request.read()
          continue

        log_list = json.loads(log_list_request.read())
        for item in log_list:
          status = get_status(
            peer.GET('log/%s?min-date=%d' % (item, get_timestamp(threshold), )
                    ).read()
          )
          if not status:
            if item == 'mariadb':
              self.switch_to_mariadb_backup()
            else:
              pass
      except:
        pass

  def get_type(self, type_):
    for peer_type, peer in self._peers.itervalues():
      if peer_type == type_:
        return peer
    raise KeyError("%s not found" % type_)

  def switch_to_mariadb_backup(self):
    mariadb_backup = self.get_type('mariadb-backup')
    mariadb = self.get_type('mariadb')
    self.down(mariadb)
    self.rename(mariadb_backup, 'MariaDB')
    self.bang()

  def down(self, connector):
    new_name = 'down_%s' % uuid.uuid4().hex
    self.rename(connector, new_name)
    # XXX: EXTREMELY Dirty Workaround to avoid bug #20120127-6487F8
    time.sleep(10)
    self.slaprequest(partition_reference=new_name,
                     software_type='down')

  def rename(self, connector, new_name):
    partition = self.get_partition(connector)
    partition.rename(new_name)

  def get_partition(self, connector):
    return self._register_cp(connector._computer_id,
                             connector._partition_id)

  def slaprequest(self, *args, **kwargs):
    partition = self._register_cp(self._computer_id,
                                  self._partition_id)
    return partition.request(self._software_release,
                             *args, **kwargs)

  def bang(self, *args, **kwargs):
    partition = self._register_cp(self._computer_id,
                                  self._partition_id)
    return partition.bang(self._software_release,
                          *args, **kwargs)

  def _register_cp(self, computer_id, partition_id):
    connection = slap()
    connection.initializeConnection(
      self._slapos_master_url,
      self._key_file,
      self._cert_file,
    )
    return connection.registerComputerPartition(computer_id,
                                                partition_id)
