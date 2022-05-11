"""
(c) Joaquim Carvalho 2021.
MIT License, no warranties.

Grammars for parsing lines from alumni records

"""
from collections import namedtuple
from typing import Optional, Type, Union
import json

import pyparsing as pp


def preserve_original(s: str, l: int, t: pp.ParseResults):
    if 'repeat' in t.keys():  # Remove the repeat prefix
        prefix = t.repeat
        line = s[s.startswith(prefix) and len(prefix):]
    else:
        line = s
    t['original'] = line
    return t


# Grammar rules
# Basic
PTWORD = pp.Word(pp.alphas + pp.alphas8bit)
PNAME = pp.Group(pp.OneOrMore(PTWORD)).setResultsName("name")
LPARENT, RPARENT = map(pp.Literal, "()")
VIDE_SEP = pp.Word('.' + '/' + '-', max=1)
VIDE = pp.Literal(', vide') | pp.Literal('; vide') | pp.Literal(',vide')

# Names
# We have Manuel Rodrigues vide Manuel Rodrigues Carvalho
#         Manuel Rodrigues (Colégio dos Militares)
#
# ver António de Almeida (D., Porcionista do Colégio de São Paulo)
#
NAME_VIDE = (PNAME("nome1") + VIDE + PNAME("nome2")).setResultsName(
    "name_with_vide")
NAME_WITH_PARENTESIS = PNAME("nome") + pp.Optional(',') + LPARENT + \
                       pp.SkipTo(RPARENT).setResultsName("nota") + RPARENT
NAME_WITH_VIDE_PARENTESIS = ( PNAME("nome1") + LPARENT + \
                       pp.SkipTo(RPARENT).setResultsName("nota") + RPARENT + VIDE + PNAME("nome2")).setResultsName(
    "name_with_vide",True)


# we have a few non closed parentesis, because of field truncation in the original catalog                       
NAME_WITH_PARENTESIS_OPEN = PNAME("nome") + pp.Optional(',') + LPARENT + \
                       pp.SkipTo(pp.StringEnd()).setResultsName("nota") 
NAME_SIMPLE = PNAME("Nome")
NAME_ANY = NAME_WITH_VIDE_PARENTESIS("remissão*") | NAME_VIDE("remissão")  | NAME_WITH_PARENTESIS(
    "anotação")| NAME_WITH_PARENTESIS_OPEN(
    "anotação") |  NAME_SIMPLE("normal")

# "Nota biográfica" (Archeevo: BiogHist) and "Registo académico"
# (Archeevo: ScopeContent)
#  These are manually created fields but very stable structure
# Generic format: field name: value
# e.g.   Faculdade: Cânones
#        Matrícula(s): 15.10.1661
#        Instituta: 10.10.1660
#        Naturalidade: Castelo de Vide
#
# Same records use ' - ' instead of ':' (e.g. 139148, 153037)
#
# Generic format for fieds
#
FIELD_NAME1 = pp.SkipTo(':').setResultsName("colon_field")
FIELD_NAME2 = pp.SkipTo('-').setResultsName('hifen-field')
FIELD_NAME = FIELD_NAME1 | FIELD_NAME2
FIELD_VALUE = pp.SkipTo(pp.StringEnd())
FIELD_1 = pp.ZeroOrMore(pp.White()) + FIELD_NAME("fname") + \
          ':' + FIELD_VALUE("fvalue")
FIELD_2 = pp.ZeroOrMore(pp.White()) + FIELD_NAME("fname") + \
          '-' + FIELD_VALUE("fvalue")
FIELD = FIELD_1 | FIELD_2

# A special case is a field with an "idem:" which means that the field name
# is repeated
# "11ª cadeira: 11.07.1906, Reprovado, Atos 22, fl. 176, idem: 12.07.1907,
# ... Aprovado com 12 valores, Atos n.º 23, fl. 160 v."
#
FIELD_IDEM = pp.ZeroOrMore(pp.White()) + FIELD_NAME("fname") + ':' \
             + pp.SkipTo(', idem:').setResultsName("fvalue") + ', idem:' \
             + FIELD_VALUE("idem")

