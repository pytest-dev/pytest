
if __name__ == '__main__':
    import cProfile
    import py
    import pstats
    stats = cProfile.run('py.test.cmdline.main(["empty.py", ])', 'prof')
    p = pstats.Stats("prof")
    p.strip_dirs()
    p.sort_stats('cumulative')
    print p.print_stats(30)
