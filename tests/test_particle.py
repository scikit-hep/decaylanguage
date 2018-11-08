from decaylanguage.particle import Charge
from decaylanguage.particle import Par
from decaylanguage.particle import Particle
from decaylanguage.particle import SpinType


def test_enums_Charge():
    assert Charge.p + Charge.m == Charge.o
    assert Charge.pp + Charge.mm == Charge.o


def test_enums_SpinType():
    assert SpinType.PseudoScalar == - SpinType.Scalar
    assert SpinType.Axial == - SpinType.Vector
    assert SpinType.PseudoTensor == - SpinType.Tensor


def test_pdg():
    assert Particle.from_pdgid(211).val == 211


def test_str():
    pi = Particle.from_pdgid(211)
    assert str(pi) == 'pi+'


def test_rep():
    pi = Particle.from_pdgid(211)
    assert 'val=211' in repr(pi)
    assert "name='pi'" in repr(pi)
    assert 'mass=0.13957' in repr(pi)


def test_prop():
    pi = Particle.from_pdgid(211)
    assert pi.name == 'pi'
    assert pi.val == 211
    assert pi.charge == Par.p


def test_ampgen_style_names():
    assert Particle.from_string('pi+').val == 211
    assert Particle.from_string('K~*0').val == -313
    assert Particle.from_string('a(1)(1260)+').val == 20213


def test_decfile_style_names():
    assert Particle.from_string('anti-K*0').val == -313
    assert Particle.from_string('a_1(1260)+').val == 20213
    # "D'_1+"
    # "D_2*+"
