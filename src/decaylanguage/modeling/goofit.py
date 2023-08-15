# Copyright (c) 2018-2023, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

"""
This is a GooFit adaptor for amplitude chain.
"""


from __future__ import annotations

from enum import Enum

import pandas as pd
from particle import SpinType
from particle.particle.utilities import programmatic_name

from ..utils import LineFailure
from .amplitudechain import LS, AmplitudeChain


class SF_4Body(Enum):
    DtoPP1_PtoSP2_StoP3P4 = 0
    DtoPP1_PtoVP2_VtoP3P4 = 1
    DtoV1V2_V1toP1P2_V2toP3P4_S = 2
    DtoV1V2_V1toP1P2_V2toP3P4_P = 3
    DtoV1V2_V1toP1P2_V2toP3P4_D = 4
    DtoAP1_AtoVP2_VtoP3P4 = 5
    DtoAP1_AtoVP2Dwave_VtoP3P4 = 6
    DtoVS_VtoP1P2_StoP3P4 = 7
    DtoV1P1_V1toV2P2_V2toP3P4 = 8
    DtoAP1_AtoSP2_StoP3P4 = 9
    DtoTP1_TtoVP2_VtoP3P4 = 10
    FF_12_34_L1 = 11
    FF_12_34_L2 = 12
    FF_123_4_L1 = 13
    FF_123_4_L2 = 14
    ONE = 15


known_spinfactors = {
    "DtoA1P1_A1toS2P2_S2toP3P4": (SF_4Body.DtoAP1_AtoSP2_StoP3P4,),
    "DtoA1P1_A1toV2P2Dwave_V2toP3P4": (SF_4Body.DtoAP1_AtoVP2Dwave_VtoP3P4,),
    "DtoA1P1_A1toV2P2_V2toP3P4": (SF_4Body.DtoAP1_AtoVP2Dwave_VtoP3P4,),
    "DtoS1S2_S1toP1P2_S2toP3P4": (SF_4Body.ONE,),
    "DtoT1P1_T1toV2P2_V2toP3P4": (SF_4Body.DtoTP1_TtoVP2_VtoP3P4,),
    "DtoV1S2_V1toP1P2_S2toP3P4": (SF_4Body.DtoVS_VtoP1P2_StoP3P4,),
    "DtoV1V2_V1toP1P2_V2toP3P4": (SF_4Body.DtoV1V2_V1toP1P2_V2toP3P4_S,),
    "DtoV1V2_V1toP1P2_V2toP3P4_D": (SF_4Body.DtoV1V2_V1toP1P2_V2toP3P4_D,),
    "DtoV1V2_V1toP1P2_V2toP3P4_P": (SF_4Body.DtoV1V2_V1toP1P2_V2toP3P4_P,),
    "Dtos1P1_s1toS2P2_S2toP3P4": (SF_4Body.DtoPP1_PtoSP2_StoP3P4,),
    "Dtos1P1_s1toV2P2_V2toP3P4": (SF_4Body.DtoPP1_PtoVP2_VtoP3P4,),
}


def sprint(stype):
    if stype in {SpinType.PseudoTensor, SpinType.PseudoScalar}:
        return stype.name[6].lower()
    return stype.name[0]


class DecayStructure(Enum):
    FF_12_34 = 0
    FF_1_2_34 = 1


