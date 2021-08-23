#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import cmd
import os

from particle import Particle

DIR = os.path.dirname(__file__)

known_models = [
    "VSS",
    "VSS_BMIX",
    "PHSP",
    "HELAMP",
    "JETSET",
    "PHOTOS",
    "ISGW2",
    "HQET",
    "GOITY_ROBERTS",
    "VUB",
    "SVS",
    "SVV_HELAMP",
    "BTOXSGAMMA",
    "BTOSLLBALL",
    "BTOXSLL",
    "SSD_CP",
    "SVV_CP",
    "BTO3PI_CP",
    "STS",
    "JSCONT",
    "SLN",
    "CB3PI-P00",
    "CB3PI-MPP",
    "VSP_PWAVE",
    "TAUSCALARNU",
    "TAUHADNU",
    "D_DALITZ",
    "VLL",
    "TSS",
    "VVP",
    "VVS_PWAVE",
    "PARTWAVE",
    "TVS_PWAVE",
    "OMEGA_DALITZ",
    "ETA_DALITZ",
    "PI0_DALITZ",
    "TAUVECTORNU",
    "SVP_HELAMP",
    "VVPIPI",
    "VPHOTOV",
    "PYTHIA",
    "BTOSLLALI",
]

if "C3_DATA" in os.environ:
    defdecfile = "%s/DECAY.DEC" % os.environ["C3_DATA"]
else:
    defdecfile = os.path.join(DIR, "../data/DECAY_LHCB.DEC")


class DaughterList(dict):
    def __init__(self):
        dict.__init__(self)

    def add(self, daughter):
        self[daughter] = self.get(daughter, 0)


class AllowedDecays(object):
    def __init__(self, particle):
        self.decay_of = particle
        self.decays = []


class Decay(object):
    def __init__(self, bf=0, daughters=None):
        if daughters is None:
            daughters = DaughterList()
        self.bf = bf
        self.daughters = daughters

    def daughters_to_string(self):
        strs = []
        for dau in self.daughters:
            strs += [dau] * self.daughters[dau]

        def sortkey(x):
            p = Particle.findall(name=x)
            if len(p) == 1:
                return p[0]
            else:
                return 100000

        strs.sort(key=sortkey, reverse=True)
        return " ".join(strs)


