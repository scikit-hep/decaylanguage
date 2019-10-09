# Copyright (c) 2018-2019, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.


from __future__ import absolute_import

try:
    from pathlib2 import Path
except ImportError:
    from pathlib import Path

import pytest

from decaylanguage.dec.dec import DecFileParser
from decaylanguage.decay.viewer import DecayChainViewer


DIR = Path(__file__).parent.resolve()


def test_single_decay():
    p = DecFileParser(DIR / '../data/test_example_Dst.dec')
    p.parse()

    chain = p.build_decay_chains('D*+', stable_particles=['D+', 'D0', 'pi0'])
    dcv = DecayChainViewer(chain)
    graph_output_as_dot = dcv.to_string()

    assert 'mother -> dec0  [label="0.677"]' in graph_output_as_dot
    assert 'mother -> dec1  [label="0.307"]' in graph_output_as_dot
    assert 'mother -> dec2  [label="0.016"]' in graph_output_as_dot


def test_simple_decay_chain():
    p = DecFileParser(DIR / '../data/test_example_Dst.dec')
    p.parse()

    chain = p.build_decay_chains('D*+')
    dcv = DecayChainViewer(chain)
    graph_output_as_dot = dcv.to_string()

    assert 'mother -> dec3  [label="0.677"]' in graph_output_as_dot
    assert 'dec3:p0 -> dec4  [label="1.0"]' in graph_output_as_dot
    assert 'mother -> dec5  [label="0.307"]' in graph_output_as_dot
    assert 'dec5:p0 -> dec6  [label="1.0"]' in graph_output_as_dot
    assert 'dec6:p3 -> dec7  [label="0.988228297"]' in graph_output_as_dot


checklist_decfiles = (
    (DIR / '../data/test_Bc2BsPi_Bs2KK.dec', 'B_c+sig'),
    (DIR / '../data/test_Bd2DDst_Ds2DmPi0.dec', 'B0sig'),
    (DIR / '../data/test_Bd2DmTauNu_Dm23PiPi0_Tau2MuNu.dec', 'B0sig'),
    (DIR / '../data/test_Bd2DMuNu.dec', 'anti-B0sig'),
    (DIR / '../data/test_Bd2DstDst.dec', 'anti-B0sig'),
    (DIR / '../data/test_example_Dst.dec', 'D*+'),
    (DIR / '../data/test_Xicc2XicPiPi.dec', 'Xi_cc+sig')
)


@pytest.mark.parametrize("decfilepath,signal_mother", checklist_decfiles)
def test_duplicate_arrows(decfilepath, signal_mother):
    """
    This test effectively checks whether any box node (node with subdecays)
    gets more than one arrow to it, which would show a bug
    in the creation of the DOT file recursively parsing the built decay chain.
    """
    p = DecFileParser(decfilepath, DIR / '../../decaylanguage/data/DECAY_LHCB.DEC')
    p.parse()

    chain = p.build_decay_chains(signal_mother)
    dcv = DecayChainViewer(chain)
    graph_output_as_dot = dcv.to_string()

    l = [i.split(' ')[0] for i in graph_output_as_dot.split('-> dec')[1:]]  # list of node identifiers
    assert len(set(l)) == len(l)


def test_init_non_defaults():
    p = DecFileParser(DIR / '../data/test_example_Dst.dec')
    p.parse()

    chain = p.build_decay_chains('D*+')
    dcv = DecayChainViewer(chain, graph_name='TEST', rankdir='TB')

    assert dcv.graph.get_name() == 'TEST'
    assert dcv.graph.get_rankdir() == 'TB'
