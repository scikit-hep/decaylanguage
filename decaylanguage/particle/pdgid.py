# encoding : utf8

from __future__ import unicode_literals, print_function, division

# PDG RULE 2
QUARKS = ('d', 'u', 's', 'c', 'b', 't', "b'", "t'")

#PDG RULE 3
LEPTONS = ('e-', 'ν_e', 'µ-', 'ν_µ', 'τ-', 'ν_τ',  "τ'-", "ν_τ'")

class PDGID(int):
    __slots__ = ()
    
    def valid(self):
        'The various queries return 0 if they are false, so this works there too'
        return self != 0
        
    @property
    def digits(self):
        return format(abs(self), '07')
    
    # The PDG digits by name
    @property
    def n(self):
        return int(self.digits[0])
    @property
    def n_r(self):
        return int(self.digits[1])
    @property
    def n_L(self):
        return int(self.digits[2])      
    @property
    def n_q1(self):
        return int(self.digits[3])
    @property
    def n_q2(self):
        return int(self.digits[4])
    @property
    def n_q3(self):
        return int(self.digits[5])
    @property
    def n_J(self):
        return int(self.digits[6])
    
    # PDG RULE 1
    def is_particle(self):
        'Check to see if this is a particle or antiparticle.'
        return self > 0
    
    # PDG RULE 2
    def is_quark(self):
        return 0 < self < 11
        
    # PDG RULE 3
    def is_lepton(self):
        return 11 < self < 19
        
    
    @property
    def compquark(self):
        return CompositeQuark(self)
        
    @property
    def diquark(self):
        return DiQuark(self)
    
    @property
    def meson(self):
        return Meson(self)
    
    @property
    def baryon(self):
        return Baryon(self)
        
        
class CompositeQuark(PDGID):
    __slots__ = ()
    
    @property
    def quarks(self):
        return ''.join(QUARKS[int(q)-1] for q in self.digits[3:6] if q != '0')
    
    @property
    def spin(self):
        return self.n_J
    
    @property
    def J(self):
        return (self.spin - 1) // 2
    
class DiQuark(CompositeQuark):
    __slots__ = ()
    
    def valid(self):
        valid =  self < 10**5 and self.n_q1 >= self.n_q2 and self.n_q3 == 0 # PDG RULE 4
        valid &= self.n_q2 > 0                        # Must contain quarks
        valid &= self.n_J % 2 == 1                    # Must not have invalid spin
        valid &= self.n_q1 <= 6 and self.n_q2 <= 6    # Must have one of 6 quarks
        return valid
    
class Meson(CompositeQuark):
    __slots__ = ()
    
    def valid(self):
        valid =  self < 10**5 and self.n_q2 >= self.n_q3 and self.n_q1 == 0 # PDG RULE 5.a
        valid &= self.n_q2 > 0                        # Must contain quarks
        valid &= self.n_J % 2 == 1                    # Must not have invalid spin
        valid &= self.n_q1 <= 6 and self.n_q2 <= 6    # Must have one of 6 quarks
        return valid

class Baryon(CompositeQuark):
    __slots__ = ()
    
class Custom(PDGID):
    __slots__ = ()
    
class SUSY(PDGID):
    __slots__ = ()

class Nuclear(PDGID):
    __slots__ = ()