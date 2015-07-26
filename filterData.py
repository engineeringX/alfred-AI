import math
import argparse
from collections import deque

IMU_data = "../parsePi/samples.txt"
filterLength = 50
LowerCutOff = 0.02
HigherCutOff = 0.05
FALL_THRESH_HIGH= 0.3
FALL_THRESH_LOW = 0.025

lines_fifo = deque()

def init():
    parser = argparse.ArgumentParser(description='input filter for IMU data')

    parser.add_argument('-i', action="store", dest="IMU_data")
    parser.add_argument('-f', action="store", dest="filterLength", type=int, default=filterLength)
    parser.add_argument('-s', action="store", dest="samplingFreq", type=float, default=filterLength)
    parser.add_argument('-l', action="store", dest="firstCutOff", type=float, default=LowerCutOff)
    parser.add_argument('-w', action="store", dest="secondCutOff", type=float, default=HigherCutOff)

    args = parser.parse_args()
    main(args)

def main(args):
    weights = []
    M = args.filterLength
    M_PI = math.pi
    ft1 = args.firstCutOff / args.samplingFreq
    ft2 = args.secondCutOff / args.samplingFreq

    for sample in xrange(0, args.filterLength):
        if (sample != M / 2):
            weights.insert(sample, math.sin(2*M_PI*ft2*(sample-M/2)/(M_PI*(sample-M/2)-math.sin(2*M_PI*ft1*(sample-M/2))/(M_PI*(sample-M/2)))))
        else:
            weights.insert(sample, 2*(ft2-ft1))
        weights.insert(sample, weights[sample]*(0.54 - 0.46 * math.cos(2*M_PI*sample/M)))

    outputSignal = 0.0

    for line in open(IMU_data, 'r'):
	#print lines_fifo
	if len(lines_fifo) >= args.filterLength:
            for sample in xrange(0, args.filterLength):
                #print "float(lines_fifo[sample]) = %f" % float(lines_fifo[sample])
		outputSignal += weights[sample]*float(lines_fifo[sample])

	    print "outputSignal = %d" % outputSignal

            if outputSignal >= FALL_THRESH_HIGH or outputSignal <= FALL_THRESH_LOW:
                print "fall detected"
                # push parse notification

            lines_fifo.popleft()
            list_line = line.split(',')
            print "list_line = %s" % list_line
	    if (len(list_line) > 2):
		lines_fifo.append(list_line[2])
        else:
            list_line = line.split(',')
            print "list_line = %s" % list_line
	    if (len(list_line) > 2):
		lines_fifo.append(list_line[2])

if __name__ == "__main__":
    init()
