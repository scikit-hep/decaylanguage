import pytest

try:
    from pathlib2 import Path
except ImportError:
    from pathlib import Path

from decaylanguage import data
from decaylanguage.dec.dec import DecFileParser
from decaylanguage.dec.dec import DecFileNotParsed, DecayNotFound


DIR = Path(__file__).parent.resolve()


def test_unknown_decfile():
    with pytest.raises(FileNotFoundError):
        p = DecFileParser('non-existent.dec')


def test_non_parsed_decfile():
    with pytest.raises(DecFileNotParsed):
        p = DecFileParser(DIR / '../decaylanguage/data/test_example_Dst.dec')
        p.list_decay_mother_names()


def test_non_existent_decay():
    with pytest.raises(DecayNotFound):
        p = DecFileParser(DIR / '../decaylanguage/data/test_example_Dst.dec')
        p.parse()
        p.list_decay_modes('XYZ')


def test_simple_dec():
    p = DecFileParser(DIR / '../decaylanguage/data/test_example_Dst.dec')
    p.parse()

    assert p.list_decay_mother_names() == ['D*+', 'D*-', 'D0', 'D+', 'pi0']

    assert p.list_decay_modes('D0') == [['K-', 'pi+']]


def test_default_grammar_loading():
    p = DecFileParser(DIR / '../decaylanguage/data/test_example_Dst.dec')

    assert p.grammar is not None


def test_explicit_grammar_loading():
    p = DecFileParser(DIR / '../decaylanguage/data/test_example_Dst.dec')
    p.load_grammar(DIR / '../decaylanguage/data/decfile.lark')

    assert p.grammar_loaded is True


def test_string_representation():
        p = DecFileParser(DIR / '../decaylanguage/data/test_example_Dst.dec')

        assert "n_decays" not in p.__str__()

        p.parse()
        assert "n_decays=5" in p.__str__()
