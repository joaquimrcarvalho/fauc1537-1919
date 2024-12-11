# flake8: max-line-length=120
# flake8: noqa: E501
"""
(c) Joaquim Carvalho 2021.
MIT License, no warranties.
"""

from logging import warning
from os.path import commonprefix
import re
from unittest import TextTestResult

from ucalumni.mapping import list_search, list_search_match
from ucalumni.grammar import NAME_ANY, DateUtility
from ucalumni.aluno import Aluno, Matricula, Grau, Exame, Instituta, Nota, Prova

faculdades_todas = {
    "cânones": "Cânones",
    "canones": "Cânones",
    "direito canônico": "Cânones",
    "direito": "Direito",
    "leis": "Leis",
    "teologia": "Teologia",
    "medicina": "Medicina",
    "matemática": "Matemática",
    "matematica": "Matemática",
    "filosofia": "Filosofia",
    "artes": "Artes",
}
cursos_juridicos_comuns = "Cursos jurídicos (Cânones ou Leis)"
escolas_menores = "Escolas Menores"
artes = "Artes"

faculdades_pre_1772 = {
    "cânones": "Cânones",
    "canones": "Cânones",
    "direito canônico": "Cânones",
    "direito": cursos_juridicos_comuns,
    "instituta": cursos_juridicos_comuns,
    "artes": artes,
    "gramática": artes,
    "retórica": artes,
    "filosofia": artes,
    "dialéctica": artes,
    "^código$": "Leis",
    "leis": "Leis",
    "teologia": "Teologia",
    "medicina": "Medicina",
    "matemática": "Matemática",
    "matematica": "Matemática",
}
faculdades_1772_1836 = {
    "cânones": "Cânones",
    "canones": "Cânones",
    "direito canônico": "Cânones",
    "direito": cursos_juridicos_comuns,
    "artes": artes,
    "leis": "Leis",
    "teologia": "Teologia",
    "medicina": "Medicina",
    "matemática": "Matemática",
    "matematica": "Matemática",
    "filosofia": "Filosofia",
}
faculdades_post_1836 = {
    "direito": "Direito",
    "teologia": "Teologia",
    "medicina": "Medicina",
    "matemática": "Matemática",
    "matematica": "Matemática",
    "filosofia": "Filosofia",
}
requisitos_pre_1772 = [cursos_juridicos_comuns, artes]
requisitos_1772_1836 = ["Filosofia", "Matemática", cursos_juridicos_comuns]
requisitos_post_1836 = ["Filosofia", "Matemática"]

def match_with_study_plan(aluno, use_initial_date=None):
    """ Examine the student dates and
    determine which list of Faculdades is relevant for this student,
    also if the student is affected by a transition of plans,

    :param aluno: Aluno object
    :param use_initial_date: boolean, if True uses the initial date
    :return: tuple

    returns: transition, faculdades, requisitos
             where transition is a boolean
                faculdades is a dictionary of faculdades
                requisitos is a list of requisitos
            when the student is in a transition period
            the function returns the post-transition plan
    """
    if use_initial_date is None:
        if hasattr(aluno, "use_initial_date"):
            use_initial_date = aluno.use_initial_date
        else:
            use_initial_date = False

    plan = "undertermined"
    transition = False
    faculdades = {}
    requisitos = []
    if use_initial_date:
        reference_date = aluno.unit_date_inicial.value
    else:
        reference_date = aluno.unit_date_final.value

    if reference_date < "1772-00-00":
        faculdades = faculdades_pre_1772
        requisitos = requisitos_pre_1772
        plan = "pre-1772"
    elif reference_date < "1836-00-00":  # check correct date
        faculdades = faculdades_1772_1836
        requisitos = requisitos_1772_1836
        plan = "1772-1836"
    else:
        faculdades = faculdades_post_1836
        requisitos = requisitos_post_1836
        plan = "post-1836"
    if aluno.unit_date_inicial.value < "1772-00-00" and aluno.unit_date_final.value > "1772-00-00":
        transition = True
        plan = "pre-1772:1772-1836"
    elif aluno.unit_date_inicial.value < "1836-00-00" and aluno.unit_date_final.value > "1836-00-00":
        transition = True
        plan = "1772-1836:post-1836"
    return plan, faculdades,requisitos, transition # This is a strange override by the algoritm


ordens = {
    "cristo": "Ordem de Cristo",
    "bernardo": "Ordem de São Bernardo",
    "ordem de s\. francisco": "Ordem de São Francisco",
    "ordem de são francisco": "Ordem de São Francisco",
    "francisco": "Ordem de São Francisco",
    "bento": "Ordem de São Bento",
    "beneditino": "Ordem de São Bento",
    "s. domingo": "Ordem de São Domingos",
    "s. tomás": "Ordem de São Domingos",
    "são tomás": "Ordem de São Domingos",
    "domingos": "Ordem de São Domingos",
    "trindade": "Ordem da Santíssima Trindade",
    "carmo": "Ordem do Carmo",
    "carmelita": "Ordem do Carmo",
    "colégio da graça": "Ordem de Santo Agostinho (Graça)",
    "nossa senhora da graça": "Ordem de Santo Agostinho (Graça)",
    "graça": "Ordem de Santo Agostinho (Graça)",
    "santa cruz": "Ordem dos Cónegos Regrantes de Santo Agostinho",
    "regrante de santo agostinho": "Ordem dos Cónegos Regrantes de Santo Agostinho",
    "regular de santo agostinho": "Ordem dos Cónegos Regrantes de Santo Agostinho",
    "descalço de santo agostinho": "Ordem de Santo Agostinho (Descalços)",
    "agostinhos descalços": "Ordem de Santo Agostinho (Descalços)",
    "agostinho descalço": "Ordem de Santo Agostinho (Descalços)",
    "santa rita": "Ordem de Santo Agostinho (Descalços)",
    "agostinho": "Ordem de Santo Agostinho",
    "pregadores": "Ordem de São Domingos",
    "jerónimo": "Ordem de São Jerónimo",
    "santo loio": "Ordem de São João Evangelista",
    "loio": "Ordem de São João Evangelista",
    "lóio": "Ordem de São João Evangelista",
    "loios": "Ordem de São João Evangelista",
    "lóios": "Ordem de São João Evangelista",
    "evangelista": "Ordem de São João Evangelista",
    "são joão": "Ordem de São João de Deus",
    "s. joão": "Ordem de São João de Deus",
    "joão de deus": "Ordem de São João de Deus",
    "tomar": "Ordem de Cristo",
    "3ª": "Ordem Terceira",
    "terceira": "Ordem Terceira",
    "avis": "Ordem de Avis",
    "santiago": "Ordem de Santiago",
    "tiago": "Ordem de Santiago",
    "alcântara": "Ordem de São Pedro de Alcântara",
    "antónio": "Ordem de Santo António",
    "são paulo": "Ordem de São Paulo",
    "s. paulo": "Ordem de São Paulo",
    "paulo": "Ordem de São Paulo",
    "padre frei do colégio dos padres de são pedro": "Ordem Terceira",
    "padre frei colégio dos padres de são pedro": "Ordem Terceira",
    "padre frei, colégio dos padres de são pedro": "Ordem Terceira",
    "ordem de são pedro": "Ordem de São Pedro",
    "ordem de s. pedro": "Ordem de São Pedro",
    "pedro": "Ordem de São Pedro",
    "companhia de jesus": "Companhia de Jesus",
    "companhia": "Companhia de Jesus",
    "colegial do colégio de jesus": "Companhia de Jesus",
    "militar": "Ordens militares",
}

