"""Tokenizer.

Could parse:

::

    spaces:     ' '
    delimiter:   (   )
    keyword:     if  else
    node:        C  S1 S2

"""

from regex import regex_compile

space = regex_compile(r" ")
delimiter = regex_compile(r"\(|\)")
keyword = regex_compile(r"(if)|(else)")
node = regex_compile(r"(S1)|(S2)|C")


class Token:
    def __init__(self, typ, value):
        self.typ = typ
        self.value = value

    def __repr__(self):
        return '<token: {}.{} >'.format(self.typ, self.value)


def tokenizer(input_stream):
    """tokenizer.

    :param input_stream:
    :return:
    """
    def split(input_stream):
        """split stream to a list that contains valid symbols.

        :param input_stream: the input code string.
        :return: a list.
        """
        symbol = ''
        for i in input_stream:
            if space.match(i):
                # if has a valid symbol before space, save to list
                #  but do nothing with space itself
                if symbol:
                    yield symbol
                    symbol = ''
            elif delimiter.match(i):
                # need check whether there is a symbol
                if symbol:
                    yield symbol
                    symbol = ''
                # delimiter itself need to be added too
                yield i
            else:
                symbol += i
        # for the last symbol
        if symbol:
            yield symbol

    def token(value):
        if delimiter.match(value): return Token(value, value)
        elif keyword.match(value): return Token(value, value)
        elif node.match(value): return Token(value, value)
        else: raise RuntimeError('"{}" unexpected symbol'.format(value))

    l = split(input_stream)
    return map(token, l)