class GooFitChain(AmplitudeChain):
    """
    Class to read an AmpGen options file and return GooFit C++ code.
    """

    __slots__ = ()

    pars: pd.DataFrame = None
    consts: pd.DataFrame = None

    @classmethod
    def make_intro(cls, all_states):
        """
        Write out definitions of constant variables and vectors to hold intermediate values.
        """
        header = f"    // Event type: {all_states[0]} ->  "
        header += "   ".join(f"{b} ({a})" for a, b in enumerate(all_states[1:]))

        header += """\n
    std::vector<std::vector<Lineshape*>> line_factor_list;
    std::vector<std::vector<SpinFactor*>> spin_factor_list;
    std::vector<Amplitude*> amplitudes_list;

"""

        final_particles = set(all_states)

        for particle in final_particles:
            name = particle.programmatic_name.upper()
            header += f"    constexpr fptype {name:8} {{ {particle.mass:<14.8g} }};\n"

        header += "\n"

        for particle in cls.all_particles - final_particles:
            name = particle.programmatic_name
            header += "    Variable {name:15} {{ {nameQ:21}, {particle.mass:<10.8g} }};\n".format(
                name=name + "_M", nameQ='"' + name + '_M"', particle=particle
            )
            header += "    Variable {name:15} {{ {nameQ:21}, {particle.width:<10.8g} }};\n".format(
                name=name + "_W", nameQ='"' + name + '_W"', particle=particle
            )

        header += "\n"
        header += "    DK3P_DI.meson_radius = 5;\n"
        header += "    DK3P_DI.particle_masses = {{{}}};\n".format(
            ", ".join(x.programmatic_name.upper() for x in all_states)
        )

        return header

    @property
    def decay_structure(self):
        """
        Determine if decay proceeds via two resonances or cascade decay.
        """
        if len(self[0]) == 2 and len(self[1]) == 2:
            return DecayStructure.FF_12_34
        return DecayStructure.FF_1_2_34

    @property
    def formfactor(self):
        """
        Return form factor based on relative angular momentum L.
        """
        norm = self.decay_structure == DecayStructure.FF_12_34
        if self.L == 0:
            return None
        if self.L == 1:
            return SF_4Body.FF_12_34_L1 if norm else SF_4Body.FF_123_4_L1
        if self.L == 2:
            return SF_4Body.FF_12_34_L2 if norm else SF_4Body.FF_123_4_L2

        raise NotImplementedError(f"L = {self.L} is not implemented")

    def spindetails(self):
        """
        Return string with spin structure.
        """
        if self.decay_structure == DecayStructure.FF_12_34:
            a = f"{sprint(self[0].particle.spin_type)}1"
            b = f"{sprint(self[1].particle.spin_type)}2"
            return (
                "Dto{a}{b}_{a}toP1P2_{b}toP3P4"
                + (
                    "_{self.spinfactor}"
                    if self.spinfactor and self.spinfactor != "S"
                    else ""
                )
            ).format(self=self, a=a, b=b)

        a = f"{sprint(self[0].particle.spin_type)}1"
        if self[0].daughters:
            b = f"{sprint(self[0][0].particle.spin_type)}2"
        else:
            raise LineFailure(self, f"{self[0]} has no daughters")
        wave = (
            f"{self[0].spinfactor}wave"
            if self[0].spinfactor and self[0].spinfactor != "S"
            else ""
        )
        return f"Dto{a}P1_{a}to{b}P2{wave}_{b}toP3P4"

    @property
    def spinfactors(self):
        """
        Check if the spin structure is known and return it together with the form factor.
        """
        if self.spindetails() in known_spinfactors:
            spinfactor = list(known_spinfactors[self.spindetails()])
            if self.L > 0:
                spinfactor.append(self.formfactor)
            return spinfactor

        raise LineFailure(
            self,
            f"Spinfactors not currently included!: {self.spindetails()}",
        )

        # if self.decay_structure == DecayStructure.FF_12_34 :
        #    if (self[0].particle.spin_type in {SpinType.Vector, SpinType.Axial}
        #        and self[1].particle.spin_type in {SpinType.Vector, SpinType.Axial}):
        #
        #        if self.spinfactor == 'D':
        #            return (SF_4Body.DtoV1V2_V1toP1P2_V2toP3P4_D, SF_4Body.FF_12_34_L2)
        #        elif self.spinfactor == 'P':
        #            return (SF_4Body.DtoV1V2_V1toP1P2_V2toP3P4_P, SF_4Body.FF_12_34_L1)
        #        elif self.spinfactor == 'S':
        #            return (SF_4Body.DtoV1V2_V1toP1P2_V2toP3P4_S,)
        # else:
        #    if (self[0].particle.spin_type == SpinType.Axial and
        #        self[0][0].particle.spin_type == SpinType.Vector):
        #        if self.spinfactor == 'D':
        #            return (SF_4Body.DtoAP1_AtoVP2Dwave_VtoP3P4, SF_4Body.FF_12_34_L2)
        #        else:
        #            return (SF_4Body.DtoAP1_AtoVP2_VtoP3P4, SF_4Body.FF_12_34_L1) # L1?

    @classmethod
    def make_pars(cls):
        """
        Write out the parameters used in the amplitudes.
        """
        headerlist = []
        header = ""

        for name, par in cls.pars.iterrows():
            pname = programmatic_name(name)
            if not par.fix:
                headerlist.append(
                    f'    Variable {pname} {{"{name}", {par.value}, {par.error} }};'
                )
            else:
                headerlist.append(f'    Variable {pname} {{"{name}", {par.value} }};')

        def strip_pararray(pars, begin, convert=lambda x: x):
            mysplines = pars.index[pars.index.str.contains(begin, regex=False)]
            vals = convert(mysplines.str.slice(len(begin))).astype(int)
            series = pd.Series(mysplines, vals).sort_index()
            return ",\n".join(series.map(lambda x: "        " + programmatic_name(x)))

        if not GooFitChain.consts.empty:
            splines = GooFitChain.consts.index[
                GooFitChain.consts.index.str.contains("Spline")
            ]
            splines = set(
                splines.str.replace("::Spline::N", "")
                .str.replace("::Spline::Min", "")
                .str.replace("::Spline::Max", "")
            )

            for spline in splines:
                header += (
                    "\n    std::vector<Variable> "
                    + programmatic_name(spline)
                    + "_SplineArr {{\n"
                )
                header += strip_pararray(GooFitChain.pars, f"{spline}::Spline::Gamma::")
                header += "\n    }};\n"

        f_scatt = GooFitChain.pars.index[GooFitChain.pars.index.str.contains("f_scatt")]
        if len(f_scatt):
            header += "\n    std::vector<Variable> f_scatt {{\n"
            header += strip_pararray(GooFitChain.pars, "f_scatt")
            header += "\n    }};\n"

        IS_mat = GooFitChain.pars.index[GooFitChain.pars.index.str.contains("IS_p")]
        if len(IS_mat):
            names = ("pipi", "KK", "4pi", "EtaEta", "EtapEta", "mass")

            def convert(x):
                i = x.str.split("_").str[0]
                j = x.str.split("_").str[1].map(names.index)
                return i.astype(int) * 6 + j.astype(int)

            header += "\n    std::vector<Variable>  IS_poles {{\n"
            header += strip_pararray(GooFitChain.pars, "IS_p", convert)
            header += "\n    }};\n"

        return "\n".join(headerlist) + "\n" + header

    def make_lineshape(self, structure, masses):
        """
        Write out the line shapes. Each kind of line shape is treated separately.
        """
        name = self.name
        par = self.particle.programmatic_name
        a = structure[0] + 1
        b = structure[1] + 1
        # order assignment
        if a > b:
            a, b = b, a
        L = self.L
        radius = 5.0 if "c" in self.particle.quarks.lower() else 1.5

        if self.ls_enum == LS.RBW:
            return 'new Lineshapes::RBW("{name}", {par}_M, {par}_W, {L}, {masses}, FF::BL2)'.format(
                name=name, par=par, L=L, masses=masses
            )
        if self.ls_enum == LS.GSpline:
            min_ = self.__class__.consts.loc[f"{self.name}::Spline::Min", "value"]
            max_ = self.__class__.consts.loc[f"{self.name}::Spline::Max", "value"]
            N = self.__class__.consts.loc[f"{self.name}::Spline::N", "value"]
            AdditionalVars = programmatic_name(self.name) + "_SplineArr"
            return """new Lineshapes::GSpline("{name}", {par}_M, {par}_W, {L}, {masses}, FF::BL2,
            {radius}, {AdditionalVars}, Lineshapes::spline_t({min},{max},{N}))""".format(
                name=name,
                par=par,
                L=L,
                masses=masses,
                radius=radius,
                AdditionalVars=AdditionalVars,
                min=min_,
                max=max_,
                N=int(N),
            )

        if self.ls_enum == LS.kMatrix:
            _, poleprod, pterm = self.lineshape.split(".")
            is_pole = "true" if poleprod == "pole" else "false"
            return f"""new Lineshapes::kMatrix("{name}", {pterm}, {is_pole},
            sA_0, sA, s0_prod, s0_scatt,
            f_scatt, IS_poles,
            {par}_M, {par}_W, {L}, {masses}, FF::BL2, {radius})"""

        if self.ls_enum == LS.FOCUS:
            _, mod = self.lineshape.split(".")
            return (
                f'new Lineshapes::FOCUS("{name}", Lineshapes::FOCUS::Mod::{mod},'
                f" {par}_M, {par}_W, {L}, {masses}, FF::BL2, {radius})"
            )

        raise NotImplementedError(f"Unimplemented GooFit Lineshape {self.ls_enum.name}")

    def make_spinfactor(self, final_states):
        """
        Write out the spin factor and push it to a vector.
        """
        spin_factors = self.spinfactors

        intro = "    spin_factor_list.push_back(std::vector<SpinFactor*>({\n"
        factor = []
        for structure in self.list_structure(final_states):
            if not spin_factors:
                factor.append(
                    "        // TODO: Spin factor not implemented yet for {spindet}".format(
                        spindet=self.spindetails()
                    )
                )
            else:
                for spin_factor in spin_factors:
                    structure_list = ", ".join(map(str, structure))
                    factor.append(
                        '        new SpinFactor("SF", SF_4Body::{spin_factor.name:37}, {structure_list})'.format(
                            spin_factor=spin_factor, structure_list=structure_list
                        )
                    )
        exit_ = "\n    }));\n"
        return intro + ",\n".join(factor) + exit_

    def make_linefactor(self, final_states):
        """
        Write out the line shape and push it to a vector.
        """
        intro = "    line_factor_list.push_back(std::vector<Lineshape*>{\n"
        factor = []

        for structure in self.list_structure(final_states):
            if self.decay_structure == DecayStructure.FF_12_34:
                mass1 = f"M_{structure[0]+1}{structure[1]+1}"
                mass2 = f"M_{structure[2]+1}{structure[3]+1}"
            else:
                mass1 = f"M_{structure[0]+1}{structure[1]+1}_{structure[2]+1}"
                mass2 = f"M_{structure[0]+1}{structure[1]+1}"
            masses = [mass1, mass2]
            for i_mass, sub in enumerate(self.vertexes):
                factor.append(
                    "        " + sub.make_lineshape(structure, masses[i_mass])
                )
        exit_ = "\n    });\n"
        return intro + ",\n".join(factor) + exit_

    def make_amplitude(self, final_states):
        """
        Write out the amplitude and push it to a vector.
        """
        n = len(self.list_structure(final_states))
        fix = "true" if self.fix else "false"
        return (
            "    amplitudes_list.push_back(new Amplitude{{\n"
            '        "{self!s}",\n'
            '        mkvar("{self!s}_r", {fix}, {self.amp.real:.6}, {self.err.real:.6}),\n'
            '        mkvar("{self!s}_i", {fix}, {self.amp.imag:.6}, {self.err.imag:.6}),\n'
            "        line_factor_list.back(),\n"
            "        spin_factor_list.back(),\n"
            "        {n}}});\n\n"
            "    DK3P_DI.amplitudes_B.push_back(amplitudes_list.back());".format(
                self=self, fix=fix, n=n
            )
        )

    def to_goofit(self, final_states):
        """
        Write the vectors with the spin factors, line shapes and amplitudes.
        """
        return (
            "    // "
            + str(self)
            + "\n\n"
            + self.make_spinfactor(final_states)
            + "\n"
            + self.make_linefactor(final_states)
            + "\n"
            + self.make_amplitude(final_states)
        )

    @classmethod
    def read_ampgen(cls, *args, **kargs):
        """
        Read in an AmpGen file.

        Returns
        ---------
        Array of AmplitudeChains, event type.
        """
        (
            line_arr,
            GooFitChain.pars,
            GooFitChain.consts,
            all_states,
        ) = super().read_ampgen(*args, **kargs)
        return line_arr, all_states


