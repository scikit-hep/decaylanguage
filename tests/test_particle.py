from decaylanguage.particle import Par
from decaylanguage.particle import Particle


def test_pdg():
    assert Particle.from_pdg(211).val == 211


def test_str():
    pi = Particle.from_pdg(211)
    assert str(pi) == 'pi+'


def test_rep():
    pi = Particle.from_pdg(211)
    assert 'val=211' in repr(pi)
    assert "name='pi'" in repr(pi)
    assert 'mass=0.13957' in repr(pi)
    assert 'charge=<Par.p: 1>' in repr(pi)


def test_prop():
    pi = Particle.from_pdg(211)
    assert pi.name == 'pi'
    assert pi.val == 211
    assert pi.charge == Par.p
