"""regex_compile a regex pattern to an nfa machine.

"""

import re
import string

from regex.parsing_table import (semantic, all_symbols, grammar,
                                  generate_syntax_table)
from regex.graph import Machine
from regex.regex_nfa import induct_star, induct_or, induct_cat, basis

class EscapeError(Exception):
    pass

class Lexeme:
    """lexeme contains value and type."""

    def __init__(self, lextype, letter):
        self.value = letter
        self.type = lextype


class Lexer:
    """parse a letter and return a lexeme."""

    def __init__(self, stream):
        self.stream = list(stream)

    def get_lexeme(self):
        try:
            letter = self.stream.pop(0)
            if letter == "\\":
                letter = self.stream.pop(0)
                if letter in "()|*$":
                    return Lexeme("a", letter)
                else:
                    raise EscapeError("is not an Escape character \{}".format(letter))
            elif letter in "()|*":
                return Lexeme(letter, letter)
            else:
                return Lexeme('a', letter)
        except IndexError:
            raise IndexError
        except EscapeError as e:
            raise EscapeError(e)


class RegexCompiler:
    """Regex compiler reads a regex pattern, and return an nfa Machine of graph.


    """

    def __init__(self):
        self.syntax_table = generate_syntax_table()
        self.state_stack = [0]
        self.arg_stack = []
        self.literal_machine = ""

    def parse(self, stream):
        lexer = Lexer(stream)
        while True:
            try:
                lexeme = lexer.get_lexeme()
                self.ahead(lexeme.type, lexeme.value)
            except IndexError:
                lexeme = Lexeme("$", "$")
                self.ahead(lexeme.type, lexeme.value)
                break
            except EscapeError as e:
                raise EscapeError(e)

    def get_action(self, state, literal):
        return self.syntax_table[state][all_symbols.index(literal)]

    def ahead(self, literal, value=None):
        action = self.get_action(self.state_stack[-1], literal)
        if action[0] == 's':  # shift action
            self.state_stack.append(int(action[1:]))
            if literal == 'a':
                self.arg_stack.append(value)
        elif action[0] == '$':
            machine_literal = self.arg_stack.pop()
            self.literal_machine = machine_literal
            # success
        elif action[0] == 'r':
            number = int(action[1:])
            production = grammar[number]
            head = production[0]
            body = production[1]
            for _ in body:
                self.state_stack.pop()
            state = self.get_action(self.state_stack[-1], head)
            self.state_stack.append(int(state))

            # translations
            args = []
            for i in re.findall(r"{}", semantic[number]):
                arg = self.arg_stack.pop()
                args.insert(0, arg)
            translation = semantic[number].format(*args)
            self.arg_stack.append(translation)

            self.ahead(literal, value)


def regex_compile(regex):
    a = RegexCompiler()
    a.parse(regex)
    m = eval(a.literal_machine)
    m.sort_state_names()
    return Machine(m)


if __name__ == "__main__":
    import sys
    import warnings

    if not sys.warnoptions:  # allow overriding with `-W` option
        warnings.filterwarnings('ignore', category=RuntimeWarning)

    a = regex_compile("ab\**c*d(e|f)ka*z")
    a.show()
