# ChamberConnectLibrary (codename: glclib-py3) 

ESPEC Chamber Connect Library for Python 3 is offered "as is" without 
technical support, guaranttee or liability. However, the offered product here has been prepared and carefully tested by ESPEC software engineer to ensure its operability and compatibility. The library also comes with a long list of various sample programs to help ESPEC customers or the public to get started with their project.

This library for interfacing with ESPEC North America chambers supports the following controllers: 

- ESPEC GL,
- ESPEC P300,
- P300 w/ vibration, 
- SCP-220, 
- ES-102, 
- Watlow F4T and Watlow F4S/D controllers

Interfacing can be configured to use Serial RS232C or TCP/IP.

Please read the disclaimer on liability in the LICENSE document as well as in all sample programs and interfacing libraries. 

The disclaimer is also presented here in its entirety: 

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,  
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Requirements

This library has been completely tested under the following Python 3 versions: 

* Python 3.8.x
* Python 3.9.x
* Python 3.10.x
* Python 3.13.x

As of January 2026, Python 3.11 or higher is recommended and should be used, as older versions (e.g., Python 3.9) have reached their end-of-life; and Python 3.10 is nearing its end-of-life cycle. 

## Installation and Configuration

There are two ways to use this distribution: 

1. PyPI
2. src folder

HOWEVER, the PyPI package or the src distribution folder has not yet been published. 

In the meantime, the simplest way to take advantage of this free library is to clone it to your local system and checkout glclib-py3. **Note:** If you do not checkout the branch, your clone contains the master branch which is the old branch (Python 2.7); and you will encounter compability issues. Use the default clone name when cloning the repository (i.e., ChamberConnectLibrary). 

* ``git clone git@github.com:EspecNorthAmerica/ChamberConnectLibrary.git ``
* ``git checkout glclib-py3``

Navigate to the root directory to execute and test run the sample programs provided in the bin directory. 

With this clone, it is probably best to create virtualenv with specific Python 3 version created in the root directory to test and run these sample programs, provided the ``pyserial`` and ``minimalmodbus`` packages have been installed (explained below). This is to avoid any conflict with the base Python 3 already exists on your system, unless it was installed and configured specifically for this project.

### GNU/Linux 

This procedure uses the old-school PIP configuration method. Modern **uv** can be used to pull a desired Python3 version to use with this library; we, however, will not cover it here. The goal here is to provide the simplest and straight-forward option to quickly get the library working to control your chamber.

* Clone the repository
* Navigate to the cloned directory
* Checkout ``glclib-py3``
* Install python3-pip python3-virtualenv 
* Create virtualenv with: ``python3 -m venv venv``
* Activate the venv with: ``source venv/bin/activate`` 
* Update pip and run pip to install the ``serial_requirement.txt`` file for serial communication using Modbus RTU. You can install these packages (pyserial and minimalmodbus) manually using pip, if a new version is required.

### Windows 

To set up Python 3 virtualenv, we set up from the base system first. 

* Ensure Python 3.x is installed on MS Windows 10/11
* Clone the repository
* Navigate to the cloned directory
* Checkout ``glclib-py3`` 
* Create virtualenv: ``python -m virtual venv``
* Activate virtualenv: ``venv\scripts\activate`` 
* Install and update/upgrade pip: ``venv\scripts\python -m pip install --upgrade pop`` or ``pip install -U pip``
* Install required pkgs with pip: ``venv\scripts\python -m pip install -r serial_requirement.txt``. You can install these packages (pyserial and minimalmodbus) manually using pip, if a new version is required.

## Program Application 

Sample programs are included in the bin folder. Program names specify the type of controllerfor; for instance, ```f4t_runRTU.py``` is a program to control and operate ESPEC chamber with Watlow F4T via Modbus RTU communication protocol, while ``f4t_runTCP.py`` is for TCP/IP communication. However, each program can be modified to one communication protocol or the other.   

### TCP/IP Communication Protocol 

Sample programs are available as follows: 

* ```glc_runTCP.py```: Sample program to test, control and operate GL chamber. Default communication protocol is TCP/IP. Programmer may modify the protocol between TCP/IP, RS232 and RS485. However, serial communication protocol is option-dependent.  
* ```f4t_runTCP.py```: Sample program to test, control and operate ESPEC chamber with F4T controller (with Temperate-only option). Programemrs may modify this program to include other feature based on their chamber available features and options. Default communication protocol is generally TCP/IP. Serial RS232 communication is available via Modbus RTU based on purchase options. Programmers may be able to switch between TCP/IP and Serial. 
* ```f4t_runTCP_TempHumi.py```: Sample program to test, control and operate ESPEC chamber with F4T controller with Temperate and Humidity options. Default communication protocol is generally TCP/IP. Serial RS232 communication is available via Modbus RTU based on purchase options. Programmers may be able to switch between TCP/IP and Serial.
* ```p300_sample_run.py```: Sample program to test, control and operate P300 chamber. Programmer may modify communication protocol using RS232 or TCP/IP. Note: TCP/IP communication is provided by the port-forwarder of ESPEC Web Controller (purchased separately or equipped with the chamber). P300 has default serial communication protocol only with options: RS232, RS485 and GB-IP. However, only RS232 is supported in this library, unless you have an adaptor to communicate between RS485 and RS232.  Additionally, TCP/IP can still be functional if you have a NET232 adaptor to provide covnersion between TCP/IP and RS232. 
* ```p300vib_sample_run.py```: Sample program to test, control and operate P300 w/ Vibration. Programmer may modify communication protocol using RS232 or TCP/IP. Note: TCP/IP communication is provided by the port-forwarder of ESPEC Web Controller (purchased separately or equipped with the chamber). P300 has default serial communication protocol only with options: RS232, RS485 and GB-IP. However, only RS232 works with this library, unless you have an adaptor to communicate between RS485 and RS232.  Additionally, TCP/IP can still be functional if you have a NET232 adaptor to provide conversion between TCP/IP and RS232. 
* ```espec-cntlr-comm_rs232.py```: Experimental sample program with option to communicate and control ESPEC P300, P300 w/ vibration, SCP-220 and ES-102 directly via raw text commands. This is a good program to test communication between the device and the target chamber/controller through controller's native commands. The programmer may need to adjust the program to align with the exact requirements. 