# These are the first names with more than 5 occurrences
# Check notebook 00-remissivas to obtain the current list

pnomes = [
    "Abel",
    "Abílio",
    "Acácio",
    "Acúrcio",
    "Adão",
    "Adelino",
    "Adolfo",
    "Adriano",
    "Adrião",
    "Afonso",
    "Agnelo",
    "Agostinho",
    "Aires",
    "Albano",
    "Alberto",
    "Albino",
    "Aleixo",
    "Alexandre",
    "Alfredo",
    "Alípio",
    "Álvaro",
    "Amadeu",
    "Amador",
    "Amancio",
    "Amândio",
    "Amaro",
    "Ambrósio",
    "Américo",
    "Anacleto",
    "Anastácio",
    "André",
    "Ângelo",
    "Aníbal",
    "Aniceto",
    "Anselmo",
    "Antão",
    "Antero",
    "António",
    "Antrónio",
    "Apolinário",
    "Arcanjo",
    "Aristides",
    "Armando",
    "Arnaldo",
    "Arsenio",
    "Artur",
    "Ascenso",
    "Atanásio",
    "Augusto",
    "Aureliano",
    "Aurélio",
    "Avelino",
    "Baltasar",
    "Barnabé",
    "Bartolomeu",
    "Basílio",
    "Batista",
    "Belchior",
    "Benjamim",
    "Bento",
    "Berardo",
    "Bernardino",
    "Bernardo",
    "Boaventura",
    "Bonifácio",
    "Brás",
    "Bruno",
    "Caetano",
    "Calisto",
    "Camilo",
    "Cândido",
    "Carlos",
    "Casimiro",
    "Celestino",
    "César",
    "Cipriano",
    "Cláudio",
    "Clemente",
    "Constantino",
    "Cosme",
    "Crisogono",
    "Crispim",
    "Cristiano",
    "Cristóvão",
    "Custódio",
    "Dâmaso",
    "Damião",
    "Daniel",
    "David",
    "Delfim",
    "Desidério",
    "Diamantino",
    "Dinis",
    "Diogo",
    "Dionísio",
    "Domingos",
    "Duarte",
    "Edmundo",
    "Eduardo",
    "Egídio",
    "Eleuterio",
    "Elias",
    "Elisío",
    "Emídio",
    "Emílio",
    "Ernesto",
    "Estácio",
    "Estanislau",
    "Estevão",
    "Eugénio",
    "Eurico",
    "Eusébio",
    "Eustáquio",
    "Evaristo",
    "Fabião",
    "Fabricio",
    "Faustino",
    "Fausto",
    "Feliciano",
    "Felício",
    "Felisberto",
    "Felix",
    "Fernando",
    "Fernão",
    "Filipe",
    "Firmino",
    "Florêncio",
    "Fortunato",
    "Fradique",
    "Francisco",
    "Frederico",
    "Fructuoso",
    "Frutuoso",
    "Gabriel",
    "Garcia",
    "Gaspar",
    "Gerardo",
    "Germano",
    "Gervásio",
    "Gil",
    "Giraldo",
    "Gomes",
    "Gonçalo",
    "Gregório",
    "Gualter",
    "Guilherme",
    "Gustavo",
    "Heitor",
    "Henrique",
    "Henriques",
    "Herculano",
    "Hermano",
    "Higidio",
    "Hilário",
    "Hipólito",
    "Horácio",
    "Ildefonso",
    "Inácio",
    "Inocêncio",
    "Isidoro",
    "Ivo",
    "Jacinto",
    "Jacome",
    "Jaime",
    "Januário",
    "Jerónimo",
    "João",
    "Joaquim",
    "Jordão",
    "Jorge",
    "José",
    "Julião",
    "Júlio",
    "Justino",
    "Lancerote",
    "Lázaro",
    "Leandro",
    "Leão",
    "Leonardo",
    "Leonel",
    "Leopoldo",
    "Libânio",
    "Lino",
    "Lopo",
    "Lourenço",
    "Lucas",
    "Luciano",
    "Lúcio",
    "Luís",
    "Macário",
    "Mamede",
    "Manuel",
    "Marçal",
    "Marcelino",
    "Marcos",
    "Mariano",
    "Mário",
    "Martim",
    "Martinho",
    "Martins",
    "Mateus",
    "Matias",
    "Mauricio",
    "Maximiano",
    "Máximo",
    "Melchior",
    "Mendo",
    "Miguel",
    "Narciso",
    "Nicolau",
    "Norberto",
    "Nuno",
    "Onofre",
    "Óscar",
    "Paio",
    "Pantaleão",
    "Pascoal",
    "Patrício",
    "Paulino",
    "Paulo",
    "Pedro",
    "Plácido",
    "Policarpo",
    "Pompeu",
    "Porfírio",
    "Possidónio",
    "Prudêncio",
    "Quintino",
    "Rafael",
    "Raimundo",
    "Ramiro",
    "Rául",
    "Ricardo",
    "Roberto",
    "Rodrigo",
    "Romão",
    "Roque",
    "Rosendo",
    "Rufino",
    "Rui",
    "Salvador",
    "Sancho",
    "Santos",
    "Sebastião",
    "Semião",
    "Serafim",
    "Sérgio",
    "Severino",
    "Silvério",
    "Silvestre",
    "Simão",
    "Simião",
    "Simplicio",
    "Teodoro",
    "Teodósio",
    "Teófilo",
    "Teotónio",
    "Timóteo",
    "Tito",
    "Tomás",
    "Tomé",
    "Torcato",
    "Tristão",
    "Urbano",
    "Valentim",
    "Valério",
    "Vasco",
    "Venâncio",
    "Ventura",
    "Veríssimo",
    "Vicente",
    "Virgílio",
    "Viriato",
    "Vital",
    "Vitor",
    "Vitoriano",
    "Vitorino",
    "Xavier",
    "Zeferino",
]


