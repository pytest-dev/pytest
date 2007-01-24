import rlcompleter2
rlcompleter2.setup()

import register, sys
try:
    hostport = sys.argv[1]
except:
    hostport = ':8888'
gw = register.ServerGateway(hostport)
