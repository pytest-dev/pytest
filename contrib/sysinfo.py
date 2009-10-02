"""
sysinfo.py [host1] [host2] [options]

obtain system info from remote machine. 
"""

import py
import sys


parser = py.std.optparse.OptionParser(usage=__doc__)
parser.add_option("-f", "--sshconfig", action="store", dest="ssh_config", default=None,
                  help="use given ssh config file, and add info all contained hosts for getting info")
parser.add_option("-i", "--ignore", action="store", dest="ignores", default=None,
                  help="ignore hosts (useful if the list of hostnames come from a file list)")

def parsehosts(path):
    path = py.path.local(path)
    l = []
    rex = py.std.re.compile(r'Host\s*(\S+)')
    for line in path.readlines():
        m = rex.match(line)
        if m is not None:
            sshname, = m.groups()
            l.append(sshname)
    return l

class RemoteInfo:
    def __init__(self, gateway):
        self.gw = gateway
        self._cache = {}

    def exreceive(self, execstring):
        if execstring not in self._cache:
            channel = self.gw.remote_exec(execstring)
            self._cache[execstring] = channel.receive()
        return self._cache[execstring]

    def getmodattr(self, modpath):
        module = modpath.split(".")[0]
        return self.exreceive("""
            import %s
            channel.send(%s)
        """ %(module, modpath))

    def islinux(self):
        return self.getmodattr('sys.platform').find("linux") != -1

    def getfqdn(self):
        return self.exreceive("""
            import socket
            channel.send(socket.getfqdn())
        """)

    def getmemswap(self):
        if self.islinux():
            return self.exreceive(""" 
            import commands, re
            out = commands.getoutput("free")
            mem = re.search(r"Mem:\s+(\S*)", out).group(1)
            swap = re.search(r"Swap:\s+(\S*)", out).group(1)
            channel.send((mem, swap))
            """)

    def getcpuinfo(self):
        if self.islinux():
            return self.exreceive("""
                # a hyperthreaded cpu core only counts as 1, although it
                # is present as 2 in /proc/cpuinfo.  Counting it as 2 is
                # misleading because it is *by far* not as efficient as
                # two independent cores.
                cpus = {}
                cpuinfo = {}
                f = open("/proc/cpuinfo")
                lines = f.readlines()
                f.close()
                for line in lines + ['']:
                    if line.strip():
                        key, value = line.split(":", 1)
                        cpuinfo[key.strip()] = value.strip()
                    else:
                        corekey = (cpuinfo.get("physical id"),
                                   cpuinfo.get("core id"))
                        cpus[corekey] = 1
                numcpus = len(cpus)
                model = cpuinfo.get("model name")
                channel.send((numcpus, model))
            """)

def debug(*args):
    print >>sys.stderr, " ".join(map(str, args))
def error(*args):
    debug("ERROR", args[0] + ":", *args[1:])

def getinfo(sshname, ssh_config=None, loginfo=sys.stdout):
    debug("connecting to", sshname)
    try:
        gw = execnet.SshGateway(sshname, ssh_config=ssh_config)
    except IOError:
        error("could not get sshagteway", sshname)
    else:
        ri = RemoteInfo(gw)
        #print "%s info:" % sshname
        prefix = sshname.upper() + " "
        print >>loginfo, prefix, "fqdn:", ri.getfqdn()
        for attr in (
            "sys.platform", 
            "sys.version_info", 
        ):
            loginfo.write("%s %s: " %(prefix, attr,))
            loginfo.flush()
            value = ri.getmodattr(attr)
            loginfo.write(str(value))
            loginfo.write("\n")
            loginfo.flush()
        memswap = ri.getmemswap()
        if memswap:
            mem,swap = memswap
            print >>loginfo, prefix, "Memory:", mem, "Swap:", swap 
        cpuinfo = ri.getcpuinfo()
        if cpuinfo:
            numcpu, model = cpuinfo
            print >>loginfo, prefix, "number of cpus:",  numcpu
            print >>loginfo, prefix, "cpu model", model 
        return ri
            
if __name__ == '__main__':
    options, args = parser.parse_args()
    hosts = list(args)
    ssh_config = options.ssh_config
    if ssh_config:
        hosts.extend(parsehosts(ssh_config))
    ignores = options.ignores or ()
    if ignores:
        ignores = ignores.split(",")
    for host in hosts:
        if host not in ignores:
            getinfo(host, ssh_config=ssh_config)
        
