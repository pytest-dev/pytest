
        
py.test --dist=each $* \
    --tx 'socket=192.168.1.106:8888'
    #--tx 'popen//python=python2.6' \
    #--tx 'ssh=noco//python=/usr/local/bin/python2.4//chdir=/tmp/pytest-python2.4' \
