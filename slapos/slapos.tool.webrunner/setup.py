from setuptools import setup, find_packages

name = "slapos.tool.runner"
version = "1.0.dev-0"

def read(name):
  return open(name).read()

long_description=( read('README.txt')
                   + '\n' +
                   read('CHANGES.txt')
                 )
setup(
    name=name,
    version=version,
    description="Web based runner for SlapOS",
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Programming Language :: Python",
    ],
    packages = find_packages('src'),
    include_package_data = True,
    package_dir = {'':'src'},
    namespace_packages = ['slapos', 'slapos.tool'],
    install_requires=[
      'Flask', # based on Flask
      'setuptools', # namespaces
      'slapos.slap', # runner is using this to communicate with proxy
      'xml_marshaller', # needed to dump information
    ],
    entry_points = """
    [console_scripts]
    slaprunner = %(name)s:run
    """ % dict(name=name),
)
