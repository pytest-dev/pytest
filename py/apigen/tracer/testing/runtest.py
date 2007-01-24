
def cut_pyc(f_name):
    if f_name.endswith('.pyc'):
        return f_name[:-1]
    return f_name