def get_extractors():
    """Ensure that extractors were loaded

    This is just a place holder to allow
    for

        from ucalumni.extractor import get_extractors()

    The result is irrelevant the import does what is necessary

    """
    return Aluno.extractors


def extract_name_note_vid(aluno: Aluno):
    """
    Extract notes and remission in names.

    - Stores clean name in aluno.nome.
    - Stores any string between parenthesis in the name in a new "nota"
      for processing by other extractors
    - Stores any string after "vide" in aluno.vide

    :param aluno: current aluno information object
    :return: None
    """

    # The following if is used during tests because
    # the name is stored in the obs of the record and
    # test_specific tests grab it from there and feed
    # to process_bioreg through which it ends in a note
    #
    # In normal import from archeevo the name is in metadata
    if (
        "*nosection*" in aluno.notas_index
        and "Nome" in aluno.notas_index["*nosection*"]
    ):
        pname, _, _ = aluno.notas_index["*nosection*"]["Nome"][0]
    else:
        pname = aluno.nome.strip()
    r = NAME_ANY.parseString(pname)
    aluno.nome = pname
    rn = r.asDict()

    # male names that end in "a"
    male_first_names = [
        "Boaventura",
        "Garcia",
        "Vieira",
        "Lima",
        "Azurara",
        "Ventura",
        "Batista",
    ]
    if "nota" in rn.keys():
        nome_ = rn.get("nome", rn.get("nome1"))
        aluno.nome = " ".join(nome_)
        nota = rn["nota"]
        aluno.nota = nota
        aluno.add_nota("nome", "nota", nota, aluno.unit_date_inicial, pname)
    if "remissão" in rn.keys():
        aluno.vide = " ".join(rn["nome2"])
        nome_vide = aluno.vide
        nome = " ".join(rn["nome1"])
        aluno.nome = nome
        # we invert the string, use commonprefix and again
        terminacao_comum = commonprefix([nome[::-1], nome_vide[::-1]])[::-1]
        # check it is a separate name and not just common letters at the end
        # a proper family name should share a starting space
        if len(terminacao_comum) > 0:
            if terminacao_comum[0] != " ":
                terminacao_comum = ""  # not a separate name, abandom
            else:
                terminacao_comum = terminacao_comum.strip()

        # infer the name of the target
        nomes = nome.split(" ")
        nomes_vide = nome_vide.split(" ")
        # Type CUT: vide is a inner part of the original name
        # e.g. André Vaz Cabaço, vide Vaz
        # but also Manuel de Almeida Cabral, vide de Almeida
        pos = nome.find(nome_vide)
        if pos > -1:
            lookup_name = nome[0:pos] + nome_vide
            vtype = "cut"
        # Type REP: vide name looks like a full name
        # e.g. António de Abreu Bacelar de Azevedo, vide António Abreu Bacelar
        # relaxing the same first name rule, lots  of leaks
        #  This leaks a lot : elif len(nomes_vide)>1 and nomes_vide[0] in pnomes :
        elif nomes[0] == nomes_vide[0]:
            lookup_name = nome_vide
            vtype = "rep"
        # Type REPAP: vide overlaps end of name
        # e.g. Joaquim Carvalho, vide Ramos de Carvalho
        # but vide must not contain first name
        # in that case probably a REP
        # otherwise generates leaks and lowers mumbers of matches
        elif terminacao_comum > "":
            if not nomes_vide[0] in pnomes:
                lookup_name = re.sub(f"{terminacao_comum}$", nome_vide, nome)
                vtype = "repap"
            else:  # if common termination and first name better replace
                lookup_name = nome_vide
                vtype = "rep"
        else:
            # TYPE Add vide name is not part of original nor a full name
            # so it must be an aditional surname
            # e.g. Fernão Cabral, vide Albuquerque = Fernão Cabral Albuquerque
            lookup_name = nome + " " + nome_vide
            vtype = "add"

        # we try to recover cases where there was replacement of first name
        # they are missed by the REP amd REPAP rules above and end up
        # producing lookup which are the sobreposition of two names
        # this was added by examining bad "ADD" and "REPAP" results
        # if the result is a long name (>5 names), both name and vide start
        # with first names and vide also long (>4) then probable a replace
        # that changes the first name.
        nomes_lookup = lookup_name.split()
        if (
            vtype != "rep"
            and nomes[0] in pnomes
            and nomes_vide[0] in pnomes
            and nomes[0] != nomes_vide[0]
            and len(nomes_vide) > 3
            and len(nomes_lookup) > 5
        ):
            lookup_name = nome_vide

        aluno.vide_type = vtype
        aluno.vide_target = lookup_name

    aluno.pnome = aluno.nome.split(" ")[0]
    # print('pnome stored! '+aluno.pnome)
    aluno.apelido = aluno.nome.split(" ")[-1]
    if aluno.pnome[-1] == "a" and aluno.pnome not in male_first_names:
        aluno.sexo = "f"
    else:
        aluno.sexo = "m"


Aluno.add_extractor(extract_name_note_vid)


