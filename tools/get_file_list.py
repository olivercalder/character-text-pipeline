#!/usr/bin/python3

import csv

with open('VEP_metadata.csv', newline='') as infile:
    reader = csv.reader(infile)
    header = True
    for row in reader:
        if header:
            header = False
            continue
        print(row[0] + '.xml')
