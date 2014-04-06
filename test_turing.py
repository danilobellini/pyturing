#!/usr/bin/env py.test
# -*- coding: utf-8 -*-
# Created on Tue Mar  4 11:05:50 2014
# MIT Licensed. See COPYING.TXT for more information.
""" Turing machine internals testing module """

from __future__ import unicode_literals, print_function
from turing import (TMSyntaxError, TMLocked, pre_tokenizer, tokenizer,
                    raw_rule_generator, sequence_cant_have,
                    evaluate_symbol_query, TuringMachine)
from pytest import raises, mark
from types import GeneratorType
p = mark.parametrize


class TestPreTokenizer(object):

    def test_no_change(self):
        data = [
            "q1 1 -> P0 R q2",
            "   0 -> P1 q2",
            "q2",
            "  1 -> E L q1",
        ]
        gen = pre_tokenizer("\n".join(data))
        assert isinstance(gen, GeneratorType)
        assert list(gen) == data

    def test_empty_remove(self):
        data = [
            "q1", "",
            "  aba ",
            "-> ---", "  ",
        ]
        gen = pre_tokenizer("\n".join(data))
        assert isinstance(gen, GeneratorType)
        assert list(gen) == [el for el in data if el.strip()]

    def test_default_comment_remove(self):
        data = [
            "# 123",
            "q1 1 -> P0 q # R # q2",
            "  #", "",
            "     -> P1 # q2", "#",
            "q1 -", " ",
        ]
        expected = [
            "q1 1 -> P0 q ",
            "     -> P1 ",
            "q1 -",
        ]
        gen = pre_tokenizer("\n".join(data))
        assert isinstance(gen, GeneratorType)
        assert list(gen) == expected

    @p("comment_symbol", ["#", ";", "//", "--", "%"])
    def test_any_comment_remove(self, comment_symbol):
        data = [
            "{symbol}{symbol}{symbol}", "", "{symbol}",
            "q1{symbol}",
            "  {symbol}", "",
            "       ->{symbol}", " R{symbol} -> 2",
            "       q2  {symbol}", "",
            "A{symbol}B{symbol}C", "{symbol} ->",
        ]
        expected = [
            "q1",
            "       ->", " R",
            "       q2  ",
            "A",
        ]
        gen = pre_tokenizer("\n".join(data).format(symbol=comment_symbol),
                            comment_symbol=comment_symbol)
        assert isinstance(gen, GeneratorType)
        assert list(gen) == expected


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
        assert list(tokenizer("\n\n\n")) == ["\n"] == \
               list(tokenizer(""))       == list(tokenizer("\n \n  \n"))

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
        assert list(tokenizer(data)) == expected

    def test_single_mconf_in_first_line(self):
        data = (
            "A \n"
            "  b -> Pxx2 R E alpha\n"
        )
        expected = ["A", "b", "->", "Pxx2", "R", "E", "alpha", "\n",]
        assert list(tokenizer(data)) == expected

    def test_square_brackets_in_symbols(self):
        data = (
            "q1 \n"
            "  [0 4] -> Pinf R aba\n"
            "  [1 '2' 3] -> P-1 k\n"
            "  [xTj'c] -> P0\n ç  \n\n"
            "  - -> +"
        )
        expected = [ # The space is an indent token
            "q1", "[", "0", "4", "]", "->", "Pinf", "R", "aba", "\n",
            " ", "[", "1", "'2'", "3", "]", "->", "P-1", "k", "\n",
            " ", "[", "xTj'c", "]", "->", "P0", "ç", "\n",
            " ", "-", "->", "+", "\n",
        ]
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
    def test_one_and_an_arrow_only_rule(self, rule):
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

    def test_group_rules(self):
        rgen = raw_rule_generator("\n".join([
            "A",
            "  0 -> P1 R",
            "       P1 R B",
            "B",
            "  0 -> P0 R C",
            "  1 -> P0 L A",
            "C",
            "  -> P1 B",
        ]))
        assert next(rgen) == (["A", "0"], ["P1", "R", "P1", "R", "B"])
        assert next(rgen) == (["B", "0"], ["P0", "R", "C"])
        assert next(rgen) == ([" ", "1"], ["P0", "L", "A"])
        assert next(rgen) == (["C"], ["P1", "B"])
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

    def test_empty_query(self):
        assert evaluate_symbol_query() == (tuple(), False)


