from multiprocessing import Process, Pipe
import ble_scanner, filterData2

if __name__ == '__main__':
  conn1, conn2 = Pipe()
  p = Process(target=filterData2.init, args=(conn1,))
  p.start()
  ble_scanner.ble_scanner(conn2)
  p.join()