def extract_colegio(aluno: Aluno):
    if getattr(aluno, "nota", None) is not None:
        nota_ao_nome = aluno.nota
        if (
            "colégio" in nota_ao_nome.lower()
            or "colegio" in nota_ao_nome.lower()
            or "colegial" in nota_ao_nome.lower()
            or "porcionista" in nota_ao_nome.lower()
            or "familiar" in nota_ao_nome.lower()
        ):
            colegio = nota_ao_nome.lower()
            if "graça" in colegio:
                colegio = "Colégio da Graça"
            elif (
                "frei" in colegio or "padre" in colegio or "3" in colegio
            ) and "pedro" in colegio:
                colegio = "Colégio de S.Pedro da Ordem Terceira"
            elif "pedro" in colegio:
                colegio = "Colégio de S.Pedro"
            elif (
                "joão" in colegio
                or "evangelista" in colegio
                or "lóios" in colegio
                or "loios" in colegio
            ):
                colegio = "Colégio de S.João Evangelista"
            elif "trindade" in colegio:
                colegio = "Colégio da Trindade"
            elif "boaventura" in colegio:
                colegio = "Colégio de S.Boaventura"
            elif "jesus" in colegio:
                colegio = "Colégio de Jesus"
            elif "cristo" in colegio:
                colegio = "Colégio de Tomar"
            elif "bento" in colegio:
                colegio = "Colégio de S.Bento"
            elif "paulo" in colegio:
                colegio = "Colégio de S.Paulo"
            elif "militar" in colegio or "militares" in colegio:
                colegio = "Colégio das Ordens Militares"
            elif "rita" in colegio:
                colegio = "Colégio de Santa Rita"
            elif "bernard" in colegio:
                colegio = "Colégio de S.Bernardo"
            else:
                stop = "padre reitor padres frei monge eremita d. religioso colegial porcionista familiar da de do dos das"
                nota_ao_nome = nota_ao_nome.replace("São ", "S.").replace(",", " ")
                clean = [
                    pal
                    for pal in nota_ao_nome.split()
                    if pal.lower() not in stop.split()
                ]
                colegio_clean = " ".join(clean)
                colegio = colegio_clean.lower()
                colegio = colegio_clean
            aluno.colegio = colegio


Aluno.add_extractor(extract_colegio)

def extract_titulo(aluno: Aluno):


    # note the space after "lente" to avoid matching "Alentejo"
    titulos = (
            "d.,Dom,frei,padre,abade,arcediago,barão,"
            "beneficiado,bispo,capelão,chantre,cónego,"
            "lente ,"
            "marquês,monge,porcionista,presbítero,"
            "visconde"
    )
    if getattr(aluno, "nota", None) is not None:
        nota_ao_nome = aluno.nota
        aluno_titulo = None
        for titulo in titulos.split(","):
            if titulo in nota_ao_nome.lower():
                if "D." in nota_ao_nome or "Dom" in nota_ao_nome or "dom" in nota_ao_nome:
                    aluno_titulo = "Dom",

                elif titulo == "padre":
                    aluno_titulo = "Padre"
                elif titulo == "lente":
                    aluno_titulo = "Lente"
                else:
                    aluno_titulo = titulo.strip().capitalize()
                aluno.titulos.append(aluno_titulo)

Aluno.add_extractor(extract_titulo)

def extract_ordem_religiosa(aluno: Aluno):
    if getattr(aluno, "nota", None) is not None:
        nota_ao_nome = aluno.nota
        if (
            "ordem" in nota_ao_nome.lower()
            or "ordens" in nota_ao_nome.lower()
            or "religioso" in nota_ao_nome.lower()
            or "monge" in nota_ao_nome.lower()
            or "frei" in nota_ao_nome.lower()
            or "companhia" in nota_ao_nome.lower()
            # why only some colleges? These are the ones that infer the ordem
            or "colégio de jesus" in nota_ao_nome.lower()
            or "colégio dos lóios" in nota_ao_nome.lower()
            or "cónego regular" in nota_ao_nome.lower()
            or "cónego regular" in nota_ao_nome.lower()
            or "cónego regrante" in nota_ao_nome.lower()
            or "santa cruz" in nota_ao_nome.lower()
        ):
            hits = list_search(ordens.keys(), nota_ao_nome.lower())
            if len(hits) > 0:
                # we keep the longer match since only one "ordem" per person is possible
                # this requires that in the case of overlapping matches the longer
                # strings come first
                ordem = sorted(hits, key=len)[-1]
                aluno.ordem = [ordens.get(ordem, ordem)]
            else:
                stop = "padre frei religioso da de do dos das e"
                nota_ao_nome = nota_ao_nome.replace("São ", "S. ")
                clean = [
                    pal
                    for pal in nota_ao_nome.split()
                    if pal.lower() not in stop.split()
                ]
                if len(clean) == 0:
                    clean = [aluno.nota]
                aluno.ordem.append(" ".join(clean))


Aluno.add_extractor(extract_ordem_religiosa)


def extract_naturalidade(aluno: Aluno):
    for nota in aluno.get_unprocessed_note():
        if nota.campo.lower() == "naturalidade":
            aluno.naturalidade = nota.valor.strip()
            nota.processed = True


Aluno.add_extractor(extract_naturalidade)


def extract_instituta(aluno: Aluno):
    """
    We do not process "inferred" field for Instituta
    except if the line was date only.

    NOTE: Must go before faculdade and matricula extractors

    """
    nota: Nota
    for nota in aluno.notas:  # Other extractors might have used the same
        if (
            "instituta" in nota.campo.lower()
            or "instituta" in nota.seccao.lower()
            or "instituta" in nota.valor.lower()
        ):
            if nota.fvalue_is_date or (
                not nota.fname_inferred and nota.fvalue_contains_date
            ):
                aluno.instituta.append(
                    Instituta(nota.data, f"{nota.obs} {nota.valor}".strip())
                )
                nota.processed = True


Aluno.add_extractor(extract_instituta)


