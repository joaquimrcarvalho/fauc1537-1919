# flake8: noqa: E501
"""
Tests for the ucalumni module

(c) Joaquim Carvalho 2021.
MIT License, no warranties.
"""

import datetime
from os import linesep as nl
from pathlib import Path


import pytest
import pyparsing as pp

from timelink.api.models import base  # noqa
from timelink.api.models.base import Source, Person, Act, Attribute, Relation
from timelink.api.database import TimelinkDatabase

import ucalumni.config as config
from ucalumni.config import Session, sqlite_main_db
from ucalumni.groups import n
from ucalumni.aluno import Aluno
from ucalumni.fields import process_bioreg
from ucalumni.extractors import (
    extract_colegio,
    extract_matriculas,
    extract_name_note_vid,
)
from ucalumni.grammar import (
    FIELD,
    PROVA,
    FILIACAO,
    DATELINE,
    DateUtility,
    preserve_original,
)
from ucalumni.config import auc_export
from ucalumni.importer import import_auc_alumni
from ucalumni.mapping import map_aluno_kperson, mapper_nomes_notes, list_search

"""
Grammar tests
"""


def test_field():
    fields = [
        "Instituta:",
        "Filiação: Simão José de Almeida",
        "Naturalidade: Lisboa",
        "Faculdade: Direito",
        "Matrícula(s): Matemática: 5.1.1774 (obrigado)",
        "Filosofia: 1.1.1775 (obrigado)",
        "Direito: 1.1.1773",
        "Direito- 1.1.1773",
        "Direito - 1.1.1773",
        "Direito -1.1.1773",
    ]
    for p in fields:
        r = FIELD.parseString(p)
        k = r.asDict().keys()
        # print(r.dump())
        assert "fname" in k, "field parsing failed for " + p


def test_provou():
    provas = [
        "Provou o tempo que se requer para Bacharel em Artes: 1.02.1557",
        "Provou ter o tempo necessário para Licenciado em Artes: 20.04.1558",
        "Provou ter o tempo necessário para Bacharel em Artes: 18.02.1551",
        "Provou Artes o tempo que se requer para Licenciado em Artes: 23.05.1560",
        "Provou duas lições grandes de Cânones: 18.1.1565 até 31.05.1566",
        "Provou cursar 1 curso de Artes na Universidade de Évora: 1.1.1569 até",
        "Provou ter cursado  2 cursos em Leis: 1544 a 1546, Livro 3, fl. 90, Caderno",
    ]
    for p in provas:
        r = PROVA.parseString(p)
        assert "Provou" == r["fname"], "Prova parsing failed for " + p


def test_provou_orgtxt():
    p = "Provou ter o tempo necessário para Licenciado em Artes: 20.04.1558"
    PROVA_OT = pp.originalTextFor(PROVA)
    rot = PROVA_OT.parseString(p)
    s = rot[0]
    assert s == p, "Did not get original text from parsed expression"


def test_filiacao_pai():
    f = "Filiação: Bernardo de Figueiredo Fernão Freire"
    r = FILIACAO.parseString(f)
    pnome = " ".join(r.pai)
    assert (
        pnome == "Bernardo de Figueiredo Fernão Freire"
    ), "Could not get father from 'Filiação'"


def test_filiacao_pai_e_mae():
    f = "Filiação: Francisco de Figueiredo Cardoso e Melo e de Ana Augusta de Abreu Madeira de Tovar e Albuquerque"
    r = FILIACAO.parseString(f)
    pnome = " ".join(r.pai)
    pmae = " ".join(r.mae)
    assert (
        pnome == "Francisco de Figueiredo Cardoso e Melo"
    ), "Could not get the father from 'Filiação'"
    assert (
        pmae == "Ana Augusta de Abreu Madeira de Tovar e Albuquerque"
    ), "Could not get the mother from 'Filiação'"


"""
Test Date expressions and DateUtility
"""


def test_date_utility():
    datestrings = [
        "24/5/1958",
        "1958/5/24",
        "1958.5.24",
        "1958.05.24",
        "24.5.1958",
    ]

    for ds in datestrings:
        # print(nl, ds)
        DATELINE.setParseAction(preserve_original)
        for d, s, e in DATELINE.scanString(ds):
            du = DateUtility(d)
            #   print(f'{du.original=}')
            #  print(f'{du.value=}')
            #    print(f'{du.short=}')
            assert du.short == "19580524", "Could not parse date " + ds


def test_date_utility_string():
    datestrings = [
        "24/5/1958",
        "1958/5/24",
        "1958.5.24",
        "1958.05.24",
        "24.5.1958",
    ]

    for ds in datestrings:
        # print(nl, ds)
        du = DateUtility(ds)
        # print(f'{du.original=}')
        # print(f'{du.value=}')
        # print(f'{du.short=}')
        assert du.short == "19580524", "Could not parse date " + ds


