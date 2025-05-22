#!/usr/local/bin/python3

import csv
from os import path, pardir, system

loc_path = path.join( path.dirname( path.abspath(__file__) ) )

id_file = path.join( loc_path, "hyperplasia_ids.tsv" )
label_file = path.join( loc_path, "hyperplasia_labels.tsv" )
hier_file = path.join( loc_path, "hyperplasia_numbered_hierarchies.tsv" )
start_count = 370514

with open(id_file, mode='r', newline='') as id_fh:
    id_lines = id_fh.readlines()

with open(label_file, mode='r', newline='') as lab_fh:
    label_lines = lab_fh.readlines()

print(f'>>>>>> {len(id_lines)} ID lines')
print(f'>>>>>> {len(label_lines)} Label lines')

hier_lines = []
for i, code in enumerate(id_lines):
	for col, cell in enumerate(code.split('\t')):
		if len(cell) > 0:
			h_l = "\t".join([
				f'NCIT:{cell.strip()}',
				label_lines[i].split('\t')[col].strip(),
				str(col),
				str(i+1+start_count)
			])
			hier_lines.append(h_l)

hier_fh = open(hier_file, "w")
for h_l in hier_lines:
	hier_fh.write(f'{h_l}\n')
hier_fh.close()