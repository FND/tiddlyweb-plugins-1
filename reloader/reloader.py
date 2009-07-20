
import os
import sys

def init(config):
    install()
    exit_code = 3
    while exit_code = 3:
        args = [sys.executable] + sys.argv
        new_environ = os.environ.copy()
        exit_code = os.spawnve(os.P_WAIT, sys.executable, args, new_environ)
        if exit_code != 3: sys.exit(exit_code)

        if os.environ.get("RUN_MAIN") == "true":
            
            thread.start_new_thread(main_func, ())

            try:
                reloader_thread()
            except KeyboardInterrupt:
                pass
        else:
            try:
                sys.exit(restart_with_reloader())
            except KeyboardInterrupt:
                _cputil.getSpecialFunction('_cpLogMessage')("<Ctrl-C> hit: shutting down", "HTTP")

# What follows is borrowed from Paste, with modifications.

# (c) 2005 Ian Bicking and contributors; written for Paste (http://pythonpaste.org)
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
"""
A file monitor and server restarter.

Use this like:

..code-block:: Python

    import reloader
    reloader.install()

Then make sure your server is installed with a shell script like::

    err=3
    while test "$err" -eq 3 ; do
        python server.py
        err="$?"
    done

or is run from this .bat file (if you use Windows)::

    @echo off
    :repeat
        python server.py
    if %errorlevel% == 3 goto repeat

or run a monitoring process in Python (``paster serve --reload`` does
this).  

Use the ``watch_file(filename)`` function to cause a reload/restart for
other other non-Python files (e.g., configuration files).  If you have
a dynamic set of files that grows over time you can use something like::

    def watch_config_files():
        return CONFIG_FILE_CACHE.keys()
    paste.reloader.add_file_callback(watch_config_files)

Then every time the reloader polls files it will call
``watch_config_files`` and check all the filenames it returns.
"""

import time
import threading
import traceback

def install(poll_interval=1):
    """
    Install the reloading monitor.

    On some platforms server threads may not terminate when the main
    thread does, causing ports to remain open/locked.  The
    ``raise_keyboard_interrupt`` option creates a unignorable signal
    which causes the whole application to shut-down (rudely).
    """
    mon = Monitor(poll_interval=poll_interval)
    t = threading.Thread(target=mon.periodic_reload)
    t.setDaemon(True)
    t.start()

class Monitor(object):

    instances = []
    global_extra_files = []
    global_file_callbacks = []

    def __init__(self, poll_interval):
        self.module_mtimes = {}
        self.keep_running = True
        self.poll_interval = poll_interval
        self.extra_files = list(self.global_extra_files)
        self.instances.append(self)
        self.file_callbacks = list(self.global_file_callbacks)

    def periodic_reload(self):
        while True:
            if not self.check_reload():
                # use os._exit() here and not sys.exit() since within a
                # thread sys.exit() just closes the given thread and
                # won't kill the process; note os._exit does not call
                # any atexit callbacks, nor does it do finally blocks,
                # flush open files, etc.  In otherwords, it is rude.
                sys.exit(3)
                break
            time.sleep(self.poll_interval)

    def check_reload(self):
        filenames = list(self.extra_files)
        for file_callback in self.file_callbacks:
            try:
                filenames.extend(file_callback())
            except:
                print >> sys.stderr, "Error calling paste.reloader callback %r:" % file_callback
                traceback.print_exc()
        for module in sys.modules.values():
            try:
                filename = module.__file__
            except (AttributeError, ImportError), exc:
                continue
            if filename is not None:
                filenames.append(filename)
        for filename in filenames:
            try:
                stat = os.stat(filename)
                if stat:
                    mtime = stat.st_mtime
                else:
                    mtime = 0
            except (OSError, IOError):
                continue
            if filename.endswith('.pyc') and os.path.exists(filename[:-1]):
                mtime = max(os.stat(filename[:-1]).st_mtime, mtime)
            elif filename.endswith('$py.class') and \
                    os.path.exists(filename[:-9] + '.py'):
                mtime = max(os.stat(filename[:-9] + '.py').st_mtime, mtime)
            if not self.module_mtimes.has_key(filename):
                self.module_mtimes[filename] = mtime
            elif self.module_mtimes[filename] < mtime:
                print >> sys.stderr, (
                    "%s changed; reloading..." % filename)
                return False
        return True

