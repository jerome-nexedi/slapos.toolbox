from setuptools import setup, find_packages
import os

name = "slapos.tool.monitor"
version = '0.0.6dev'

def read(*rnames):
  return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

long_description=(
        read('README.txt')
        + '\n' +
        read('CHANGES.txt')
    )

setup(
    name = name,
    version = version,
    description = "Monitoring for SlapOS provided partitions",
    long_description=long_description,
    license = "GPLv3",
    keywords = "slapos partition monitor",
    classifiers=[
      "Programming Language :: Python",
      ],
    packages = find_packages('src'),
    include_package_data = True,
    package_dir = {'':'src'},
    namespace_packages = [ 'slapos' ],
    install_requires = [
      'setuptools', # namespaces
      'lxml',
      'psutil',
    ],
    zip_safe=True,
    entry_points = """
    [console_scripts]
    slapmonitor = %(name)s.slapmonitor:run_slapmonitor
    slapreport = %(name)s.slapmonitor:run_slapreport
    """ % dict(name=name),
    )