def test_date_utility2():
    datestrings = [
        "24/5/1958 até 24/7/2021",
        "1958/5/24 até 2021/07/24",
        "1958.5.24 até 2021.05.24",
        "1958.05.24 até 2021.07.24",
        "24.5.1958 até 24.7.2021",
    ]

    for ds in datestrings:
        # print(nl, ds)
        for d, s, e in DATELINE.scanString(ds):
            du = DateUtility(d)
            #  print(f'{du.date1=}')
            #  print(f'{du.date2=}')
            #  print(f'{du.original=}')
            #  print(f'{du.value=}')
            #  print(f'{du.short=}')
            assert du.is_range, "Could not parse range date " + ds


def test_date_utility2_string():
    datestrings = [
        "24/5/1958 até 24/7/2021",
        "1958/5/24 até 2021/07/24",
        "1958.5.24 até 2021.05.24",
        "1958.05.24 até 2021.07.24",
        "24.5.1958 até 24.7.2021",
    ]

    for ds in datestrings:
        # print(nl, ds)
        du = DateUtility(ds)
        #  print(f'{du.date1=}')
        #   print(f'{du.date2=}')
        #  print(f'{du.original=}')
        #  print(f'{du.value=}')
        #  print(f'{du.short=}')
        assert du.is_range, "Could not parse range date " + ds


def test_date_utility1():
    d = DateUtility("1-5-1582")
    year, month, day = d.date
    assert year == "1582"
    assert month == "5"
    assert day == "1"


def test_date_utility_original():
    d = DateUtility("1-5-1582")
    assert d.value == "1582-05-01"
    assert d.original == "1-5-1582"


def test_date_utility_original2():
    d = DateUtility("The date is 1-5-1582")
    assert d.value == "1582-05-01"
    assert d.original == "The date is 1-5-1582"
    assert d.original_date == "1-5-1582"


def test_date_utility_original3():
    d = DateUtility(
        "Examepara Bacharel corrente e grau de Bacharel 1556.07.09 Aprovado Nenime Discrepante"
    )
    assert d.value == "1556-07-09"
    assert (
        d.original
        == "Examepara Bacharel corrente e grau de Bacharel 1556.07.09 Aprovado Nenime Discrepante"
    )
    assert d.original_date == "1556.07.09"


def test_date_utility_none():
    d = DateUtility(None)
    assert d.date == ("0000", "00", "00")
    assert d.short == "00000000"


"""
Tests Aluno
"""


@pytest.fixture
def sample_aluno() -> Aluno:
    aluno = Aluno(
        "145567",
        "PT/12345/",
        "Joaquim Manuel",
        DateUtility("1537/03/01"),
        DateUtility("1910/10/05"),
        datetime.datetime.now(),  # fake we store it in ls
        "http://pesquisa.auc.uc.pt/details?id=145567",
    )
    aluno.obs = ""
    return aluno


def test_add_nota_1(sample_aluno: Aluno):
    sample_aluno.add_nota(
        "seccao_1",
        "campo_1",
        "valor 1",
        DateUtility("since 1656-6-1"),
        obs="first note",
    )
    assert len(sample_aluno.notas) == 1, "note not added"
    nota = sample_aluno.notas[0]
    sec1 = nota.seccao
    campo1 = nota.campo
    val1 = nota.valor
    date1 = nota.data
    obs1 = nota.obs
    assert sec1 == "seccao_1"
    assert campo1 == "campo_1"
    assert val1 == "valor 1"
    assert date1.original_date == "1656-6-1"
    assert obs1 == "first note"
    notas = sample_aluno.notas_index
    valor, data, obs = notas["seccao_1"]["campo_1"][0]
    assert valor == val1
    assert data.value == date1.value
    assert obs == obs1


"""
Tests extractors
"""


def test_get_record_date(sample_aluno: Aluno):
    record_date_as_string = sample_aluno.get_record_date()
    assert record_date_as_string[:2] == "20"  # hopefully this only used this century


def test_extract_note_from_nome(sample_aluno: Aluno):
    sample_aluno.nome = "Joaquim Carvalho (professor)"
    extract_name_note_vid(sample_aluno)
    assert len(sample_aluno.notas) > 0
    assert sample_aluno.nota == "professor"


def test_extract_note_from_nome_comma(sample_aluno: Aluno):
    sample_aluno.nome = "Joaquim Carvalho, (professor)"
    extract_name_note_vid(sample_aluno)
    assert len(sample_aluno.notas) > 0
    assert sample_aluno.nota == "professor"


def test_extract_open_note_from_nome(sample_aluno: Aluno):
    sample_aluno.nome = "Joaquim Carvalho (professor"
    extract_name_note_vid(sample_aluno)
    assert len(sample_aluno.notas) > 0


def test_extract_vide_from_nome(sample_aluno: Aluno):
    sample_aluno.nome = "Joaquim Carvalho, vide Ramos de Carvalho"
    extract_name_note_vid(sample_aluno)
    assert sample_aluno.vide == "Ramos de Carvalho"
    assert sample_aluno.nome == "Joaquim Carvalho"
    assert sample_aluno.vide_target == "Joaquim Ramos de Carvalho"


