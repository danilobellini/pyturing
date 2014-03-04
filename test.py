#!/usr/bin/env py.test
# -*- coding: utf-8 -*-
# Created on Tue Mar  4 11:05:50 2014
# MIT Licensed. See COPYING.TXT for more information.

from __future__ import unicode_literals
from turing import tokenizer

class TestTokenizer(object):

  def test_simple_full_line_rule(self):
    data = "q1 1 -> P0 R q2"
    expected = ["q1", "1", "->", "P0", "R", "q2", "\n"]
    assert list(tokenizer(data)) == expected
