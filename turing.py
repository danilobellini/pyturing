# -*- coding: utf-8 -*-
# Created on Tue Mar  4 11:05:22 2014
# MIT Licensed. See COPYING.TXT for more information.
""" Turing machine module, for source parsing and simulation """

from __future__ import unicode_literals
import re

__all__ = ["TMSyntaxError", "tokenizer", "raw_rule_generator"]

class TMSyntaxError(SyntaxError):
    """ Syntax errors for a Turing machine code (rules description) """

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
        blocks.extend(re.findall("->|\S+", line))
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

