import queue
from typing import Set
from tokenizer import Token

grammar = [("startsup", ("start", )),
           ("start", ("stmt", )),
           ("stmt", ("if", "(", "C", ")", "S1", "else", "S2")),
          ]
terminals = ("if", "(", "C", ")", "S1", "else", "S2", '$')
n_terminals = ("startsup", "start", "stmt")
all_symbols = terminals + n_terminals


class Item(object):
    """The Canonical LR(1) Item definition.

    :param symbol: str, the left part of production.
    :param body: str, the right part of production.
    :param dot: int, current position in the item.
    :param follow: str, possible input for the current configuration.
    """

    def __init__(self, symbol, body, dot, follow):
        self.symbol = symbol
        self.body = body
        self.pos = dot
        self.follow = follow

    def __str__(self):
        p = list(self.body)
        p.insert(self.pos, '◆')
        pr = ' '.join(p)
        return "[{}]  {} -> {}".format( self.follow, self.symbol, pr)

    def __repr__(self):
        return "<Item:{} >\n".format(self.__str__())

    def __eq__(self, other):
        if isinstance(other, Item):
            return ((self.symbol == other.symbol) and
                    (self.body == other.body) and
                    (self.pos == other.pos) and
                    (self.follow == other.follow))
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.__str__())


class Closure(object):
    def __init__(self, sets: Set[Item], label: int = None):
        self.label = label
        self.sets = sets
        self.goto = dict()  # type: dict[str, int]

    def __len__(self):
        return len(self.sets)

    def __iter__(self):
        return self.sets.__iter__()

    def __str__(self):
        return "\n".join([i.__str__() for i in self.sets])

    def __repr__(self):
        return "<Closure>:{}\n{}\n</Closure>\n".format(self.label,
                                                       self.__str__())

    def __eq__(self, other):
        return self.sets == other.sets

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.__str__())

    def __contains__(self, item):
        return item in self.sets


def isnterm(symbol):
    return symbol in n_terminals


def isterm(symbol):
    return symbol in terminals


def produce_epsilon(none_terminal):
    return 'EPSILON' in [i[1] for i in grammar if i[0] == none_terminal]


def first(symbol):
    """Return the first terminal sets that may occur in the Symbol."""
    first_sets = set()
    if isterm(symbol):
        return set(symbol)
    elif produce_epsilon(symbol):
        first_sets = first_sets.union('EPSILON')
    elif isnterm(symbol):
        for i in grammar:
            if i[0] == symbol:
                body = i[1]
                epsilons = True
                current = 0
                while epsilons is True and current < len(body):
                    if body[current] != symbol:
                        first_sets = first_sets.union(first(body[current]))
                    if not produce_epsilon(body[current]):
                        epsilons = False
                    current += 1
    return first_sets


def firsts(suffix):
    if len(suffix) == 1:
        return first(suffix[0])
    else:
        if not produce_epsilon(suffix[0]):
            return first(suffix[0])
        else:
            return first(suffix[0]).union(firsts(suffix[1:]))


def get_closure(cl: Closure, label: int) -> Closure:
    """get all Item of a Closure from given Items, by adding implied Items.

    The implied Items are the productions of the None terminals after the
    current position, which put a dot on the head."""
    def get_nterm(item):
        pos, prod = (item.pos, item.body)
        if pos < len(prod):
            symbol = prod[pos]
            if isnterm(symbol):
                return symbol
        return None
    item_set = set()
    q = queue.Queue()
    for i in cl.sets:
        item_set.add(i)
        q.put(i)
    while not q.empty():
        item = q.get()
        symbol = get_nterm(item)
        if symbol:
            products = [i for i in grammar if i[0] == symbol]
            suffix = item.body[item.pos+1:] + tuple(item.follow)
            termins = firsts(suffix)
            for product in products:
                for terminal in termins:
                    new_item = Item(symbol, product[1], 0, terminal)
                    if new_item not in item_set:
                        item_set.add(new_item)
                        q.put(new_item)
    c = Closure(item_set, label)
    return c


def goto(clos: Closure, letter: str) -> Closure:
    """a closure that could get from the current closure by input a letter.

    :param clos: the current closure.
    :param letter: the input letter.
    :return: Closure.
    """
    item_set = set()
    for item in clos.sets:
        dot, prod = (item.pos, item.body)
        if dot < len(prod) and prod[dot] == letter:
            new_item = Item(item.symbol,
                            item.body,
                            item.pos + 1,
                            item.follow)
            item_set.add(new_item)
    c = Closure(item_set)
    return get_closure(c, label=None)


