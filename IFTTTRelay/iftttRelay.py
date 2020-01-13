#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

from pprint import pprint

from PyInquirer import style_from_dict, Token, prompt, Separator, Validator, ValidationError

from examples import custom_style_2

from bluepy.btle import Scanner, DefaultDelegate, Peripheral, UUID, BTLEException

from time import sleep

import re

from os import system

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
        
def enable_notify(bleReader, characteristic):
    setup_data = b"\x01\x00"
#    notify = bleReader.getCharacteristics(uuid=chara_uuid)[0]
#    notify_handle = notify.getHandle() + 1
    notify_handle = characteristic.getHandle() + 1
    bleReader.writeCharacteristic(notify_handle, setup_data, withResponse=True)

def commandToReader(bleReader, characteristic, commandData):
    try:
        bleReader.writeCharacteristic(characteristic.getHandle(), commandData, withResponse=False)
    except:
        print("exception")

def get_delivery_options(answers):
    options = ['bike', 'car', 'truck']
    if answers['size'] == 'jumbo':
        options.append('helicopter')
    return options

level01_questions = [
    {
        'type': 'list',
        'name': 'level01',
        'message': 'What do you want to do?',
        'choices': [
            'Set Frequency',
            'Set Antenna',
            'Set Tx power',
            'Continuous Transmit',
            'Set tuning capacitors to default',
            'Measure reflected power',
            'Minimize reflected power',
            'Quit',
        ]
    },
]

class frequencyIndexValidator(Validator):
    def validate(self, document):
        freqInd = int(document.text)
        ok = (freqInd >= 0) and (freqInd < 50)
        if not ok:
            raise ValidationError(
                message='Please enter a valid index in [0,49]',
                cursor_position=len(document.text))
            
class antennaIndexValidator(Validator):
    def validate(self, document):
        antInd = int(document.text)
        ok = (antInd >= 0) and (antInd < 7)
        if not ok:
            raise ValidationError(
                message='Please enter a valid antenna number in [0,6]',
                cursor_position=len(document.text))
            
class contTXValidator(Validator):
    def validate(self, document):
        duration = int(document.text)
        ok = (duration >= 0) and (duration <= 120)
        if not ok:
            raise ValidationError(
                message='Please enter a valid duration in [0,120]',
                cursor_position=len(document.text))
            
class digitalCapValidator(Validator):
    def validate(self, document):
        capacitor = int(document.text)
        ok = (capacitor >= 0) and (capacitor <= 31)
        if not ok:
            raise ValidationError(
                message='Please enter a valid capcitor setting in [0,31]',
                cursor_position=len(document.text))
            
set_frequency_questions = [
    {
        'type': 'input',
        'name': 'setFrequency',
        'message': 'Set the 500 kHz channel index [0,49]',
        'validate': frequencyIndexValidator
    },
]

set_antenna_questions = [
    {
        'type': 'input',
        'name': 'setAntenna',
        'message': 'Select the antenna [1,6 : 0 = off]',
        'validate': antennaIndexValidator
    },
]

set_power_questions = [
    {
        'type': 'list',
        'name': 'setPower',
        'message': 'Choose the power level',
        'choices': [
            'Off',
            'Minimum (G16=low  G8=low)',
            'Low     (G16=low  G8=high)',
            'Medium  (G16=high G8=low)',
            'High    (G16=high G8=high)',
        ]
    },
]

continuous_tx_questions = [
    {
        'type': 'input',
        'name': 'contTX',
        'message': 'Set the duration in seconds [0,120]',
        'validate': contTXValidator
    },
]

set_capacitor_questions = [
    {
        'type': 'input',
        'name': 'setCapacitors',
        'message': 'Select the digital capacitors setting [0,31]',
        'validate': digitalCapValidator
    },
]


continue_questions = [
    {
        'type': 'input',
        'name': 'continue',
        'message': 'Hit enter to continue...'
    },
]

currentFrequency = 902750
currentAntenna = 1
currentTxPower = 1
currentTuningCaps = 0

