from setuptools import setup, find_packages
import os

name = "slapos.tool.cloudmgr"
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
    author = 'Lukasz Nowak',
    author_email = 'luke@nexedi.com',
    description = "cloudmgr -- tools to manage clouds by using libcloud",
    long_description=long_description,
    license = "GPL",
    keywords = "cloud libcloud manager",
    classifiers=[
      ],
    packages = find_packages('src'),
    include_package_data = True,
    package_dir = {'':'src'},
    namespace_packages = [ 'slapos', 'slapos.tool' ],
    install_requires = [
      'setuptools', # namespaces
      'paramiko',
      'apache_libcloud>=0.4.0', #False name, 0.4.0 is not yet released on pypi
                                # and erpypi does not support names with "-"
    ],
    url='https://svn.erp5.org/repos/vifib/trunk/utils/slapos.tool.cloudmgr/',
    zip_safe=True,
    entry_points = """
    [console_scripts]
    cloudmgr=slapos.tool.cloudmgr.cloudmgr:main
    cloudlist=slapos.tool.cloudmgr.list:main
    clouddestroy=slapos.tool.cloudmgr.destroy:main
    cloudstart=slapos.tool.cloudmgr.start:main
    cloudstop=slapos.tool.cloudmgr.stop:main
    cloudgetprivatekey=slapos.tool.cloudmgr.getprivatekey:main
    cloudgetpubliciplist=slapos.tool.cloudmgr.getpubliciplist:main
    """ % dict(name=name),
    )
