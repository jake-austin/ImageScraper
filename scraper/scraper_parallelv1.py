import os
import multiprocessing
from multiprocessing import Process

from multiprocessing import Semaphore
import time
import sys


def task(semaphore, args):
    semaphore.acquire()
    os.system(args)
    semaphore.release()


if __name__ == "__main__":
    config = open("scraper_config.txt", 'r')
    config = config.read()
    maxProcesses = int(sys.argv[1])
    print("Max Threads: " + str(maxProcesses))
    assert maxProcesses <= multiprocessing.cpu_count()

    searches = config.split('\n')
    taskNumber = 0
    proc = []
    sema = Semaphore(maxProcesses)

    for i in range(len(searches)):
        p = Process(target=task, args=(sema, 'python scraper.py ' + str(taskNumber)))
        p.start()
        proc.append(p)
        taskNumber += 1
        time.sleep(5)

    for p in proc:
        time.sleep(10)
        p.join()
