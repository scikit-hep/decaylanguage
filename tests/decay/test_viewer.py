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
    graph_output_as_dot = dcv.to_string()

    assert 'dec0 [label="D0 pi+"];' in graph_output_as_dot
    assert 'dec1 [label="D+ pi0"];' in graph_output_as_dot
    assert 'dec2 [label="D+ gamma"];' in graph_output_as_dot


def test_simple_decay_chain():
    p = DecFileParser(DIR / '../data/test_example_Dst.dec')
    p.parse()

    chain = p.build_decay_chain('D*+')
    dcv = DecayChainViewer(chain)
    graph_output_as_dot = dcv.to_string()

    assert 'label="<p0> D0 | <p1> pi+"' in graph_output_as_dot
    assert 'label="<p0> D+ | <p1> pi0"' in graph_output_as_dot
    assert 'label="<p0> K- | <p1> pi+ | <p2> pi+ | <p3> pi0"' in graph_output_as_dot
    assert 'label="<p0> D+ | <p1> gamma"' in graph_output_as_dot
    assert 'label="<p0> K- | <p1> pi+ | <p2> pi+ | <p3> pi0"' in graph_output_as_dot
