import os
import sys

executable = os.path.join(os.getcwd(), 'build', 'runtests_script')
if sys.platform.startswith('win'):
    executable += '.exe'
sys.exit(os.system('%s tests' % executable))