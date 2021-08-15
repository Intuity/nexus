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

import logging

import simpy

class Base:
    """ Base object for simulation """

    ID  = {}
    LOG = None

    def __init__(self, env):
        """ Initialise the Base object.

        Args:
            env: SimPy Environment
        """
        assert isinstance(env, simpy.Environment) or env == None
        self.id      = Base.issue_id(self)
        self.env     = env
        self.name    = f"{type(self).__name__}[{self.id}]"
        self.created = self.env.now if self.env else 0

    @classmethod
    def issue_id(cls, inst):
        type_str = type(inst).__name__
        if type_str not in Base.ID: Base.ID[type_str] = 0
        issued = Base.ID[type_str]
        Base.ID[type_str] = issued + 1
        return issued

    @classmethod
    def setup_log(cls, env, verbosity, log_path=None):
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
            fh = logging.FileHandler(log_path, "w")
            Base.LOG.addHandler(fh)
            fh.setFormatter(formatter)

    # Logging aliases
    def error(self, msg):
        if Base.LOG: return Base.LOG.error(msg)
        else       : print(f"ERROR: {msg}")

    def warn (self, msg):
        if Base.LOG: return Base.LOG.warning(msg)
        else       : print(f"WARN: {msg}")

    def info (self, msg):
        if Base.LOG: return Base.LOG.info(msg)
        else       : print(f"INFO: {msg}")

    def debug(self, msg):
        if Base.LOG: return Base.LOG.debug(msg)
        else       : print(f"DEBUG: {msg}")
