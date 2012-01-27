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
import urllib
import urllib2
import urlparse
import subprocess
import sys
import cgi

def main():
  parser = argparse.ArgumentParser(description='Notifier')
  parser.add_argument('-w', '--write', help='Feed to write into',
                      action='store', required=True)
  parser.add_argument('-t', '--title', help='Entry title',
                      action='store', required=True)
  parser.add_argument('-n', '--notify', action='append', default=[],
                     help='Feed to notify, multiple allowed')
  parser.add_argument('argument', nargs='+', help='Command line argument')

  args = parser.parse_args()

  process = subprocess.Popen(args.argument, stdin=subprocess.PIPE,
                             stderr=subprocess.PIPE)
  process.stdin.flush()
  process.stdin.close()

  returncode =  process.wait()

  url = urlparse.urljoin(args.write, '?%s' % urllib.quote(args.title))

  if returncode == 0:
    data = '<p>OK</p>'
  else:
    data = '<p>FAIL</p><pre>%s</pre>' % cgi.escape(process.stderr.read())
  urllib2.urlopen(urllib2.Request(url, data=data,
    headers={'Content-Type': 'application/octet-stream'}))

  data = urllib.urlencode(
    {'hub.mode': 'publish',
     'hub.url': args.write}
  )
  for agent in args.notify:
    try:
      urllib2.urlopen(agent, data=data)
    except (KeyboardInterrupt, SystemExit):
      raise
    except:
      pass

  return returncode

if __name__ == '__main__':
  sys.exit(main())
