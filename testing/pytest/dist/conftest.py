try:
    import execnet
except ImportError:
    collect_ignore = ['.']
