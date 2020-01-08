# Copyright (c) 2018-2020, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

"""
Submodule with classes and utilities to visualize decay chains.
Decay chains are typically provided by the parser of .dec decay files,
see the `DecFileParser` class.
"""

import itertools
try:
    counter = itertools.count().__next__
except AttributeError:
    counter = itertools.count().next

try:
    import pydot
except ImportError:
    raise ImportError("You need pydot for this submodule. Please install pydot with for example 'pip install pydot'\n")

from particle import latex_to_html_name
from particle.converters.bimap import DirectionalMaps


_EvtGen2LatexNameMap, _Latex2EvtGenNameMap = DirectionalMaps("EvtGenName", "LaTexName")


class GraphNotBuiltError(RuntimeError):
    pass


class DecayChainViewer(object):
    """
    The class to visualize a decay chain.

    Example
    -------
    >>> dfp = DecFileParser('my-Dst-decay-file.dec')
    >>> dfp.parse()
    >>> chain = dfp.build_decay_chains('D*+')
    >>> dcv = DecayChainViewer(chain)
    >>> dcv  # display the SVG figure in a notebook
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

        # Instantiate digraph with defaults possibly overriden by user attributes
        self._graph = self._instantiate_graph(**attrs)

        # Build the actual graph from the input decay chain structure
        self._build_decay_graph()

    def _build_decay_graph(self):
        """
        Recursively navigate the decay chain tree and produce a Graph
        in the DOT language.
        """
        def safe_html_name(name):
            """
            Get a safe HTML name from the EvtGen name.

            Note
            ----
            The match is done using a conversion map rather than via
            `Particle.from_evtgen_name(name).html_name` for 2 reasons:
            - Some decay-file-specific "particle" names (e.g. cs_0)
              are not in the PDG table.
            - No need to load all particle information if all that's needed
              is a match EvtGen - HTML name.
            """
            try:
                return latex_to_html_name(_EvtGen2LatexNameMap[name])
            except:
                return name

        def html_table_label(names, add_tags=False, bgcolor='#9abad6'):
            if add_tags:
                label = '<<TABLE BORDER="0" CELLSPACING="0" BGCOLOR="{bgcolor}">'.format(bgcolor=bgcolor)
            else:
                label = '<<TABLE BORDER="0" CELLSPACING="0" CELLPADDING="0" BGCOLOR="{bgcolor}"><TR>'.format(bgcolor=bgcolor)
            for i, n in enumerate(names):
                if add_tags:
                    label += '<TR><TD BORDER="1" CELLPADDING="5" PORT="p{tag}">{name}</TD></TR>'.format(tag=i, name=safe_html_name(n))
                else:
                    label += '<TD BORDER="0" CELLPADDING="2">{name}</TD>'.format(name=safe_html_name(n))
            label += "{tr}</TABLE>>".format(tr='' if add_tags else '</TR>')
            return label

        def new_node_no_subchain(list_parts):
            label = html_table_label(list_parts, bgcolor='#eef3f8')
            r = 'dec%s' % counter()
            self._graph.add_node(pydot.Node(r, label=label, style='filled', fillcolor='#eef3f8'))
            return r

        def new_node_with_subchain(list_parts):
            list_parts = [list(p.keys())[0] if isinstance(p,dict) else p for p in list_parts]
            label = html_table_label(list_parts, add_tags=True)
            r = 'dec%s' % counter()
            self._graph.add_node(pydot.Node(r, shape='none', label=label))
            return r

        def iterate_chain(subchain, top_node=None, link_pos=None):
            if not top_node: top_node = node_mother
            n_decaymodes = len(subchain)
            for idm in range(n_decaymodes):
                _list_parts = subchain[idm]['fs']
                if not has_subdecay(_list_parts):
                    _ref = new_node_no_subchain(_list_parts)
                    _bf = subchain[idm]['bf']
                    if link_pos is None:
                        self._graph.add_edge(pydot.Edge(top_node, _ref, label=str(_bf)))
                    else:
                        self._graph.add_edge(pydot.Edge('%s:p%s'%(top_node, link_pos), _ref, label=str(_bf)))
                else:
                    _ref_1 = new_node_with_subchain(_list_parts)
                    _bf_1 = subchain[idm]['bf']
                    if link_pos is None:
                        self._graph.add_edge(pydot.Edge(top_node, _ref_1, label=str(_bf_1)))
                    else:
                        self._graph.add_edge(pydot.Edge('%s:p%s'%(top_node, link_pos), _ref_1, label=str(_bf_1)))
                    for i, _p in enumerate(_list_parts):
                        if not isinstance(_p,str):
                            _k = list(_p.keys())[0]
                            iterate_chain(_p[_k], top_node=_ref_1, link_pos=i)

        has_subdecay = lambda ds: not all([isinstance(p,str) for p in ds])

        k = list(self._chain.keys())[0]
        label = html_table_label([k], add_tags=True, bgcolor='#568dba')
        node_mother = pydot.Node("mother",  shape='none', label=label)
        self._graph.add_node(node_mother)
        sc = self._chain[k]

        # Actually build the whole decay chain, iteratively
        iterate_chain(sc)

    def visualize_decay_graph(self, format='png'):
        """
        Visualize the Graph produced, opening the file ('png' by default)
        with the machine default program.
        """
        import tempfile
        import webbrowser
        tmpf = tempfile.NamedTemporaryFile(prefix='DecayChainViewer',
                                           suffix='.{0}'.format(format),
                                           delete=False)
        self.graph.write(tmpf.name, format=format)
        tmpf.close()
        return webbrowser.open(tmpf.name)

    @property
    def graph(self):
        """
        Get the actual Graph. The user now has full control ...
        """
        return self._graph

    def to_string(self):
        """
        Return a string representation of the built Graph in the DOT language.
        The function is a trivial shortcut for `Graph.to_string()`.
        """
        return self.graph.to_string()

    def _instantiate_graph(self, **attrs):
        """
        Return a pydot.Dot class instance using the default attributes
        specified in this class:
        - Default graph attributes are overriden by input by the user.
        - Class and node and edge defaults.
        """
        # Make sure the user cannot override the graph type
        try:
            del attrs['graph_type']
        except KeyError:
            pass

        default_args = self._get_graph_defaults()
        default_args.update(**attrs)

        g = pydot.Dot(**default_args)

        g.set_node_defaults(**self._get_node_defaults())
        g.set_edge_defaults(**self._get_edge_defaults())

        return g

    def _get_graph_defaults(self):
        """
        Note: the graph type cannot be overriden.
        """
        return dict(graph_type='digraph', graph_name='DecayChainGraph',
                    rankdir='LR')

    def _get_node_defaults(self):
        return dict(fontname='Helvetica', fontsize=11, shape='oval')

    def _get_edge_defaults(self):
        return dict(fontcolor='#4c4c4c', fontsize=11)

    def _repr_svg_(self):
        """
        IPython display in SVG format.
        """

        return self.graph.create_svg().decode('UTF-8')
