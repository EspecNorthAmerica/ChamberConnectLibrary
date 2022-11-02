'''setup script for this module'''

from setuptools import setup

def readme():
    '''pull iin the readme file for the long description'''
    with open('README.md') as rfile:
        return rfile.read()

setup(
    name='chamberconnectlibrary',
    version='3.6',
    description='A library for interfacing with Espec North America chambers',
    long_description=readme(),
    url='https://github.com/EspecNorthAmerica/ChamberConnectLibrary',
    author='Espec North America',
    author_email='pnong-laolam@espec.com',
    license='MIT',
    packages=['chamberconnectlibrary'],
    install_requires=['pyserial'],
    zip_safe=False,
    keywords='Espec P300 SCP220 F4T F4',
    include_package_data=True,
    scripts=['bin/f4t_controller.py','bin/example.py'],

    classicifiers=[
        'Programming Language :: Python :: 3.6.8',
        'Programming Language :: Python :: 3.7.3',
        'Programming Language :: Python :: 3.9.3',
    ]
)