class TestTuringMachine(object):

    @p("tape_list", [
        [], ["A"], ["1", "2"], ("1", "2", "3"),
    ])
    def test_tape_simple_assignment_without_blank(self, tape_list):
        tape_dict = dict(enumerate(tape_list))
        tm_list = TuringMachine() # Without rules
        tm_dict = TuringMachine()
        assert tm_list.index == tm_dict.index == 0
        assert tm_list.tape == tm_dict.tape == {}
        tm_list.tape = tape_list
        tm_dict.tape = tape_dict
        assert tm_list.index == tm_dict.index == 0
        assert tm_list.tape == tm_dict.tape == tape_dict
        for symbol in tape_list:
            assert tm_list.scan() == tm_dict.scan() == symbol
            tm_list.perform("R")
            tm_dict.perform("R")

    def test_tape_str_assignment(self):
        tm = TuringMachine() # Without rules
        tape = __import__("string").ascii_letters
        tm.tape = tape
        assert tm.tape == dict(enumerate(tape))
        for symbol in tape:
            assert tm.scan() == symbol
            tm.perform("R")

    @p("blank_index", [0, 1, 3, 27, -1, -5])
    def test_tape_list_assignment_with_blank(self, blank_index):
        tm = TuringMachine() # Without rules
        tape = list(__import__("string").ascii_letters)
        tape[blank_index] = "None"
        expected_tape = {k: v for k, v in enumerate(tape)
                              if k != blank_index % len(tape)}
        tm.tape = tape
        assert len(tm.tape) == len(tape) - 1
        assert tm.tape == expected_tape
        for symbol in tape:
            assert tm.scan() == symbol
            tm.perform("R")

    @p("blank_index", [0, 3, 27, -1])
    @p("delta", [-2, -1, 0, 1, 2])
    def test_tape_dict_assignment(self, blank_index, delta):
        tm = TuringMachine() # Without rules
        tape = list(__import__("string").ascii_letters)
        tape[blank_index] = "None"
        expected_tape = {k + delta: v for k, v in enumerate(tape)
                                      if k != blank_index % len(tape)}
        tape_dict = dict(enumerate(tape, delta))
        tm.tape = tape_dict
        assert tm.tape == expected_tape
        assert tm.index == 0
        assert tm.scan() == tape[-delta] if delta <= 0 else "None"
        for task in delta * "R" + -delta * "L":
            tm.perform(task)
        assert tm.index == delta
        for symbol in tape:
            assert tm.scan() == symbol
            tm.perform("R")

    @p(("task", "index_delta", "tape_list_before", "tape_dict_after"), [
        ("L", -1, [], {}),
        ("R",  1, [], {}),
        ("N",  0, [], {}),
        ("L", -1, ["A"], {0: "A"}),
        ("R",  1, ["A"], {0: "A"}),
        ("N",  0, ["A"], {0: "A"}),
        ("PNone", 0, [], {}),
        ("PNone", 0, ["A"], {}),
        ("P1", 0, [], {0: "1"}),
        ("P1", 0, ["A"], {0: "1"}),
    ])
    def test_perform_one_task(self, task, index_delta,
                                    tape_list_before, tape_dict_after):
        tm = TuringMachine() # Without rules
        assert tm.index == 0
        assert tm.tape == {}
        tm.tape = tape_list_before
        assert tm.tape == dict(enumerate(tape_list_before))
        tm.perform(task)
        assert tm.index == index_delta
        assert tm.tape == tape_dict_after

    def test_one_rule_no_tape(self):
        tm = TuringMachine("q4 -> q3")
        assert tm.mconf == "q4" # First m-conf in code is first in simulation
        tm.move()
        assert tm.mconf == "q3"
        with raises(TMLocked):
            tm.move()

    def test_two_rules_no_tape(self):
        tm = TuringMachine("a -> b\nb None -> R c\n")
        assert tm.mconf == "a"
        tm.move()
        assert tm.mconf == "b"
        assert tm.scan() == "None"
        tm.move()
        assert tm.mconf == "c"
        with raises(TMLocked):
            tm.move()

    def test_zero_one_zero_one(self):
        tm = TuringMachine(
            "a -> P0 R b\n"
            "b -> P1 R a\n"
        )
        for unused in range(40):
            assert tm.mconf == "a"
            tm.move()
            assert tm.mconf == "b"
            tm.move()
        tape = tm.tape
        assert len(tape) == 80
        for idx in range(80):
            assert tape[idx] == str(idx % 2)

    def test_turing_first_example(self):
        tm1 = TuringMachine( # On p. 233 of his article
            "b None -> P0  R c\n"
            "c None ->   R   e\n"
            "e None -> P1  R f\n"
            "f None ->   R   b\n"
        )
        tm2 = TuringMachine( # On p. 234 of his article, the same idea
            "b None ->   P0   b\n"
            "     0 -> R R P1 b\n"
            "     1 -> R R P0 b\n"
        )
        assert tm1.mconf == tm2.mconf == "b"
        assert tm1.index == tm2.index == 0
        tm1.move() # Syncronizing them
        tm2.move()
        for idx in range(50):
            assert tm2.mconf == "b"

            assert tm1.index == 2 * idx + 1
            tm1.move()
            assert tm1.index == 2 * idx + 2
            tm1.move()
            assert tm1.index == 2 * idx + 3

            assert tm2.index == 2 * idx
            tm2.move()
            assert tm2.index == 2 * idx + 2

            assert tm1.tape == tm2.tape

        tape = tm1.tape
        tape_length = abs(max(tm1.tape) - min(tm1.tape))
        assert tape_length == 100
        for idx in range(100):
            if idx % 2 == 0:
                assert tape[idx] == str(idx // 2 % 2)
            else:
                assert idx not in tape # "None"

    @p("binary_number_string", ["0011", "010", "10", "110", "11", "0", "111",
                                "101", "111100", "1010"])
    def test_mod_3_equals_zero(self, binary_number_string):
        code = "\n".join(
             # Starting with an empty tape, adds the digits to the tape
            ["pre-start -> L"] +
            ["             R P{}".format(el) for el in binary_number_string] +
            ["             goto-start",

             # Go back with the "cursor" to the first symbol in tape
             "goto-start",
             "  None -> R start",
             "       -> L goto-start",

             # Starts with zero in mind, so modulo is zero
             "start -> mod0",

             # Every digit d appended to x makes the new number y = x * 2 + d,
             # and the same follows in modulo 3
             "mod0",
             "  0    -> R mod0",
             "  1    -> R mod1",
             "  None -> L return_T",
             "mod1",
             "  0    -> R mod2",
             "  1    -> R mod0",
             "  None -> L return_F",
             "mod2",
             "  0    -> R mod1",
             "  1    -> R mod2",
             "  None -> L return_F",

             # Clears the tape and "prints" to it the desired result
             "return_T",
             "  [0 1] -> E L return_T",
             "  None  -> R PT loop",
             "return_F",
             "  [0 1] -> E L return_F",
             "  None  -> R PF loop",

             # Deadlock
             "loop -> loop",
            ]
        )

        number = int(binary_number_string, base=2)
        all_numbers_tape = dict(enumerate(binary_number_string))
        result = "T" if number % 3 == 0 else "F"
        tm = TuringMachine(code)
        print(code)
        assert tm.tape == {}
        assert tm.index == 0
        assert tm.mconf == "pre-start"

        # Puts the digits into the machine
        tm.move()
        assert tm.tape == all_numbers_tape
        assert tm.index == len(binary_number_string) - 1
        assert tm.mconf == "goto-start"

        # Go back to the beginning
        for digit in reversed(binary_number_string):
            assert tm.scan() == digit
            old_idx = tm.index
            tm.move()
            assert tm.tape == all_numbers_tape
            assert tm.index == old_idx - 1
            assert tm.mconf == "goto-start"
        assert tm.scan() == "None"
        assert tm.index == -1
        tm.move()
        assert tm.tape == all_numbers_tape
        assert tm.index == 0
        assert tm.mconf == "start"

        # Initialization
        tm.move()
        assert tm.tape == all_numbers_tape
        assert tm.index == 0
        assert tm.mconf == "mod0"

        # Follow the digits
        mod_value = 0
        for idx, digit in enumerate(binary_number_string, 1):
            assert tm.scan() == digit
            tm.move()
            mod_value = (mod_value * 2 + int(digit, base=2)) % 3
            assert tm.tape == all_numbers_tape
            assert tm.index == idx
            assert tm.mconf == "mod{}".format(mod_value)

        # After last digit
        return_mconf = "return_" + result
        assert tm.scan() == "None"
        tm.move()
        assert tm.tape == all_numbers_tape
        assert tm.index == len(binary_number_string) - 1
        assert tm.mconf == return_mconf

        # Erases digit per digit
        for digit in reversed(binary_number_string):
            assert tm.scan() == digit
            old_idx = tm.index
            tm.move()
            assert tm.tape == {k: v for k, v in all_numbers_tape.items()
                                    if k < old_idx}
            assert tm.index == old_idx - 1
            assert tm.mconf == return_mconf

        # Returns!
        assert tm.scan() == "None"
        for unused in range(5):
          tm.move()
          assert tm.tape == {0: result}
          assert tm.index == 0
          assert tm.mconf == "loop"