class decparser(cmd.Cmd):
    def __init__(self, stdin=None, stdout=None):
        self.prompt = ""
        self.file_parse_status = ""
        self.current_decay_top = None
        self.ignoreUntilSemicolon = False
        self.decaylist = {}
        self.cdecay_delayed = []
        cmd.Cmd.__init__(self, "tab", stdin, stdout)

    def default(self, line):
        if line[:1] == "#" or "Photos" in line:
            pass
        elif self.ignoreUntilSemicolon:
            if ";" in line:
                self.ignoreUntilSemicolon = False
        elif self.file_parse_status == "Decay":
            self.addline(line)
        else:
            cmd.Cmd.default(self, line)

    def emptyline(self):
        return ""

    #    def precmd(self, line):
    #        print line
    #        return line

    def do_EOF(self, line):
        return True

    def do_Define(self, line):
        pass

    def do_Alias(self, line):
        pass

    def do_ChargeConj(self, line):
        pass

    def do_JetSetPar(self, line):
        pass

    def do_SetLineshapePW(self, line):
        pass

    def do_ModelAlias(self, line):
        if ";" not in line:
            self.ignoreUntilSemicolon = True

    def do_Decay(self, line):
        if self.file_parse_status == "Decay":
            raise Exception("Repeated Decay statement: %s" % line)
        self.file_parse_status = "Decay"
        particle = Particle.from_string(line.split()[0])
        self.current_decay_top = AllowedDecays(particle)

    def do_CDecay(self, line):
        #        print 'CDecay for', line
        if self.file_parse_status == "Decay":
            raise Exception("Cannot do CDecay in Decay block: %s" % line)
        conj = Particle.from_string(line.split()[0]).invert()
        if conj not in self.decaylist:
            print(line)
            self.cdecay_delayed.append(line)
            return
        self.current_decay_top = AllowedDecays(line.split()[0])
        #        print conj
        for cdecay in self.decaylist[conj].decays:
            #            print cdecay.daughters
            ndecay = Decay()
            ndecay.bf = cdecay.bf
            for dau in cdecay.daughters:
                #                print cdecay.daughters
                ndecay.daughters[Particle.from_string(dau).invert()] = cdecay.daughters[
                    dau
                ]
            #            print                 ndecay.daughters

            #            print cdecay.daughters, ndecay.daughters
            #        print line
            self.current_decay_top.decays.append(ndecay)
        self.decaylist[self.current_decay_top.decay_of] = self.current_decay_top
        self.current_decay_top = None

    def do_End(self, line):
        #        return self.do_EOF(line)
        if self.cdecay_delayed != []:
            print("Ought to be [] 0!:", self.cdecay_delayed, len(self.cdecay_delayed))
        while self.cdecay_delayed:
            self.do_CDecay(self.cdecay_delayed.pop())

    def addline(self, line):
        spl = line.split()
        try:
            bf = float(spl[0])
        except Exception:
            raise RuntimeError("Cannot parse decay line: %s" % line)
        #        mod_found = False
        #         for x in known_models:
        #             if x in line:
        #                 mod_found = True
        #         if not mod_found:
        #             print '\n', line
        while spl[-1][-1:] != ";":
            if self.use_rawinput:
                line = " ".join((line, input()))
            else:
                line = " ".join((line, self.stdin.readline()))
            spl = line.split()
        killindex = None
        i = 0
        while killindex is None and i < len(spl):
            if spl[i][-1] == ";":
                spl[i] = spl[i][:-1]
            if spl[i] in known_models:
                killindex = i
            i += 1
        if killindex is None:
            print(spl)
            raise Exception("No decay model specified: %s" % line)
        decay = Decay()
        decay.bf = bf
        for part in spl[1:killindex]:
            if part in decay.daughters:
                decay.daughters[part] += 1
            else:
                decay.daughters[part] = 1

        assert self.current_decay_top is not None
        self.current_decay_top.decays.append(decay)

    def do_Enddecay(self, line):
        if self.file_parse_status != "Decay":
            raise Exception("Enddecay with no decay: %s" % line)
        self.file_parse_status = ""
        assert self.current_decay_top is not None
        self.decaylist[self.current_decay_top.decay_of] = self.current_decay_top
        self.current_decay_top = None

    def do_hi(self, aft):
        print("hi", aft)


