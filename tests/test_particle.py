from decaylanguage.particle import Particle

def test_pdg():
    assert Particle.from_pdg(211).val == 211
