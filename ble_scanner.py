#!/usr/bin/env python

import bglib, serial, time, datetime, signal, httplib, json, sys
from time import strftime

appID = "kKW7oJS0nwEG4V6f3LvYooU5BQxFnH6eZ9aS31A3"
apiKey = "HEZHvUyEqV4VOV61YaEFbMywGKq7pJNlPhlQtWRt"
connection = httplib.HTTPSConnection('api.parse.com', 443)
connection.connect()

fall_detected = 0
abnormal_pulse = 0
abnormal_temp = 0
packet_count = 0
#mac = "EB16450404D9"
mac = "C94B9DC414AF"

# handler to notify of an API parser timeout condition
def my_timeout(sender, args):
  # might want to try the following lines to reset, though it probably
  # wouldn't work at this point if it's already timed out:
  #ble.send_command(ser, ble.ble_cmd_system_reset(0))
  #ble.check_activity(ser, 1)
  print "BGAPI parser timed out. Make sure the BLE device is in a known/idle state."

# handler to print scan responses with a timestamp
def my_ble_evt_gap_scan_response(sender, args):
  global fall_detected
  global abnormal_pulse
  global abnormal_temp
  global packet_count
  t = datetime.datetime.now()
  sender = ''.join(['%02X' % b for b in args["sender"][::-1]])
  if(sender == mac):
      it = iter(args["data"][args["data"].index(0xff)+1:])
      data_bytes = [((next(it) << 8) | x) for x in it]
      data = [(x - 65536) if (x & 0x8000) else x for x in data_bytes]
      print(','.join(['%d' % b for b in data]))

      packet_count = packet_count+1 if packet_count < 50 else 0
      fall_detected = fall_detected+1 if data[0] == 1 else 0
      abnormal_pulse = abnormal_pulse+1 if data[1] == 1 else 0
      abnormal_temp = abnormal_temp+1 if data[2] == 1 else 0

      if fall_detected == 1:
        send_push_fall(data[3], data[4])
        try:
			      send_data(data[3], data[4])
        except:
			      pass

      if abnormal_pulse == 1:
        send_push_pulse()
        try:
			      send_data(data[3], data[4])
        except:
			      pass

      if abnormal_temp == 1:
        send_push_temp()
        try:
			      send_data(data[3], data[4])
        except:
			      pass

      if packet_count == 0:
        try:
			      send_data(data[3], data[4])
        except:
			      pass

def ble_scanner():
  # Handle ctrl-c
  signal.signal(signal.SIGINT, exit_handler)

  # NOTE: CHANGE THESE TO FIT YOUR TEST SYSTEM
  port_name = "/dev/ttyACM0"
  baud_rate = 115200
  packet_mode = True

  # create BGLib object
  ble = bglib.BGLib()
  ble.packet_mode = packet_mode

  # add handler for BGAPI timeout condition (hopefully won't happen)
  ble.on_timeout += my_timeout

  # add handler for the gap_scan_response event
  ble.ble_evt_gap_scan_response += my_ble_evt_gap_scan_response

  # create serial port object and flush buffers
  ser = serial.Serial(port=port_name, baudrate=baud_rate, timeout=1)
  ser.flushInput()
  ser.flushOutput()

  # disconnect if we are connected already
  ble.send_command(ser, ble.ble_cmd_connection_disconnect(0))
  ble.check_activity(ser, 1)

  # stop advertising if we are advertising already
  ble.send_command(ser, ble.ble_cmd_gap_set_mode(0, 0))
  ble.check_activity(ser, 1)

  # stop scanning if we are scanning already
  ble.send_command(ser, ble.ble_cmd_gap_end_procedure())
  ble.check_activity(ser, 1)

  # set scan parameters
  ble.send_command(ser, ble.ble_cmd_gap_set_scan_parameters(0xC8, 0xC8, 1))
  ble.check_activity(ser, 1)

  # start scanning now
  ble.send_command(ser, ble.ble_cmd_gap_discover(1))
  ble.check_activity(ser, 1)

  while (1):
    # check for all incoming data (no timeout, non-blocking)
    ble.check_activity(ser)

    # don't burden the CPU
    #time.sleep(0.01)

def send_push_fall(temp, bpm):
    try:
        connection.request('POST', '/1/push', json.dumps({
          "channels": [
              "Alfred"
              ],
          "data": {
              "alert": "Raunaq fell :("
              }
          }), {
              "X-Parse-Application-Id": appID,
              "X-Parse-REST-API-Key": apiKey,
              "Content-Type": "application/json"
              })
        result = json.loads(connection.getresponse().read())
        send_historical_data(strftime("%Y-%m-%d_%H:%M:%S", time.localtime()), temp, bpm)
    except:
        pass
    print result

def send_push_pulse():
    try:
        connection.request('POST', '/1/push', json.dumps({
          "channels": [
              "Alfred"
              ],
          "data": {
            "alert": "Raunaq's pulse is abnormal :("
              }
          }), {
              "X-Parse-Application-Id": appID,
              "X-Parse-REST-API-Key": apiKey,
              "Content-Type": "application/json"
              })
        result = json.loads(connection.getresponse().read())
    except:
        pass
    print result

def send_push_temp():
    try:
        connection.request('POST', '/1/push', json.dumps({
          "channels": [
              "Alfred"
              ],
          "data": {
              "alert": "Raunaq's temp is abnormal"
              }
          }), {
              "X-Parse-Application-Id": appID,
              "X-Parse-REST-API-Key": apiKey,
              "Content-Type": "application/json"
              })
        result = json.loads(connection.getresponse().read())
    except:
        pass
    print result

def send_data(temp, bpm):
    try:
        connection.request('PUT', '/1/classes/PatientDetailObject/CqNA6XCsu2', json.dumps({
        "tmp": temp/32,
        "bpm": bpm,
        }),
        {
        "X-Parse-Application-Id": appID,
        "X-Parse-REST-API-Key": apiKey,
        "Content-Type": "application/json"
      })
        result = json.loads(connection.getresponse().read())
    except:
        pass
    print result

def send_historical_data(currentTime, temp, bpm):
    try:
        connection.request('POST', '/1/classes/NumFallsObject', json.dumps({
        "firstName": "Raunaq",
        "lastName": "Sawhney",
        "tmp": temp/32,
        "bpm": bpm,
        "fall_timestamp": currentTime,
        }),
        {
        "X-Parse-Application-Id": appID,
        "X-Parse-REST-API-Key": apiKey,
        "Content-Type": "application/json"
      })
        result = json.loads(connection.getresponse().read())
    except:
        pass
    print result

def exit_handler(signal, frame):
  exit(0)

if __name__ == '__main__':
  ble_scanner()
