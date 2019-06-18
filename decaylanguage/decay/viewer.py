"""
Submodule with classes and utilities to visualize decay chains.
Decay chains are typically provided by the parser of .dec decay files,
see the `DecFileParser` class.
"""

try:
    import pydot
except ImportError:
    raise ImportError("You need pydot for this submodule. Please install pydot with for example 'pip install pydot'\n")


class GraphNotBuiltError(RuntimeError):
    pass


class DecayChainViewer(object):
    """
    The class to visualize a decay chain.

    Example
    -------
    >>> dfp = DecFileParser.from_file('my-Dst-decay-file.dec')
    >>> dfp.parse()
    >>> chain = dfp.build_decay_chain('D*+')
    >>> dcv = DecayChainViewer(chain)
    """

    __slots__ = ("_chain",
                 "_graph",
                 "_graph_attributes")

    def __init__(self, decaychain, **attrs):
        """
        Default constructor.

        Parameters
        ----------
        decaychain: dict
            Input .dec decay file name.
        attrs: optional
            User input pydot.Dot class attributes.

        See also
        --------
        decaylanguage.dec.dec.DecFileParser: class for creating an input decay chain.
        """
        # Store the input decay chain
        self._chain = decaychain

        # Override the default graph settings with the user input, if any
        args = self._get_digraph_defaults()
        args.update(**attrs)
        self._graph_attributes = args

        self._build_decay_graph()

    def visualize_decay_graph(self, format='png'):
        """
        Visualize the Graph produced, opening the file ('png' by default)
        with the machine default program.
        """
        self._build_decay_graph()

        import tempfile
        import webbrowser
        tmpf = tempfile.NamedTemporaryFile(prefix='DecayChainViewer',
                                           suffix='.{0}'.format(format),
                                           delete=False)
        self.graph.write(tmpf.name, format=format)
        tmpf.close()
        return webbrowser.open(tmpf.name)

    def _build_decay_graph(self):
        """
        Recursively navigate the decay chain tree and produce a Graph
        in the DOT language.
        """

        def new_node_no_subchain(dec_number, list_parts):
            label = ' '.join(['%s'%p for p in list_parts])
            #label = ' '.join(['%s'%Particle.from_dec(p).html_name for p in list_parts])
            r = 'dec%s' % dec_number
            self._graph.add_node(pydot.Node(r, label=label))
            return r

        def new_node_with_subchain(dec_number, list_parts):
            list_parts = [list(p.keys())[0] if isinstance(p,dict) else p for p in list_parts]
            label = ' | '.join(['<p%s> %s'%(i,n) for i, n in enumerate(list_parts)])
            r = 'dec%s' % dec_number
            self._graph.add_node(pydot.Node(r, shape='record', label=label, fillcolor="#9abad6"))
            return r

        def iterate_chain(subchain, top_node=None, offset=0, link_pos=None):
            if not top_node: top_node = node_mother
            n_decaymodes = len(subchain)
            for idm in range(n_decaymodes):
                _list_parts = subchain[idm]['fs']
                if not has_subdecay(_list_parts):
                    _ref = new_node_no_subchain(offset+idm, _list_parts)
                    _bf = subchain[idm]['bf']
                    if link_pos is None:
                        self._graph.add_edge(pydot.Edge(top_node, _ref, label=str(_bf)))
                    else:
                        self._graph.add_edge(pydot.Edge('%s:p%s'%(top_node, link_pos), _ref, label=str(_bf)))
                else:
                    _ref_1 = new_node_with_subchain(offset+idm, _list_parts)
                    _bf_1 = subchain[idm]['bf']
                    if link_pos is None:
                        self._graph.add_edge(pydot.Edge(top_node, _ref_1, label=str(_bf_1)))
                    else:
                        self._graph.add_edge(pydot.Edge('%s:p%s'%(top_node, link_pos), _ref_1, label=str(_bf_1)))
                    for i, _p in enumerate(_list_parts):
                        if not isinstance(_p,str):
                            _k = list(_p.keys())[0]
                            offset += offset+n_decaymodes+len(_list_parts)
                            iterate_chain(_p[_k], top_node=_ref_1, offset=offset+n_decaymodes+len(_list_parts), link_pos=i)

        # Effectively do a reset and produce a new graph
        self._graph = self._instantiate_digraph()

        has_subdecay = lambda ds: not all([isinstance(p,str) for p in ds])

        k = list(self._chain.keys())[0]

        node_mother = pydot.Node("mother", style="filled", fillcolor="#568dba", shape='box', label=str(k))
        self._graph.add_node(node_mother)
        sc = self._chain[k]

        # Actually build the whole decay chain, iteratively
        iterate_chain(sc)

    @property
    def graph(self):
        """
        Get the actual Graph. The user now has full control ...
        """
        return self._graph

    def to_string(self):
        """
        Return a string representation of the built Graph in the DOT language.
        The function is simply `Graph.to_string()`.
        """
        return self.graph.to_string()

    def _instantiate_digraph(self):
        """
        Return a pydot.Dot class instance using the default attributes
        specified in this class:
        - Default graph attributes are overriden by input by the user.
        - Class nd node and edge defaults.
        """
        g = pydot.Dot(graph_type='digraph', graph_name='DecayChainGraph')

        g.set_graph_defaults(**self._graph_attributes)
        g.set_node_defaults(**self._get_node_defaults())
        g.set_edge_defaults(**self._get_edge_defaults())

        return g

    def _get_digraph_defaults(self):
        return dict(graph_name='DecayChainGraph', rankdir='LR')

    def _get_node_defaults(self):
        return dict(style='filled', fillcolor='#eef3f8',
                    fontname='Helvetica', fontsize=11)

    def _get_edge_defaults(self):
        return dict(fontcolor='#4c4c4c', fontsize=11)

    def _repr_svg_(self):
        """
        IPython display
        """

        return self.graph.create_svg().decode('UTF-8')
