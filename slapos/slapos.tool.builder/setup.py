# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os

name = 'slapos.tool.builder'

def read(*rnames):
  return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

long_description=(
        read('README.txt')
        + '\n' +
        read('CHANGES.txt')
    )

setup(
    name = name,
    version = '1.0-dev-2',
    description = "slapos - partitioning tools for servers",
    long_description=long_description,
    license = "GPLv3",
    keywords = "slapos server builder",
    include_package_data = True,
    packages = find_packages('src'),
    package_dir = {'':'src'},
    namespace_packages = ['slapos'],
    # slapgos use this to create a clean ouput
    install_requires = [
      'setuptools', # namespace
      ],
    entry_points = """
    [console_scripts]
    slapbuilder = %s:main
    """ % name,
    )
