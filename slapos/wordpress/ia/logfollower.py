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
import re
import os
import urllib2
import urlparse

from slapos import logfollower

def main():
  parser = argparse.ArgumentParser(description="Log follower.")
  parser.add_argument('--regex', '-r', help="Regular expression which "
                                            "trigger the callback.",
                      required=True)
  parser.add_argument('--rotated', action='store_const', default=False,
                      const=True, help="Specify that the logfile can be "
                                       "rotated. This will detect the "
                                       "rotation and reload it.")
  parser.add_argument('--timeout', '-t', default=-1, type=int)
  parser.add_argument('--wait-for-creation', action='store_const', default=False,
                      const=True, help="Wait for the log file creation.")
  parser.add_argument('logfile', metavar='LOGFILE', nargs=1,
                      help="Log file to follow.")
  parser.add_argument('url', metavar='URL', nargs=1,
                      help="Url where to posts logs")
  args = parser.parse_args()

  try:
    regex = re.compile(args.regex)
  except:
    parser.error("Bad regular expression.")

  log_filename = os.path.abspath(os.path.join(os.getcwd(), args.logfile[0]))

  if args.wait_for_creation:
    try:
      logfollower.wait_for_creation(log_filename)
    except:
      return 1 # Exit failure
  elif not os.path.isfile(log_filename):
    return 1 # Exit failure

  for line in logfollower.follow_each_line(args.logfile[0], args.rotated,
                                           args.timeout):
    message = '<p>OK</p>'
    if line == None:
      message = '<p>TIMEOUT</p>'
    elif regex.match(line):
      message = '<p>FAIL</p>'
    urllib2.urlopen(urllib2.Request(
      url=urlparse.urljoin(args.url[0], '?Status'),
      data=message,
      headers={'Content-Type': 'application/octet-stream'},
    )).read()

if __name__ == '__main__':
  __import__('sys').exit(main())
