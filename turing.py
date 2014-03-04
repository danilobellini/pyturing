# -*- coding: utf-8 -*-
# Created on Tue Mar  4 11:05:22 2014
# MIT Licensed. See COPYING.TXT for more information.

from __future__ import unicode_literals
import re

__all__ = ["tokenizer"]

def tokenizer(data):
    for line in data.splitlines():
        for token in re.findall("->|\S+", data):
            yield token
        yield "\n"
