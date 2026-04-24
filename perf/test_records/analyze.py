import re
import sys

platform = sys.argv[1]
count = int(sys.argv[2])

file_pattern = re.compile(r"^     Running (.+) \(")
func_pattern = re.compile(r"^test ([\w:/ -]+) (\(.*\) )?\.\.\.")
dur_pattern = re.compile(r"\[dur: (\d+) ms \(([a-zA-Z0-9_]+)\)\]")

def read_durs(record_filename):
    #print("reading:", record_filename)
    durs = dict()
    tested_funcs = set()
    unmatching_func_count = 0
    unexpected_unmatching_func_count = 0

    with open(record_filename, "r") as record:
        file_name = "xxx"
        func_path = "yyy"
        for line in record:
            #line = "test src\\authorship\\agent_detection.rs - authorship::agent_detection::match_email_to_agent (line 41) ... ok"
            line = line.replace("\\", "/")
            file_match = file_pattern.search(line)
            if file_match is not None:
                file_name = file_match.groups()[0]

            line = line.replace(".rs", "")
            func_match = func_pattern.search(line)
            if func_match is not None:
                func_path = func_match.groups()[0]
                tested_funcs.add(func_path)

            dur_match = dur_pattern.search(line)
            if dur_match is not None:
                (dur, func_name) = dur_match.groups()
                if func_name == func_path.split("::")[-1]:
                    durs[(file_name, func_path)] = int(dur)
                else:
                    unmatching_func_count += 1
                    if not func_path.endswith("worktree"):
                        unexpected_unmatching_func_count += 1

    #print("  unmatching funcs:", unmatching_func_count)
    #print("  unexpected unmatching funcs:", unexpected_unmatching_func_count)
    funcs_with_durs = {func_path for (file_name, func_path) in durs.keys()}
    #print("  tested funcs without durs:", len(tested_funcs - funcs_with_durs))
    #print("  funcs with durs:", len(durs))

    return durs

def dur_magnitudes(durs):
    mag1 = 0
    mag2 = 0
    mag3 = 0
    mag4 = 0
    mag5 = 0
    mag6 = 0
    for dur in durs.values():
        if dur < 10:
            mag1 += 1
        elif dur < 100:
            mag2 += 1
        elif dur < 1000:
            mag3 += 1
        elif dur < 10000:
            mag4 += 1
        elif dur < 100000:
            mag5 += 1
        else:
            mag6 += 1
        
    #print("0-10 ms:", mag1)
    #print("10-100 ms:", mag2)
    #print("100-1000 ms:", mag3)
    #print("1000-10000 ms:", mag4)
    #print("10000-100000 ms:", mag5)
    #print(">100000 ms:", mag6)

win_durs = read_durs("ct.win.serial.stdall")
wsl_durs = read_durs("ct.wsl.serial.stdall")
linux_durs = read_durs("ct.linux.serial.stdall")

#print("win total dur:", sum(win_durs.values()) / 60000, "minutes")
#print("wsl total dur:", sum(wsl_durs.values()) / 60000, "minutes")
#print("linux total dur:", sum(linux_durs.values()) / 60000, "minutes")

dur_magnitudes(win_durs)

# filter for only slow windows tests
slow_win_durs = dict()
for test in win_durs:
    if win_durs[test] >= 1000:
        slow_win_durs[test] = win_durs[test]
win_durs = slow_win_durs

# filter linux tests that take no time
nonzero_linux_durs = dict()
for test in linux_durs:
    if linux_durs[test] > 0:
        nonzero_linux_durs[test] = linux_durs[test]
linux_durs = nonzero_linux_durs

win_tests = set(win_durs.keys())
wsl_tests = set(wsl_durs.keys())
linux_tests = set(linux_durs.keys())

common_tests = win_tests.intersection(wsl_tests).intersection(linux_tests)

#print("win tests not in common:", len(win_tests - common_tests))
#print("wsl tests not in common:", len(wsl_tests - common_tests))
#print("linux tests not in common:", len(linux_tests - common_tests))
#print("common tests:", len(common_tests))

win_tests = win_tests.intersection(common_tests)
wsl_tests = wsl_tests.intersection(common_tests)
linux_tests = linux_tests.intersection(common_tests)

common_win_durs = dict()
for test in win_durs:
    if test in win_tests:
        common_win_durs[test] = win_durs[test]
win_durs = common_win_durs
 
common_wsl_durs = dict()
for test in wsl_durs:
    if test in wsl_tests:
        common_wsl_durs[test] = wsl_durs[test]
wsl_durs = common_wsl_durs

common_linux_durs = dict()
for test in linux_durs:
    if test in linux_tests:
        common_linux_durs[test] = linux_durs[test]
linux_durs = common_linux_durs

dur_magnitudes(win_durs)
dur_magnitudes(wsl_durs)
dur_magnitudes(linux_durs)

win_total_dur = sum(win_durs.values())
wsl_total_dur = sum(win_durs.values())
linux_total_dur = sum(linux_durs.values())

win_proportions = dict()
wsl_proportions = dict()
linux_proportions = dict()

for test in win_durs:
    win_proportions[test] = win_durs[test] / win_total_dur
for test in wsl_durs:
    wsl_proportions[test] = wsl_durs[test] / wsl_total_dur
for test in linux_durs:
    linux_proportions[test] = linux_durs[test] / linux_total_dur

relative_win_to_linux_proportions = dict()
for test in common_tests:
    relative_win_to_linux_proportions[test] = win_proportions[test] / linux_proportions[test]

proportions_copy = relative_win_to_linux_proportions.copy()
ordered_proportions = []
while len(proportions_copy) > 0:
    ordered_proportions.append(max(proportions_copy))
    del(proportions_copy[ordered_proportions[-1]])

#print("max win to linux proportion:", ordered_proportions[0], win_proportions[ordered_proportions[0]], linux_proportions[ordered_proportions[0]], relative_win_to_linux_proportions[ordered_proportions[0]])
#print("min win to linux proportion:", ordered_proportions[-1], win_proportions[ordered_proportions[-1]], linux_proportions[ordered_proportions[-1]], relative_win_to_linux_proportions[ordered_proportions[-1]])

for test in ordered_proportions[:count]:
    win_dur = win_durs[test]
    wsl_dur = wsl_durs[test]
    linux_dur = linux_durs[test]
    #print(f"test: {test}, win: {win_dur}, wsl: {wsl_dur}, linux: {linux_dur}")

    test_type = "integration"
    test_src_path = test[0]
    if test_src_path.startswith("unittests "):
        test_type = "unit"
        test_src_path = test_src_path.removeprefix("unittests ")
    test_identifier = test[1]

    print(f"python3 measure.py {platform} {test_type} {test_src_path} {test_identifier}")
