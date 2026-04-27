import shlex
import subprocess
import sys

platform = sys.argv[1]
command_range = eval(f"range({sys.argv[2]})")

with open(f"commands_{platform}.py") as command_file:
    commands = eval(command_file.read())

for i in command_range:
    command = commands[i]
    print(f"Running `{command}`")
    print(shlex.split(command))
    try:
        subprocess.run(shlex.split(command))
    except KeyboardInterrupt:
        pass

    try:
        pass
        #input("\n[Enter to continue]")
    except (KeyboardInterrupt, EOFError):
        print("\n[Aborting]")
        break

print("[Finished]")
