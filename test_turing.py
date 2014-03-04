#!/usr/bin/env py.test
# -*- coding: utf-8 -*-
# Created on Tue Mar  4 11:05:50 2014
# MIT Licensed. See COPYING.TXT for more information.
""" Turing machine internals testing module """

from __future__ import unicode_literals
from turing import tokenizer

class TestTokenizer(object):

  def test_simple_full_line_rule(self):
    data = "q1 1 -> P0 R q2" # Newline token is always implicit
    expected = ["q1", "1", "->", "P0", "R", "q2", "\n"]
    assert list(tokenizer(data)) == expected

  def test_three_full_line_rules(self):
    data = (
      "q1 1 -> P0 R q2\n"
      "q2 0 -> P1 q2\n"
      "q2 1 -> E L q1\n"
    )
    expected = [
      "q1", "1", "->", "P0", "R", "q2", "\n",
      "q2", "0", "->", "P1", "q2", "\n",
      "q2", "1", "->", "E", "L", "q1", "\n",
    ]
    assert list(tokenizer(data)) == expected

  def test_simple_multiline_rule(self):
    data = (
      "q3 0 -> P1 R\n"
      "        P0 R q2\n"
    )
    expected = ["q3", "0", "->", "P1", "R", "P0", "R", "q2", "\n"]
    assert list(tokenizer(data)) == expected

  def test_no_token_at_all(self): # Empty files have a single token
    assert list(tokenizer("\n\n\n")) == ["\n"] == list(tokenizer(""))

  def test_empty_lines(self):
    data = (
      "\n\nq312 0 -> P1 R\n\n\n"
      "              P0 L L q2\n\n"
    )
    expected = ["q312", "0", "->", "P1", "R", "P0", "L", "L", "q2", "\n"]
    assert list(tokenizer(data)) == expected

  def test_indent_arrow(self):
    data = (
      "q4 0 -> P1 R q3\n"
      "   1 -> Px q4\n\n"
      "   x -> P0 L q3\n\n"
    )
    expected = [ # The space is an indent token
      "q4", "0", "->", "P1", "R", "q3", "\n",
      " ", "1", "->", "Px", "q4", "\n",
      " ", "x", "->", "P0", "L", "q3", "\n",
    ]
    print(list(tokenizer(data)))
    assert list(tokenizer(data)) == expected