# vide with no effect, not sure better way to handle this
def test_extract_vide_from_nome_inv(sample_aluno: Aluno):
    sample_aluno.nome = "Joaquim Ramos de Carvalho, vide Carvalho"
    extract_name_note_vid(sample_aluno)
    assert sample_aluno.vide == "Carvalho"
    assert sample_aluno.nome == "Joaquim Ramos de Carvalho"
    assert sample_aluno.vide_target == "Joaquim Ramos de Carvalho"


def test_extract_vide_from_nome2(sample_aluno: Aluno):
    sample_aluno.nome = "Joaquim Carvalho; vide Ramos de Carvalho"
    extract_name_note_vid(sample_aluno)
    assert sample_aluno.vide == "Ramos de Carvalho"
    assert sample_aluno.nome == "Joaquim Carvalho"


def test_extract_vide_from_nome4(sample_aluno: Aluno):
    sample_aluno.nome = "João Mateus Camelo da Silva e Rocha, vide Machado e Rocha"
    extract_name_note_vid(sample_aluno)
    assert (
        sample_aluno.vide_target == "João Mateus Camelo da Silva Machado e Rocha"
    ), "could not handle multiple common termination names"


def test_extract_vide_from_nome5(sample_aluno: Aluno):
    sample_aluno.nome = "Dionísio Dinis de Oliveira, vide Dinis de Oliveira da Fonseca"
    extract_name_note_vid(sample_aluno)
    assert (
        sample_aluno.vide_target == "Dinis de Oliveira da Fonseca"
    ), "could not handle substiution of first name"


# https://linode.timelink-mhk.net/mhk/servlet/do?action=show&id=130281
# Nuno da Câmara (D.), vide Nuno Casimiro da Câmara e Nuno José da Câmara
def test_extract_note_and_vide(sample_aluno: Aluno):
    sample_aluno.nome = (
        "Nuno da Câmara (D.), vide Nuno Casimiro da Câmara e Nuno José da Câmara"
    )
    extract_name_note_vid(sample_aluno)
    assert sample_aluno.vide == "Nuno Casimiro da Câmara e Nuno José da Câmara"
    assert sample_aluno.nome == "Nuno da Câmara"
    assert sample_aluno.nota == "D."


def test_extract_vide_from_nome3(sample_aluno: Aluno):
    sample_aluno.nome = "Joaquim Carvalho,vide Ramos de Carvalho"
    extract_name_note_vid(sample_aluno)
    assert sample_aluno.vide == "Ramos de Carvalho"
    assert sample_aluno.nome == "Joaquim Carvalho"


def test_extract_matriculas(sample_aluno: Aluno):
    """

    :rtype: None
    """
    sample_aluno.faculdade = [("Leis", DateUtility("31.1.1795"), "")]
    sample_aluno.add_nota(
        "*nosection*",
        "matricula",
        "31.1.1795",
        DateUtility("31.1.1795"),
        obs="(obrigado)",
    )
    extract_matriculas(sample_aluno)


"""
Test mappings
"""


def test_mapping_vide(sample_aluno):
    sample_aluno.nome = "Joaquim Carvalho, vide Ramos de Carvalho"
    extract_name_note_vid(sample_aluno)
    p: n = n(sample_aluno.nome, "m", id=sample_aluno.id)
    mapper_nomes_notes(sample_aluno, p)
    kleio = p.to_kleio()
    print(kleio)


def test_mapping_colegio(sample_aluno):
    sample_aluno.nome = (
        "José de Noronha (D., porcionista do Colégio Real de São Paulo, cónego)"
    )
    extract_name_note_vid(sample_aluno)
    assert sample_aluno.nome == "José de Noronha"
    extract_colegio(sample_aluno)
    assert sample_aluno.colegio == "Colégio de S.Paulo"


def test_list_search():
    titulos = (
        "d\\.,frei,padre,abade,arcediago,barão,"
        "beneficiado,bispo,capelão,chantre,cónego,"
        "lente,marquês,monge,porcionista,presbítero,"
        "religioso,visconde"
    )
    titulos_lista = titulos.split(",")
    hits = list_search(
        titulos_lista, "Francisco da Fonseca (abade de São Tiago de Bougado)"
    )
    assert len(hits) == 1


"""
Apply extractors to specific records, already imported

Since we keep in the database the original text of the ScopeContent
record, we can test the extractors in specific records.
"""

# set the database which will provide the test records
db_main_db = config.default_sqlite_test_records

db = TimelinkDatabase(db_url=db_main_db)
Session.configure(bind=db.get_engine())


# Some auxiliary functions
def ls_check_type(p: n, type_: str):
    """
    Check if a person has an attribute of a specific type
    """
    return len([ls for ls in p.dots.lss if ls.type == type_]) > 0


def atr_check_type(p: n, type_: str):
    """
    Check if a person has an attribute of a specific type
    """
    return len([atr for atr in p.dots.atrs if atr.type == type_]) > 0


def ls_check_value(p: n, type_: str, value: str):
    """
    Check if a person has an attribute with a specific value
    """
    return value in [ls.value for ls in p.dots.lss if ls.type == type_]


