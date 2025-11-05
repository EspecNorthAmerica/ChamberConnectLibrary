'''setup script for this module'''

from setuptools import setup

def readme():
    '''pull in the readme file for the long description'''
    with open('README.md') as rfile:
        return rfile.read()

setup(
    name='chamberconnectlibrary',       # should match the pkg folder
    version='3.0.0',                    # important for future updates
    description='A library for interfacing with Espec North America chambers via Python 3.6+',
    long_description=readme(),          # loads the README.md file 
    url='https://github.com/EspecNorthAmerica/ChamberConnectLibrary',
    author='Paul Nong-Laolam', 
    author_email='pnong-laolam@espec.com',
    license='MIT',
    packages=['chamberconnectlibrary'],
    install_requires=['pyserial', 'minimalmodbus'],
    zip_safe=False,
    keywords='Espec P300 P300vib SCP220 ES102 F4T F4',
    include_package_data=True,
    scripts=[
        'bin/f4t_runTCP.py', 
        'bin/f4_runRTU.py',
        'bin/f4t_runTCP_TempHumi.py',
        'bin/f4t_runTCP_PTCON_cascade.py',
        'bin/p300_sample_run.py',
        'bin/p300vib_sample_run.py'
        'bin/sco220_sample_run.py'
        ],

    classifiers=[
        'Programming Language :: Python :: 3.7.3',
        'Programming Language :: Python :: 3.8.10',
        'Programming Language :: Python :: 3.9.3',
        'Programming Language :: Python :: 3.10.12',
    ],
)