class GooFitPyChain(AmplitudeChain):
    """
    Class to read an AmpGen options file and return a GooFit Python script.
    """

    __slots__ = ()

    pars: pd.DataFrame = None
    consts: pd.DataFrame = None

    @classmethod
    def make_intro(cls, all_states):
        """
        Write out definitions of constant variables and lists to hold intermediate values.
        """
        header = f"#Event type: {all_states[0]} ->  "
        header += "   ".join(f"{b} ({a})" for a, b in enumerate(all_states[1:]))
        header += "\nfrom goofit import *\n"
        header += "\nDK3P_DI = DecayInfo4()\n"

        header += (
            "\nline_factor_list = []"
            "\nspin_factor_list = []"
            "\namplitudes_list = []\n"
        )

        final_particles = set(all_states)

        for particle in final_particles:
            name = particle.programmatic_name.upper()
            header += f"{name:8} = {particle.mass:<14.8g}\n"

        header += "\n"

        for particle in cls.all_particles - final_particles:
            name = particle.programmatic_name
            header += (
                "{name:15} = Variable({nameQ:21}, {particle.mass:<10.8g})\n".format(
                    name=name + "_M", nameQ='"' + name + '_M"', particle=particle
                )
            )
            header += (
                "{name:15} = Variable({nameQ:21}, {particle.width:<10.8g})\n".format(
                    name=name + "_W", nameQ='"' + name + '_W"', particle=particle
                )
            )

        header += "\n"
        header += "DK3P_DI.meson_radius = 5\n"
        header += "DK3P_DI.particle_masses = ({})\n".format(
            ", ".join(x.programmatic_name.upper() for x in all_states)
        )

        return header

    @property
    def decay_structure(self):
        """
        Determine if the decay proceeds via two resonances or a cascade decay.
        """
        if len(self[0]) == 2 and len(self[1]) == 2:
            return DecayStructure.FF_12_34
        return DecayStructure.FF_1_2_34

    @property
    def formfactor(self):
        """
        Return the form factor based on relative angular momentum L.
        """
        norm = self.decay_structure == DecayStructure.FF_12_34
        if self.L == 0:
            return None
        if self.L == 1:
            return SF_4Body.FF_12_34_L1 if norm else SF_4Body.FF_123_4_L1
        if self.L == 2:
            return SF_4Body.FF_12_34_L2 if norm else SF_4Body.FF_123_4_L2

        raise NotImplementedError(f"L = {self.L} is not implemented")

    def spindetails(self):
        """
        Return string with spin structure.
        """
        if self.decay_structure == DecayStructure.FF_12_34:
            a = f"{sprint(self[0].particle.spin_type)}1"
            b = f"{sprint(self[1].particle.spin_type)}2"
            return (
                "Dto{a}{b}_{a}toP1P2_{b}toP3P4"
                + (
                    "_{self.spinfactor}"
                    if self.spinfactor and self.spinfactor != "S"
                    else ""
                )
            ).format(self=self, a=a, b=b)

        a = f"{sprint(self[0].particle.spin_type)}1"
        if self[0].daughters:
            b = f"{sprint(self[0][0].particle.spin_type)}2"
        else:
            raise LineFailure(self, f"{self[0]} has no daughters")
        wave = (
            f"{self[0].spinfactor}wave"
            if self[0].spinfactor and self[0].spinfactor != "S"
            else ""
        )
        return f"Dto{a}P1_{a}to{b}P2{wave}_{b}toP3P4"

    @property
    def spinfactors(self):
        """
        Check if the spin structure is known and return it together with the form factor.
        """
        if self.spindetails() in known_spinfactors:
            spinfactor = list(known_spinfactors[self.spindetails()])
            if self.L > 0:
                spinfactor.append(self.formfactor)
            return spinfactor

        raise LineFailure(
            self,
            f"Spinfactors not currently included!: {self.spindetails()}",
        )

        # if self.decay_structure == DecayStructure.FF_12_34 :
        #    if (self[0].particle.spin_type in {SpinType.Vector, SpinType.Axial}
        #        and self[1].particle.spin_type in {SpinType.Vector, SpinType.Axial}):
        #
        #        if self.spinfactor == 'D':
        #            return (SF_4Body.DtoV1V2_V1toP1P2_V2toP3P4_D, SF_4Body.FF_12_34_L2)
        #        elif self.spinfactor == 'P':
        #            return (SF_4Body.DtoV1V2_V1toP1P2_V2toP3P4_P, SF_4Body.FF_12_34_L1)
        #        elif self.spinfactor == 'S':
        #            return (SF_4Body.DtoV1V2_V1toP1P2_V2toP3P4_S,)
        # else:
        #    if (self[0].particle.spin_type == SpinType.Axial and
        #        self[0][0].particle.spin_type == SpinType.Vector):
        #        if self.spinfactor == 'D':
        #            return (SF_4Body.DtoAP1_AtoVP2Dwave_VtoP3P4, SF_4Body.FF_12_34_L2)
        #        else:
        #            return (SF_4Body.DtoAP1_AtoVP2_VtoP3P4, SF_4Body.FF_12_34_L1) # L1?

    @classmethod
    def make_pars(cls):
        """
        Write out the parameters used in the amplitudes.
        """
        headerlist = []
        header = ""

        for name, par in cls.pars.iterrows():
            pname = programmatic_name(name)
            if not par.fix:
                headerlist.append(
                    f'{pname} = Variable("{name}", {par.value}, {par.error} )'
                )
            else:
                headerlist.append(f'{pname} = Variable("{name}", {par.value})')

        def strip_pararray(pars, begin, convert=lambda x: x):
            mysplines = pars.index[pars.index.str.contains(begin, regex=False)]
            vals = convert(mysplines.str.slice(len(begin))).astype(int)
            series = pd.Series(mysplines, vals).sort_index()
            return ",\n".join(series.map(lambda x: "        " + programmatic_name(x)))

        if not GooFitPyChain.consts.empty:
            splines = GooFitPyChain.consts.index[
                GooFitPyChain.consts.index.str.contains("Spline")
            ]
            splines = set(
                splines.str.replace("::Spline::N", "")
                .str.replace("::Spline::Min", "")
                .str.replace("::Spline::Max", "")
            )

            for spline in splines:
                header += "\n" + programmatic_name(spline) + "_SplineArr =  [\n"
                header += strip_pararray(
                    GooFitPyChain.pars, f"{spline}::Spline::Gamma::"
                )
                header += "]\n"

        f_scatt = GooFitPyChain.pars.index[
            GooFitPyChain.pars.index.str.contains("f_scatt")
        ]
        if len(f_scatt):
            header += "f_scatt = [\n"
            header += strip_pararray(GooFitPyChain.pars, "f_scatt")
            header += "]\n"

        IS_mat = GooFitPyChain.pars.index[GooFitPyChain.pars.index.str.contains("IS_p")]
        if len(IS_mat):
            names = ("pipi", "KK", "4pi", "EtaEta", "EtapEta", "mass")

            def convert(x):
                i = x.str.split("_").str[0]
                j = x.str.split("_").str[1].map(names.index)
                return i.astype(int) * 6 + j.astype(int)

            header += "\nIS_poles = [\n"
            header += strip_pararray(GooFitPyChain.pars, "IS_p", convert)
            header += "]\n"

        return "\n".join(headerlist) + "\n" + header

    def make_lineshape(self, structure, masses):
        """
        Write out the line shapes. Each kind of line shape is treated separately.
        """
        name = self.name
        par = self.particle.programmatic_name
        a = structure[0] + 1
        b = structure[1] + 1
        # order assignment
        if a > b:
            a, b = b, a
        L = int(self.L)
        radius = 5.0 if "c" in self.particle.quarks.lower() else 1.5

        if self.ls_enum == LS.RBW:
            return f'Lineshapes.RBW("{name}", {par}_M, {par}_W, {L}, {masses}, FF.BL2)'
        if self.ls_enum == LS.GSpline:
            min_ = self.__class__.consts.loc[f"{self.name}::Spline::Min", "value"]
            max_ = self.__class__.consts.loc[f"{self.name}::Spline::Max", "value"]
            N = self.__class__.consts.loc[f"{self.name}::Spline::N", "value"]
            AdditionalVars = programmatic_name(self.name) + "_SplineArr"
            return """Lineshapes.GSpline("{name}", {par}_M, {par}_W, {L}, {masses}, FF.BL2,
            {radius}, {AdditionalVars}, ({min},{max},{N}))""".format(
                name=name,
                par=par,
                L=L,
                masses=masses,
                radius=radius,
                AdditionalVars=AdditionalVars,
                min=min_,
                max=max_,
                N=int(N),
            )

        if self.ls_enum == LS.kMatrix:
            _, poleprod, pterm = self.lineshape.split(".")
            is_pole = "True" if poleprod == "pole" else "False"
            return f"""Lineshapes.kMatrix("{name}", {pterm}, {is_pole},
            sA_0, sA, s0_prod, s0_scatt,
            f_scatt, IS_poles,
            {par}_M, {par}_W, {L}, {masses}, FF.BL2, {radius})"""

        if self.ls_enum == LS.FOCUS:
            _, mod = self.lineshape.split(".")
            return (
                f'Lineshapes.FOCUS("{name}", Lineshapes.FocusMod.{mod},'
                f" {par}_M, {par}_W, {L}, {masses}, FF.BL2, {radius})"
            )

        raise NotImplementedError(f"Unimplemented GooFit Lineshape {self.ls_enum.name}")

    def make_spinfactor(self, final_states):
        """
        Write out the spin factor and push it to a vector.
        """
        spin_factors = self.spinfactors

        intro = "spin_factor_list.append((\n"
        factor = []
        for structure in self.list_structure(final_states):
            if not spin_factors:
                factor.append(
                    "        // TODO: Spin factor not implemented yet for {spindet}".format(
                        spindet=self.spindetails()
                    )
                )
            else:
                for spin_factor in spin_factors:
                    structure_list = ", ".join(map(str, structure))
                    factor.append(
                        '        SpinFactor("SF", SF_4Body.{spin_factor.name:37}, {structure_list})'.format(
                            spin_factor=spin_factor, structure_list=structure_list
                        )
                    )
        exit_ = "))\n"
        return intro + ",\n".join(factor) + exit_

    def make_linefactor(self, final_states):
        """
        Write out the line shape and push it to a vector.
        """
        intro = "line_factor_list.append((\n"
        factor = []
        for structure in self.list_structure(final_states):
            if self.decay_structure == DecayStructure.FF_12_34:
                mass1 = f"M_{structure[0]+1}{structure[1]+1}"
                mass2 = f"M_{structure[2]+1}{structure[3]+1}"
            else:
                mass1 = f"M_{structure[0]+1}{structure[1]+1}_{structure[2]+1}"
                mass2 = f"M_{structure[0]+1}{structure[1]+1}"
            masses = [mass1, mass2]
            for i_mass, sub in enumerate(self.vertexes):
                factor.append(
                    "        " + sub.make_lineshape(structure, masses[i_mass])
                )
        exit_ = "))\n"
        return intro + ",\n".join(factor) + exit_

    def make_amplitude(self, final_states):
        """
        Write out the amplitude and push it to a vector.
        """
        n = len(self.list_structure(final_states))
        real_coeff = (
            f'Variable("{self!s}_r", {self.amp.real:.6})'
            if self.fix
            else f'Variable("{self!s}_r", {self.amp.real:.6},{self.err.real:.6}, 0., 1000.)'
        )
        imag_coeff = (
            f'Variable("{self!s}_i", {self.amp.imag:.6})'
            if self.fix
            else f'Variable("{self!s}_r", {self.amp.imag:.6},{self.err.imag:.6}, 0., 1000.)'
        )
        return (
            "amplitudes_list.append(Amplitude(\n"
            f'        "{self!s}",\n'
            f"        {real_coeff},\n"
            f"        {imag_coeff},\n"
            "        line_factor_list[-1],\n"
            "        spin_factor_list[-1],\n"
            f"        {n}))\n\n"
        )

    def to_goofit(self, final_states):
        """
        Write the lists with the spin factors, line shapes and amplitudes.
        """
        return (
            "#"
            + str(self)
            + "\n\n"
            + self.make_spinfactor(final_states)
            + "\n"
            + self.make_linefactor(final_states)
            + "\n"
            + self.make_amplitude(final_states)
            + "\n"
        )

    @classmethod
    def read_ampgen(cls, *args, **kargs):
        """
        Read in the AmpGen file.

        Returns
        ---------
        Array of AmplitudeChains, event type.
        """
        (
            line_arr,
            GooFitPyChain.pars,
            GooFitPyChain.consts,
            all_states,
        ) = super().read_ampgen(*args, **kargs)
        return line_arr, all_states
