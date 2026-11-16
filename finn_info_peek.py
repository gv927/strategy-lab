#!/usr/bin/env python3
import json, re, sys, subprocess, html
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
page = subprocess.run(["curl","-sL","--max-time","40","-H",f"User-Agent: {UA}","https://www.finn.no/job/ad/479238499"],capture_output=True,text=True).stdout
idx = page.find("Arbeidsspråk")
print(repr(page[idx-600:idx+600]))