def closure_groups():
    def find_label(closure, group):
        for i in group:
            if closure == i:
                return i.label
        return None
    group = set()
    label = 0
    start_item = Item('startsup', ('start',), 0, '$')
    start = get_closure(Closure({start_item}), label)
    q = queue.Queue()
    q.put(start)
    group.add(start)
    while not q.empty():
        c = q.get()
        for literal in all_symbols: # terminals + n_terminals:
            go_clos = goto(c, literal)
            if go_clos:
                if go_clos not in group:
                    label += 1
                    go_clos.label = label
                    q.put(go_clos)
                    group.add(go_clos)
                    c.goto[literal] = label
                    # print('add closure', go_clos)
                else:
                    go_label = find_label(go_clos, group)
                    if go_label:
                        c.goto[literal] = go_label
    return group


def get_states_map(closure_group):
    def get_state_map(closure):
        """ table row like all_symbols list state maps."""
        row = ["." for i in all_symbols]
        # None terminals GOTO action and Terminals shift action.
        for input, goto_label in closure.goto.items():
            row_pos = all_symbols.index(input)
            for item in closure:
                if item.pos < len(item.body):      # shape like [A -> ⍺.aβ b]
                    if item.body[item.pos] == input:
                        # None terminals GOTO state
                        if input in n_terminals:
                            row[row_pos] = str(goto_label)
                        # Terminals action shift state
                        elif input in terminals:
                            row[row_pos] = "s" + str(goto_label)
        # Terminals reduce action. shape like  [A -> ⍺.  a]
        for row_pos, input in enumerate(all_symbols):
            for item in closure:
                if item.pos == len(item.body) and \
                        item.follow == input and \
                        item.symbol != 'startsup':
                    production_num = grammar.index((item.symbol, item.body))
                    row[row_pos] = 'r' + str(production_num)
        # accept condition 'startsup -> start. , $'
        acc_item = Item('startsup', ('start',), 1, '$')
        if acc_item in closure:
            input = '$'
            row_pos = all_symbols.index('$')
            row[row_pos] = '$'
        return row

    state_map = [None for i in range(len(closure_group))]
    for closure in closure_group:
        row = get_state_map(closure)
        state_map[closure.label] = row
    return state_map


def generate_syntax_table():
    g = closure_groups()
    state_map = get_states_map(g)
    return state_map


class SDT:
    def __init__(self):
        self.syntax_table = generate_syntax_table()
        self.state_stack = [0]
        self.accept = False

    def get_action(self, state, literal):
        return self.syntax_table[state][all_symbols.index(literal)]

    def ahead(self, token):
        action = self.get_action(self.state_stack[-1], token.typ)
        # shift action push a current state into state_stack
        if action[0] == 's':
            current_state = int(action[1:])
            self.state_stack.append(current_state)
        elif action[0] == '$':
            self.accept = True   # success
        # reduce action reduct a production and push
        elif action[0] == 'r':
            # get the production in grammar
            number = int(action[1:])
            production = grammar[number]
            head, body = production
            # pop the states of production body
            for _ in body:
                self.state_stack.pop()
            # push the state of head GOTO(I,X)
            state = self.get_action(self.state_stack[-1], head)
            self.state_stack.append(int(state))

            # reduce actions does not consume a token,
            # only when shifting, a token was consume and passed
            self.ahead(token)
        else:
            raise SyntaxError(f"Not a correct token '{token.__str__()}'.")

    def parse(self, token_stream):
        while True:
            try:
                token = next(token_stream)
                self.ahead(token)
            except StopIteration:
                # patch "$" in the end of token stream
                # to match the augmented grammar
                self.ahead(Token("$", "$"))
                break


if __name__ == "__main__":
    g = closure_groups()
    state_map = get_states_map(g)
    args = ''.join(list(map(lambda x: '{:'+str(max(5, len(x)+2))+'s}',
                            all_symbols)))
    s = "{:10s}" + args
    head = ['state', ] + list(all_symbols)
    print(s.format(*head))
    for j, i in enumerate(state_map):
        state = [str(j), ] + i
        print(s.format(*state))
