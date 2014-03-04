# -*- coding: utf-8 -*-
# Created on Tue Mar  4 11:05:22 2014
# MIT Licensed. See COPYING.TXT for more information.
""" Turing machine module, for source parsing and simulation """

from __future__ import unicode_literals
from functools import wraps
from collections import OrderedDict
import re

__all__ = ["TMSyntaxError", "TMLocked", "tokenizer", "raw_rule_generator",
           "sequence_cant_have", "evaluate_symbol_query", "config_parser",
           "action_parser", "TuringMachine"]


class TMSyntaxError(SyntaxError):
    """ Syntax errors for a Turing machine code (rules description) """


class TMLocked(Exception):
    """ No action assigned to current configuration, the machine is locked """


TOKENIZER_REGEX = re.compile(
    "\[|\]"       # Single character special tokens
    "|->"         # Two character special token
    "|[^\s\[\]]+" # Identifiers and reserved words
)


def tokenizer(data):
    """
    Lexical tokenizer for raw text data containing Turing machine rules.
    """
    blocks = []
    for line in data.splitlines():
        if "->" in blocks and "->" in line:
            for token in blocks:
                yield token
            blocks = ["\n"]
            if line[0] == " ":
                blocks.append(" ")
        blocks.extend(re.findall(TOKENIZER_REGEX, line))
    for token in blocks:
        yield token
    yield "\n"


def raw_rule_generator(data):
    """
    Generator for pairs (config, action), following

    <rule> ::= <config> "->" <action> "\n"

    Also ensures that neither the config nor the action should be empty, raising
    TMSyntaxError when that happens.
    """
    config, action = [], []
    block = config
    for token in tokenizer(data):
        if token == "->":
            block = action
        elif token == "\n":
            if action:
                if not config:
                    raise TMSyntaxError("Incomplete rule (missing config)")
                yield config, action
                config, action = [], []
                block = config
            elif config:
                raise TMSyntaxError("Incomplete rule (missing action)")
            elif block is action:
                raise TMSyntaxError("Incomplete rule")
        else:
            block.append(token)
    if block is action:
        raise TMSyntaxError("Incomplete rule at the end of file")


def sequence_cant_have(*invalids):
    """
    Parametrized decorator for raising a TMSyntaxError when invalid symbols
    are found in the resulting sequence of the decorated function.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            for el in result:
                if el in invalids:
                    raise TMSyntaxError("Invalid use of the '{}' "
                                        "symbol".format(el))
            return result
        return wrapper
    return decorator


def evaluate_symbol_query(*args):
    """
    Validate the symbol query and returns a tuple (tuple of symbols,
    presence). The presence boolean (flag) is True when the query acts in
    the presence of the symbols in the list, and false when the query acts
    in the absence of the symbols in the list.

    Turing model doesn't include an absence query per se, but such an
    expression was used by him in his tables, mainly for defining his
    m-functions without having to enumerate all "other" symbols of the
    given alphabet. Storing the absence query allows one to use that
    resource without having to care about how many symbols are in the
    alphabet for a given use of the machine.
    """
    @sequence_cant_have("Not", "[", "]")
    def find_tuple_of_symbols_without_not(fargs):
        if len(fargs) == 1:
            return fargs
        if len(fargs) == 2 or fargs[0] != "[" or fargs[-1] != "]":
            raise TMSyntaxError("Invalid grouping of symbols")
        return fargs[1:-1]

    if not args:
        return tuple(), False # Everything as "not nothing"
    if args[0] == "Not":
        if len(args) == 1:
            raise TMSyntaxError("Missing symbols for the 'Not' keyword")
        return find_tuple_of_symbols_without_not(args[1:]), False
    return find_tuple_of_symbols_without_not(args), True


def config_parser(*args):
    """
    <config> ::= <m-confs> <symbols>
    <m-confs> ::= " " | <id> | "[" <id> {<id>} "]"
    <symbols> ::= [["Not"] (<id> | "[" <id> {<id>} "]")]

    Empty spaces in <m-confis> means "keep the previous input m-configuration
    list <m-confs>". Both "None" and "Any", as symbol <id>s, have special
    meaning: a the "blank"/empty square and a non-"blank"/non-empty square,
    respectively.
    """
    if len(args) == 1:
      return args, []
    return args[:1], args[1:] # For now, only a single m-conf


def action_parser(*args):
    """
    <action> ::= <behaviour> <m-conf>
    <behaviour> ::= {<task>}
    <m-conf> ::= <id>
    <task> ::= {"L" | "R" | "P" <id> | "E" | "PNone"}

    The "P" (for the printing task) isn't separated from the <id> by the
    tokenizer.
    """
    return args[:-1], args[-1]


class TuringMachine(OrderedDict):
    """
    Turing a-machine (automatic-machine) based on his model from "On
    computable numbers, with an application to the Entscheidungsproblem"
    (1936).
    """
    def __init__(self, data):
        """
        Constructor from the raw string data with the rules.
        """
        super(TuringMachine, self).__init__()
        self.inv_dict = OrderedDict() # "Inverse" rules ("Not" and blank),
                                      # with lower priority
        quad_gen = (config_parser(*config) + action_parser(*action)
                    for config, action in raw_rule_generator(data))
        last_m = ""
        for mconfs_in, symbols_in, tasks, mco in quad_gen:

            # Rule m-configuration determination
            if mconfs_in == " ":
                if last_m:
                    mconfs_in = last_m
                else:
                    raise TMSyntaxError("Missing m-configuration in "
                                        "the first rule")
            else:
                if not last_m and not hasattr(self, "mconf"):
                    self.mconf = mconfs_in[0] # 1st m-config. is from 1st rule
                last_m = mconfs_in

            # Rule storage
            for mci in mconfs_in:
                symbs, presence = evaluate_symbol_query(*symbols_in)
                act = (tasks, mco)
                if presence:
                    for s in symbs:
                        self.setdefault((mci, s), act) # Changes only if unset
                else:
                    self.inv_dict.setdefault(mci, []).append((symbs, act))

    def read(self):
        return "None" # Still there's no tape to read

    def perform(self, task):
        return NotImplemented

    def move(self):
        tasks, mco = self[self.mconf, self.read()]
        for task in tasks:
            self.perform(task)
        self.mconf = mco

    def __missing__(self, key):
        mci, symb = key
        if mci in self.inv_dict:
            for symbs, act in self.inv_dict[mci]:
                if symb not in symbs:
                    return act
        raise TMLocked("No rule found for the current configuration")

