#!/usr/bin/python
import fileinput
import sys
for file in sys.argv[1:]:
    fh = fileinput.hook_compressed(file, 'r')
    data = fh.read(32768)
    while data:
        sys.stdout.write(data)
        data = fh.read(32768)
