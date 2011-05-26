##############################################################################
#
# Copyright (c) 2010 ViFiB SARL and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################


import hashlib
import os
import shutil
import slapos.tool.networkcached as networkcached
import tempfile
import unittest


class NetworkcacheTestCase(unittest.TestCase):

  def setUp(self):
    networkcached.app.config['CACHE_BASE_FOLDER'] = tempfile.mkdtemp()
    self.cache_base_folder = networkcached.app.config['CACHE_BASE_FOLDER']
    self.app = networkcached.app.test_client()
    self.file_content = 'test file content.'

  def tearDown(self):
    shutil.rmtree(self.cache_base_folder)

  def create_file_into_cache_base_folder(self):
    """
      Create a binary file into the directory.
    """
    file_name = hashlib.sha512(self.file_content).hexdigest()
    file_path = os.path.join(self.cache_base_folder, file_name)
    f = open(file_path, 'w')
    try:
      f.write(self.file_content)
    finally:
      f.close()
    return file_path

  def test_get_non_existing_file(self):
    """
      When the client tries to download a file which does not exists, it must
      return a 404 error.
    """
    result = self.app.get('/does_not_exists')
    self.assertEquals('404 NOT FOUND', result.status)
    self.assertTrue('File not found.' in result.data)

  def test_get_existing_file(self):
    """
      Check if the file is returned if it exists.
    """
    file_path = self.create_file_into_cache_base_folder()
    result = self.app.get('/%s' % file_path.split('/')[-1])
    self.assertEquals('200 OK', result.status)
    self.assertEquals('application/octet-stream',
                            result.headers['Content-Type'])
    self.assertEquals(self.file_content, result.data)

  def test_puti_file(self):
    """
      Check if the file will be upload just fine.
    """
    file_content = 'file does not exist yet'
    file_name = hashlib.sha512(file_content).hexdigest()

    result = self.app.put('/', data=file_content)
    self.assertEquals('200 OK', result.status)
    self.assertEquals('Success', result.data)

    f = open(os.path.join(self.cache_base_folder, file_name), 'r')
    try:
      data = f.read()
    finally:
      f.close()
    self.assertEquals(file_content, data)


def run():
  unittest.main(module=networkcached.test)

if __name__ == '__main__':
  run()
