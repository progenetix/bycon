#!/usr/bin/env python3

import cgitb
import subprocess
cgitb.enable()

print("Content-Type: text/html;charset=utf-8")
print()

pp = subprocess.run(['which','python3'], stdout=subprocess.PIPE)
print(pp.stdout.decode('utf-8'))
