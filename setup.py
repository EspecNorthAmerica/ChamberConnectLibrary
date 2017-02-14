from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='chamberconnectlibrary',
      version='1.1.3',
      description='A library for interfacing with Espec North America chambers',
      long_description=readme(),
      url='https://github.com/EspecNorthAmerica/ChamberConnectLibrary',
      author='Espec North America',
      author_email='mmetzler@espec.com',
      license='MIT',
      packages=['chamberconnectlibrary'],
      install_requires=['pyserial'],
      zip_safe=False,
      keywords='Espec P300 SCP220 F4T',
      include_package_data=True,
      scripts=['bin/chamberconnectlibrary-test.py'])