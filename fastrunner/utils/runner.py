#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil
import sys
import os
import subprocess
import tempfile
from fastrunner.utils import loader
from fastrunner import models

EXEC = sys.executable

if 'uwsgi' in EXEC:
    EXEC = "/usr/bin/python3"


class DebugCode(object):

    def __init__(self, code, project, filename):
        self.__code = code
        self.resp = None
        self.temp = tempfile.mkdtemp(prefix='FasterRunner')
        self.project = project
        self.filename = filename

    def run(self):
        """ dumps file.py and run
        """
        try:
            files = models.Pycode.objects.filter(project__id=self.project)
            for file in files:
                file_path = os.path.join(self.temp, file.name)
                loader.FileLoader.dump_python_file(file_path, file.code)

            run_file_path = os.path.join(self.temp, self.filename)
            # loader.FileLoader.dump_python_file(file_path, self.__code)
            self.resp = decode(subprocess.check_output([EXEC, run_file_path], stderr=subprocess.STDOUT, timeout=60))

        except subprocess.CalledProcessError as e:
            self.resp = decode(e.output)

        except subprocess.TimeoutExpired:
            self.resp = 'RunnerTimeOut'

        shutil.rmtree(self.temp)


def decode(s):
    try:
        return s.decode('utf-8')

    except UnicodeDecodeError:
        return s.decode('gbk')
