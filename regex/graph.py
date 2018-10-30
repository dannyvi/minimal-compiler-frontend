"""Provides a mechanism for NFA state machine construction and visualizing.

State is a circle with a number as name.

Path is a line links two states with direction, from start point to end point
via a label, which means the input letter.

Graph contains States and Path, which forms the state map. It transfers the map
to digraph by graphviz language. and show visualization by generating picture.

Machine constructs and runs upon the Graph. it could calculate the current
ε_closure. and judge whether machine is finished.

"""

import queue
import string
import random
import subprocess
from PIL import Image
from functools import reduce


epsilon = "ε"


def is_epsilon(label):
    return label == epsilon


class NotMatchException(Exception):
    pass


class State(object):
    """A container that includes the state name."""

    def __init__(self, number: int = None):
        self.number = number

    def __eq__(self, other):
        return id(self) == id(other)

    def __str__(self):
        return str(self.number)

    def __repr__(self):
        return str(self.number)

    def __hash__(self):
        return hash(id(self))

    def rename(self, number):
        self.number = number


class Path:
    """Draw a base nfa path."""

    def __init__(self, begin: State, end: State, label: str):
        self.begin = begin
        self.end = end
        self.label = label

    def __str__(self):
        return "{} {} {}".format(self.begin, self.end, self.label)

    def __repr__(self):
        return "<{} -> {}> {}".format(self.begin, self.end, self.label)


class Graph:
    """A graph helps construct an nfa machine.

    Contains Paths, Start state, End state.

    :param paths: a list with Path type elements.
    :param init: the init State type object.
    :param finish: the finished State type object.
    """

    def __init__(self, paths, start, finish):
        self.paths = paths
        self.start = start
        self.finish = finish

    def get_states(self):
        """Get all states in every path in the graph."""
        states = set()
        for path in self.paths:
            states.add(path.begin)
            states.add(path.end)
        return states

    def alter_init_state(self, state):
        """Move init state to other state. Intended to concat two graphs."""
        for i in self.paths:
            if i.begin is self.start:
                i.begin = state
            elif i.end is self.start:
                i.end = state
        self.start = state

    def get_dot_content(self):
        """generate dot file content in a list."""
        digraph = []
        header = 'digraph state_machine {'
        enclose = '}'
        declarations = ['node [shape="circle"];', 'rankdir=LR;']
        digraph.append(header)
        digraph = digraph + declarations
        states = self.get_states()
        digraph.append('StartArrow [style = invis];')
        for state in states:
            if state == self.finish:
                s = '{} [shape = "doublecircle"];'
                digraph.append(s.format(state))
            else:
                digraph.append("{};".format(state))
        s = 'StartArrow -> {} [label="start"];'
        digraph.append(s.format(self.start))
        for path in self.paths:
            s = '{} -> {} [label="{}"];'
            digraph.append(s.format(path.begin, path.end, path.label))
        digraph.append(enclose)
        return digraph

    def _compile_digraph(self):
        """write dot file, regex_compile with graphviz dot and make a png
        picture."""
        # dot file
        digraph = self.get_dot_content()
        filename = ''.join(random.choices(string.ascii_uppercase +
                                          string.digits, k=6))
        with open('/tmp/' + filename + '.dot', 'w', encoding='utf-8') as f:
            f.writelines(["%s\n" % line for line in digraph])
        # regex_compile to png
        output = "/tmp/" + filename + ".png"
        dot_file = "/tmp/" + filename + ".dot"
        subprocess.call(["dot", "-Tpng", "-o", output, dot_file])
        return output

    def show(self):
        """Show a picture of this graph."""
        image_file = self._compile_digraph()
        im = Image.open(image_file)
        im.show()

    def sort_state_names(self):
        # map(lambda x: x.rename(0), self.get_states())
        visited = set()
        self.start.rename(1)
        name = 2
        q = queue.Queue()
        q.put(self.start)
        while not q.empty():
            u = q.get()
            forwards = [p.end for p in self.paths if p.begin is u]
            for v in forwards:
                if v not in visited:
                    v.rename(name)
                    name += 1
                    visited.add(v)
                    q.put(v)


class Machine(Graph):
    """Machine provides mechanism of running an input stream.

    Machine has a current state represented as ε-closure, which was initiated
    to a start state. Each time an input will step the state forward. If the
    input reached the end, then check that whether the finish state is in the
    closure. If so, then return success, else the input fails to pass in this
    machine.
    """

    def __init__(self, graph):
        """initialize from graph."""
        super(Machine, self).__init__(graph.paths, graph.start, graph.finish)
        self.current = self.e_closure({self.start, })

    @classmethod
    def frompaths(cls, paths, init, finish):
        """initialize from paths, init state and finish state."""
        graph = Graph(paths, init, finish)
        return cls(graph)

    def is_finished(self):
        return self.finish in self.current

    def get_dot_content(self):
        """override graph contents by draw current state red."""
        digraph = []
        header = 'digraph state_machine {'
        enclose = '}'
        declarations = ['node [shape="circle"];', 'rankdir=LR;']
        digraph.append(header)
        digraph = digraph + declarations
        states = self.get_states()
        digraph.append('StartArrow [style = invis];')
        for state in states:
            if state == self.finish:
                s = '{} [shape = "doublecircle"];'
                if state in self.current:
                    s = '{} [shape = "doublecircle"; color=red];'
                digraph.append(s.format(state))
            elif state in self.current:
                digraph.append("{} [color=red];".format(state))
            else:
                digraph.append("{};".format(state))
        s = 'StartArrow -> {} [label="start"];'
        digraph.append(s.format(self.start))
        for path in self.paths:
            s = '{} -> {} [label="{}"];'
            digraph.append(s.format(path.begin, path.end, path.label))
        digraph.append(enclose)
        return digraph

    def e_closure(self, clos: set):
        """The states that could get through a path labeled e from the clos. """

        def recur_forwards(target: set):
            """walk all states through paths which labeled e."""

            def forwards(cl: set):  # cl -- closure
                """return states at path ends through e by states in cl."""

                def forward(stt: State):
                    """return states reached from stt through e by paths."""
                    s = set([i.end for i in self.paths
                             if i.begin == stt and is_epsilon(i.label)])
                    return s

                iterate = map(forward, list(cl))
                step_closure = reduce(lambda x, y: x.union(y), iterate)
                return step_closure

            next = forwards(target)
            if next.issubset(target):
                return target
            else:
                target = target.union(next)
                return recur_forwards(target)

        return recur_forwards(clos)

    def step_by(self, letter):
        """Goto next state closure by input letter."""
        try:
            self.current = self.e_closure(set([path.end for path in self.paths
                                              if path.begin in self.current and
                                               path.label == letter]))
        except TypeError:
            raise NotMatchException("""does not match this letter "{}"."""
                                    .format(letter))

    def match(self, stream):
        try:
            for letter in stream:
                self.step_by(letter)
            if self.finish in self.current:
                self.current = self.e_closure({self.start, })
                return True
            else:
                self.current = self.e_closure({self.start, })
                return False
        except NotMatchException:
            self.current = self.e_closure({self.start, })
            return False
