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
import mechanize
import urlparse

# XXX-Antoine: Not Working ! This is a first draft.

def import_wordpress(from_wordpress, to_wordpress):
  """Import data from a wordpress to another using WordPress XML.
  Install wordpress xml importer on targeted wordpress instance if needed.

  from_wordpress: a tuple (url, login, password)
  to_wordpress: a tuple (url, login, password)
  """
  from_wordpress_export = urlparse.urljoin(from_wordpress[0], 'wp-admin/export.php')
  to_wordpress_import = urlparse.urljoin(to_wordpress[0], 'wp-admin/import.php')

  from_browser = mechanize.Browser()
  from_browser.open(from_wordpress_export)

  # Log in
  login, password = from_wordpress[1:3]
  from_browser.select_form('loginform')
  from_browser['log'] = login
  from_browser['pwd'] = password
  from_browser.submit()

  # Export
  from_browser.select_form(predicate=lambda form: form.attrs.get('id') == 'export-filters')
  #  Select to export all content
  from_browser['content'] = ['all']


  to_browser = mechanize.Browser()
  to_browser.open(to_wordpress_import)
  # Log in
  login, password = to_wordpress[1:3]
  to_browser.select_form('loginform')
  to_browser['log'] = login
  to_browser['pwd'] = password
  to_browser.submit()

  # Import
  to_browser.follow_link(text='WordPress')
  # If wordpress import plugin not installed.
  if any([link.text == 'Install Now' for link in to_browser.links()]):
    to_browser.follow_link(text='Install Now')
    to_browser.open(to_wordpress_import)
    to_browser.follow_link(text='WordPress')
  # XXX: Select the first form (which should be the only one)
  to_browser.select_form(predicate=lambda form: form.attrs.get('id') == 'import-upload-form')
  data = from_browser.submit()
  to_browser.add_file(data, name='import')
  to_browser.submit()

  return 0
