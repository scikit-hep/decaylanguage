There are a few instructions related to working on DecayLanguage itself.

To regenerate the particle file from the fixed width file:

```bash
python3 -m particle.particle.convert extended \
    decaylanguage/data/MintDalitzSpecialParticles.fwf \
    decaylanguage/data/MintDalitzSpecialParticlesLatex.csv \
    decaylanguage/data/MintDalitzSpecialParticles.csv
```

To quickly setup a virtual env for development, just run:

```bash
python3 -m venv .env
source .env/bin/activate
pip install -e .[test]
```