def atr_check_value(p: n, type_: str, value: str):
    """
    Check if a person has an attribute with a specific value
    """
    return value in [atr.value for atr in p.dots.atrs if atr.type == type_]


def ls_check_date(p: n, type_: str, value: str, date: str):
    """
    Check if a person has an attribute with a specific value
      and a specific date
    """
    r = date in [ls.data for ls in p.dots.lss if ls.type == type_ and ls.value == value]
    return r


@pytest.mark.parametrize(
    "description,id,expression",
    [
        # Matriculas
        # 128197 curso dialéctica
        (
            "Matriculas: curso dialetica",
            "128197",
            "ls_check_value(kaluno,'matricula-curso','Dialética')",
        ),
        (
            "Matriculas: erradas",
            "140349",
            "ls_check_value(kaluno,'matricula-faculdade.ano','Cânones.1573')",
        ),
        (
            "Matriculas: Canones 1712",
            "152448",
            "ls_check_value(kaluno,'matricula-faculdade.ano','Cânones.1712')",
        ),
        (
            "Matricula: Leis 1718",
            "155322",
            "ls_check_value(kaluno,'matricula-faculdade.ano','Leis.1718')",
        ),
        # Must use the inferred faculdade, not the original
        #  144910
        (
            "Matricula: Canones 1796",
            "144910",
            "ls_check_value(kaluno,'matricula-faculdade.ano','Cânones.1795')",
        ),
        # But the original is some cases must be preserved sometimes
        # if not in error and no date in matrículas
        (
            "Matricula: original faculdade used for matricula",
            "221833",
            "ls_check_value(kaluno,'matricula-faculdade.ano','Matemática.1773')",
        ),
        (
            "Matriculas: simple case, pre 1772",
            "139883",
            "ls_check_value(kaluno,'matricula-faculdade.ano','Cânones.1586') and ls_check_value(kaluno,'matricula-faculdade.ano','Cânones.1594')",
        ),
        (
            "Matriculas: faculdade, curso, classe, complex",
            "316297",
            "ls_check_value(kaluno,'matricula-faculdade','Matemática') and "
            "ls_check_value(kaluno,'matricula-curso','Curso jurídico')",
        ),
        (
            "Matriculas: complex sequence of matricula, just for debug",
            "205781",
            "ls_check_value(kaluno,'matricula-faculdade','Medicina')",
        ),
        (
            "Matriculas: carry over class information in incomplete lines",
            "153341",
            "ls_check_value(kaluno,'matricula-classe','Medicina, 4º ano')",
        ),
        # 151042 avoid taking "livro" for "ano"
        (
            "Matriculas: avoid livro for ano",
            "151042",
            "not ls_check_type(kaluno,'matricula-classe')",
        ),
        (
            "Matriculas: Misses sequence of of matricula",
            "153341",
            "ls_check_value(kaluno,'matricula-faculdade','Medicina')",
        ),
        (
            "Matriculas: obrigado",
            "153341",
            "ls_check_value(kaluno,'matricula-faculdade.obrigado','Filosofia')",
        ),
        (
            "Matriculas: Complex matriculas sequence",
            "185916",
            "ls_check_value(kaluno,'matricula-faculdade.ano','Filosofia.1775')",
        ),
        (
            "Matricula: just curso with date",
            "167307",
            "ls_check_type(kaluno,'matricula-curso')",
        ),
        (
            "Matricula: no faculdade just curso",
            "146875",
            "ls_check_type(kaluno,'matricula-curso')",
        ),
        (
            "Matricula: just curso",
            "141333",
            "ls_check_type(kaluno,'matricula-curso') and "
            "ls_check_type(kaluno,'matricula-curso.ano') ",
        ),
    ],
)
def test_from_db_matricula(description, id, expression):
    """
    Test a specific "aluno" with `id` by
    fetching from the database the original bionote+scope_content
    and metadata, running the extraction and mapping procedure
    and asserting `expression`. `Description` is the message
    used for the assert.

    For `expression` the following variables can be used:
    * `aluno`is the object of type Aluno afters running the extractors
    * `kaluno`is the KPerson object after running the mappers.
    * kleio is a string representation of kaluno in kleio notation

    Helper functions for testing kleio mappings:

    * ls_check_value(p: n, type_:str, value:str): test if `n` as an attribute
        (ls) with `type`and `value`.
    * ls_check_type(p: n, type_:str): test if `n` as an attribute
        (ls) with `type` (value not relevant).

    Examples of expressions:

        ls_check_value(kaluno,'nome.apelido','Lacerda')
        aluno.nome == 'Aarão Soeiro Moreira de Lacerda'

    """
    if id == "185916":
        print("debug")

    aluno = Aluno.from_db(id)
    aluno.process()
    kaluno = map_aluno_kperson(aluno)
    entry = aluno.as_entry()
    assert eval(expression), description


