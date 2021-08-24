# -*- coding: utf-8 -*-
# Copyright (c) 2018-2021, Eduardo Rodrigues and Henry Schreiner.
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
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    chain = p.build_decay_chains("D*+", stable_particles=["D+", "D0", "pi0"])
    dcv = DecayChainViewer(chain)
    graph_output_as_dot = dcv.to_string()

    assert "mother -> dec0 [label=0.677]" in graph_output_as_dot
    assert "mother -> dec1 [label=0.307]" in graph_output_as_dot
    assert "mother -> dec2 [label=0.016]" in graph_output_as_dot


def test_simple_decay_chain():
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    chain = p.build_decay_chains("D*+")
    dcv = DecayChainViewer(chain)
    graph_output_as_dot = dcv.to_string()

    assert "mother -> dec3 [label=0.677]" in graph_output_as_dot
    assert "dec3:p0 -> dec4 [label=1.0]" in graph_output_as_dot
    assert "mother -> dec5 [label=0.307]" in graph_output_as_dot
    assert "dec5:p0 -> dec6 [label=1.0]" in graph_output_as_dot
    assert "dec6:p3 -> dec7 [label=0.988228297]" in graph_output_as_dot


checklist_decfiles = (
    (DIR / "../data/test_Bc2BsPi_Bs2KK.dec", "B_c+sig"),
    (DIR / "../data/test_Bd2DDst_Ds2DmPi0.dec", "B0sig"),
    (DIR / "../data/test_Bd2DmTauNu_Dm23PiPi0_Tau2MuNu.dec", "B0sig"),
    (DIR / "../data/test_Bd2DMuNu.dec", "anti-B0sig"),
    (DIR / "../data/test_Bd2DstDst.dec", "anti-B0sig"),
    (DIR / "../data/test_example_Dst.dec", "D*+"),
    (DIR / "../data/test_Xicc2XicPiPi.dec", "Xi_cc+sig"),
)


@pytest.mark.parametrize("decfilepath,signal_mother", checklist_decfiles)
def test_duplicate_arrows(decfilepath, signal_mother):
    """
    This test effectively checks whether any box node (node with subdecays)
    gets more than one arrow to it, which would show a bug
    in the creation of the DOT file recursively parsing the built decay chain.
    """
    p = DecFileParser(decfilepath, DIR / "../../src/decaylanguage/data/DECAY_LHCB.DEC")

    p.parse()

    chain = p.build_decay_chains(signal_mother)

    dcv = DecayChainViewer(chain)
    graph_output_as_dot = dcv.to_string()

    ls = [
        i.split(" ")[0] for i in graph_output_as_dot.split("-> dec")[1:]
    ]  # list of node identifiers
    assert len(set(ls)) == len(ls)


def test_init_non_defaults_basic():
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    chain = p.build_decay_chains("D*+")
    dcv = DecayChainViewer(chain, name="TEST", format="pdf")

    assert dcv.graph.name == "TEST"
    assert dcv.graph.format == "pdf"


def test_init_non_defaults_attributes():
    p = DecFileParser(DIR / "../data/test_example_Dst.dec")
    p.parse()

    chain = p.build_decay_chains("D*+")
    node_attr = dict(shape="egg")
    edge_attr = dict(fontsize="9")
    dcv = DecayChainViewer(chain, node_attr=node_attr, edge_attr=edge_attr)

    assert dcv.graph.node_attr == dict(fontname="Helvetica", fontsize="11", shape="egg")
    assert dcv.graph.edge_attr == dict(fontcolor="#4c4c4c", fontsize="9")


def test_graphs_with_EvtGen_specific_names():
    p = DecFileParser(DIR / "../../src/decaylanguage/data/DECAY_LHCB.DEC")
    p.parse()

    # Not setting many of the particles as stable would result in a gargantuesque chain,
    # which would also take a fair amount of time to build!
    list_stable_particles = [
        "Xi_c0",
        "Xi-",
        "D0",
        "Omega_c0",
        "Sigma_c0",
        "tau-",
        "D_s-",
        "J/psi",
        "pi0",
        "Lambda0",
        "psi(2S)",
    ]

    chain = p.build_decay_chains("Xi_b-", stable_particles=list_stable_particles)
    dcv = DecayChainViewer(chain)

    assert "(cs)<SUB>0</SUB>" in dcv.to_string()  # not 'cs_0' ;-)
    assert "&Xi;<SUB>c</SUB><SUP>0</SUP>" in dcv.to_string()
