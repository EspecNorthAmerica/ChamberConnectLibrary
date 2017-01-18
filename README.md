# ChamberConnectLibrary
Python library for interfacing with Espec North America chambers with P300, SCP-220 &amp; Watlow F4T controllers.

## Requirements
python 2.7.x

## Installation
```pip install chamberconnectlibrary```

## Testing

To test run chamberconnectlibrary-test.py(on windows using COM port #3, test script is located in Python2.7\Scripts directory)

P300: ```chamberconnectlibrary-test.py Espec Serial \\.\COM3 19200```

SCP-220: ```chamberconnectlibrary-test.py EspecSCP220 Serial \\.\COM3 9600```

Watlow F4T: ```chamberconnectlibrary-test.py WatlowF4T RTU \\.\COM3 38400```

## Documentation
Documentation to be added to github wiki as time permits.
For now see [controllerinterface.py](https://github.com/EspecNorthAmerica/ChamberConnectLibrary/blob/master/ChamberConnectLibrary/controllerinterface.py)