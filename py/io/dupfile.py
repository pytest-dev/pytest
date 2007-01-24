
import os

def dupfile(f, mode=None, buffering=0, raising=False): 
    try: 
        fd = f.fileno() 
    except AttributeError: 
        if raising: 
            raise 
        return f
    newfd = os.dup(fd) 
    mode = mode and mode or f.mode
    return os.fdopen(newfd, mode, buffering) 
