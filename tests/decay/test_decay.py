from decaylanguage.decay.decay import DaughtersDict
from decaylanguage.decay.decay import DecayMode


def test_DaughtersDict_constructor_from_dict():
    dd = DaughtersDict({'K+': 1, 'K-': 2, 'pi+': 1, 'pi0': 1})
    assert dd == {'K+': 1, 'K-': 2, 'pi+': 1, 'pi0': 1}


def test_DaughtersDict_constructor_from_list():
    dd = DaughtersDict(['K+', 'K-', 'K-', 'pi+', 'pi0'])
    assert dd == {'K+': 1, 'K-': 2, 'pi+': 1, 'pi0': 1}


def test_DaughtersDict_constructor_from_string():
    dd = DaughtersDict('K+ K- pi0')
    assert dd == {'K+': 1, 'K-': 1, 'pi0': 1}


def test_DaughtersDict_string_repr():
    dd = DaughtersDict(['K+', 'K-', 'K-', 'pi+', 'pi0'])
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


def test_DecayMode_constructor_default():
    dm = DecayMode()
    assert dm.bf == 0
    assert dm.daughters == DaughtersDict()
    assert dm.metadata == dict(model=None, model_params=None)


def test_DecayMode_constructor_simple():
    dd = DaughtersDict('K+ K-')
    dm = DecayMode(0.1234, dd)
    assert dm.bf == 0.1234
    assert dm.daughters == DaughtersDict('K+ K-')
    assert dm.metadata == dict(model=None, model_params=None)


def test_DecayMode_constructor_from_pdgids():
    dm = DecayMode.from_pdgids(0.5, [321, -321],
                               model='TAUHADNU',
                               model_params=[-0.108, 0.775, 0.149, 1.364, 0.400])
    assert dm.daughters == DaughtersDict('K+ K-')


def test_DecayMode_constructor_with_model_info():
    dd = DaughtersDict('pi- pi0 nu_tau')
    dm = DecayMode(0.2551, dd,
                   model='TAUHADNU',
                   model_params=[-0.108, 0.775, 0.149, 1.364, 0.400])
    assert dm.metadata == {'model': 'TAUHADNU',
                           'model_params': [-0.108, 0.775, 0.149, 1.364, 0.4]}


def test_DecayMode_constructor_with_user_model_info():
    dd = DaughtersDict('K+ K-')
    dm = DecayMode(0.5, dd, model='PHSP', study='toy', year=2019)
    assert dm.metadata == {'model': 'PHSP',
                           'model_params': None,
                           'study': 'toy',
                           'year': 2019}


def test_DecayMode_describe_simple():
    dd = DaughtersDict('pi- pi0 nu_tau')
    dm = DecayMode(0.2551, dd, model='TAUHADNU', model_params=[-0.108, 0.775, 0.149, 1.364, 0.400])
    assert 'BF: 0.2551' in dm.describe()
    assert 'Decay model: TAUHADNU [-0.108, 0.775, 0.149, 1.364, 0.4]' in dm.describe()


def test_DecayMode_describe_with_extra_info():
    dd = DaughtersDict('K+ K-')
    dm = DecayMode(1.e-6, dd, model='PHSP', study='toy', year=2019)
    assert 'Extra info:' in dm.describe()
    assert 'study: toy' in dm.describe()
    assert 'year: 2019' in dm.describe()


def test_DecayMode_string_repr():
    dd = DaughtersDict('p p~ K+ pi-')
    dm = DecayMode(1.e-6, dd, model='PHSP')
    assert str(dm) == "<DecayMode: daughters=K+ p pi- p~, BF=1e-06>"


def test_DecayMode_number_of_final_states():
    dd = DaughtersDict('p p~ K+ pi-')
    dm = DecayMode(1.e-6, dd, model='PHSP')
    assert len(dm) == 4
