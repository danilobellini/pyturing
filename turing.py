# -*- coding: utf-8 -*-
# Created on Tue Mar  4 11:05:22 2014
# MIT Licensed. See COPYING.TXT for more information.
""" Turing machine module, for source parsing and simulation """

from __future__ import unicode_literals
from functools import wraps
import re

__all__ = ["TMSyntaxError", "tokenizer", "raw_rule_generator",
           "sequence_cant_have", "evaluate_symbol_query"]


class TMSyntaxError(SyntaxError):
    """ Syntax errors for a Turing machine code (rules description) """


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
        return [], False # Everything as "not nothing"
    if args[0] == "Not":
        if len(args) == 1:
            raise TMSyntaxError("Missing symbols for the 'Not' keyword")
        return find_tuple_of_symbols_without_not(args[1:]), False
    return find_tuple_of_symbols_without_not(args), True
