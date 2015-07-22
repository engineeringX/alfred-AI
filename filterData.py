import math
import argparse

IMU_data = "/home/simar/parse/inputFolder/imu.dat"

def init():
    parser = argparse.ArgumentParser(description='input filter for IMU data')

    parser.add_argument('-i', action="store", dest="IMU_data")
    parser.add_argument('-f', action="store", dest="filterLength", type=int)
    parser.add_argument('-s', action="store", dest="samplingFreq", type=float)
    parser.add_argument('-l', action="store", dest="firstCutOff", type=float)
    parser.add_argument('-w', action="store", dest="secondCutOff", type=float)

    parser.add_argument('--input', action="store", dest="IMU_data")
    parser.add_argument('--filterLength', action="store", dest="filterLength")
    parser.add_argument('--samplingFreq', action="store", dest="samplingFreq", type=float)
    parser.add_argument('--firstCutOff', action="store", dest="firstCutOff", type=float)
    parser.add_argument('--secondCutOff', action="store", dest="secondCutOff", type=float)

    args = parser.parse_args()
    main(args)

def main(args):
    weights = []
    M = args.filterLength - 1
    M_PI = math.pi
    ft1 = args.firstCutOff / args.samplingFreq
    ft2 = args.secondCutOff / args.samplingFreq

    for sample in xrange(1, args.filterLength):
        if (sample != M / 2):
            weights.insert(sample, math.sin(2*M_PI*ft2*(sample-M/2)/(M_PI*(sample-M/2)-math.sin(2*M_PI*ft1*(sample-M/2))/(M_PI*(sample-M/2)))))
        else:
            weights.insert(sample, 2*(ft2-ft1))
        weights.insert(sample, weights[sample]*(0.54 - 0.46 * math.cos(2*M_PI*sample/M)))

    outputSignal = 0

if __name__ == "__main__":
    init()
