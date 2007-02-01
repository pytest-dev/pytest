
import os

def dupfile(f, mode=None, buffering=0, raising=False): 
    """ return a new open file object that's a duplicate of f

        mode is duplicated if not given, 'buffering' controls 
        buffer size (defaulting to no buffering) and 'raising'
        defines whether an exception is raised when an incompatible
        file object is passed in (if raising is False, the file
        object itself will be returned)
    """
    try: 
        fd = f.fileno() 
    except AttributeError: 
        if raising: 
            raise 
        return f
    newfd = os.dup(fd) 
    mode = mode and mode or f.mode
    return os.fdopen(newfd, mode, buffering) 

