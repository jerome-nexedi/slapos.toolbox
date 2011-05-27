from setuptools import setup, find_packages
import glob
import os

version = '0.1'
name = 'slapos.toolbox'
long_description = open("README.txt").read() + "\n" + \
    open("CHANGES.txt").read() + "\n"

for f in sorted(glob.glob(os.path.join('slapos', 'README.*.txt'))):
  long_description += '\n' + open(f).read() + '\n'

additional_install_requires = []
# Even if argparse is available in python2.7, some python2.7 installations
# do not have it, so checking python version is dangerous
try:
  import argparse
except ImportError:
  additional_install_requires.append('argparse')

setup(name=name,
      version=version,
      description="SlapOS toolbox.",
      long_description=long_description,
      classifiers=[
          "Programming Language :: Python",
        ],
      keywords='slapos toolbox',
      license='GPLv3',
      namespace_packages=['slapos'],
      packages=find_packages(),
      include_package_data=True,
      install_requires=[
        'Flask', # needed by servers
        'apache_libcloud>=0.4.0', # needed by cloudmgr
        'lxml', # needed for xml parsing
        'paramiko', # needed by cloudmgr
        'psutil', # needed for playing with processes in portable way
        'setuptools', # namespaces
        'slapos.core', # as it provides library for slap
        'xml_marshaller', # needed to dump information
      ] + additional_install_requires,
      zip_safe=False, # proxy depends on Flask, which has issues with
                      # accessing templates
      entry_points={
        'console_scripts': [
          'clouddestroy = slapos.cloudmgr.destroy:main',
          'cloudgetprivatekey = slapos.cloudmgr.getprivatekey:main',
          'cloudgetpubliciplist = slapos.cloudmgr.getpubliciplist:main',
          'cloudlist = slapos.cloudmgr.list:main',
          'cloudmgr = slapos.cloudmgr.cloudmgr:main',
          'cloudstart = slapos.cloudmgr.start:main',
          'cloudstop = slapos.cloudmgr.stop:main',
          'onetimeupload = slapos.onetimeupload:main',
          'shacache = slapos.shacache:main',
          'slapbuilder = slapos.builder:main',
          'slapmonitor = slapos.monitor:run_slapmonitor',
          'slapreport = slapos.monitor:run_slapreport',
          'slaprunner = slapos.runner:run',
        ]
      },
    )
