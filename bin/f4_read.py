import minimalmodbus

 TE1007C = minimalmodbus.Instrument("COM5", 1)
 # Set baudrate
 TE1007C.serial.baudrate = 9600
 temp = TE1007C.read_register(100, 1, signed=True)
 print(temp)

