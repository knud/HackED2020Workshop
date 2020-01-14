#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
from pprint import pprint
from bluepy import btle
from bluepy.btle import Scanner, DefaultDelegate, Peripheral, UUID, BTLEException
from time import sleep
from Adafruit_IO import Client, RequestError
import re
import os
from os import system

nanoConnected = False

#----------------------------------------------------------------------------
# BLE stuff
#----------------------------------------------------------------------------

# create a delegate class to receive the BLE broadcast packets
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    # when this python script discovers a BLE broadcast packet, print a message with the device's MAC address
    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            print ( "Discovered device %s" % dev.addr )
        elif isNewData:
            print ( "Received new data from %s" % dev.addr )
           
 
class ReceptionDelegate(DefaultDelegate):
    
    receiving = False
    recCount = 0
    recStr = ""
        
    def __init__(self):
        DefaultDelegate.__init__(self)
        # ... initialise here
#        self.recCount = 0
#        self.recStr = ""
#        self.message = False

    def handleNotification(self, cHandle, data):
        if 'dataAvailable' in data:
            self.receiving = True
            self.recCount = 0
            self.recStr = ""
            msg, lenStr = data.split(':',1)
            self.recCount = int(lenStr)
#            print("%d chars available" % self.recCount)
        else:
#            print(data)
#            print("remaining chars %d" % self.recCount)
            if self.recCount > 0:
                self.recCount = self.recCount - len(data)
                self.recStr = self.recStr + data
#                print("recCount = %d" % self.recCount)
                if self.recCount <= 0:
                    process_response(self.recStr)
                    self.receiving = False
                    
    def isReceiving(self):
        return self.receiving
        
def enable_notify(blePeripheral, characteristic):
    setup_data = b"\x01\x00"
#    notify = blePeripheral.getCharacteristics(uuid=chara_uuid)[0]
#    notify_handle = notify.getHandle() + 1
    notify_handle = characteristic.getHandle() + 1
    blePeripheral.writeCharacteristic(notify_handle, setup_data, withResponse=True)

def commandToPeripheral(blePeripheral, characteristic, commandData):
    try:
        blePeripheral.writeCharacteristic(characteristic.getHandle(), commandData, withResponse=False)
    except BTLEException as e:
        print("exception"+str(e))
        nanoConnected = False



print('-----------------------------')
print('Scanning 5 s for Nano v1')
print('-----------------------------')

# create a scanner object that sends BLE broadcast packets to the ScanDelegate
scanner = Scanner().withDelegate(ScanDelegate())

# create a list of unique devices that the scanner discovered during a 10-second scan
devices = scanner.scan(5.0)

# for each device  in the list of devices

for dev in devices:
#    print ( "Device %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi) )

    # For each of the device's advertising data items, print a description of the data type and value of the data itself
    # getScanData returns a list of tupples: adtype, desc, value
    # where AD Type means "advertising data type," as defined by Bluetooth convention:
    # https://www.bluetooth.com/specifications/assigned-numbers/generic-access-profile
    # desc is a human-readable description of the data type and value is the data itself\
    found = False
    for (adtype, desc, value) in dev.getScanData():
        if value == "Nordic_PWM":
            found = True
            print ( "  %s = %s" % (desc, value) )
    if found == True:
        rb_nanov1Device = dev
        break;


if found == True:
    # print  the device's MAC address, its address type,
    # and Received Signal Strength Indication that shows how strong the signal was when the script received the broadcast.
    print('---------------------------------------------------------------------------')
    print("Found RedBear Nano v1 with address %s (%s), RSSI=%d dB" % (rb_nanov1Device.addr, rb_nanov1Device.addrType, rb_nanov1Device.rssi) )
    print('---------------------------------------------------------------------------')

    # connect to the reader
    if rb_nanov1Device.connectable:
        try:
            rb_nanov1 = Peripheral(rb_nanov1Device.addr, btle.ADDR_TYPE_RANDOM)
#            rb_nanov1.setDelegate(ReceptionDelegate())
            services = rb_nanov1.getServices()
            for s in services:
                if s.uuid == "00001523-1212-efde-1523-785feabcd123":
                    print(s.uuid)
                    characteristics = s.getCharacteristics()
                    for c in characteristics:
                        print("%s: %s" % (c.uuid, c.propertiesToString()))
                        if c.uuid == "00001524-1212-efde-1523-785feabcd123":
                            dataNotifyCharacteristic = c
                            enable_notify(rb_nanov1, dataNotifyCharacteristic)
                        if c.uuid == "00001525-1212-efde-1523-785feabcd123":
                            commandCharacteristic = c

        except BTLEException as e:
            print("exception"+str(e))
            print("Error: Unable to connect to Nano")
            
        nanoConnected = True
#             
#         commandStringOFF = b"\x00"
#         commandStringON = b"\xFF"
#         while  True:
#             if nanoConnected:
#                 commandToPeripheral(rb_nanov1, commandCharacteristic, commandStringOFF)
#                 sleep(1);
#                 commandToPeripheral(rb_nanov1, commandCharacteristic, commandStringON)
#                 sleep(1);
#             else:
#                 try:
#                     sleep(0.1)
#                     rb_nanov1.connect(rb_nanov1Device.addr, btle.ADDR_TYPE_RANDOM)
#                 except BTLEException as e:
#                     print("connecting exception"+str(e))
                    
    else:
        print ("not connectable")