@pytest.mark.parametrize(
    "description,id,expression",
    [
        # Instituta
        (
            "Instituta: non date",
            "140367",
            "len([ls for ls in kaluno.dots.lss if ls.type == 'instituta'])==0",
        ),
        (
            "Instituta: non date",
            "145402",
            "len([ls for ls in kaluno.dots.lss if ls.type == 'instituta'])==0",
        ),
        (
            "instituta with non date",
            "250519",
            "len([ls for ls in kaluno.dots.lss if ls.type == 'instituta'])==0",
        ),
        (
            "multiple 'instituta'",
            "140348",
            "len([ls for ls in kaluno.dots.lss if ls.type == 'instituta']) > 1",
        ),
    ],
)
def test_from_db_instituta(description, id, expression):
    """ """
    aluno = Aluno.from_db(id)
    aluno.process()
    kaluno = map_aluno_kperson(aluno)
    assert eval(expression), description


@pytest.mark.parametrize(
    "description,id,expression",
    # Graus
    # 159940 Empty graus not processed
    [
        (
            "Graus: skip empty graos",
            "159940",
            "not ls_check_type(kaluno,'grau')",
        ),
        # Should be Bacharel em Leis
        # 249629
        (
            "Graus: Should bacharel em Leis",
            "249629",
            "ls_check_value(kaluno,'grau','Bacharel em Leis')",
        ),
        # Many empty fields have a dash
        # 163034
        (
            "Graus: take dash as empty",
            "163034",
            "not ls_check_value(kaluno,'grau','Bacharel')",
        ),
        (
            "Graus: Mestre is mestre (no false negative)",
            "137651",
            "not ls_check_value(kaluno,'grau','mestre')",
        ),
        (
            "Graus: Mestre escola not mestre (no false positive)",
            "206117",
            "not ls_check_value(kaluno,'grau','mestre')",
        ),
        (
            "Graus: Missed formatura",
            "288876",
            "ls_check_value(kaluno,'grau','Formatura em Cânones')",
        ),
        # graus with ambito
        # 180447 Doutor em Leis
        (
            "Graus: Doutor em Leis",
            "180447",
            "ls_check_value(kaluno,'grau','Doutor em Leis')",
        ),
        # Infer ambito from Faculdade
        # 150587
        (
            "Graus: Doutor em Medicina",
            "150587",
            "ls_check_value(kaluno,'grau','Doutor em Medicina')",
        ),
        # Bacharel em Artes in the field name
        # 140346
        (
            "Graus:Bacharel em Artes",
            "140346",
            "ls_check_value(kaluno,'grau','Bacharel em Artes')",
        ),
    ],
)
def test_from_db_graus(description, id, expression):
    """ """
    aluno = Aluno.from_db(id)
    aluno.process()
    kaluno = map_aluno_kperson(aluno)
    assert eval(expression), description


@pytest.mark.parametrize(
    "description,id,expression",
    # Title "lente"
    [
        (
            "Lente not title (Alentejo)",
            "216502",
            "not ls_check_value(kaluno,'titulo','lente')",
        ),
        (
            "Lente",
            "203081",
            "ls_check_value(kaluno,'titulo','lente')",
        ),
        (
            "Lente not title",
            "232178",
            "ls_check_value(kaluno,'titulo','lente')",
        ),
    ],
)
def test_from_db_lente(description, id, expression):
    """ """
    aluno = Aluno.from_db(id)
    aluno.process()
    kaluno = map_aluno_kperson(aluno)
    assert eval(expression), description


@pytest.mark.parametrize(
    "description,id,expression",
    # Religious order
    [
        (
            "Ordem religiosa more than one wrong",
            "192333",
            "len([ls for ls in kaluno.dots.lss if ls.type == 'ordem-religiosa'])==1",
        ),
        (
            "Order Religiosa Padre de Santa Cruz",
            "192460",
            "ls_check_value(kaluno,'ordem-religiosa','Ordem dos Cónegos Regrantes de Santo Agostinho')",
        ),
        (
            "Ordem Religiosa Cónego regular de Santo Agostinho",
            "271615",
            "ls_check_value(kaluno,'ordem-religiosa','Ordem dos Cónegos Regrantes de Santo Agostinho')",
        ),
        (
            "Ordem Religiosa Descalço de Santo Agostinho",
            "278135",
            "ls_check_value(kaluno,'ordem-religiosa','Ordem de Santo Agostinho (Descalços)')",
        ),
        (
            "Ordem religiosa Agostinhos descalços",
            "195629",
            "ls_check_value(kaluno,'ordem-religiosa','Ordem de Santo Agostinho (Descalços)')",
        ),
        (
            "Ordem Religiosa agostinho descalço",
            "195803",
            "ls_check_value(kaluno,'ordem-religiosa','Ordem de Santo Agostinho (Descalços)')",
        ),
        (
            "Ordem religiosa Companhia de Jesus",
            "206346",
            "ls_check_value(kaluno,'ordem-religiosa','Companhia de Jesus')",
        ),
        (
            "Ordem Religiosa Companhia de Jesus",
            "210697",
            "ls_check_value(kaluno,'ordem-religiosa','Companhia de Jesus')",
        ),
        (
            "Ordem religiosa S.Tomás - São Domingos",
            "295948",
            "ls_check_value(kaluno,'ordem-religiosa','Ordem de São Domingos')",
        ),
        (
            "Ordem religiosa indeterminada",
            "234961",
            "ls_check_value(kaluno,'ordem-religiosa',aluno.nota)",
        ),
        (
            "Ordem religiosa implicit in name note",
            "240344",
            "ls_check_value(kaluno,'ordem-religiosa','Ordem da Santíssima Trindade')",
        ),
        # 150020 misses João Evangelista
        (
            "Ordem a partir do colégio",
            "150020",
            "ls_check_value(kaluno,'ordem-religiosa','Ordem de São João Evangelista')",
        ),
        # 273519 generates "frei"
        (
            "Ordem cannot be just 'frei",
            "273519",
            "not ls_check_value(kaluno,'ordem-religiosa','rei')",
        ),
    ],
)
def test_from_db_ordem(description, id, expression):
    """ """
    aluno = Aluno.from_db(id)
    aluno.process()
    kaluno = map_aluno_kperson(aluno)
    assert eval(expression), description