# Occasionally we get section followed by field:
# e.g.  Exames: Bacharel: 29.07.1738
#       Outras informações: Incorporação de Bacharel em Artes: 23.03.1736, Atos 71, fl. 208 v.
#
SECTION_FIELD = pp.ZeroOrMore(pp.White()) + FIELD_NAME("section") + ':' \
                + FIELD_NAME("fname") + ':' \
                + FIELD_VALUE("fvalue")

# Special sequences:
# Provou ..... para ....
PROVOU = pp.Literal("Provou").setResultsName("fname") \
         + pp.SkipTo(pp.StringEnd()).setResultsName('fvalue')
PROVAS_DE = pp.Literal("Provas").setResultsName("fname") + pp.Literal("de") \
            + pp.SkipTo(pp.StringEnd()).setResultsName('fvalue')

# PROVOU_CURSAR_1 = pp.Literal("Provou cursar")
# PROVOU_CURSAR_2 = pp.Literal("Provou ter cursado")
# PROVOU_CURSAR = PROVOU_CURSAR_1 | PROVOU_CURSAR_2
# PROVOU_CURSOU = PROVOU_CURSAR("prova")+pp.SkipTo(':').setResultsName("cursou")+":"+pp.SkipTo(pp.StringEnd()).setResultsName('FIELD_VALUE')
# PROVOU_GRAU = PROVOU("prova")+pp.SkipTo(" para ")+"para"+pp.SkipTo(':').setResultsName("grau")+":"+pp.SkipTo(pp.StringEnd()).setResultsName('FIELD_VALUE')
# PROVOU_GENERICO = PROVOU("prova")+pp.SkipTo(':')+":"+pp.SkipTo(pp.StringEnd()).setResultsName('FIELD_VALUE')
# PROVA = PROVOU_GRAU("prova_de_grau") | PROVOU_CURSOU("prova_de_cursar") | PROVOU_GENERICO("prova_varia")

PROVA = PROVOU("provas") | PROVAS_DE("provas")

# Grau de .....
GRAU = pp.Literal("Grau").setResultsName("fname") + pp.Literal("de") \
       + pp.SkipTo(pp.StringEnd()).setResultsName('fvalue')

SPECIAL_FIELD = PROVA | GRAU


# Especial case is parents
# We can have Filiação: Father name
#         or  Filiação: Father name e de Mother name
#
FILIACAO_PAI = "Filiação:" + PNAME("pai")
FILIACAO_PAI_MAE = "Filiação:" + pp.Group(pp.SkipTo(" e de ")).setResultsName(
    "pai") \
                   + "e de" + PNAME("mae")
FILIACAO = FILIACAO_PAI_MAE | FILIACAO_PAI

# Dates
# There are lines only with dates after field "Matrícula(s)" and others
# Matrícula(s): 01.10.1733
# 01.10.1734
# 01.10.1735
# 01.10.1736
# 01.10.1737
# 01.10.1738
# 01.10.1741
# 01.10.1745
#
# Many dates in format YYYY/MM/DD and YYYY.MM.DD
# Check (id: 140789)
#  Provou cursar as lições de Prima e Véspera de Leis e as de Instituta:
#        1.11.1574 até 30.04.1575

