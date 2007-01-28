"""

Testing Host setup and rsyncing operations. 

"""

import py
from py.__.test.host import parsehostspec

def test_parse_hostspec_ssh():
    hostspec = parsehostspec("ssh:xyz@domain.net:directory")
    assert hostspec.host == "domain.net"
    assert hostspec.basedir == "directory"
    assert hostspec.sshaddress == "xyz@domain.net"

    hostspec = parsehostspec("ssh:xyz@domain.net:direc:tory")
    assert hostspec.host == "domain.net"
    assert hostspec.basedir == "direc:tory"
    assert hostspec.sshaddress == "xyz@domain.net"

    hostspec = parsehostspec("ssh:xyz@domain.net")
    assert hostspec.host == "domain.net"
    assert hostspec.basedir == ""
    assert hostspec.sshaddress == "xyz@domain.net"

    hostspec = parsehostspec("ssh:domain.net:directory")
    assert hostspec.host == "domain.net"
    assert hostspec.basedir == "directory"
    assert hostspec.sshaddress == "domain.net"

    hostspec = parsehostspec("ssh:domain.net:/tmp/hello")
    assert hostspec.host == "domain.net"
    assert hostspec.basedir == "/tmp/hello"
    assert hostspec.sshaddress == "domain.net"

def test_parse_hostspec_socket():
    hostspec = parsehostspec("socket:domain.net:1234:directory")
    assert hostspec.host == "domain.net"
    assert hostspec.port == 1234
    assert hostspec.basedir == "directory" 

    hostspec = parsehostspec("socket:domain.net:1234")
    assert hostspec.host == "domain.net"
    assert hostspec.port == 1234
    assert hostspec.basedir == ""
    
def test_parse_hostspec_error():
    py.test.raises(ValueError, """
        parsehostspec('alksd:qweqwe')
    """)
    py.test.raises(ValueError, """
        parsehostspec('ssh')
    """)
    py.test.raises(ValueError, """
        parsehostspec('socket:qweqwe')
    """)
