try:
    from importlib.resources import open_text
except ImportError:
    from importlib_resources import open_text

def open_text_file(name):
    return open_text('decaylanguage.data', name)

def get_mass_width():
    return open_text_file('mass_width_2008.csv')

def get_special():
    return open_text_file('MintDalitzSpecialParticles.csv')

def get_latex():
    return open_text_file('pdgID_to_latex.txt')