import threading
import queue
import time


class ThreadPool(object):
    # 线程池+任务队列
    def __init__(self, max_work_num, thread_num=4):
        self.max_thread_num = thread_num
        self.cur_num = 0
        self.work_queue = queue.Queue(max_work_num)
        self.pool = list()
        self.init_thread_pool()

    def init_thread_pool(self):
        for i in range(self.max_thread_num):
            self.pool.append(Worker(i, self.work_queue))

    def add_job(self, func, *args):
        self.work_queue.put((func, *args))

    # def add_jobs(self, jobs):
    #     for job in jobs:
    #         self.work_queue.put(job)

    def start(self):
        for thread in self.pool:
            time.sleep(1.0)
            thread.start()

    def wait_complete(self):
        for thread in self.pool:
            if thread.isAlive():
                thread.join()


class Worker(threading.Thread):

    def __init__(self, thread_id, work_queue):
        threading.Thread.__init__(self)
        self.work_queue = work_queue
        self.thread_id = thread_id

    def run(self):
        while True:
            if not self.work_queue.empty():
                self.do_job()
            else:
                break

    def do_job(self):
        func, *args = self.work_queue.get()
        func(*args)