"""define basis and induction rules of the nfa graph construction."""


from regex.graph import State, Path, Graph, Machine, epsilon


def basis(letter, names=(None, None)):
    """Basic Machine.

    Construct from an input letter.    A -> a (a is a terminal)

    Any terminal input letter comes a basic machine that have 2 states.
    from begin state directed to end state with the input as its label.

    And if the production contains ε, the label would be an ε.

    A -> ε

    like:

    ::

             start           ε
          ────────> ○ ───────────────> ◎
                   init              finish

    :param letter: the input letter.
    :param names: state names.
    :return: a new Graph type as nfa base machine.
    """
    init, finish = [State(names[i]) for i in range(2)]
    path = Path(init, finish, letter)
    graph = Graph([path], init, finish)
    return graph


def induct_or(former: Graph, later: Graph, names=(None, None)):
    """Or Machine.

    An or Machine comes from the reduction from the production like A -> D | E
    It's build on the origin nfa of D and E.
    It creates a new state as new init state and another state as finish state.
    Put a path to the previous init state of D and E and mark ε as label.
    Put a path from the previous finish state of D and E, direct to new finish.

    like:

    ::

                           ┌┈┈┈┈┈┈┈┈┈┈┈┈┈┐
                        ε  ┊             ┊  ε
                       ┌───> ○    D    ○ ──────┐
               start   │   └┈┈┈┈┈┈┈┈┈┈┈┈┈┘     │
            ─────────> ○   ┌┈┈┈┈┈┈┈┈┈┈┈┈┈┐     ├───> ◎
                       │   ┊             ┊     │   finish
                       └───> ○    E    ○ ──────┘
                        ε  └┈┈┈┈┈┈┈┈┈┈┈┈┈┘  ε

                                 A

    :param former: type Graph, base graph to construct or machine.
    :param later: type Graph, base graph to construct or machine.
    :param names: type list[int], the name for 2 new state needed in the machine.
    :return: type Graph, a new Graph type as nfa machine constructed.
    """
    init, finish = [State(names[i]) for i in range(2)]
    paths = former.paths + later.paths
    new_paths = [Path(init, former.start, epsilon),
                 Path(init, later.start, epsilon),
                 Path(former.finish, finish, epsilon),
                 Path(later.finish, finish, epsilon)
                 ]
    paths = paths + new_paths
    graph = Graph(paths, init, finish)
    return graph


def induct_cat(former: Graph, later: Graph):
    """Cat Machine.

    Concatenate two graphs in one doesn't need new states, it just change the
    init state of later Graph to the finish state of former one. and make the
    former init state as init, the later finish state as finish of the new
    Graph.

    production: A -> DE

    like::

                       ┌┈┈┈┈┈┈┈┈┈┈┬┈┈┈┬┈┈┈┈┈┈┈┈┈┈┈┐
               start   ┊          ┊   ┊           ┊
            ───────────> ○    D   ┊ ○ ┊   E     ◎ ┊
                       └┈┈┈┈┈┈┈┈┈┈┴┈┈┈┴┈┈┈┈┈┈┈┈┈┈┈┘

                                    A

    :param former: type Graph.
    :param later: type Graph.
    :return: type Graph.
    """
    concat = former.finish
    later.alter_init_state(concat)
    init = former.start
    finish = later.finish
    paths = former.paths + later.paths
    graph = Graph(paths, init, finish)
    return graph


def induct_star(graph: Graph, names = (None, None)):
    """Star Machine.

    Star means repeat 0 or any times of the previous element.

    production:   A -> s*

    like:

    ::

                              ε
                         ┌─────────┐
                         │         │
                       ┌┈│┈┈┈┈┈┈┈┈┈│┈┐
         start      ε  ┊ ▼         │ ┊  ε
       ──────> ○ ──────> ○    D    ○ ───────> ◎
               │       └┈┈┈┈┈┈┈┈┈┈┈┈┈┘        ▲
               │                        ε     │
               └──────────────────────────────┘

    :param graph: type Graph.
    :return: type Graph.
    """
    init, finish = [State(names[i]) for i in range(2)]
    new_paths = [Path(init, graph.start, epsilon),
                 Path(init, finish, epsilon),
                 Path(graph.finish, finish, epsilon),
                 Path(graph.finish, graph.start, epsilon)]
    paths = graph.paths + new_paths
    new_graph = Graph(paths, init, finish)
    return new_graph


