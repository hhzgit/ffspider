# -*- coding: UTF-8 -*-
import os
import sys
import signal


def kill(pid):

    try:
        a = os.kill(pid, signal.SIGKILL)
        # a = os.kill(pid, signal.9) #　与上等效
        print '已杀死pid为%s的进程,　返回值是:%s' % (pid, a)
    except OSError, e:
        print '没有如此进程!!!'

if __name__ == '__main__':
    os.popen('taskkill /pid 5336 -f')