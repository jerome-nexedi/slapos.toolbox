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
import sys
import traceback
from flask import Flask, request, helpers, abort, make_response
from config import NetworkcacheConfiguration, NetworkcacheParser


app = Flask(__name__)


@app.route('/', methods=['POST'])
def post():
  """ Save the file on the cache server. """
  if getattr(request, 'data', None) is None:
    abort(400, 'POST requires data.')

  cache_base_folder = app.config.get('CACHE_BASE_FOLDER')
  file_name = hashlib.sha512(request.data).hexdigest()
  try:
    f = open(os.path.join(cache_base_folder, file_name), "w+")
    try:
      f.write(request.data)
    finally:
      f.close()
  except:
    app.logger.info(traceback.format_exc())
    abort(500, "Faile to upload the file.")

  return make_response(file_name, 201)


@app.route('/<key>', methods=['GET'])
def get(key):
  """ Return the file if found, otherwise 404 is raised. """
  cache_base_folder = app.config.get('CACHE_BASE_FOLDER')
  file_path = os.path.join(cache_base_folder, key)
  if not os.path.exists(file_path):
    abort(404, 'File not found.')

  return helpers.send_file(file_path)


def main():
  "Run default configuration."
  usage = "usage: %s [options] CONFIGURATION_FILE" % sys.argv[0]

  try:
    # Parse arguments
    configuration = NetworkcacheConfiguration()
    configuration.setConfig(*NetworkcacheParser(usage=usage).check_args())

    app.config['CACHE_BASE_FOLDER'] = configuration.cache_base_folder
    app.run(host=configuration.host, port=int(configuration.port), debug=True)
    return_code = 0
  except SystemExit, err:
    # Catch exception raise by optparse
    return_code = err

  sys.exit(return_code)
