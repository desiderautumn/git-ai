import json
import pathlib
import subprocess
import shlex
import sys

def main():
    crate_name = "git_ai"

    platform = sys.argv[1]
    test_type = sys.argv[2]
    test_src_file = sys.argv[3]
    test_command = sys.argv[4]

    if test_type == "unit" or test_type == "integration":
        test_identifier = test_command
    elif test_type == "run":
        test_identifier = "run." + test_command.split(' ')[0]
    else:
        print("Error: unknown test type")
        return

    if test_type == "unit" or test_type == "integration":
        cmd = f"cargo test --no-run --quiet --message-format json {test_identifier}"
        print(f"Running `{cmd}`")
        cargo_test_stdout = subprocess.run(shlex.split(cmd), capture_output=True, encoding="utf-8", check=True).stdout

        cargo_test_json_records = cargo_test_stdout.split("\n")

        test_src_path = pathlib.Path(test_src_file)
        if test_type == "integration":
            crate_name = test_src_path.name.removesuffix(".rs")
        binary_filename = None
        record_found = False
        for json_record in cargo_test_json_records:
            try:
                record = json.loads(json_record)
                if record["profile"]["test"] == True:
                    if record["target"]["name"] == crate_name:
                        record_src_path = pathlib.Path(record["target"]["src_path"])
                        if test_src_path.parts == record_src_path.parts[-len(test_src_path.parts):]:
                            binary_filename = record["filenames"][0]
                            record_found = True
                            break
            except Exception as e:
                continue

        if record_found == False:
            print("Error: could not locate binary")
            return
    elif test_type == "run":
        cmd = f"cargo build"
        print(f"Running {cmd}")
        cargo_build_stdout = subprocess.run(shlex.split(cmd), capture_output=True, check=True)
        binary_filename = "../target/debug/git-ai"

    profile_path = pathlib.Path("measurements") / test_identifier.replace("::", ".") / platform
    profile_path.mkdir(exist_ok=True, parents=True)
    profile_file = profile_path / f"profile.json.gz"

    presymbolicate_flag = ""
    if platform == "linux":
        presymbolicate_flag = "--unstable-presymbolicate"

    capture_output = False
    if test_type == "unit":
        cmd = f'samply record {presymbolicate_flag} -o "{profile_file}" -s "{binary_filename}" --exact {test_identifier}'
    elif test_type == "integration":
        cmd = f'cargo samply --samply-args="{presymbolicate_flag} -o \'{profile_file}\' -s" --test {crate_name} {test_identifier}'
    elif test_type == "run":
        capture_output = True
        cmd = f'samply record {presymbolicate_flag} -o "{profile_file}" -s "{binary_filename}" {test_command}'
    else:
        print("Error: unknown test type")
        return

    print(f"Running `{cmd}`")
    subprocess.run(shlex.split(cmd), check=True, capture_output=capture_output)

    print(f"Output written to {profile_file}")

    cmd = f'samply load "{profile_file}"'
    print(f"Running `{cmd}`")
    try:
        subprocess.run(shlex.split(cmd))
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
