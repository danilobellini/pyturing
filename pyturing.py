# -*- coding: utf-8 -*-
# Created on Tue Mar  4 11:05:22 2014
# MIT Licensed. See COPYING.TXT for more information.
""" Turing machine module, for source parsing and simulation """

from __future__ import unicode_literals, print_function
from functools import wraps
from collections import OrderedDict
import re

__all__ = ["TMSyntaxError", "TMLocked", "pre_tokenizer", "tokenizer",
           "raw_rule_generator", "sequence_cant_have",
           "evaluate_symbol_query", "config_parser",
           "action_parser", "TuringMachine"]

__version__ = "0.1dev"


class TMSyntaxError(SyntaxError):
    """ Syntax errors for a Turing machine code (rules description) """


class TMLocked(Exception):
    """ No action assigned to current configuration, the machine is locked """


def pre_tokenizer(data, comment_symbol="#"):
    """
    Line generator that removes empty lines and comments from the given
    multiline string.
    """
    for line_raw in data.splitlines():
        line = line_raw.split(comment_symbol, 1)[0]
        if line.rstrip():
            yield line


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
    for line in pre_tokenizer(data):
        keep_last = line.startswith(" ")
        if "->" in blocks and ("->" in line or not keep_last):
            for token in blocks:
                yield token
            blocks = ["\n"]
            if keep_last:
                blocks.append(" ")
        elif keep_last and not blocks: # Corner case (starting with an space)
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
    if config or block is action:
        raise TMSyntaxError("Incomplete rule (unexpected end of tokens)")


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
    <task> ::= {"L" | "R" | "P" <id> | "E" | "N" | "PNone"}

    The "P" (for the printing task) isn't separated from the <id> by the
    tokenizer. See TuringMachine.perform for more information about the tasks.
    """
    return args[:-1], args[-1]


class TuringMachine(OrderedDict):
    """
    Turing a-machine (automatic-machine) based on his model from "On
    computable numbers, with an application to the Entscheidungsproblem"
    (1936).
    """
    def __init__(self, data=""):
        """
        Constructor from the raw string data with the rules.
        The starting complete configuration is:

        - self.index = 0
        - self.tape = []
        - self.mconf = First m-configuration in data (machine source)

        If data is empty (no rule is given), self.mconf isn't initialized,
        and should be assigned before any rule querying self[m_conf, symbol]
        and before any self.move() call.
        """
        super(TuringMachine, self).__init__()
        self._tape = {} # Tape is a dictionary whose keys are integers
        self.index = 0 # Starting index in tape
        self.inv_dict = OrderedDict() # "Inverse" rules ("Not" and blank),
                                      # with lower priority
        quad_gen = (config_parser(*config) + action_parser(*action)
                    for config, action in raw_rule_generator(data))
        last_m = ""
        for mconfs_in, symbols_in, tasks, mco in quad_gen:
            # Rule m-configuration determination
            if mconfs_in == (" ",):
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

    @property
    def tape(self):
        return self._tape

    @tape.setter
    def tape(self, value):
        if isinstance(value, dict):
            self._tape = {k: v for k, v in value.items() if v != "None"}
        else:
            self._tape = {k: v for k, v in enumerate(value) if v != "None"}

    def scan(self):
        """
        Returns the current symbol as a string, or "None".

        Perform one rule in the machine, changing its current
        configuration (self.mconf and self.index) accordingly.
        """
        return self.tape.get(self.index, "None")

    def print(self, symbol):
        """
        Perform a print task, printing the given symbol in the tape, or
        erasing if symbol is "None".
        """
        if symbol == "None":
            if self.index in self.tape:
                del self.tape[self.index]
        else:
            self.tape[self.index] = symbol

    def perform(self, task):
        """
        Perform one single task in the Turing machine, given the task string.
        The operations are "P", "E", "L", "R" and "N", following [P]rint,
        [E]rase, [L]eft, [R]ight and [N]o operation. The "P" operation should
        be followed with the symbol to be print, such as "P1" to print "1".
        """
        if task == "R": # Right
            self.index += 1
        elif task == "L": # Left
            self.index -= 1
        elif task == "E": # Erase
            self.print("None")
        elif task.startswith("P"): # Print
            self.print(task[1:])
        elif task == "N": # No operation (used for "not left nor right")
            pass
        else:
            raise ValueError("Unknown task")

    def move(self):
        """
        Perform one rule in the machine, changing its complete configuration
        (self.index, self.tape and self.mconf) where needed, accordingly.
        """
        tasks, mco = self[getattr(self, "mconf", None), self.scan()]
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

    def copy(self):
        """
        Returns a shallow copy of this Turing Machine, but with a complete
        configuration (self.index, self.mconf and self.tape) copy (including
        the tape).
        """
        tm = TuringMachine()

        # Copy the rules
        tm.update(self)
        tm.inv_dict.update(self.inv_dict)

        # Copy the complete configuration
        tm.index = self.index
        if hasattr(self, "mconf"):
            tm.mconf = self.mconf
        tm.tape = self.tape

        return tm
