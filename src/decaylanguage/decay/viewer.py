# Copyright (c) 2018-2022, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

"""
Submodule with classes and utilities to visualize decay chains.
Decay chains are typically provided by the parser of .dec decay files,
see the `DecFileParser` class.
"""

import itertools
from typing import Any, Optional, Union

import graphviz
from particle import latex_to_html_name
from particle.converters.bimap import DirectionalMaps

counter = iter(itertools.count())


_EvtGen2LatexNameMap, _Latex2EvtGenNameMap = DirectionalMaps("EvtGenName", "LaTexName")


class GraphNotBuiltError(RuntimeError):
    pass


class DecayChainViewer:
    """
    The class to visualize a decay chain.

    Examples
    --------
    >>> dfp = DecFileParser('my-Dst-decay-file.dec')
    >>> dfp.parse()
    >>> chain = dfp.build_decay_chains('D*+')
    >>> dcv = DecayChainViewer(chain)
    >>> dcv  # display the SVG figure in a notebook

    When not in notebooks the graph can easily be visualized with the
    `graphviz.dot.Digraph.render` or `graphviz.dot.Digraph.view` functions, e.g.:
    >>> dcv.graph.render(filename="test", format="pdf", view=True, cleanup=True)
    """

    __slots__ = ("_chain", "_graph", "_graph_attributes")

    def __init__(
        self,
        decaychain: dict[str, list[dict[str, Union[float, str, list[Any]]]]],
        **attrs: dict[str, Union[bool, int, float, str]],
    ) -> None:
        """
        Default constructor.

        Parameters
        ----------
        decaychain: dict
            Input decay chain in dict format, typically created from `decaylanguage.DecFileParser.build_decay_chains`
            after parsing a .dec decay file, or from building a decay chain representation with `decaylanguage.DecayChain.to_dict`.
        attrs: optional
            User input `graphviz.dot.Digraph` class attributes.

        See also
        --------
        decaylanguage.DecFileParser.build_decay_chains for creating a decay chain dict from parsing a .dec file.
        decaylanguage.DecFileParser: class for creating an input decay chain.
        """
        # Store the input decay chain
        self._chain = decaychain

        # Instantiate the digraph with defaults possibly overridden by user attributes
        self._graph = self._instantiate_graph(**attrs)

        # Build the actual graph from the input decay chain structure
        self._build_decay_graph()

    def _build_decay_graph(self) -> None:
        """
        Recursively navigate the decay chain tree and produce a Digraph
        in the DOT language.
        """

        def safe_html_name(name: str) -> str:
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
            except Exception:
                return name

        def html_table_label(
            names: list[str],
            add_tags: bool = False,
            bgcolor: str = "#9abad6",
        ) -> str:
            if add_tags:
                label = (
                    '<<TABLE BORDER="0" CELLSPACING="0" BGCOLOR="{bgcolor}">'.format(
                        bgcolor=bgcolor
                    )
                )
            else:
                label = '<<TABLE BORDER="0" CELLSPACING="0" CELLPADDING="0" BGCOLOR="{bgcolor}"><TR>'.format(
                    bgcolor=bgcolor
                )
            for i, n in enumerate(names):
                if add_tags:
                    label += '<TR><TD BORDER="1" CELLPADDING="5" PORT="p{tag}">{name}</TD></TR>'.format(
                        tag=i, name=safe_html_name(n)
                    )
                else:
                    label += '<TD BORDER="0" CELLPADDING="2">{name}</TD>'.format(
                        name=safe_html_name(n)
                    )
            label += "{tr}</TABLE>>".format(tr="" if add_tags else "</TR>")
            return label

        def new_node_no_subchain(list_parts: list[str]) -> str:
            label = html_table_label(list_parts, bgcolor="#eef3f8")
            r = f"dec{next(counter)}"
            self.graph.node(r, label=label, style="filled", fillcolor="#eef3f8")
            return r

        def new_node_with_subchain(list_parts: list[Any]) -> str:
            _list_parts = [
                list(p.keys())[0] if isinstance(p, dict) else p for p in list_parts
            ]
            label = html_table_label(_list_parts, add_tags=True)
            r = f"dec{next(counter)}"
            self.graph.node(r, shape="none", label=label)
            return r

        def iterate_chain(
            subchain: list[dict[str, Union[float, str, list[Any]]]],
            top_node: Optional[str] = None,
            link_pos: Optional[int] = None,
        ) -> None:
            if not top_node:
                top_node = "mother"
                self.graph.node("mother", shape="none", label=label)
            n_decaymodes = len(subchain)
            for idm in range(n_decaymodes):
                _list_parts = subchain[idm]["fs"]
                if not has_subdecay(_list_parts):  # type: ignore
                    _ref = new_node_no_subchain(_list_parts)  # type: ignore
                    _bf = subchain[idm]["bf"]
                    if link_pos is None:
                        self.graph.edge(top_node, _ref, label=str(_bf))
                    else:
                        self.graph.edge(f"{top_node}:p{link_pos}", _ref, label=str(_bf))
                else:
                    _ref_1 = new_node_with_subchain(_list_parts)  # type: ignore
                    _bf_1 = subchain[idm]["bf"]
                    if link_pos is None:
                        self.graph.edge(top_node, _ref_1, label=str(_bf_1))
                    else:
                        self.graph.edge(
                            f"{top_node}:p{link_pos}",
                            _ref_1,
                            label=str(_bf_1),
                        )
                    for i, _p in enumerate(_list_parts):  # type: ignore
                        if not isinstance(_p, str):
                            _k = list(_p.keys())[0]
                            iterate_chain(_p[_k], top_node=_ref_1, link_pos=i)

        def has_subdecay(ds: list[Any]) -> bool:
            return not all(isinstance(p, str) for p in ds)

        k = list(self._chain.keys())[0]
        label = html_table_label([k], add_tags=True, bgcolor="#568dba")
        sc = self._chain[k]

        # Actually build the whole decay chain, iteratively
        iterate_chain(sc)

    @property
    def graph(self) -> graphviz.dot.Digraph:
        """
        Get the actual `graphviz.dot.Digraph` object.
        The user now has full control ...
        """
        return self._graph

    def to_string(self) -> str:
        """
        Return a string representation of the built graph in the DOT language.
        The function is a trivial shortcut for ``graphviz.dot.Digraph.source`.
        """
        return self.graph.source  # type: ignore

    def _instantiate_graph(
        self, **attrs: dict[str, Union[bool, int, float, str]]
    ) -> graphviz.dot.Digraph:
        """
        Return a ``graphviz.dot.Digraph` class instance using the default attributes
        specified in this class:
        - Default graph attributes are overridden by input by the user.
        - Class and node and edge defaults.
        """
        graph_attr = self._get_graph_defaults()
        node_attr = self._get_node_defaults()
        edge_attr = self._get_edge_defaults()
        if "graph_attr" in attrs:
            graph_attr.update(**attrs["graph_attr"])
            attrs.pop("graph_attr")
        if "node_attr" in attrs:
            node_attr.update(**attrs["node_attr"])
            attrs.pop("node_attr")
        if "edge_attr" in attrs:
            edge_attr.update(**attrs["edge_attr"])
            attrs.pop("edge_attr")

        arguments = self._get_default_arguments()
        arguments.update(**attrs)  # type: ignore

        return graphviz.Digraph(
            graph_attr=graph_attr, node_attr=node_attr, edge_attr=edge_attr, **arguments
        )

    def _get_default_arguments(self) -> dict[str, Union[bool, int, float, str]]:
        """
        `graphviz.dot.Digraph` default arguments.
        """
        return dict(
            name="DecayChainGraph",
            comment="Created by https://github.com/scikit-hep/decaylanguage",
            engine="dot",
            format="png",
        )

    def _get_graph_defaults(self) -> dict[str, Union[bool, int, float, str]]:
        d = self._get_default_arguments()
        d.update(rankdir="LR")
        return d

    def _get_node_defaults(self) -> dict[str, Union[bool, int, float, str]]:
        return dict(fontname="Helvetica", fontsize="11", shape="oval")

    def _get_edge_defaults(self) -> dict[str, Union[bool, int, float, str]]:
        return dict(fontcolor="#4c4c4c", fontsize="11")

    def _repr_mimebundle_(
        self,
        include: Optional[bool] = None,
        exclude: Optional[bool] = None,
        **kwargs: Any,
    ) -> Any:
        """
        IPython display helper.
        """
        try:
            return self._graph._repr_mimebundle_(
                include=include, exclude=exclude, **kwargs
            )
        except AttributeError:
            return {"image/svg+xml": self._graph._repr_svg_()}  # for graphviz < 0.19
