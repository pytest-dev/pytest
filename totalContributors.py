import subprocess
PIPE = subprocess.PIPE
branch = 'my_branch'

process = subprocess.Popen(['git', 'pull', branch], stdout=PIPE, stderr=PIPE)
stdoutput, stderroutput = process.communicate()

if 'fatal' in stdoutput:
    # Handle error case
else:
    # Success!