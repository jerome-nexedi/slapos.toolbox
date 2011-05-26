from setuptools import setup, find_packages
import os

name = "slapos.tool.networkcached"
version = '1.1'

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
    description = "networkcached - The networkcached is cache provider.",
    long_description=long_description,
    license = "GPLv3",
    keywords = "vifib slapos cache",
    classifiers=[
      ],
    packages = find_packages('src'),
    include_package_data = True,
    package_dir = {'':'src'},
    namespace_packages = ['slapos', 'slapos.tool'],
    install_requires = [
      'Flask', # used to create this
      'setuptools', # namespaces
    ],
    zip_safe=False,
    entry_points = """
    [console_scripts]
    networkcached = %(name)s:main
    runNetorkcacheTest = %(name)s.test:run
    """ % dict(name=name),
    )