def extract_faculdade(aluno: Aluno):
    """
    Extract all references to faculdades and also
    to pre-requisite studies, like Artes, Instituta, "Direito"
    check dictionnaries of terms at the top of this file
    """
    # Determine which list of Faculdades is relevant for this student
    use_initial_date = False  # use initial or final date to determina study plan
    plan, faculdades, requisitos, transition = match_with_study_plan(aluno, use_initial_date=use_initial_date)

    if getattr(aluno, "faculdade", None) is None:
        aluno.faculdade = []
    backup_fac = []
    aluno.has_faculdade = False
    if aluno.faculdade_problem_obs is None:
        aluno.faculdade_problem_obs = ""
    if aluno.faculdade_problem is None:
        aluno.faculdade_problem = ""

    if transition:
        aluno.faculdade_problem_obs = f"Reforma durante estudos: {aluno.unit_date_inicial} a {aluno.unit_date_final}. {aluno.faculdade_problem_obs}"

    for nota in aluno.notas:
        data = nota.data
        obs = nota.obs
        fvalor = nota.valor
        line = str(nota)
        if nota.campo.lower() == "faculdade":

            # we save the value of faculdade at this point
            if len(fvalor.strip(" -:?")) > 0:
                aluno.faculdade_original = fvalor

            aluno.has_faculdade = True
            # check if value of faculdade is a faculdade in the relevant period
            hits = list_search(faculdades.keys(), fvalor.lower())
            if len(hits) > 0:
                for fac in hits:  # add to list of aluno faculdade if not already there
                    if fac not in [fac.lower() for (fac, d, o) in aluno.faculdade]:
                        match = list_search_match(faculdades.keys(), fac)
                        aluno.faculdade.append((faculdades.get(match, fac), data, obs))
            elif transition:  # student affected by study plan change
                # use alternate plan instead
                plan2, faculdades2, requisitos2, transition2 = match_with_study_plan(aluno, use_initial_date=not use_initial_date)
                hits = list_search(faculdades2.keys(), fvalor.lower())
                if len(hits) > 0:
                    for fac in hits:
                        if fac not in [fac.lower() for (fac, d, o) in aluno.faculdade]:
                            match = list_search_match(faculdades2.keys(), fac)
                            aluno.faculdade.append((faculdades2.get(match, fac), data, obs))
                    # use alternate plan
                    plan = plan2
                    faculdades = faculdades2
                    requisitos = requisitos2
                    transition = transition2
                    # we save the date used to determine the plan
                    # so that other extractors that rely on plans
                    # get the same one
                    aluno.use_initial_date = not use_initial_date
            if len(hits) == 0:
                # the field faculdade contained something unexpected
                # we save it anyway
                aluno.faculdade.append((f"{fvalor}", data, obs))
                aluno.faculdade_problem = (
                    "Erro: Valor não corresponde a faculdade neste período"
                )
                faculdade_problem_obs = f"'{fvalor}' não é faculdade em {aluno.unit_date_final}"
                aluno.faculdade_problem_obs = aluno.faculdade_problem_obs.replace(faculdade_problem_obs,"")  # remove duplicates
                aluno.faculdade_problem_obs = (
                    f"{faculdade_problem_obs}. {aluno.faculdade_problem_obs} "
                )
            nota.processed = True
        else:

            # avoid lines with just "Instituta" e.g. 138472
            if (
                nota.seccao == "*nosection*"
                and nota.campo == "*no-field-line*"
                and nota.valor.lower().strip() == "instituta"
            ):
                pass
            else:
                # The field was not "faculdade"
                # Check if the name of a faculdade appears
                # anywhere in the current note, save it,
                # just in case we end up with none or one that
                # is not coherent with the "matriculas"
                # then we can use whatever we find
                hits: list = list_search(faculdades.keys(), line.lower())
                # some specific cases the search fails in the line but
                # suceeds in the campo or valor fields
                if len(hits) == 0:
                    hits = list_search(faculdades.keys(), nota.campo.lower())
                if len(hits) == 0:
                    hits = list_search(faculdades.keys(), nota.valor.lower())
                for fac in hits:
                    match = list_search_match(faculdades.keys(), fac)
                    fac_value = faculdades.get(
                        match, fac
                    )  # get the normal name from the table
                    if ( fac_value.lower() != match.lower() or
                        fac.lower() != fvalor.lower()
                        or fac.lower() != nota.campo.lower()
                    ):
                        obs = nota.campo + ": " + fvalor + " " + obs
                    if fac_value not in [fac.lower() for (fac, d, o) in backup_fac]:
                        backup_fac.append((fac_value, data, obs))

    # Remove "faculdades" that are a requirement and keep the
    #  the main one.
    #  After 1772 all students should take courses in Philosophy and
    #  Mathematics.
    #  Also students of Leis and Cânones shared two years foundational
    #  studies in Law, often referred in the records as "Faculdade: Direito"
    #  We remove the requisitos form the list, we should get the main faculdade

    fac_names = list(set([fac for fac, date, obs in aluno.faculdade]))
    more_names = list(set([fac for fac, date, obs in backup_fac]))
    all_facs = fac_names + more_names  # all the faculdades in the record
    main_fac = sorted(list(set(all_facs).difference(set(requisitos))))

    # if empty probably is a faculdade that is both a requisite and degree awarding
    #   or it is a requisite only and it is helpful to keep
    if len(main_fac) == 0:
        if len(fac_names) > 0:  # keep the original then
            main_fac = fac_names
        elif len(backup_fac) > 0:  # if no original keep the backup
            main_fac = more_names

    same_fac = sorted(main_fac) == sorted(fac_names)

    # check if we need to make a note of any change
    # no faculdade was found
    if len(aluno.faculdade) == 0 and len(main_fac) == 0:
        if (
            aluno.faculdade_original is None
            and aluno.unit_date_inicial.value != "0000-00-00"
        ):
            aluno.faculdade_problem = "Erro: não foi possível determinar a faculdade"
    elif same_fac:  # catalog and inferred faculdade the same
        pass
    else:
        # overring catalog faculdade
        aluno.faculdade = []
        for fac in main_fac:
            fac_obs = ""
            if aluno.has_faculdade:
                aluno.faculdade_problem = "Aviso: faculdade corrigida"
                faculdade_problem_obs = (
                    f'Faculdade corrigida de "{aluno.faculdade_original}" para "{", ".join(main_fac)}"'
                )
                aluno.faculdade_problem_obs = aluno.faculdade_problem_obs.replace(faculdade_problem_obs,"")  # remove duplicates
                aluno.faculdade_problem_obs = f"{faculdade_problem_obs}. {aluno.faculdade_problem_obs}"
                fac_obs = f'Ficha original: {aluno.faculdade_original}'

            else:
                aluno.faculdade_problem = "Aviso: faculdade inferida"
                aluno.faculdade_problem_obs = f"Faculdade inferida: '{fac}'. {aluno.faculdade_problem_obs}"
                fac_obs = "Faculdade inferida"
            aluno.faculdade.append((fac, aluno.unit_date_inicial, fac_obs))

    problem = aluno.faculdade_problem
    aluno.faculdade_strange = None
    if problem is not None and problem > "" and aluno.faculdade_original is not None:
        # the original faculdade was changed algoritmically
        # if it was Filosofia or Matemática is OK
        # if the result is Canones or Leis is OK too
        # other changes (e.g. Direito corrected to Teologia) are
        # marked as "strange"
        fac_names = [f for (f, d, o) in aluno.faculdade]
        if aluno.faculdade_original in ["Filosofia", "Matemática"]:
            pass
        elif "Cânones" not in fac_names and "Leis" not in fac_names:
            aluno.faculdade_strange = (
                aluno.faculdade_problem_obs
            )

Aluno.add_extractor(extract_faculdade)


