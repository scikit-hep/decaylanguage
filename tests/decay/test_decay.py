from decaylanguage.decay.decay import DaughtersDict


def test_DaughtersDict_constructor():
    dd = DaughtersDict({'K+': 1, 'K-': 2, 'pi+': 1, 'pi0': 1})
    assert dd == {'K+': 1, 'K-': 2, 'pi+': 1, 'pi0': 1}


def test_DaughtersDict_constructor_from_list():
    dd = DaughtersDict.from_list(['K+', 'K-', 'K-', 'pi+', 'pi0'])
    assert dd == {'K+': 1, 'K-': 2, 'pi+': 1, 'pi0': 1}


def test_DaughtersDict_constructor_from_string():
    dd = DaughtersDict('K+ K- pi0')
    assert dd == {'K+': 1, 'K-': 1, 'pi0': 1}


def test_DaughtersDict_string_repr():
    dd = DaughtersDict.from_list(['K+', 'K-', 'K-', 'pi+', 'pi0'])
    assert dd.__str__() == "<DaughtersDict: ['K+', 'K-', 'K-', 'pi+', 'pi0']>"


def test_DaughtersDict_len():
    dd = DaughtersDict({'K+': 1, 'K-': 3, 'pi0': 1})
    assert len(dd) == 5


def test_DaughtersDict_add():
    dd1 = DaughtersDict({'K+': 1, 'K-': 2, 'pi0': 3})
    dd2 = DaughtersDict({'K+': 1, 'K-': 1})
    dd3 = dd1 + dd2
    assert len(dd3) == 8


def test_DaughtersDict_to_string():
    dd1 = DaughtersDict({'K+': 1, 'K-': 2, 'pi0': 3})
    assert dd1.to_string() == 'K+ K- K- pi0 pi0 pi0'