### Modbus RTU Communication Protocol 

Sample programs are available as follows: 

* ```glc_runRS232.py```: Sample program via TCP/IP and serial RS232C
* ```f4t_runRTU.py```: Sample program via RTU Modbus for F4T w/ Temp
* ```f4_runRTU.py```: Sample program via RTU Modbus for F4 w/ Temp
* ```f4_test_read.py```: Sample program to test RTU modbus connection for F4; a quick and small program to test the cable as well as communication settings.  
* ```f4nf4t_sample_run.py```: Sample program with options on F4 RTU, F4T RTU and F4T TCP/IP. A connection to either F4 or F4T via RTU or TCP/IP must be established prior to selecting the option. Default baud rate for F4T is 38400 and F4 9600. It is best to select the one used by the controller.  
* ```p300_rs232-direct.py```: Sample program using a direct serial connect via RS232 to a "modified" ESPEC P300 main library (called ```p300serial.py```); this program bypasses the chamberconnectlibrary (espec.py and especinteract.py). ```p300serial.py``` is simply a modified ```p300.py``` to provide a direct connect via RS232. 
* ```espec-ctlr_rs232.py```: Sample program with option to communicate and control ESPEC P300, SCP-220 and ES-102. Vibration features w/ P300 will be reimplemented.
* ```espec-cntlr-comm_rs232.py```: Sample program with option to communicate and control ESPEC P300, P300 w/ vibration, SCP-220 and ES-102 directly via raw text commands. This is a good program to test communication between the device and the target chamber/controller through controller's native commands. 
* ```p300vib_sample_run.py```: Sample program to test, control and operate P300 w/ Vibration. Programmer may modify communication using RS232 or TCP/IP.  
* ```p300_sample_run.py```: Sample program to test, control and operate P300. Programmer may modify communication using RS232 or TCP/IP.  
* ```glc_runTCP.py```: Sample program to test, control and operate our new GL controller. Programmer may modify communication using RS232 or TCP/IP. Default communication protocol is TCP/IP. 

These and other sample programs may be modified to include different communication interfaces for your application requirements as outlined in the [controllerinterface.md](controllerinterface.md). 

### MISC Communication Protocol

These are few experimental programs. 

* ```f4nf4t_sample_run.py```: Sample program with options on F4 RTU, F4T RTU and F4T TCP/IP. A connection to either F4 or F4T via RTU or TCP/IP must be established prior to selecting the option. Default baud rate for F4T is 38400 and F4 9600. It is best to select the one used by the controller.  
* ```p300_rs232-direct.py```: Sample program using a direct serial connect via RS232 to a "modified" ESPEC P300 main library (called ```p300serial.py```); this program bypasses the chamberconnectlibrary (espec.py and especinteract.py). ```p300serial.py``` is simply a modified ```p300.py``` to provide a direct connect via RS232. 
* ```espec-ctlr_rs232.py```: Sample program with option to communicate and control ESPEC P300, SCP-220 and ES-102. Vibration features w/ P300 will be reimplemented.

## Executing Sample Programs  

### MS Windows

To test the above program, navigate to first-level ChamberConnectLibrary directory and execute the program as follows:

```cd \path\to\chamberconnectlibrary```

start venv:

```venv\scripts\activate```

```run a specific programm:``

```venv\scripts\python bin\f4t_runTCP.py``` 

or 

```venv\scripts\python bin\f4t_runRTU.py```

### GNU/Linux

To test the above program, navigate to first-level ChamberConnectLibrary (root) directory and execute the program as follows:

```sudo python3 bin/f4t_runTCP.py```

or 

```su -c 'python3 bin/f4t_runTCP.py'```

Accessing TCP/IP or RTU modbus port requires a root privilege in GNU/Linux. The ```sudo``` may be used on a GNU/Linux system for a regular user with sudoer privilege; or, ```su -c``` may be used on a system with regular user to execute the program as root.

A virtualenv is a viable option, again, since all the necessary modules or libraries can be installed and used without interfering with the main setup. 
Examples to run the sample programs: 

```sudo venv/bin/python bin/f4nf4t_sample_run.py```

```sudo venv/bin/python bin/p300vib_sample_run.py```

```sudo venv/bin/python bin/p300_sample_run.py```

A ```sudo``` prefix in the command is to ensure the privilege to access and use USB port. 
In the venv, double check that ```python``` symbolic links to ```python3```. Otherwise, explicitely apply:   

```sudo venv/bin/python3 bin/p300_sample_run.py```

Questions on how to use the library, contact Paul Nong-Laolam at ESPEC <pnong-laolam@espec.com>. Limited support will be given. 

## Documentation

For further documentation on the different communication interface and controller type options, see [controllerinterface.md](controllerinterface.md)