def extract_graus(aluno: Aluno):
    # NOTE in overlapping longer must come before shorter
    # 'bacharel em artes' before 'bacharel'
    graus = {
        "bacharel": "Bacharel",
        "formatura": "Formatura",
        "licenciado": "Licenciado",
        "mestre escola": "*SKIP*",
        "mestre em artes": "Mestre",
        "mestrado": "Mestre",
        "Doutoramento": "Doutor",
        "doutor": "Doutor",
    }
    # Determine which list of Faculdades is relevant for this student
    # we will use this to determine the area of the degree
    plan, faculdades, requisitos, transition = match_with_study_plan(aluno)

    for nota in aluno.get_unprocessed_note():
        campo = nota.campo.lower()
        # case 1: the field name is the name of a degree:
        #
        #  Bacharel: 1538/7/8
        #  Bacharel em Artes: 1540/2/12, Livro 3, fl. 100v., Caderno 3.º
        #
        grau_in_field = False
        hits = list_search(graus.keys(), campo.lower())

        # we need to note where the grau was detected to avoid
        # errors when processing this:
        #
        # ID: 249629
        #  Instituta:
        #    Bacharel em Leis 06.07.1538
        # Note that in this type of construct "Instituta" is
        # the field and "Bacharel em Leis" is the value
        # And Instituta decodes to "Cursos Jurídicos"
        #
        if len(hits) > 0:
            grau_in_field = True
        # case 2: the degree just appears in the line
        #
        # Bacharel, 16.ª 26.11.1915, aprovado com 12 valores,...
        #
        # We must take care of these cases:
        #  because the pre processor will keep the degree names
        #  as they do not end in ":" and not removed as empty fields
        #
        # 159940
        # Matrícula(s): 10.11.1640
        # Instituta
        # Bacharel
        # Formatura
        # Licenciado
        # Mestre

        # if no grau in the field name check the value
        if len(hits) == 0:
            hits = list_search(graus.keys(), nota.valor.lower())

        if len(hits) > 0:
            for g in hits:
                if g == "mestre" and "mestre escola" in hits:
                    continue  # skip
                if graus[g] == "*SKIP*":
                    continue
                if g.lower() == nota.valor.lower().strip(
                    " -:"
                ):  # just the degree name in the field
                    continue
                if nota.data.date_only:
                    obs = nota.obs
                else:
                    obs = nota.valor + " " + nota.obs

                # now lets see if we get a faculdade
                if (
                    grau_in_field
                ):  # only search field for fac in grau in field see above
                    hits = list_search(faculdades.keys(), campo.lower())
                else:
                    hits = []
                if len(hits) == 0:  # if not in the field check the value
                    hits = list_search(faculdades.keys(), nota.valor.lower())
                ambito = None
                for fac in hits:
                    match = list_search_match(faculdades.keys(), fac)
                    ambito = faculdades.get(match, fac)  # get the fac name
                if (
                    ambito is None and len(aluno.faculdade) > 0
                ):  # get the ambito from faculdade
                    facname, fdata, fobs = aluno.faculdade[0]
                    ambito = facname
                grau_nome = graus[g]
                if ambito is not None:
                    grau_nome = grau_nome + " em " + ambito
                else:
                    continue

                grau = Grau(grau_nome, ambito, nota.data, obs)
                if grau_nome not in [grau.nome for grau in aluno.graus]:
                    nota.processed = True
                    aluno.graus.append(grau)
                else:  # grau previously recorded check date
                    updated_graus = []
                    for g in aluno.graus:
                        if g.nome == grau.nome and g.data.value < grau.data.value:
                            updated_graus.append(grau)
                        else:
                            updated_graus.append(g)
                    aluno.graus = updated_graus


Aluno.add_extractor(extract_graus)


