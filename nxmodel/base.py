# Copyright 2021, Peter Birch, mailto:peter@lightlogic.co.uk
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from enum import IntEnum
import logging

import simpy

class Verbosity(IntEnum):
    ERROR = 0
    WARN  = 1
    INFO  = 2
    DEBUG = 3

class Base:
    """ Base object for simulation """

    ID        = {}
    VERBOSITY = Verbosity.INFO
    LOG       = None

    def __init__(self, env):
        """ Initialise the Base object.

        Args:
            env: SimPy Environment
        """
        assert isinstance(env, simpy.Environment)
        self.id      = Base.issue_id(self)
        self.env     = env
        self.name    = f"{type(self).__name__}[{self.id}]"
        self.created = self.env.now

    @classmethod
    def issue_id(cls, inst):
        type_str = type(inst).__name__
        if type_str not in Base.ID: Base.ID[type_str] = 0
        Base.ID[type_str] = (issued := Base.ID[type_str]) + 1
        return issued

    @classmethod
    def setup_log(cls, env, verbosity, log_path):
        assert isinstance(env, simpy.Environment)
        class LogFilter(logging.Filter):
            def filter(self, record):
                record.sim_time = env.now
                return True
        Base.LOG  = logging.getLogger("nxmodel")
        stream    = logging.StreamHandler()
        formatter = logging.Formatter("%(sim_time)08i nxmodel : %(message)s")
        stream.setFormatter(formatter)
        Base.LOG.addFilter(LogFilter())
        Base.LOG.setLevel(verbosity)
        Base.LOG.addHandler(stream)
        if log_path:
            Base.LOG.addHandler(fh := logging.FileHandler(log_path, "w"))
            fh.setFormatter(formatter)

    # Logging aliases
    def error(self, msg): return Base.LOG.error(msg)
    def warn (self, msg): return Base.LOG.warning(msg)
    def info (self, msg): return Base.LOG.info(msg)
    def debug(self, msg): return Base.LOG.debug(msg)
