import json
import pathlib
import subprocess
import shlex
import sys

def main():
    crate_name = "git_ai"

    platform = sys.argv[1]
    test_src_file = sys.argv[2]
    test_identifier = sys.argv[3]
    #platform = "win"
    #test_src_file = "src/lib.rs"
    #test_identifier = "git::repository::tests::test_list_commit_files_with_utf8_filename"

    cmd = f"cargo test --no-run --quiet --message-format json {test_identifier}"
    print(f"Running `{cmd}`")
    cargo_test_stdout = subprocess.run(shlex.split(cmd), capture_output=True, encoding="utf-8", check=True).stdout

    cargo_test_json_records = cargo_test_stdout.split("\n")

    test_src_path = pathlib.Path(test_src_file)
    cargo_test_filename = None
    record_found = False
    for json_record in cargo_test_json_records:
        try:
            record = json.loads(json_record)
            if record["profile"]["test"] == True and record["target"]["name"] == crate_name:
                    record_src_path = pathlib.Path(record["target"]["src_path"])
                    if test_src_path.parts == record_src_path.parts[-len(test_src_path.parts):]:
                        cargo_test_filename = record["filenames"][0]
                        record_found = True
                        break
        except Exception as e:
            continue

    if record_found == False:
        print("Error: could not locate binary")
        return

    profile_path = pathlib.Path("measurements") / test_identifier.replace("::", ".")
    profile_path.mkdir(exist_ok=True)
    profile_file = profile_path / f"profile.{platform}.json.gz"

    cmd = f'samply record -o "{profile_file}" -s "{cargo_test_filename}" --exact {test_identifier}'
    print(f"Running `{cmd}`")
    subprocess.run(shlex.split(cmd), check=True)

    print(f"Output written to {profile_file}")

if __name__ == "__main__":
    main()
