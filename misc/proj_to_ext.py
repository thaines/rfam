#! /usr/bin/env python3

# Simple helper that loads a .json file and vomits out the external assets in credit form - useful for cleaning up post-event fuckups...

import sys
import json

proj = json.load(open(sys.argv[1]))

for ext_asset in sorted(proj['ext_assets'].values(), key=lambda ext_asset: ext_asset['description']):
  print(ext_asset['description'])
  print(ext_asset['license'])
  print(ext_asset['origin'])
  print('\n\n')

