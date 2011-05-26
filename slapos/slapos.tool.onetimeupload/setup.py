from setuptools import setup, find_packages
import os

name = "slapos.tool.onetimeupload"
version = '0.0.2'

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
    description = "onetimeupload -- tools to upload a file",
    long_description=long_description,
    license = "GPLv3",
    keywords = "upload web",
    classifiers=[
        "Programming Language :: Python",
      ],
    packages = find_packages('src'),
    include_package_data = True,
    package_dir = {'':'src'},
    namespace_packages = [ 'slapos', 'slapos.tool' ],
    install_requires = [
      'setuptools', # namespaces
      'Flask',
    ],
    url='https://svn.erp5.org/repos/vifib/trunk/utils/slapos.tool.onetimeupload/',
    zip_safe=False,
    entry_points = """
    [console_scripts]
    onetimeupload = slapos.tool.onetimeupload:main
    """,
    )

