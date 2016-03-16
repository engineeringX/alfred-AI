#!/usr/bin/env python

import bglib, serial, time, datetime, signal, httplib, json, sys
from multiprocessing import Pipe

appID = "kKW7oJS0nwEG4V6f3LvYooU5BQxFnH6eZ9aS31A3"
apiKey = "HEZHvUyEqV4VOV61YaEFbMywGKq7pJNlPhlQtWRt"
connection = httplib.HTTPSConnection('api.parse.com', 443)
connection.connect()

send = None
pipe = None
fall_detected = 0
#mac = "EB16450404D9"
mac = "C94B9DC414AF"

def pipe_send(pipe, data):
  pipe.send(data)

def file_write(f, data):
  f.write(','.join(['%d' % b for b in data]) + "\n")

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
  t = datetime.datetime.now()
  sender = ''.join(['%02X' % b for b in args["sender"][::-1]])
  if(sender == mac):
      it = iter(args["data"][args["data"].index(0xff)+1:])
      data_bytes = [((next(it) << 8) | x) for x in it]
      data = [(x - 65536) if (x & 0x8000) else x for x in data_bytes]
      send(pipe, data)
      fall_detected = fall_detected+1 if data[0] == 1 else 0
      if fall_detected == 1:
        send_push()
      send_data(data[2], data[3])

def ble_scanner(p):
  # Set the pipe and send function
  global pipe
  global send
  pipe = p
  if hasattr(p, 'send'):
    send = pipe_send
  else:
    send = file_write

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

def send_push():
  connection.request('POST', '/1/push', json.dumps({
      "channels": [
          "Alfred"
          ],
      "data": {
          "alert": "A fall has been detected"
          }
      }), {
          "X-Parse-Application-Id": appID,
          "X-Parse-REST-API-Key": apiKey,
          "Content-Type": "application/json"
          })
  result = json.loads(connection.getresponse().read())
  print result

def send_data(temp, bpm):
  connection.request('PUT', '/1/classes/PatientDetailObject/CqNA6XCsu2', json.dumps({
    "tmp": temp,
    "bpm": bpm,
    }), 
    {
    "X-Parse-Application-Id": appID,
    "X-Parse-REST-API-Key": apiKey,
    "Content-Type": "application/json"
  })
  result = json.loads(connection.getresponse().read())
  print result

def exit_handler(signal, frame):
  pipe.close()
  exit(0)

if __name__ == '__main__':
  if len(sys.argv) > 1:
    with open(sys.argv[1], 'r') as f:
      ble_scanner(f)
  else:
      ble_scanner(sys.stdout)
