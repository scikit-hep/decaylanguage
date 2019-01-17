from ..data import open_text
from .. import data
from ..decay.decay import Decay

from enum import Enum

from lark import Lark, Transformer, Tree


class ProtosEnum(Enum):
    no = 0
    yes = 1


class TreeToDec(Transformer):
    def yes(self, items):
        return True
    def no(self, items):
        return False
    def global_photos(self, items):
        item, = items
        return ProtosEnum.yes if item else ProtosEnum.no
    def value(self, items):
        item, = items
        return float(item)
    def label(self, items):
        item, = items
        return str(item)
    def photos(self, items):
        return ProtosEnum.yes

    
    

def define(transformed):
    return {x.children[0]:x.children[1] for x in transformed.find_data('define')}
def pythia_def(transformed):
    return [x.children for x in transformed.find_data('pythia_def')]
def alias(transformed):
    return {x.children[0]:x.children[1] for x in transformed.find_data('alias')}

def chargeconj(transformed):
    return {x.children[0]:x.children[1] for x in transformed.find_data('chargeconj')}

# Commands
def global_photos(transformed):
    return {x.children[0]:x.children[1] for x in transformed.find_data('global_photos')}

def decay(transformed):
    return Tree('decay', list(transformed.find_data('decay')))
def cdecay(transformed):
    return [x.children[0] for x in transformed.find_data('cdecay')]
def setlspw(transformed):
    return list(transformed.find_data('setlspw'))