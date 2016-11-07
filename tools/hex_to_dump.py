#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from intelhex import IntelHex

flash = IntelHex(sys.argv[1])
flash.dump()
