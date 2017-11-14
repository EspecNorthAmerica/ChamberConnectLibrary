'''setup script for this module'''

from setuptools import setup

def readme():
    '''pull iin the readme file for the long description'''
    with open('README.md') as rfile:
        return rfile.read()

setup(
    name='chamberconnectlibrary',
    version='2.1.3',
    description='A library for interfacing with Espec North America chambers',
    long_description=readme(),
    url='https://github.com/EspecNorthAmerica/ChamberConnectLibrary',
    author='Espec North America',
    author_email='mmetzler@espec.com',
    license='MIT',
    packages=['chamberconnectlibrary'],
    install_requires=['pyserial'],
    zip_safe=False,
    keywords='Espec P300 SCP220 F4T F4',
    include_package_data=True,
    scripts=['bin/chamberconnectlibrary-test.py']
)