@pytest.mark.parametrize(
    "description,id,expression",
    # Faculdade
    # These are cases where the operator recorded a value that analysis of the record
    #  shows is wrong according to curricular constraints. This happens after 1772
    #  when students would enrol in Matematics and Philosopy as compulsory requirements for Medicione and Law degrees
    [
        (
            "Faculdade: correct should be medicina",
            "221833",
            "ls_check_value(kaluno,'faculdade','Medicina')",
        ),
        # 140359 Faculdade inferred must loose "modalidade"
        ("Faculdade: inferred must loose modalidade", "140359", "True"),
        # 140359 should not be matemática
        (
            "Faculdade: not matematica",
            "140359",
            "not ls_check_value(kaluno,'faculdade','Matemática')",
        ),
        # 141208
        (
            "Faculdade: both canones and leis",
            "141208",
            "ls_check_value(kaluno,'faculdade','Leis') and "
            "ls_check_value(kaluno,'faculdade','Cânones')",
        ),
        # 138472 should not have Direito (Canones ou Leis)
        (
            "Faculdade: not Direito (Cânones ou Leis)",
            "138472",
            "len([ls for ls in kaluno.dots.lss if ls.type == 'faculdade']) == 1 and "
            "not ls_check_value(kaluno,'faculdade','Direito (Cânones ou Leis)')",
        ),
        # 268660
        (
            "Faculdade: correct Leis not Direito",
            "268660",
            "len([ls for ls in kaluno.dots.lss if ls.type == 'faculdade']) == 1 and "
            "ls_check_value(kaluno,'faculdade','Leis')",
        ),
        (
            "Faculdade: correct should be Filosofia",
            "140352",
            "ls_check_value(kaluno,'faculdade','Filosofia')",
        ),
        # 285035
        (
            "Faculdade: correct should be Canones",
            "285035",
            "ls_check_value(kaluno,'faculdade','Cânones')",
        ),
        # 144910
        (
            "Faculdade: correct should be Canones",
            "144910",
            "ls_check_value(kaluno,'faculdade','Cânones')",
        ),
        # 128431 Use Instituta to infer Direito
        (
            "Faculdade: instituta for direito (Canones or leis)",
            "128431",
            "ls_check_value(kaluno,'faculdade','Cursos jurídicos (Cânones ou Leis)')",
        ),
        # 140404 use Instituta to infer Direito
        (
            "Faculdade: instituta for direito (Canones or leis)",
            "140404",
            "ls_check_value(kaluno,'faculdade','Cursos jurídicos (Cânones ou Leis)')",
        ),
        #
        (
            "Faculdade: missing in vide record",
            "144919",
            "not ls_check_type(kaluno,'faculdade.problema')",
        ),
        (
            "Faculdade: correct should be Leis",
            "145472",
            "ls_check_value(kaluno,'faculdade','Leis')",
        ),
        (
            "Faculdade: correct canones only, not direito",
            "316297",
            "ls_check_value(kaluno,'faculdade','Cânones') and "
            "not ls_check_value(kaluno,'faculdade','Direito') ",
        ),
        (
            "Faculdade: correct should be Medicina",
            "190269",
            "ls_check_value(kaluno,'faculdade','Medicina')",
        ),
        (
            "Faculdade: duplicate",
            "132750",
            "len([ls for ls in kaluno.dots.lss if ls.type == 'faculdade']) == 1",
        ),
        (
            "Faculdade: duplicate",
            "132763",
            "len([ls for ls in kaluno.dots.lss if ls.type == 'faculdade']) == 1",
        ),
        # Duplicate
        (
            "Faculdade: duplicate",
            "129044",
            "len([ls for ls in kaluno.dots.lss if ls.type == 'faculdade']) == 1",
        ),
        (
            "Faculdade: filter alternative",
            "161445",
            "not ls_check_value(kaluno,'faculdade','Instituta')",
        ),
        (
            "Faculdade: Filter alternative",
            "179233",
            "not ls_check_value(kaluno,'faculdade','1600-10-24')",
        ),
        (
            "Faculdade: Filter alternative",
            "163555",
            "not ls_check_value(kaluno,'faculdade','1562-10-05:1563-07-31')",
        ),
        (
            "Faculdade: repeated in the original record",
            "199046",
            "len([ls for ls in kaluno.dots.lss if ls.type == 'faculdade']) == 1",
        ),
        (
            "Faculdade: repeated in the original record",
            "227677",
            "len([ls for ls in kaluno.dots.lss if ls.type == 'faculdade']) == 1",
        ),
        (
            "Faculdade: repeated in the original record",
            "285231",
            "len([ls for ls in kaluno.dots.lss if ls.type == 'faculdade']) == 1",
        ),
        (
            "Faculdade: repeated in the original record",
            "165559",
            "len([ls for ls in kaluno.dots.lss if ls.type == 'faculdade']) == 1",
        ),
        (
            "Faculdade: correct should be Leis",
            "215732",
            "ls_check_value(kaluno,'faculdade','Leis')",
        ),
        (
            "Faculdade: medicina, not artes",
            "140340",
            "ls_check_value(kaluno,'faculdade','Medicina')",
        ),
        ("Faculdade: detected", "177385", "len(aluno.faculdade) > 0"),
        (
            "Faculdade: indeterminada",
            "141248",
            "atr_check_type(kaluno,'nota-processamento')",
        ),
    ],
)
def test_from_db_faculdade(description, id, expression):
    """ """
    aluno = Aluno.from_db(id)
    aluno.process()
    kaluno = map_aluno_kperson(aluno)
    assert eval(expression), description


