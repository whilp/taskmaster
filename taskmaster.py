import functools
import logging
import optparse
import os
import signal
import stat
import subprocess
import sys
import time

try:
    NullHandler = logging.NullHandler
except AttributeError:
    class NullHandler(logging.Handler):
        def emit(self, record): pass

log = logging.getLogger("taskmaster")
log.addHandler(NullHandler())

def targetrange(value):
    idx = value.find("-")
    if idx < 0 or value.startswith('"'):
        return [value.strip('"')]

def groups(stream, default=None, data=None):
    if data is None:
        data = {}
    group = None
    for line in stream:
        line = line.strip()
        if not line:
            group = None
            continue
        elif line.startswith("["):
            group = line.strip("[]")
            continue

        ops = {
            "-": "difference_update",
            "+": "update",
        }
        ongroup = ops.get(line[0], False) and True
        method = ops.get(line[0], "update")
        value = line.strip(''.join(ops))

        if value not in data:
            if ongroup and method == "update":
                continue
            value = targetrange(value)
        else:
            value = data[value]

        groups = [group, default]
        [getattr(data.setdefault(g, set()), method)(value)
                for g in groups if g is not None]

    return data

def ncpu_bsd():
    stdout = subprocess.Popen(["sysctl", "-n", "hw.ncpufound"],
        stdout=subprocess.PIPE).communicate()[0].strip()
    if stdout:
        return int(stdout.strip())

def ncpu_linux():
    ncpu = 0
    for line in open("/proc/cpuinfo", 'r'):
        if line.startswith("processor"):
            ncpu += 1
    if ncpu > 0:
        return ncpu
    
ncpuos = {
    "openbsd4": ncpu_bsd,
    "linux2": ncpu_linux,
}

def ncpu():
    getter = ncpuos.get(sys.platform, None)
    ncpu = None
    if getter is not None:
        ncpu = getter()
    if ncpu is None:
        ncpu = 1

    return ncpu

def status(procs):
    running, succeeded, failed = [], [], []
    for proc in procs:
        poll = proc.poll()
        target = failed
        if poll is None:
            target = running
        elif poll == 0:
            target = succeeded
        target.append(proc)
    return running, succeeded, failed

def summarize(procs, nprocs=None):
    running, succeeded, failed = status(procs)
    if nprocs is None:
        nprocs = len(procs)

    succeeded = len(succeeded)
    failed = len(failed)
    completed = succeeded + failed

    return ("%d/%d/%d tasks running/completed/total, %0.2f%% failed",
        len(running), completed, nprocs, (100.0 * failed)/nprocs)

def logfile(*paths):
    path = os.path.join(".", *paths)

    try:
        os.makedirs(os.path.dirname(path))
    except OSError, e:
        if e.errno not in (17,):
            raise
    return open(path, "a")

def maptask(task, targets, logfile, maxrunning=1, interval=.2, handler=None):
    ttargets = len(targets)
    procs = []

    if handler is not None:
        def sighandler(sig, frame):
            handler(procs, ttargets)

        if hasattr(signal, "SIGUSR1"):
            signal.signal(signal.SIGUSR1, sighandler)
        if hasattr(signal, "SIGINFO"):
            signal.signal(signal.SIGINFO, sighandler)

    while targets:
        running, succeeded, failed = status(procs)
        if len(running) >= maxrunning:
            time.sleep(interval)
            continue

        target = targets.pop()

        out, err = [logfile(target, x) for x in ("out", "err")]
        log.debug("starting %s %r", task, target)
        process = subprocess.Popen([task, target], stdout=out, stderr=err)
        procs.append(process)

    while status(procs)[0]:
        time.sleep(interval)

    return procs, ttargets

def parseargs(argv):
    """Parse command line arguments.

    Returns a tuple (*opts*, *args*), where *opts* is an
    :class:`optparse.Values` instance and *args* is the list of arguments left
    over after processing.

    :param argv: a list of command line arguments, usually :data:`sys.argv`.
    """
    prog = argv[0]
    usage = "[options] task target[, target, ...]"
    parser = optparse.OptionParser(prog=prog, usage=usage)
    parser.allow_interspersed_args = False

    defaults = {
        "targets": "./targets",
        "running": None,
        "interval": .2,
        "quiet": 0,
        "silent": False,
        "verbose": 0,
    }

    # Global options.
    parser.add_option("-t", "--targets", dest="targets",
        default=defaults["targets"], action="store",
        help="target file (default: %(targets)r)" % defaults)
    parser.add_option("-n", "--running", dest="running",
        default=defaults["running"], action="store",
        help="number of running tasks (default: number of CPUs or 1)")
    parser.add_option("-i", "--interval", dest="interval",
        default=defaults["interval"], action="store",
        help="polling interval in seconds (default: %(interval).02f)" % defaults)
    parser.add_option("-q", "--quiet", dest="quiet",
        default=defaults["quiet"], action="count",
        help="decrease the logging verbosity")
    parser.add_option("-s", "--silent", dest="silent",
        default=defaults["silent"], action="store_true",
        help="silence the logger")
    parser.add_option("-v", "--verbose", dest="verbose",
        default=defaults["verbose"], action="count",
        help="increase the logging verbosity")

    (opts, args) = parser.parse_args(args=argv[1:])
    return (opts, args)

def main(argv, stdin=None, stdout=None, stderr=None, tasks={}):
    """Main entry point.

    Returns a value that can be understood by :func:`sys.exit`.

    :param argv: a list of command line arguments, usually :data:`sys.argv`.
    :param out: stream to write messages; :data:`sys.stdout` if None.
    :param err: stream to write error messages; :data:`sys.stderr` if None.
    """
    if stdin is None: # pragma: nocover
        stdin = sys.stdin
    if stdout is None: # pragma: nocover
        stdout = sys.stdout
    if stderr is None: # pragma: nocover
        stderr = sys.stderr

    (opts, args) = parseargs(argv)
    level = logging.WARNING - ((opts.verbose - opts.quiet) * 10)
    if opts.silent:
        level = logging.CRITICAL + 1
    level = max(1, level)

    format = "%(name)s: %(message)s"
    handler = logging.StreamHandler(stderr)
    handler.setFormatter(logging.Formatter(format))
    log.addHandler(handler)
    log.setLevel(level)

    task = args.pop(0)
    targets = args
    maxrunning = opts.running

    e = None
    try:
        isexec = os.stat(task).st_mode & stat.S_IEXEC
    except OSError, e:
        isexec = False

    if not isexec:
        msg = "cannot execute task %r" % task
        if e:
            msg += " (%s)" % e
        stderr.write(msg + "\n")
        return 1

    if maxrunning is None:
        maxrunning = ncpu()
    interval = float(opts.interval)

    alltargets = {}
    try:
        alltargets = groups(open(opts.targets, 'r'))
        log.debug("read %d groups from targets file %r", len(alltargets), opts.targets)
    except IOError:
        pass

    targets = groups(targets, default="all", data=alltargets)["all"]

    def handler(procs, nprocs):
        log.info(*summarize(procs, nprocs))

    procs, nprocs = maptask(task, targets, interval=interval,
            maxrunning=maxrunning, logfile=logfile, handler=handler)
    handler(procs, nprocs)

def entry():
    try:
        ret = main(sys.argv, sys.stdin, sys.stdout, sys.stderr)
    except KeyboardInterrupt:
        ret = None

    sys.exit(ret)

if __name__ == "__main__": # pragma: nocover
    entry()
