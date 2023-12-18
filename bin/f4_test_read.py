import minimalmodbus
"""
A simple procedure to perform communication test with the BTZ133 F4 controller

the following four lines set communication RS232 via COMM4 on MS Windows
sets baud rate at 19200 with address 1 (default settings) 

program reads Temp value fro mthe controller stored at a register 100. 
"""

# comm port selected from PC selection 
BTZ133 = minimalmodbus.Instrument("COM4", 1)

# Set baudrate
BTZ133.serial.baudrate = 19200

# set readTemp cmd 
temp = BTZ133.read_register(100, 1, signed=True)
print(temp)