def extract_matriculas(aluno: Aluno):
    """Extracts matrículas. Must run after extract_faculdade

    Deals with

            Matrícula(s): Matemática 0.1.1792 (ordinário)
            Filosofia: 29.1.1792 (obrigado)
            3.1.1793
            13.1.1795
            Direito: 18.1.1793
            4.1.1794
            Leis: 3.1.1795
            4.1.1796
            4.1.1797

    and also

            Id: 139883
            Faculdade: Cânones
            Matrícula(s):01.10.1586
            01.10.1587
            04.01.1588
            10.02.1590

    The extractor for degrees should be run before this one and flag as
    "processed" lines under the "Matrícula(s):" header that relate to degrees
    e.g.
            # 142372
            Matrícula(s):
            Instituta:
            Bacharel:
            Formatura: 1572/3/29
            Licenciado em Artes: 1566/6/9
             A. Nemine

            146875
            Matrícula(s): Gramática: 1540

    Complex cases
            Matrícula(s):Filosofia 1775 (obrigado)
            Matemática 16.10.177 (obrigado)
            Teologia 10.1776
            16.10.1777
            23.10.1778
            10.1779
            18.10.1780

            Id: 316297
            Matrículas: 1.º ano jurídico 15.11.1774, Vol. III, L. I, fl. 20v.
            2.º jurídico 1775, Vol. IV, L. I, fl. 48
            1.º ano matemática (obrigado) 1775, Vol. IV, L. 4, fl. 48
            2.º ano jurídico 18.10.1776, Vol. V, L. I, fl. 35v.
            1.º ano matemática (obrigado) 08.10.1776, Vol. V, L. IV, fl. 12v.
            3.º ano cânones 06.10.1777, Vol. VI, fl. 10
            1.º ano filosofia 16.10.1777, Vol. VI, L. VI, fl. 13
            4.º ano cânones 02.10.1778, Vol VII, L. 2, fl. 26
            5.º ano cânones 03.11.1779, Vol. VII, L. 2, fl. 42
            6.º ano cânones 27.11.1780, Vol IX, L. 3, fl. 73

            Id: 153341
            Faculdade: Matemática # in fact Medicina

            Matrícula(s): 14.10.1794 (obrigado)
            2º ano - 16.10.1795 (obrigado)
            Filosofia - 14.10.1794 (obrigado)
            2º ano - 16.10.1795
            3º ano - 04.10.1796
            Medicina 1º ano - 04.10.1797
            2º ano - 09.10.1798
            3º ano - 02.10.1799
            4º ano - 23.10.1800
            5 º ano - 03.10.1801

    :param aluno: record with the notes to be processed
    :return: None
    """
    # set the list of Faculdades for this student
    plan, faculdades, requisitos, transition = match_with_study_plan(aluno)
    # other than Faculdades, we extract matrículas in
    cursos = {
        "gramática": "Gramática",
        "jurídico": "Curso jurídico",
        "dialética": "Dialética",
    }
    anos = {
        "1º": "1º ano",
        "1.º": "1º ano",
        "2º": "2º ano",
        "2.º": "2º ano",
        "3º": "3º ano",
        "3.º": "3º ano",
        "4º": "4º ano",
        "4.º": "4º ano",
        "5º": "5º ano",
        "5.º": "5º ano",
        "6º": "6º ano",
        "6.º": "6º ano",
    }
    previous_tipo = None  # used for lines with year fields only see 153341
    previous_faculdade = None
    previous_curso = None
    previous_classe = None

    # When processing matrículas with only dates
    # we need to deal with the situation where the
    # faculdade was changed by the algoritm
    # in some cases the matriculas should be associated
    # with the original faculdade in others with the
    # corrected one.
    # in the following example Matemática was changed to Medicina
    # because Matemática is a prerequisite.
    # But the first matriculas are in Matemática
    # Faculdade: Matemática
    #
    # Id: 221833
    #
    # Matrícula(s): 02.12.1772 (obrigado)
    # 11.10.1773
    # 10.10.1774
    # 13.10.1775
    # Medicina 19.10.1774
    # 13.10.1775
    # 23.10.1776
    # 23.10.1777
    # 19.10.1778
    #
    # But in the following we use "Cânones"
    # because the Faculdade original was overriden
    #  Id: 144910
    # Faculdade: Direito
    #
    # Matrícula(s): 29.10.1795
    # 04.10.1796
    # 13.10.1797
    # 02.10.1798
    # 02.10.1799
    # Exames em Cânones: 3º: 14.07.1798, Aprovado Nemine Discrepante, Atos nº 6, fl. 12
    fac_from_aluno = aluno.faculdade
    problem = aluno.faculdade_problem
    if problem is not None and problem > "" and aluno.faculdade_original is not None:
        # the faculdade was changed algoritmically
        # we accept the original for undated matriculas
        # if it was Filosofia or Matemática
        # this means that corrections to Direito are accepted
        # other changes (e.g. Direito corrected to Teologia) are
        # marked as "strange"
        fac_names = [f for (f, d, o) in aluno.faculdade]
        if aluno.faculdade_original in ["Filosofia", "Matemática"]:
            fac_from_aluno = [(aluno.faculdade_original, aluno.unit_date_inicial, "")]

    for nota in aluno.get_unprocessed_note():
        if (
            "matrícula" in nota.campo.lower()
            or "matrícula" in nota.seccao.lower()
            or "matricula" in nota.campo.lower()  # this is a common misspelling
            or "matricula" in nota.seccao.lower()
        ):
            data = nota.data
            obs = nota.obs
            valor = nota.valor
            campo = nota.campo
            tipo = "outra"

            # Determining what the matrícula is about (âmbito)
            # if matrícula is a seccao then the field can specifiy the "âmbito"
            # e.g. Matrícula(s): Leis: 1.1.1741 [140434]
            ambito_in_field = not "matrícula" in nota.campo.lower()

            # If field is not "matrícula(s)" then it may specifcy,
            #     "Faculdade", "Curso", "Year" or some combinations.
            #
            # Ex id: 153341
            # ...
            # Faculdade: Matemática
            # Matrícula(s): 14.10.1794 (obrigado)
            # 2º ano - 16.10.1795 (obrigado)
            # Filosofia - 14.10.1794 (obrigado)
            # 2º ano - 16.10.1795
            # 3º ano - 04.10.1796
            # Medicina 1º ano - 04.10.179
            # note that the "-" is treated as a field separator
            #

            if ambito_in_field:
                faculdade_in_campo = list_search(faculdades.keys(), campo.lower())
                curso_in_campo = list_search(cursos.keys(), campo.lower())
                year_in_campo = list_search(anos.keys(), campo.lower())
            else:
                faculdade_in_campo = []
                curso_in_campo = []
                year_in_campo = []

            # The same patterns can also occur in the value part, with no field separator
            #
            # Id: 316297
            # Matrículas: 1.º ano jurídico 15.11.1774, Vol. III, L. I, fl. 20v.
            # 2.º jurídico 1775, Vol. IV, L. I, fl. 48
            # 1.º ano matemática (obrigado) 1775, Vol. IV, L. 4, fl. 48
            #
            faculdade_in_valor = list_search(faculdades.keys(), valor.lower())
            curso_in_valor = list_search(cursos.keys(), valor.lower())
            year_in_valor = list_search(anos.keys(), valor.lower())

            # Look for mode (modalidade) of "matrícula": it can occur in the value but also in the date
            # so we concatenate field, value and date to look for the obrigado, ordinário
            if data.obs is None:
                data_obs = ""
            else:
                data_obs = data.obs

            if obs > " ":
                obs = obs + data_obs
            else:
                obs = data_obs.removeprefix(",")
            line = f"{campo.lower()} {valor.lower()} {data_obs}"
            obrigado = "obrigado" in line
            ordinario = "ordinário" in line
            voluntario = "voluntário" in line
            modalidade = (
                "obrigado"
                if obrigado
                else "voluntário" if voluntario else "ordinário" if ordinario else ""
            )

            # Faculdade
            facs = faculdade_in_campo + faculdade_in_valor
            if len(facs) > 0:
                tipo = "faculdade"
                previous_tipo = tipo
                for ambito in facs:
                    match = list_search_match(faculdades.keys(), ambito)
                    fac_name = faculdades.get(match, ambito)
                    if fac_name.lower() != ambito.lower():
                        obs = f"original: {ambito} {obs}"
                    aluno.matriculas.append(
                        Matricula(fac_name, tipo, modalidade, data, obs)
                    )
                    previous_faculdade = faculdades[match]

            # Cursos
            curs = curso_in_campo + curso_in_valor
            if len(curs) > 0:
                tipo = "curso"
                previous_tipo = tipo
                for ambito in curs:
                    match = list_search_match(cursos.keys(), ambito)
                    curso_name = cursos.get(match, ambito)
                    if curso_name.lower() != ambito.lower():
                        obs = f"original: {ambito} {obs}"
                    aluno.matriculas.append(
                        Matricula(curso_name, tipo, modalidade, data, obs)
                    )
                    previous_curso = cursos[match]

            # Classes
            # Check if we are not confusing year of programme with other ordinal numbers
            # like in
            # Id: 151042
            # Matrícula(s): 1578/10/16, Volume 1, Livro 3.º, fl. 2

            classes_ = year_in_campo + year_in_valor
            if (
                len(classes_) > 0
                and not "livro" in valor.lower()
                and not "caderno" in valor.lower()
            ):
                tipo = "classe"
                if previous_tipo == "faculdade":
                    base_classe = previous_faculdade
                    if (
                        len(facs) == 0
                    ):  # no faculdade on this line, generate for this date
                        aluno.matriculas.append(
                            Matricula(
                                previous_faculdade, previous_tipo, modalidade, data, obs
                            )
                        )
                elif previous_tipo == "curso":
                    base_classe = previous_curso
                    if len(curs) == 0:
                        aluno.matriculas.append(
                            Matricula(
                                previous_curso, previous_tipo, modalidade, data, obs
                            )
                        )
                elif previous_tipo == "classe":
                    base_classe = previous_classe
                else:
                    base_classe = " - ".join([fac for (fac, d, o) in fac_from_aluno])
                    obs = obs + " (âmbito da classe inferido)"
                for ambito in classes_:
                    classe = f'{base_classe}, {anos.get(ambito,f"!{ambito}!")}'
                    aluno.matriculas.append(
                        Matricula(classe, tipo, modalidade, data, obs)
                    )

            # Line does not contain faculdade,curso or class
            # we assume that matricula refers to faculdade
            # we use the original value if no problem detected
            # if not the inferred or corrected
            #  example 139883, 190269, 221833
            if tipo == "outra" and nota.fvalue_contains_date and not ambito_in_field:
                if previous_tipo == "faculdade":
                    ambitos = [previous_faculdade]
                    tipo = previous_tipo
                else:
                    ambitos = [fac for (fac, data, obs) in fac_from_aluno]
                    # it can happen that we have at this point no information for ambito
                    if len(ambitos) > 0:
                        tipo = "faculdade"
                        previous_tipo = tipo
                    else:  # if no ambito then set it to "Universidade"
                        ambitos = ["Universidade"]
                        tipo = "universidade"
                        previous_tipo = tipo
                for ambito in ambitos:
                    aluno.matriculas.append(
                        Matricula(ambito, tipo, modalidade, data, obs)
                    )
                    previous_faculdade = ambito

            if tipo == "outra":
                # could not determine type of matricula
                aluno.matriculas.append(
                    Matricula(f"{campo}: {valor}", tipo, modalidade, data, obs)
                )

            nota.processed = True


