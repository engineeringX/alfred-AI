from multiprocessing import Process, Pipe
import ble_scanner, filterData

if __name__ == '__main__':
  conn1, conn2 = Pipe()
  p = Process(target=filterData.init, args=(conn1,))
  p.start()
  ble_scanner.scan(conn2)
  p.join()
