import json, httplib
import math
import argparse
from collections import deque
import time

appID = "kKW7oJS0nwEG4V6f3LvYooU5BQxFnH6eZ9aS31A3"
apiKey = "HEZHvUyEqV4VOV61YaEFbMywGKq7pJNlPhlQtWRt"
connection = httplib.HTTPSConnection('api.parse.com', 443)
connection.connect()

IMU_data = "./data/test5"
filterLength = 50
secondFilterLength = 70
LowerCutOff = 0.005
HigherCutOff = 0.006
FALL_THRESH_HIGH= 550
FALL_THRESH_LOW = 100
PARSE_FALL_GROUP_LIMIT = 20
dataPoint = 0
total_nots = 0
args = ""

lines_fifo = deque()
sum_data = deque()


def init():
    parser = argparse.ArgumentParser(description='input filter for IMU data')

    parser.add_argument('-i', action="store", dest="IMU_data")
    parser.add_argument('-f', action="store", dest="filterLength", type=int, default=filterLength)
    parser.add_argument('-s', action="store", dest="samplingFreq", type=float, default=filterLength)
    parser.add_argument('-l', action="store", dest="firstCutOff", type=float, default=LowerCutOff)
    parser.add_argument('-w', action="store", dest="secondCutOff", type=float, default=HigherCutOff)

    global args
    args = parser.parse_args()
    main(args)

def motionFilter(line, weights):
    global dataPoint
    dataPoint += 1
    outputSignal = 0.0
    #print "lines_fifo = %s" % lines_fifo
    list_line = line.split(',')
    print list_line
    if len(lines_fifo) >= args.filterLength:
        for sample in xrange(0, args.filterLength):
            #print "float(lines_fifo[sample]) = %f" % float(lines_fifo[sample])
            #print "weights = %f " % weights[sample]
            #print "float(lines_fifo = %f)" % float(lines_fifo[sample])
            outputSignal = outputSignal + weights[sample]*float(lines_fifo[sample])

        #print ("[{}] outputSignal = {}").format(dataPoint, outputSignal)

        sum_data.append(outputSignal)
        #print ("sum_data = {}".format(sum_data))

        if (len(sum_data) >= secondFilterLength):
            total_sum_data = 0
            for elem in sum_data:
                total_sum_data +=elem
            if total_sum_data >= FALL_THRESH_HIGH or total_sum_data <= FALL_THRESH_LOW:
                #print "fall detected"
                #print ("total_sum_data = {}".format(total_sum_data))
                global total_nots
                total_nots += 1
                # push parse notification
                if(total_nots % PARSE_FALL_GROUP_LIMIT == 0):
                    send_push()
            sum_data.popleft()

        '''
        if outputSignal >= FALL_THRESH_HIGH or outputSignal <= FALL_THRESH_LOW:
            print "fall detected"
            global total_nots
            total_nots += 1
            # push parse notification
            if(total_nots % 20 == 0):
                send_push()
        '''

        lines_fifo.popleft()
        #print "list_line = %s" % list_line
        if (len(list_line) > 2):
            lines_fifo.append(list_line[2])
    else:
        list_line = line.split(',')
        #print "list_line = %s" % list_line
        if (len(list_line) > 2):
            lines_fifo.append(list_line[2])

def main(args):
    weights = []
    M = args.filterLength - 1
    #print "M = %d" % M
    M_PI = math.pi
    ft1 = args.firstCutOff / args.samplingFreq
    ft2 = args.secondCutOff / args.samplingFreq

    for sample in xrange(0, args.filterLength):
        if (sample != M / 2):
            weights.insert(sample, ((math.sin(2*M_PI*ft2*(sample-M/2))/(M_PI*(sample-M/2)))-(math.sin(2*M_PI*ft1*(sample-M/2))/(M_PI*(sample-M/2)))) * (0.54 - 0.46 * math.cos(2*M_PI*sample/M)))
    else:
        weights.insert(sample, (2*(ft2-ft1)) * (0.54 - 0.46 * math.cos(2*M_PI*sample/M)))

    weight = 0
    #for weight in xrange(0, len(weights)):
        #print ("[{}] = {}".format(weight, weights[weight]))
    fd = open(IMU_data, 'r')


    while (1):
        outputSignal = 0.0
        line = fd.readline()
        if line:
            motionFilter(line, weights)
        else:
            print "waiting for more data.."
            time.sleep(1)

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

if __name__ == "__main__":
    init()