@pytest.mark.parametrize(
    "description,id,expression",
    [
        # Colégio
        # 140448
        (
            "Colegio porcionista",
            "140448",
            "ls_check_value(kaluno,'colegio','Colégio de S.Paulo')",
        ),
        (
            "Colegio orderm terceira",
            "186633",
            "ls_check_value(kaluno,'colegio','Colégio de S.Pedro da Ordem Terceira')",
        ),
        (
            "Colegio orderm terceira",
            "218743",
            "ls_check_value(kaluno,'colegio','Colégio de S.Pedro da Ordem Terceira')",
        ),
        (
            "Colegio orderm terceira",
            "154002",
            "ls_check_value(kaluno,'colegio','Colégio de S.Pedro da Ordem Terceira')",
        ),
        (
            "Colegio not detected",
            "268593",
            "ls_check_value(kaluno,'colegio','Colégio das Ordens Militares')",
        ),
    ],
)
def test_from_db_colegio(description, id, expression):
    """ """
    aluno = Aluno.from_db(id)
    aluno.process()
    kaluno = map_aluno_kperson(aluno)
    assert eval(expression), description


@pytest.mark.parametrize(
    "description,id,expression",
    [
        # Names
        (
            "Nome Extract Nome",
            "193804",
            "aluno.nome == 'Aarão Soeiro Moreira de Lacerda'",
        ),
        (
            "Nome Tratamento de apelidos",
            "193804",
            "ls_check_value(kaluno,'nome-apelido','Moreira de Lacerda')",
        ),
        (
            "Nome Tratamento de apelidos",
            "193804",
            "ls_check_value(kaluno,'nome-apelido','Soeiro Moreira de Lacerda')",
        ),
        # 141442 map alternate nome from vide
        (
            "Nome Tratamento de vide",
            "141442",
            "ls_check_value(kaluno,'nome','Paulo Afonso Albuquerque')",
        ),
        # geração de parentesco a partir da filiação
        (
            "Pai e mae as relations",
            "150543",
            "kaluno.includes('referido') is not None"
            " and kaluno.includes('referida') is not None"
            " and kaluno.includes('rel')[0].data.core =='1837-10-21'",
        ),
        #
        (
            "Pai e mae as attributes",
            "150543",
            "ls_check_type(kaluno,'nome-pai') and " "ls_check_type(kaluno,'nome-mae')",
        ),
    ],
)
def test_from_db_names(description, id, expression):
    """Tests with names"""
    aluno = Aluno.from_db(id)
    aluno.process()
    kaluno = map_aluno_kperson(aluno)
    assert eval(expression), description