def set_frequency(bleReader, characteristic):
    global currentFrequency
    freqIndex = prompt(set_frequency_questions, style=custom_style_2)
    print("freq index = %s" % freqIndex['setFrequency']);
    currentFrequency = 902750 + int(freqIndex['setFrequency'])*500
    print("frequency = %d" % currentFrequency)
    commandString = b"\xE0006"+str(currentFrequency).encode('ascii')
    commandToReader(rb_nanov1, commandCharacteristic, commandString)
    if receivedCommandResponse():
        sleep(0.001)
    dummy = prompt(continue_questions, style=custom_style_2)
    clear()
    
def set_antenna(bleReader, characteristic):
    global currentAntenna
    antIndex = prompt(set_antenna_questions, style=custom_style_2)
    print("Antenna E%s selected" % antIndex['setAntenna']);
    currentAntenna = int(antIndex['setAntenna'])
    commandString = b"\xE1001"+str(currentAntenna)
    commandToReader(rb_nanov1, commandCharacteristic, commandString)
    if receivedCommandResponse():
        sleep(0.001)
    dummy = prompt(continue_questions, style=custom_style_2)
    clear()

def set_power(bleReader, characteristic):
    global currentTxPower
    powerIndex = prompt(set_power_questions, style=custom_style_2)
    print("%s power selected" % powerIndex['setPower']);
    powerSetting = powerIndex['setPower']
    if 'Off' in powerSetting:
        currentTxPower = 0
        commandString = b"\xE20010"
    if 'Minimum' in powerSetting:
        currentTxPower = 1
        commandString = b"\xE20011"
    if 'Low' in powerSetting:
        currentTxPower = 2
        commandString = b"\xE20012"
    if 'Medium' in powerSetting:
        currentTxPower = 3
        commandString = b"\xE20013"
    if 'High' in powerSetting:
        currentTxPower = 4
        commandString = b"\xE20014"
    commandToReader(rb_nanov1, commandCharacteristic, commandString)
    if receivedCommandResponse():
        sleep(0.001)
    dummy = prompt(continue_questions, style=custom_style_2)
    clear()

def continuous_tx(bleReader, characteristic):
    print("Using frequency %dkHz, antenna E%d, and %s TX power" %(currentFrequency, currentAntenna, txPowerToString(currentTxPower)))
    durationResp = prompt(continuous_tx_questions, style=custom_style_2)
    print("Transmitting for %s seconds" % durationResp['contTX']);
    dur = int(durationResp['contTX'])
    if dur < 10:
        commandString = b"\xE300300"+str(dur)
    else:
        if dur < 100:
            commandString = b"\xE30030"+str(dur)
        else:
            commandString = b"\xE3003"+str(dur)
    commandToReader(rb_nanov1, commandCharacteristic, commandString)
    if receivedCommandResponse():
        sleep(0.001)
    dummy = prompt(continue_questions, style=custom_style_2)
    clear()
    
def set_tuning_caps(bleReader, characteristic):
    global currentTuningCaps
    capIndex = prompt(set_capacitor_questions, style=custom_style_2)
    print("3 capacitors will be set to %s" % capIndex['setCapacitors']);
    currentTuningCaps = int(capIndex['setCapacitors'])
    if currentTuningCaps < 10:
        commandString = b"\xE40020"+str(currentTuningCaps)
    else:
        commandString = b"\xE4002"+str(currentTuningCaps)
    commandToReader(rb_nanov1, commandCharacteristic, commandString)
    if receivedCommandResponse():
        sleep(0.001)
    dummy = prompt(continue_questions, style=custom_style_2)
    clear()
    
def measure_refl_power(bleReader, characteristic):
    print("Using antenna E%d, and %s TX power" %(currentAntenna, txPowerToString(currentTxPower)))
    commandString = b"\xE5000"
    print("Waiting for data...This can take a while...")
    commandToReader(rb_nanov1, commandCharacteristic, commandString)
    if receivedCommandResponse():
        sleep(0.001)
    sleep(0.5)
    if receivedCommandResponse():
        sleep(0.001)
    dummy = prompt(continue_questions, style=custom_style_2)
    clear()
    
def minimize_refl_power(bleReader, characteristic):
    print("Using antenna E%d, and %s TX power" %(currentAntenna, txPowerToString(currentTxPower)))
    commandString = b"\xE6000"
    commandToReader(rb_nanov1, commandCharacteristic, commandString)
    print("Waiting for data...This can take a while...")
    if receivedCommandResponse():
        sleep(0.001)
    sleep(0.5)
    if receivedCommandResponse():
        sleep(0.001)
    dummy = prompt(continue_questions, style=custom_style_2)
    clear()
    