DD = pp.Word(pp.nums, min=1, max=2)
MM = pp.Word(pp.nums, min=1, max=2)
# Some dates use the word for month, when the day is missing "Junho de 1567" (139931)
JAN = pp.CaselessLiteral("Janeiro").setResultsName("jan")
FEB = pp.CaselessLiteral("Fevereiro").setResultsName("feb")
MAR = pp.CaselessLiteral("Março").setResultsName("mar")
APR = pp.CaselessLiteral("Abril").setResultsName("apr")
MAY = pp.CaselessLiteral("Maio").setResultsName("may")
JUNE = pp.CaselessLiteral("Junho").setResultsName("june")
JULY = pp.CaselessLiteral("Julho").setResultsName("jul")
AUG = pp.CaselessLiteral("Agosto").setResultsName("aug")
SEP = pp.CaselessLiteral("Setembro").setResultsName("set")
OUT = pp.CaselessLiteral("Outubro").setResultsName("out")
NOV = pp.CaselessLiteral("Novembro").setResultsName("nov")
DEZ = pp.CaselessLiteral("Dezembro").setResultsName("dez")
MONTH = (JAN | FEB | MAR | APR | MAY | JUNE | JULY | AUG | SEP | NOV | DEZ)
months_names_to_numbers = {'Janeiro': 1,
                           'Fevereiro': 2,
                           'Março': 3,
                           'Abril': 4,
                           'Maio': 5,
                           'Junho': 6,
                           'Julho': 7,
                           'Agosto': 8,
                           'Setembro': 9,
                           'Outubro': 10,
                           'Novembro': 11,
                           'Dezembro': 12}
MONTH.setParseAction(lambda sml, t: [str(months_names_to_numbers[t[0]])])

YYYY = pp.Word(pp.nums, exact=4)
DSEP = pp.Word('.' + '/' + '-', max=1)
DATE1 = DD('day*') + DSEP + MM('month*') + DSEP + YYYY('year*')
DATE2 = YYYY('year*') + DSEP + MM('month*') + DSEP + DD('day*')

DAY_OPTIONAL = pp.Optional(DD, default='0')
MONTH_OPTIONAL = pp.Optional(MM, default='0')
DATE3 = (DAY_OPTIONAL('day*') + pp.Optional("de")
         + MONTH('month*')
         + pp.Optional("de") +
         YYYY('year*')
         ).setResultsName("noday")
DATE4 = (DAY_OPTIONAL('day*') + pp.Optional("de")
         + MONTH_OPTIONAL('month*')
         + pp.Optional("de") +
         YYYY('year*')
         ).setResultsName("noday-nomonth")
DATE = DATE1 | DATE2 | DATE3 | DATE4

# Date range
DATE_RANGE1 = DATE("date1") + "até" + DATE("date2")
DATE_RANGE2 = DATE("date1") + "a" + DATE("date2")
DATE_RANGE3 = pp.CaselessLiteral("desde") + DATE + "até" + DATE

DATE_RANGE = DATE_RANGE1 | DATE_RANGE2 | DATE_RANGE3

DATELINE = (DATE_RANGE("date_range") | DATE) \
           + pp.SkipTo(pp.StringEnd()).setResultsName('obs')

# BLANK
BLANKLINE = pp.ZeroOrMore(pp.White()).setResultsName("blank") + pp.StringEnd()

# REPEATING FLAG (lines created from ';' found in field value, have a flag)
# This is done during pre-processing of the bio-academic information before
# the grammar rules are applied. So it is not part of the original data.
REPEAT_FLAG = pp.Literal('#')

# Final catchall
# Lines with "nomatch" in the results could not be processed
NOMATCH = pp.SkipTo(pp.StringEnd()).setResultsName("nomatch")

# Top level grammar for lines in "Nota Biográfica" a "Registo Académico"
# Note that order of matching is relevant
#
BIOLINE = pp.Optional(REPEAT_FLAG("repeat")) \
          + (BLANKLINE("blank")
             | FILIACAO
             | DATELINE
             | SPECIAL_FIELD
             | FIELD_IDEM
             | SECTION_FIELD
             | FIELD
             | NOMATCH)


def scan_date(some_string: str) -> Optional[Type['DateUtility']]:
    """.. py:function:: scan_date(some_string: str)

    Detect if the string has a date, return first match or *None*
    :param str some_string: text to scan, can have date and other elements
    :return: the first match found
    :rtype: ucalumni.grammar.DateUtility
    """
    DATELINE.setParseAction(preserve_original)
    dates_in_fvalue = list(DATELINE.scanString(some_string))
    if len(dates_in_fvalue) > 0:
        date, s, e = dates_in_fvalue[0]
        d = DateUtility(date, start=s, end=e)
        return d
    else:
        return None


YMD = namedtuple('YMD', 'year month day')


