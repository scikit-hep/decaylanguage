from decaylanguage.decay.ampgen2goofit import ampgen2goofit

try:
    from pathlib2 import Path
except ImportError:
    from pathlib import Path

DIR = Path(__file__).parent.resolve()

def test_full_convert():
    text = ampgen2goofit(DIR / '../models/DtoKpipipi_v2.txt', ret_output=True)
    with (DIR / 'output/DtoKpipipi_v2.cu').open() as f:
        assert (set(x.strip() for x in text.splitlines() if 'Generated on' not in x)
             == set(x.strip() for x in f.readlines() if 'Generated on' not in x))
