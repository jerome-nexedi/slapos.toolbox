from setuptools import setup, find_packages
import glob
import os

version = '0.14'
name = 'slapos.toolbox'
long_description = open("README.txt").read() + "\n" + \
    open("CHANGES.txt").read() + "\n"

for f in sorted(glob.glob(os.path.join('slapos', 'README.*.txt'))):
  long_description += '\n' + open(f).read() + '\n'

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
        'atomize', # needed by pubsub
        'feedparser', # needed by pubsub
        'apache_libcloud>=0.4.0', # needed by cloudmgr
        'lxml', # needed for xml parsing
        'paramiko', # needed by cloudmgr
        'psutil', # needed for playing with processes in portable way
        'setuptools', # namespaces
        'slapos.core', # as it provides library for slap
        'xml_marshaller', # needed to dump information
      ],
      extras_require = {
        'lampconfigure':  ["mysql-python"] #needed for MySQL Database access
      },
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
          'onetimedownload = slapos.onetimedownload:main',
          'shacache = slapos.shacache:main',
          'slapbuilder = slapos.builder:main',
          'slapmonitor = slapos.monitor:run_slapmonitor',
          'slapreport = slapos.monitor:run_slapreport',
          'slaprunner = slapos.runner:run',
          'killpidfromfile = slapos.systool:killpidfromfile',
          'lampconfigure = slapos.lamp:run [lampconfigure]',
          'equeue = slapos.equeue:main',
          'pubsubserver = slapos.pubsub:main',
          'pubsubnotifier = slapos.pubsub.notifier:main',
        ]
      },
    )
