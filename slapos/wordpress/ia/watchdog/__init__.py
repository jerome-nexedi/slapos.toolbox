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
import time

from .connection import Server

def main():

  parser = argparse.ArgumentParser(description="Wordpress Watch Dog")
  parser.add_argument('url', metavar='URL', nargs=1, help="Url of one node.")
  parser.add_argument('--frequency', '-f', type=int, help="Frequency of watchdog.",
                      default=60)
  parser.add_argument('--master-url', '-m', help='ViFiB Master Url')
  parser.add_argument('--cert-file', '-c', required=True)
  parser.add_argument('--key-file', '-k', required=True)
  parser.add_argument('--software-release-url', '-s', required=True)
  args = parser.parse_args()

  server = Server(args.url[0], args.software_release_url,
                  args.master_url, args.key_file, args.cert_file)
  while True:
    time.sleep(args.frequency)
    server.get_master()
    server.think(1)



if __name__ == '__main__':
  main()
