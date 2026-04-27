import shlex
import subprocess
import sys

platform = sys.argv[1]
count = int(sys.argv[2])

with open(f"commands_{platform}.py") as command_file:
    commands = eval(command_file.read())

for i in range(0, count):
    command = commands[i]
    try:
        subprocess.run(shlex.split(command))
    except:
        pass

    try:
        input("\n[Enter to continue]")
    except KeyboardInterrupt:
        print("\nAborting")
        break
