# ChamberConnectLibrary

Python library for interfacing with ESPEC North America chambers with P300, SCP-220, Watlow F4T and Watlow F4S/D controllers. 

## Requirements

Python 3.6.8 and above is required for using this distributed library. 

This library has been completely tested under the following Python 3 versions: 

* Python 3.6.8
* Python 3.7.3
* Python 3.9.4

Such requirements were due to the use of new print function calls to shorten the source code. 

## Install

**IMPORTANT NOTE:** The PyPI package has not yet been published. 
In the meantime, if you would like to use this library, simply clone it and git checkout py3-chamberconnectlibrary, then select and execute:

```python3 bin/f4t_runTCP.py```

or 

```python3 bin/f4t_runRTU.py```

for your specific protocol. Both programs should work as intended. Any questions, contact Paul Nong-Laolam at ESPEC <pnong-laolam@espec.com> for assistance.  


There are two ways to use this distribution: 

1. Obtain the PyPI package and install it:

```pip3 install chamberconnectlibrary-3.6.8```

The version 3.6.8 actually refers to the Python 3 version number. 
The command ```pip3``` should be the Python3 pip. 
However, if the system is linked from pip to pip3, then this command should also work: 

```pip install chamberconnectlibrary-3.6.8```

To check and confirm if pip links to pip3, run: 

```pip --version``` 

and 

```pip3 --version```

Both commands should be able to run on Linux or MS Windows (CMD). 

The following commands should also work: 

For UNIX/Linux: ```python3 -m pip --version```

For MS Windows 8/10/11: ```python -m pip --version```

## Use the src Distribution

The src distribution in .tar.gz may be obtaiend and extracted to use on the existing platform. 

### For UNIX/Linux, run the following commands:

1. Extract the package: ```tar -xzvf chamberconnectlibrary-3.6.8```
2. Change directory to: chamberconnectlibrary-3.6.8 with command: ```cd chamberconnectlibrary-3.6.8```
3. Execute the program directly from this parent directory at the shell prompt with:  
   ```sudo python3 bin/f4t_runTCP.py```

### For MS Windows 8/10

1. Extract the package: ```tar -xzvf chamberconnectlibrary-3.6.8```
2. Change directory to: chamberconnectlibrary-3.6.8 with command: ```cd chamberconnectlibrary-3.6.8```
3. Copy the ```f4t_runTCP.py``` file from the bin folder into the main directory above it. 
4. Open the text terminal within MS VS code or with cmd terminal in your working directory.
5. Execute the program with this command: 
   ```python f4t_runTCP.py```

## Testing (using SRC distribution) 

A test script for Watlow F4T using TCP/IP protocol has been prepared for testing, with filename in the bin directory.

filename: f4t_runTCP.py

This sample program provides a starting point for manipulating and using our ChamberConnectLibrary in the Python 3 environment. This program can be executed in GNU/Linux or MS Windows 8/10/11 as outlined previously. 

For other controllers: 

To test run chamberconnectlibrary-test.py or f4t_sample_run.py 

P300: ```chamberconnectlibrary-test.py Espec Serial \\.\COM3 19200```

SCP-220: ```chamberconnectlibrary-test.py EspecSCP220 Serial \\.\COM3 9600```

Watlow F4T TCP: ```f4t_runTCP.py```

Watlow F4T RTU: 

```f4t_runRTU.py``` use \\.\COM# 38400 with # the COM value assigned in MS Windows 

```f4t_runRTU.py``` use /dev/ttyUSB# 38400 with # the USB value assigned and listed in GNU/Linux with ```ls -l /dev/ttyUSB*```

Watlow F4: ```chamberconnectlibrary-test.py WatlowF4 RTU \\.\COM3 19200```

## Documentation

See [controllerinterface.md](controllerinterface.md)
