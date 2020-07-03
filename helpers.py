#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""  """

import os
import subprocess
import re
import datetime
import time
import json
import pickle
from collections import deque


def kill_firefox():
    process = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
    output, error = process.communicate()
    for line in output.splitlines():
        if "firefox" in str(line):
            pid = int(line.split(None, 1)[0])
            os.kill(pid, 9)
