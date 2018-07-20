try:
    from importlib.resources import open_text
except ImportError:
    from importlib_resources import open_text


def get_mass_width():
    return open_text('decaylanguage.data', 'mass_width_2008.csv')


def get_special():
    return open_text('decaylanguage.data', 'MintDalitzSpecialParticles.csv')


def get_latex():
    return open_text('decaylanguage.data', 'pdgID_to_latex.txt')