@pytest.mark.parametrize(
    "description,id,expression",
    [
        ("Exame: processamento de data", "316810", "True"),
        (
            "Exame em campo de hifen",
            "127987",
            "ls_check_value(kaluno,'exame','Exame Privado')",
        ),
        # 140358 misses exame privado
        (
            "Exame privado",
            "140358",
            "ls_check_value(kaluno,'exame','Exame Privado')",
        ),
        # 140363 misses de exame for grau de bacharel
        (
            "Exame grau de bacharel",
            "140363",
            "ls_check_value(kaluno,'exame','4º e Grau de Bacharel')",
        ),
        # Naturalidade
        (
            "Naturalidade parentesis",
            "129046",
            "ls_check_value(kaluno,'nome-geografico','Diamantina')",
        ),
        (
            "Naturalidade parentesis",
            "280433",
            "ls_check_value(kaluno,'nome-geografico','Leiria')",
        ),
        # Corrects naturalidade
        # 233763
        (
            "Naturalidade corrected minus slash and ?",
            "233763",
            "ls_check_value(kaluno,'naturalidade','Canêdo, Feira')",
        ),
        # Handling (?) in naturalidade
        # 140411
        (
            "Naturalidade corrected (?) ",
            "140411",
            "ls_check_value(kaluno,'naturalidade','Cão')",
        ),
        # filiação
        (
            "Filiacao: father and mother present",
            "150456",
            "len(kaluno.dots.referidos) > 0 and len(kaluno.dots.referidas) > 0 ",
        ),
        # Bugs
        # artifacts 141208
        (
            "Artifact: #29;",
            "140828",
            "not ls_check_value(kaluno,'matricula','\"#29;\"')",
        ),
        (
            "Artifac: #29; in records",
            "140434",
            "not chr(29) in aluno.scope_content",
        ),
    ],
)
def test_from_db_varia(description, id, expression):
    """ """
    aluno = Aluno.from_db(id)
    aluno.process()
    kaluno = map_aluno_kperson(aluno)
    assert eval(expression), description


@pytest.mark.parametrize(
    "description,id,expression",
    [
        ("Entry: exams", "195173", "True"),
        (
            "Entry colegio",
            "140448",
            "True",
        ),
    ],
)
def test_from_db_as_entry(description, id, expression):
    """ """
    aluno = Aluno.from_db(id)
    aluno.process()
    entry = aluno.as_entry()
    print(entry)
    assert True, description


# Use this as a template
# @pytest.mark.parametrize(
#     "description,id,expression",
#     [
#         # ("This is a test", 99999, "True")
#     ],
# )
# def test_from_db_template(description, id, expression):
#     """ """
#     aluno = Aluno.from_db(id)
#     aluno.process()
#     kaluno = map_aluno_kperson(aluno)
#     assert eval(expression), description


@pytest.mark.parametrize(
    "description,id,expression",
    [
        # Problems in the records, better solved with errata
        (
            "Errata: typo in Faculdade",
            "132428",
            "ls_check_value(kaluno,'faculdade','Cânones')",
        ),
        # Problems in the records, better solved with errata
        (
            "Errata: no field punctuation",
            "252365",
            "ls_check_type(kaluno,'instituta')",
        ),
        # on the same record multi lines with same grau, should keep last date
        (
            "Errata: if grau repeats keep last date",
            "252365",
            "ls_check_date(kaluno,'grau','Licenciado em Artes','1566-06-09')",
        ),
        # 268593 Date of segundo exame de formatura
        (
            "Errata: exame date 1738 not 1873",
            "268593",
            "ls_check_date(kaluno,'exame','Formatura','1738-07-05')",
        ),
        # TODO 145095 wrong date 1478
        # TODO 145401 wrong date first matricula
    ],
)
def test_from_db_errata(description, id, expression):
    """ """
    Aluno.collect_errata(config.path_to_errata)
    aluno = Aluno.from_db(id)
    aluno.check_errata()
    aluno.process()
    kaluno = map_aluno_kperson(aluno)
    k = kaluno.to_kleio()
    assert eval(expression), description


"""
Test transform and import
"""


def test_csv_to_kleio():
    import_auc_alumni(
        auc_export,
        "notebooks/ucalumni/tests/sources/",
        "",
        max_rows_to_process=1000,
        batch=50,
        testing=False,
    )
    assert True, "Problemas in import test"


def test_csv_to_sqlite():

    path_to_sqlite_dir = "notebooks/ucalumni/tests/db"
    try:
        import_auc_alumni(
            auc_export,
            path_to_sqlite_dir,
            config.sqlite_test_db,
            max_rows_to_process=10000,
            batch=500,
            testing=False,
        )
    except Exception as e:
        print(f"An error occurred: {e}")
    # Test correct linkage to source and act
    with Session() as session:
        p: Person = session.query(Person).order_by(Person.id).first()
        function_in_act: Relation = [
            r for r in p.rels_out if r.the_type == "function-in-act"
        ][0]
        destination = function_in_act.destination
        act: Act = session.get(Act, destination)
        assert act is not None, "Could not find act of first person"

        pai: Person = session.get(Person, "140337-pai")
        assert pai.sex is not None, "Father stored with no sex info"

        pai_function: Relation = [
            r for r in pai.rels_out if r.the_type == "function-in-act"
        ][0]
        assert pai_function is not None, "Father store with no function in act"

    assert True, "Problemas in import directly to database test"


from timelinknb import get_mhk_db


def test_geoentities_problem():
    db_name = config.default_sqlite_test_records
    print("Selected database:", db_name)
    db = TimelinkDatabase(db_url=db_name)
    assert "geoentities" in db.table_names()