class DateUtility:
    """ Generate useful representations from dates in alumni records

    du = DateUtility(d) where d is a string or the result of
         DATELINE.scanString(S)[n]

    If d is a string it is parsed with DATELINE and the first match is used.

    :param original: string that was parsed (can have more than one date)
    :param original_date: the date part of the original string
    :param value: date in kleio format: YYYY-MM-DD or range DATE1:DATE2
    :param short: date in compact format, no separators YYYYMMDD or range with ":"
    """

    def __init__(self, d: Type[Union[str, pp.ParseResults]], start=0, end=-1):
        """

        :param d:
        :param start:
        :param end:
        """
        self.date1 = None
        self.date2 = None
        self.scan_results = None
        self.is_range = False
        self.original = None
        self.original_date = None
        self.date = None
        self.obs = None
        self.start=start
        self.end=end

        if d is None or d == '':
            self.scan_results = None
            self.is_range = False
            self.date = YMD('0000', '00', '00')
            self.original = '* empty value *'
            self.original_date = self.original
        elif type(d) is str:
            DATELINE.setParseAction(
                preserve_original)  # this adds 'original' key
            l = list(DATELINE.scanString(d))
            if len(l) > 0:
                date, s, e = l[0]
                self.from_scan_results(date, start=s, end=e)
            else:
                raise ValueError("No date in string argument: "+d)
        elif type(d) is pp.ParseResults:
            self.from_scan_results(d, start=start, end=end)
        else:
            raise TypeError("Argument of wrong type (str or ParseResults)")


    def from_scan_results(self, d, start=0, end=-1):
        """d is the result of DATELINE.scanString(S)[n]"""
        self.start = start
        self.end = end
        if 'date_range' in d.keys():
            self.scan_results = d
            self.is_range = True
            self.date1 = YMD(d.year[0], d.month[0], d.day[0])
            self.date2 = YMD(d.year[1], d.month[1], d.day[1])
            self.date = self.date1 + self.date2
        else:
            self.scan_results = d
            self.is_range = False
            self.date = YMD(d.year[0], d.month[0], d.day[0])
            # print(f'{self.scan_results.dump()=}')

        self.original = d.get('original', " ".join(d)).strip()
        if 'obs' in d.keys():  # obs is any text following the date
            self.original_date = self.original[start:end].removesuffix(d.obs).strip() 
            self.obs = d.obs
        else:
            self.original_date = self.original[start:end] # need to remove suffix d.obs


    def __str__(self):
        if self.is_range:
            y1, m1, d1, y2, m2, d2 = self.date
            return f'{y1.zfill(4)}-{m1.zfill(2)}-{d1.zfill(2)}:{y2.zfill(4)}-{m2.zfill(2)}-{d2.zfill(2)}'
        else:
            y, m, d = self.date
            return f'{y.zfill(4)}-{m.zfill(2)}-{d.zfill(2)}'

    def __repr__(self):
        return f'DateUtility("{self.value}")'

    def toJson(self):
        jdu: dict = {}
        if self.is_range:
            y1, m1, d1, y2, m2, d2 = self.date
            jdu ={"is_range":True,
                  "year1":y1,
                  "month1":m1,
                  "day1":d1,
                  "year2":y2,
                  "month2":m2,
                  "day2":d2,
                  "date":self.value                 
                  }
        else:
            y, m, d = self.date
            jdu ={"is_range":False,
                  "year":y,
                  "month":m,
                  "day":d,
                  "date":self.value                 
                  }

        return json.dumps(jdu)

    @property
    def value(self):
        return self.__str__()

    @property
    def short(self):
        if self.is_range:
            y1, m1, d1, y2, m2, d2 = self.date
            return f'{y1.zfill(3)}{m1.zfill(2)}{d1.zfill(2)}:{y2.zfill(4)}{m2.zfill(2)}{d2.zfill(2)}'
        else:
            y, m, d = self.date
            return f'{y.zfill(4)}{m.zfill(2)}{d.zfill(2)}'

    @property
    def date_only(self):
        return (self.original == self.original_date)
