#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pylint.lint import Run

THRESHOLD = 9.9

score = Run(["./kipubot"], exit=False).linter.stats.global_note

if score < THRESHOLD:
    print(f'Linter failed: Score ({score}) < Threshold ({THRESHOLD}) value')
    sys.exit(1)

sys.exit(0)