class interactive(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.decaylist = {}
        # These are particles we don't decay
        self.termpart = ["pi0", "K_S0"]

    def do_readfile(self, line):
        "Read a file in (defaults to the one built into this package)"
        fname = defdecfile if line == "" else line
        with open(fname, "r") as infile:
            q = decparser(stdin=infile)
            q.use_rawinput = False
            q.cmdloop()
            self.decaylist = q.decaylist

    def do_dump(self, line):
        #        print line
        lpart = self.decaylist if line == "" else line.split()
        for part in lpart:
            if part not in self.decaylist:
                print("Unknown particle %s" % part)
            else:
                print("-------------", part, "-------------")
                for decay in self.decaylist[part].decays:
                    print(decay.bf, end=" ")
                    print(decay.daughters_to_string(), end=" ")
                    print()

    def do_termpart(self, line):
        if line == "":
            print(self.termpart)
        elif len(line.split()) == 2:
            cmd = line.split()[0].lower()
            if cmd not in ("add", "del"):
                print("Unknown command %s" % cmd)
            else:
                part = line.split()[1]
                if cmd == "add" and part not in self.termpart:
                    self.termpart.append(part)
                elif cmd == "del":
                    if part not in self.termpart:
                        print("%s not in list of terminating particles" % part)
                    else:
                        del self.termpart[self.termpart.index(part)]
        else:
            print("Syntax: termpart [(add|del) particle]")

    def do_exit(self, line):
        return self.do_EOF(line)

    def do_quit(self, line):
        return self.do_EOF(line)

    def do_final(self, line):
        #         predeclist = self.decaylist[line].decays[:]
        #         declist = []
        #         for dec in predeclist:
        #             declist.append([[],dec])
        #         decaytable = self.decaylist.copy()
        #         for j in self.termpart:
        #             del decaytable[j]
        #         last = []
        #         while last != declist:
        #             last = declist[:]
        #             recurseOneLevel(declist, decaytable)
        declist = self.getDecList(line)
        declist = compactDecayList(declist)
        declist.sort(key=lambda x: x.bf, reverse=True)
        for dec in declist:
            #            print dec
            print(dec.bf, dec.daughters_to_string())

    def getDecList(self, line):
        predeclist = self.decaylist[line].decays[:]
        declist = [[[(line, dec)], dec] for dec in predeclist]
        #            print dec
        #            declist.append([[],dec])
        #         dlist = DaughterList()
        #         dlist.add(line)
        #         declist = [[[],Decay(1,dlist)]]
        decaytable = self.decaylist.copy()
        for j in self.termpart:
            del decaytable[j]
        last = []  # type: ignore
        while last != declist:
            last = declist[:]
            recurseOneLevel(declist, decaytable)
        return declist

    def do_explain(self, line):
        part = input("Parent particle? ")
        if part not in self.decaylist:
            print("%s not known. Have you read the file yet?" % part)
            return
        final = input("Final state? ").split()
        finalhash = {}  # type: dict
        termpartcpy = self.termpart[:]
        for p in final:
            finalhash[p] = finalhash.get(p, 0) + 1
            if p in self.decaylist and p not in self.termpart:
                self.termpart.append(p)
        declist = self.getDecList(part)
        self.termpart[:] = termpartcpy
        sublist = [dec for dec in declist if dec[1].daughters == finalhash]
        sublist.sort(key=lambda x: x[1].bf, reverse=True)
        for entry in sublist:
            print(entry[1].bf, end=" ")
            if len(entry[0]) == 0:
                print("Direct ")
            else:
                print("Chain: ")
                for e2 in entry[0]:
                    #                    print e2
                    print("\t", e2[0], "->", e2[1].daughters_to_string())

    def do_oneshot(self, line):
        declist = self.decaylist[line].decays[:]
        recurseOneLevel(declist, self.decaylist)
        for dec in declist:
            print(dec.bf, dec.daughters)

    def do_EOF(self, line):
        print()
        return True


def recurseOneLevel(decaylist, decaytable):
    """Do one sweep at replacing particles with daughters."""
    """decaylist should be tuple of [[(particle, decay) ...], finalstate]"""
    rv = []
    for decay in decaylist:
        # Only do one daughter!
        toexpand = None
        for dau in decay[1].daughters:
            if toexpand is None and dau in decaytable:
                toexpand = dau
        if toexpand is None:
            rv.append(decay)
        else:
            for subdec in decaytable[toexpand].decays:
                chain = decay[0][:]
                chain.append((toexpand, subdec))
                dlist = DaughterList()
                dlist.update(decay[1].daughters)
                dlist[toexpand] -= 1
                if dlist[toexpand] == 0:
                    del dlist[toexpand]
                for entry in subdec.daughters:
                    dlist[entry] = dlist.get(entry, 0) + subdec.daughters[entry]
                newdecay = Decay(decay[1].bf * subdec.bf, dlist)
                rv.append([chain, newdecay])
    decaylist[:] = rv


def compactDecayList(decaylist):
    rv = []
    used_daughter_list = []
    for decay in decaylist:
        if decay[1].daughters not in used_daughter_list:
            rv.append(Decay(decay[1].bf, decay[1].daughters))
            used_daughter_list.append(decay[1].daughters)
        else:
            for dec2 in rv:
                if dec2.daughters == decay[1].daughters:
                    dec2.bf += decay[1].bf
    return rv


if __name__ == "__main__":
    #     decparser().cmdloop(
    #         """Hi! We are beginning the loop."""
    #         )
    #    q = decparser(stdin=file('/home/ponyisi/DECAY.DEC', 'r'), stdout=sys.stdout)
    #    q.use_rawinput = False
    #    q.cmdloop()
    #    print q.decaylist
    interactive().cmdloop(
        "Hi! Welcome to the DECAY.DEC parser program.\n"
        "Blame ponyisi@lepp if any problems arise."
    )