Aluno.add_extractor(extract_matriculas)


def extract_exames(aluno: Aluno):
    """ "
    Exames: 3.º 11.06.1796 Aprovado Nemine Discrepante, Atos n.º 5, fl. 55
    4.º e grau de Bacharel 10.06.1797 Aprovado Nemine Discrepante, Atos n.º 6, fl. 74
    Formatura 5.06.1798 Aprovado Nemine Discrepante, Atos n.º 6, fl. 167

    Exames: 11.ª 9.11.1911, aprovado com 12 valores, Atos n.º 27, fl. 194.
    9.ª 3.08.1912, aprovado com 12 valores, Atos n.º 28, fl. 85v.
    8.ª 19.11.1912, aprovado com 11 valores, Atos n.º 28, fl. 26.
    17.ª 28.11.1912, aprovado com 12 valores, Atos n.º 41, fl. 128.
    18.ª 18.07.1913, aprovado com 13 valores, Atos n.º 42, fl. 143.
    10.ª 14.08.1914, aprovado com 12 valores, Atos n.º 29, fl. 141v.
    Bacharel, 16.ª 26.11.1915, aprovado com 12 valores, Atos n.º 42, fl. 49.
    19.ª 20.1.1915, aprovado com 10 valores, Atos n.º 42, fl. 230v.

    Exames: 8.ª cadeira: 9.07.1911, Aprovado com 17 valores, Atos n.º 27, fl. 17
    9.ª cadeira: 20.06.1911, Aprovado com 15 valores, fl. 51
    10.ª cadeira: 31.07.1911, Aprovado com 17 valores, fl. 111 v.
    11.ª cadeira: 21.07.1911, Aprovado com 17 valores, fl. 180
    16.ª cadeira: 29.07.1913, Aprovado com 12 valores, Atos n.º 42, fl. 3v.
    17.ª cadeira: 20.07.1912, Aprovado com 14 valores, Atos n.º 41, fl. 108
    18.ª cadeira: 17.06.1912, Aprovado com 16 valores, fl. 152
    19.ª cadeira: 28.06.1912, Aprovado com 14 valores, fl. 224 v.
    """
    for nota in aluno.notas:  # Other extractors might have used the same
        if "exame" in nota.campo.lower() or "exame" in nota.seccao.lower():
            if "exame" not in nota.campo.lower():
                # The section name is exame and the field should be the ambito
                # note that in this case the field could have many words and
                # in that case it is truncated to the first word during
                # pre-processing, with the original pushed to value.
                #
                # see 1403363
                # Exames:
                #   4º e Grau de Bacharel: 27.06.1877, ...

                if len(nota.valor.split(":")) > 1:
                    # the original field was pushed to the value
                    ambito = nota.valor.split(":")[0]
                else:
                    ambito = nota.campo.strip()
            else:
                if nota.data.date_only:
                    # if we have only a date then the field name is used
                    ambito = nota.campo.strip()
                else:
                    if "exame" != nota.campo.lower() and "exames" != nota.campo.lower():
                        # we have exame in the field name but something more
                        #   e.g. "exame privado"
                        ambito = nota.campo.strip()
                    else:
                        ambito = ""

                    ambito = ambito + " " + nota.valor[0 : nota.data.start]
                    ambito = ambito.strip(".,: ")  # check  pre date
            try:
                data = nota.data
                if nota.data.scan_results is not None:
                    resultado = nota.data.scan_results["obs"].strip(
                        "., "
                    )  # whatever after the date
                    obs = nota.obs
                    aluno.exames.append(Exame(ambito, data, resultado, obs))
                    nota.processed = True
            except:
                nota.processed = False
    pass


Aluno.add_extractor(extract_exames)


def extract_provas(aluno: Aluno):
    """Extract notes like "provou"""
    for nota in aluno.notas:  # Other extractors might have used the same
        if ("prova" in nota.campo.lower()
            or "prova" in nota.seccao.lower()):

            aluno.provas.append(Prova(nota.valor, nota.data, nota.obs))
            nota.processed = True


Aluno.add_extractor(extract_provas)