def receivedCommandResponse():
    # TODO should really be more robust; report timeout, etc
    while not rb_nanov1.waitForNotifications(1.0):
        print("waiting for notification")
#        sleep(2.0)
    while rb_nanov1.delegate.isReceiving():
        if not rb_nanov1.waitForNotifications(1.0):
            sleep(0.1)
    return True
    
def process_response(response):
    respParse = response.split(',')
#    print("got %d parsed parts" % len(respParse))
    if 'command_result' in respParse[0]:
        if '1' in respParse[1]:
            print("---------- SUCCESS ----------")
        else:
            print("########## FAILURE ##########")
    if ('test_measure_refl_power' in respParse[0]) or ('test_minimize_refl_power' in respParse[0]):
# 50 values for reflected power
# {"name":"test_measure_refl_power","data":"{ 3809, 3653, ..., 545}","timestamp":"20190311114159","coreid":"2f0041001147363330363431"}
        respParse = response.split('{')
        #print(respParse[2])
        respParse = respParse[2].split('}')
        reflPowerStrs = respParse[0].split(',')
        channelCount = 0
        for s in reflPowerStrs:
            print("f = %6d P = %s" %(902750+channelCount*500,s))
            channelCount = channelCount + 1
#    if 'test_minimize_refl_power' in respParse[0]:
#        print("test_minimize_refl_power")

def txPowerToString(powerIndex):
    powerStrs = {
        0 : 'Off',
        1 : 'Minimum (G16=low  G8=low)',
        2 : 'Low     (G16=low  G8=high)',
        3 : 'Medium  (G16=high G8=low)',
        4 : 'High    (G16=high G8=high)'
    }
    return powerStrs.get(powerIndex, 'Invalid power')

clear = lambda: system('clear')

print('-----------------------------')
print('Scanning 10 s for Nano v1')
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
        print ( "  %s = %s" % (desc, value) )
        if value == "Nordic_PWM":
            found = True
    if found == True:
        betaDev = dev
        break;


if found == True:
    # print  the device's MAC address, its address type,
    # and Received Signal Strength Indication that shows how strong the signal was when the script received the broadcast.
    print('---------------------------------------------------------------------------')
    print("Found RedBear Nano v1 with address %s (%s), RSSI=%d dB" % (betaDev.addr, betaDev.addrType, betaDev.rssi) )
    print('---------------------------------------------------------------------------')

    # connect to the reader
    if betaDev.connectable:
        try:
            rb_nanov1 = Peripheral(betaDev)
            rb_nanov1.setDelegate(ReceptionDelegate())
#            rb_nanov1.setDelegate(ScanDelegate)
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

        except BTLEException:
            print("Error: Unable to connect to Nanor")
            
        while  True:
            commandString = b"\x00"
            commandToReader(rb_nanov1, commandCharacteristic, commandString)
            sleep(0.5);
            commandString = b"\xFF"
            commandToReader(rb_nanov1, commandCharacteristic, commandString)
            sleep(0.5);
    else:
        print ("not connectable")

#     clear()
#     answers = prompt(level01_questions, style=custom_style_2)
#     while answers['level01'] != 'Quit':
#         if answers['level01'] == 'Set Frequency':
#             set_frequency(rb_nanov1, commandCharacteristic)
#         if answers['level01'] == 'Set Antenna':
#             set_antenna(rb_nanov1, commandCharacteristic)
#         if answers['level01'] == 'Set Tx power':
#             set_power(rb_nanov1, commandCharacteristic)
#         if answers['level01'] == 'Continuous Transmit':
#             continuous_tx(rb_nanov1, commandCharacteristic)
#         if answers['level01'] == 'Set tuning capacitors to default':
#             set_tuning_caps(rb_nanov1, commandCharacteristic)
#         if answers['level01'] == 'Measure reflected power':
#             measure_refl_power(rb_nanov1, commandCharacteristic)
#         if answers['level01'] == 'Minimize reflected power':
#             minimize_refl_power(rb_nanov1, commandCharacteristic)
#             
#        if rb_nanov1.waitForNotifications(1.0):
#            print("notification...")
#            continue
#                         
#         answers = prompt(level01_questions, style=custom_style_2)

