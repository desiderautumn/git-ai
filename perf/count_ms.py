with open("millis_win.out") as f:
    sum = 0
    for thing in f:
        thing = thing.removeprefix("xxx MILLIS ")
        thing = thing.removesuffix(" xxx\n")
        num = int(thing)
        sum += num

    print(sum)
