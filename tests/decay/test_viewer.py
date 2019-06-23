# Copyright (c) 2018-2019, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

try:
    from pathlib2 import Path
except ImportError:
    from pathlib import Path

from decaylanguage.dec.dec import DecFileParser
from decaylanguage.decay.viewer import DecayChainViewer


DIR = Path(__file__).parent.resolve()


def test_single_decay():
    p = DecFileParser(DIR / '../data/test_example_Dst.dec')
    p.parse()

    chain = p.build_decay_chain('D*+', stable_particles=['D+', 'D0', 'pi0'])
    dcv = DecayChainViewer(chain)

    graph_output_as_dot = """digraph DecayChainGraph {
graph [graph_name=DecayChainGraph, rankdir=LR];
node [style=filled, fillcolor="#eef3f8", fontname=Helvetica, fontsize=11];
edge [fontcolor="#4c4c4c", fontsize=11];
mother [style=filled, fillcolor="#568dba", shape=box, label="D*+"];
dec0 [label="D0 pi+"];
mother -> dec0  [label=0.677];
dec1 [label="D+ pi0"];
mother -> dec1  [label=0.307];
dec2 [label="D+ gamma"];
mother -> dec2  [label=0.016];
}
"""

    assert 'dec0 [label="D0 pi+"];' in graph_output_as_dot
    assert 'dec1 [label="D+ pi0"];' in graph_output_as_dot
    assert 'dec2 [label="D+ gamma"];' in graph_output_as_dot


def test_simple_decay_chain():
    p = DecFileParser(DIR / '../data/test_example_Dst.dec')
    p.parse()

    chain = p.build_decay_chain('D*+')
    dcv = DecayChainViewer(chain)

    graph_output_as_dot = """digraph DecayChainGraph {
graph [graph_name=DecayChainGraph, rankdir=LR];
node [style=filled, fillcolor="#eef3f8", fontname=Helvetica, fontsize=11];
edge [fontcolor="#4c4c4c", fontsize=11];
mother [style=filled, fillcolor="#568dba", shape=box, label="D*+"];
dec0 [shape=record, label="<p0> D0 | <p1> pi+", fillcolor="#9abad6"];
mother -> dec0  [label="0.677"];
dec10 [label="K- pi+"];
dec0:p0 -> dec10  [label="1.0"];
dec6 [shape=record, label="<p0> D+ | <p1> pi0", fillcolor="#9abad6"];
mother -> dec6  [label="0.307"];
dec20 [shape=record, label="<p0> K- | <p1> pi+ | <p2> pi+ | <p3> pi0", fillcolor="#9abad6"];
dec6:p0 -> dec20  [label="1.0"];
dec50 [label="gamma gamma"];
dec20:p3 -> dec50  [label="0.988228297"];
dec51 [label="e+ e- gamma"];
dec20:p3 -> dec51  [label="0.011738247"];
dec52 [label="e+ e+ e- e-"];
dec20:p3 -> dec52  [label="3.3392e-05"];
dec53 [label="e+ e-"];
dec20:p3 -> dec53  [label="6.5e-08"];
dec40 [label="gamma gamma"];
dec6:p1 -> dec40  [label="0.988228297"];
dec41 [label="e+ e- gamma"];
dec6:p1 -> dec41  [label="0.011738247"];
dec42 [label="e+ e+ e- e-"];
dec6:p1 -> dec42  [label="3.3392e-05"];
dec43 [label="e+ e-"];
dec6:p1 -> dec43  [label="6.5e-08"];
dec37 [shape=record, label="<p0> D+ | <p1> gamma", fillcolor="#9abad6"];
mother -> dec37  [label="0.016"];
dec80 [shape=record, label="<p0> K- | <p1> pi+ | <p2> pi+ | <p3> pi0", fillcolor="#9abad6"];
dec37:p0 -> dec80  [label="1.0"];
dec170 [label="gamma gamma"];
dec80:p3 -> dec170  [label="0.988228297"];
dec171 [label="e+ e- gamma"];
dec80:p3 -> dec171  [label="0.011738247"];
dec172 [label="e+ e+ e- e-"];
dec80:p3 -> dec172  [label="3.3392e-05"];
dec173 [label="e+ e-"];
dec80:p3 -> dec173  [label="6.5e-08"];
}
"""

    assert 'label="<p0> D0 | <p1> pi+"' in graph_output_as_dot
    assert 'label="<p0> D+ | <p1> pi0"' in graph_output_as_dot
    assert 'label="<p0> K- | <p1> pi+ | <p2> pi+ | <p3> pi0"' in graph_output_as_dot
    assert 'label="<p0> D+ | <p1> gamma"' in graph_output_as_dot
    assert 'label="<p0> K- | <p1> pi+ | <p2> pi+ | <p3> pi0"' in graph_output_as_dot
