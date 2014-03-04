#!/usr/bin/env py.test
# -*- coding: utf-8 -*-
# Created on Tue Mar  4 11:05:50 2014
# MIT Licensed. See COPYING.TXT for more information.
""" Turing machine internals testing module """

from __future__ import unicode_literals
from turing import (TMSyntaxError, tokenizer, raw_rule_generator,
                    sequence_cant_have, evaluate_symbol_query)
from pytest import raises, mark
p = mark.parametrize


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
    assert list(tokenizer("\n\n\n")) == ["\n"] == list(tokenizer("")) \
                                               == list(tokenizer("\n \n  \n"))

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


class TestRawRuleGenerator(object):

  def test_no_rules(self):
    assert list(raw_rule_generator("\n \n\n")) == [] == \
           list(raw_rule_generator(""))

  def test_one_rule(self):
    rgen = raw_rule_generator("q1 1 -> P0 R q2")
    assert next(rgen) == (["q1", "1"], ["P0", "R", "q2"])
    with raises(StopIteration):
        next(rgen)

  def test_half_rule(self):
    rgen = raw_rule_generator("q1 1")
    with raises(TMSyntaxError):
        next(rgen)

  @p("rule", ["q1 1 ->", "-> q0"])
  def test_one_and_a_half_rule_with_arrow(self, rule):
    rgen = raw_rule_generator("q0 -> q1\n" + rule)
    assert next(rgen) == (["q0"], ["q1"])
    with raises(TMSyntaxError):
        next(rgen)

  @p("rule", ["  ->", "->", "\n->", "->\n\n", "->\n\nq0 -> q1"])
  def test_one_and_a_arrow_only_rule(self, rule):
    rgen = raw_rule_generator("q1 1 -> E q0\n" + rule)
    assert next(rgen) == (["q1", "1"], ["E", "q0"])
    with raises(TMSyntaxError):
        next(rgen)

  def test_five_rules(self):
    rgen = raw_rule_generator(
      "q4 0 -> P1 R q3\n"
      "   1 -> Px q4\n\n"
      "   x -> P0 L\n\n\n"
      "        P1 q3\n"
      "q3 0 -> P1 q4\n"
      "   1 -> P0 L q3"
    )
    assert next(rgen) == (["q4", "0"], ["P1", "R", "q3"])
    assert next(rgen) == ([" ", "1"], ["Px", "q4"])
    assert next(rgen) == ([" ", "x"], ["P0", "L", "P1", "q3"])
    assert next(rgen) == (["q3", "0"], ["P1", "q4"])
    assert next(rgen) == ([" ", "1"], ["P0", "L", "q3"])
    with raises(StopIteration):
        next(rgen)


class TestSequenceCantHave(object):

    def test_empty_input(self):
        func = sequence_cant_have()(lambda: [1, "2", sequence_cant_have])
        assert func() == [1, "2", sequence_cant_have]

    def test_empty_function_output(self):
        func = sequence_cant_have("a", "Not")(lambda x: x)
        assert func([]) == []

    def test_empty_both_input_and_output(self):
        assert sequence_cant_have()(lambda x: x)([]) == []

    def test_occurrence(self):
        data = ["a", "", self]
        func = sequence_cant_have("Not", "Neither")(lambda: data)
        assert func() == data
        data.append("Neither")
        with raises(TMSyntaxError):
            func()
        data.pop()
        assert func() == data
        data[1] = "Not"
        with raises(TMSyntaxError):
            func()


class TestEvaluateSymbolQuery(object):

    @p("symb", ["a", "1", "noot", "_bad", "q1", "Ç", "That'sIt"])
    def test_valid_one_symbol_scenarios(self, symb):
        assert evaluate_symbol_query(symb) == ((symb,), True)
        assert evaluate_symbol_query("Not", symb) == ((symb,), False)

    def test_simple_multisymbol_without_repeat(self):
        symbs = "abc defgh ijk lmnop qrs".split()
        input_data = ["["] + symbs + ["]"]
        expected = tuple(symbs)
        assert evaluate_symbol_query(*input_data) == (expected, True)
        assert evaluate_symbol_query("Not", *input_data) == (expected, False)
        with raises(TMSyntaxError):
            evaluate_symbol_query(*symbs)
        with raises(TMSyntaxError):
            evaluate_symbol_query("Not", *symbs)

    @p("symbs", [("Not",), ("1", "Not"), ("ABC", "Not", "Neither")])
    def test_not_twice_or_invalidly_alone(self, symbs):
        with raises(TMSyntaxError):
            evaluate_symbol_query(*symbs)
        with raises(TMSyntaxError):
            evaluate_symbol_query("Not", *symbs)
