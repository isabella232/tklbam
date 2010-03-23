import os
import re
import commands

class Error(Exception):
    pass

class DpkgSelections(set):
    Error = Error

    @staticmethod
    def _parse(buf):
        for line in buf.strip().split('\n'):
            package, state = re.split(r'\t+', line)
            if state in ('deinstall', 'purge'):
                continue
            yield package

    @staticmethod
    def _dpkg_get_selections():
        cmd = "dpkg --get-selections"
        errno, output = commands.getstatusoutput(cmd)
        if errno:
            raise Error("command failed (%d): %s" % (os.WEXITSTATUS(errno), cmd))

        return output

    def __init__(self, arg=None):
        """If arg is not provided we get selections from dpkg.
           arg can be a filename, a string."""

        if arg:
            if os.path.exists(arg):
                buf = file(arg).read()
            else:
                buf = arg
        else:
            buf = self._dpkg_get_selections()

        set.__init__(self, self._parse(buf))

class AptCache(set):
    Error = Error

    def __init__(self, packages):
        command = "apt-cache show " + " ".join(packages)
        status, output = commands.getstatusoutput(command)
        status = os.WEXITSTATUS(status)
        if status not in (0, 100):
            raise self.Error("execution failed (%d): %s\n%s" % (status, command, output))
        
        cached = [ line.split()[1] 
                   for line in output.split("\n") if
                   line.startswith("Package: ") ]

        set.__init__(self, cached)

def installable(packages):
    selections = DpkgSelections()
    aptcache = AptCache(packages)

    installable = []
    skipped = []
    for package in set(packages):
        if package in selections:
            continue

        if package not in aptcache:
            skipped.append(package)
            continue

        installable.append(package)

    return installable, skipped

class Installer:
    """
    Interface::
        installer.command       Command executed
        installer.installing    List of packages to be installed
        installer.skipping      List of packages we're skipping
                                (e.g., because we couldn't find them in the apt-cache)

        installer.install()     Run command and return an error code
                                By default noninteractive...
    """
    def __init__(self, packages):
        self.installing, self.skipping = installable(packages)

        self.installing.sort()
        self.skipping.sort()

        self.command = None

        if self.installing:
            self.command = "apt-get install " + " ".join(self.installing)

    def install(self, interactive=False):
        """Install packages.
        If no packages are to be installed:
            return None 
        Else:
            return exitcode from execution of installation of command
        """
        if not self.command:
            return None

        command = self.command
        if not interactive:
            command = "DEBIAN_FRONTEND=noninteractive " + command

        return os.system(command)
