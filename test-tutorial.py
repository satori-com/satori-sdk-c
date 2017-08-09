#!/usr/bin/env python
# encoding: utf-8

import json
import os
import re
import signal
import shutil
import subprocess
import tempfile
import threading
import time


TUTORIALS = {
    # key is directory name, value is an iterable of regular expressions that must
    # each match against the command's output
    "simple": {"Animal is received", "Animal is published"},
    "libuv":  {"Animal is received", "Animal with ID [0-9]+ is published"},
    "boost_asio": {"Sent out an animal", "Received animal"},
}


class TemporaryDirectory(object):
    def __init__(self):
        self._d = tempfile.mkdtemp()

    def remove(self):
        try:
            shutil.rmtree(self._d)
        except OSError:
            pass

    def __del__(self):
        self.remove()

    def __enter__(self):
        return self._d

    def __exit__(self, type, value, tb):
        self.remove()


def main():
    start_dir = os.getcwd()
    with TemporaryDirectory() as build_dir:
        os.chdir(build_dir)
        print "Building in", build_dir
        subprocess.check_call(["cmake", "-DTUTORIALS=1", start_dir])
        subprocess.check_call(["cmake", "--build", "."])
        print

        for tutorial in TUTORIALS.items():
            test(*tutorial)

def kill_after(process, seconds=10):
    time.sleep(seconds)
    try:
        if process.poll() is None:
            process.terminate()
    except:
        pass

def test(tutorial_name, test_strings):
    print "Testing if tutorial %s works" % tutorial_name

    binary_name = './tutorial/%(n)s/%(n)s_tutorial' % {"n": tutorial_name}

    if not os.path.isfile(binary_name):
        print " Executable not found. Skipping tutorial."
        print
        return

    p = subprocess.Popen([binary_name],
        stdout=subprocess.PIPE,
        bufsize=1)

    kill_thread = threading.Thread(target=kill_after, args=(p, 10))
    kill_thread.daemon = True
    kill_thread.start()

    out, err = p.communicate()

    # Should either have terminated on its own or due to us terminating the
    # process
    assert p.returncode in (-signal.SIGTERM, 0)

    for test_string in test_strings:
        if not re.search(test_string, out):
            print "Test string '%s' did not match against output:\n%s" % (test_string, out)
            raise AssertionError()

    print "Tutorial %s seems to be working fine" % tutorial_name
    print

if __name__ == '__main__':
    main()
