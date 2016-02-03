#!/usr/bin/env python

import bglib, serial, time, datetime, signal, sys

f = open(sys.argv[1], 'w')
packet_count = 0

# handler to notify of an API parser timeout condition
def my_timeout(sender, args):
    # might want to try the following lines to reset, though it probably
    # wouldn't work at this point if it's already timed out:
    #ble.send_command(ser, ble.ble_cmd_system_reset(0))
    #ble.check_activity(ser, 1)
    print "BGAPI parser timed out. Make sure the BLE device is in a known/idle state."

# handler to print scan responses with a timestamp
def my_ble_evt_gap_scan_response(sender, args):
    t = datetime.datetime.now()
    sender = ''.join(['%02X' % b for b in args["sender"][::-1]])
    if(sender == "EB16450404D9"):
        it = iter(args["data"][args["data"].index(0xff)+1:])
        data_bytes = [((next(it) << 8) | x) for x in it]
        data = [(x - 65536) if (x & 0x8000) else x for x in data_bytes]
        #disp_list = []
        #disp_list.append("%ld.%03ld" % (time.mktime(t.timetuple()), t.microsecond/1000))
        #disp_list.append("%d" % args["rssi"])
        #disp_list.append("%d" % args["packet_type"])
        #disp_list.append("%s" % sender)
        #disp_list.append("%d" % args["address_type"])
        #disp_list.append("%d" % args["bond"])
        #disp_list.append("%s" % ','.join(['%d' % b for b in data]))
        f.write(','.join(['%d' % b for b in data]) + "\n")
        global packet_count
        packet_count += 1
        if(packet_count >= 1500):
            exit_handler(0, 0)

def main():
    # Handle ctrl-c
    signal.signal(signal.SIGINT, exit_handler)

    # NOTE: CHANGE THESE TO FIT YOUR TEST SYSTEM
    port_name = "/dev/cu.usbmodem1"
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

def exit_handler(signal, frame):
    f.close()
    exit(0)

if __name__ == '__main__':
    main()
