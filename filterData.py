import json, httplib
import math
import argparse
from collections import deque
import time
import sys
from multiprocessing import Pipe

appID = "kKW7oJS0nwEG4V6f3LvYooU5BQxFnH6eZ9aS31A3"
apiKey = "HEZHvUyEqV4VOV61YaEFbMywGKq7pJNlPhlQtWRt"
connection = httplib.HTTPSConnection('api.parse.com', 443)
connection.connect()

fd = None 
filterLength = 50
LowerCutOff = 0.02
HigherCutOff = 0.05
FALL_THRESH_HIGH= 0.03
FALL_THRESH_LOW = 0.025
total_nots = 0

lines_fifo = deque()

def pipe_recv(pipe):
  return pipe.recv()

def file_readline(f):
  return f.readline()

def init(p):
    fd = p
    if hasattr(p, 'recv'):
      recv = pipe_recv
    else:
      recv = file_readline

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
  M = args.filterLength - 1
  #print "M = %d" % M
  M_PI = math.pi
  ft1 = args.firstCutOff / args.samplingFreq
  ft2 = args.secondCutOff / args.samplingFreq

  for sample in xrange(0, args.filterLength):
    if (sample != M / 2):
        weights.insert(sample, (math.sin(2*M_PI*ft2*(sample-M/2))/(M_PI*(sample-M/2))-math.sin(2*M_PI*ft1*(sample-M/2))/(M_PI*(sample-M/2))) * (0.54 - 0.46 * math.cos(2*M_PI*sample/M)))
    else:
        weights.insert(sample, (2*(ft2-ft1)) * (0.54 - 0.46 * math.cos(2*M_PI*sample/M)))

  print "weights = %s" % weights

  while (1):
    outputSignal = 0.0
    data = recv(fd)
	
    #print "lines_fifo = %s" % lines_fifo
	  if len(lines_fifo) >= args.filterLength:
	    for sample in xrange(0, args.filterLength):
	  	  #print "float(lines_fifo[sample]) = %f" % float(lines_fifo[sample])
	  	  #print "weights = %f " % weights[sample]
	  	  #print "float(lines_fifo = %f)" % float(lines_fifo[sample])
	  	  outputSignal = outputSignal + weights[sample]*float(lines_fifo[sample])

	    print "outputSignal = %f" % outputSignal

	    if outputSignal >= FALL_THRESH_HIGH or outputSignal <= FALL_THRESH_LOW:
	  	  print "fall detected"
	  	  global total_nots
	  	  total_nots += 1
	  	
      # push parse notification
	  	if(total_nots % 50 == 0):
	  		send_push()

	    lines_fifo.popleft()
	    #print "data = %s" % data
	    
      if (len(data) > 2):
	  	  lines_fifo.append(data[2])
	  else:
	      #print "data = %s" % data
	      if (len(data) > 2):
		      lines_fifo.append(data[2])

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
  if len(sys.argv) > 1:
    init(sys.argv[1])
  else:
    init(sys.stdout)
