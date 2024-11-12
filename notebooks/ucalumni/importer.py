"""
(c) Joaquim Carvalho 2021.
MIT License, no warranties.
"""

import csv
import os
from pathlib import Path
import time

from copy import deepcopy
from datetime import datetime
from math import trunc
from os import linesep as nl

from pyparsing import ParseResults

from timelink import version as timelink_version
from timelink.api.models import base  # noqa
from timelink.api.database import TimelinkDatabase
from timelink.api.models.pom_som_mapper import PomSomMapper
from timelink.kleio.groups import KElement, KPerson, KSource, KAct

from ucalumni import config
from ucalumni.config import Session
from ucalumni.fields import break_lines_with_repetitions, process_bioreg, process_field
from ucalumni.groups import atr, fonte, lista, n, kleio
from ucalumni.grammar import BIOLINE, preserve_original, DateUtility, scan_date
from ucalumni.aluno import Aluno
from ucalumni import extractors  # noqa this is necessary to map the extractors
from ucalumni.mapping import map_aluno_kperson


def process_bioreg_(aluno: Aluno) -> Aluno:
    """Pre process the information in BioHist and ScopeContent

    This function works as pre-processor for the subsequent stages
    of extraction of information from the original catalog record.

    It will process the lines in the BioHist and ScopeContent
    and detect field names, dates, repetition notes (";").
    It is here that dates are parsed and implicit fields names
    are inferred.

    The results are stored in the `Aluno` object mainly
    in an array of "Notes". Each note contains a Section, Field,
    Value, Date and Obs.

    After the collection of notes aluno.extract() is called to apply
    the extractors to the notes and other fields.

    See `READE_ucalumni` for details.


    """
    # new archeevo version export introduces ascii 29 artifact
    if chr(29) in aluno.scope_content:
        aluno.scope_content = aluno.scope_content.replace(chr(29), " ")
    if "#29;" in aluno.scope_content:
        aluno.scope_content = aluno.scope_content.replace("#29;", " ")
    bioreg = aluno.bio_hist + nl + aluno.scope_content
    if hasattr(aluno, "obs") and aluno.obs.startswith("# DB LOAD"):
        aluno.obs = aluno.scope_content
    else:
        aluno.obs = f"""
Id: {aluno.id}
Código de referência: {aluno.codref}

Nome        : {aluno.nome}
Data inicial: {aluno.unit_date_inicial}
Data final  : {aluno.unit_date_final}
{aluno.bio_hist}
{aluno.scope_content}
"""

    udi = aluno.unit_date_inicial
    udf = aluno.unit_date_final
    try:
        aluno.unit_date_inicial = DateUtility(udi)
    except Exception:
        aluno.unit_date_inicial = DateUtility("")
    try:
        aluno.unit_date_final = DateUtility(udf)
    except Exception:
        aluno.unit_date_final = DateUtility("")

    section = ""
    line_is_just_date = False
    fname = ""
    fvalue = ""
    nbioreg = break_lines_with_repetitions(
        bioreg
    )  # we join again with new lines and '#'
    first_word_of_prev_line = ""
    BIOLINE.setParseAction(preserve_original)
    line_number = 0
    for line in nbioreg.splitlines():
        # if len(line.strip()) == 0:
        #    line = '# Empty line'
        if len(line.strip()) > 0 and line.strip()[0] == "#":
            continue  # we treat lines starting with # as comments
        line_number = line_number + 1
        line_parsed = False
        # print('Line: ',line)
        r = BIOLINE.parseString(line)
        # print(r.dump())
        k = r.asDict().keys()
        if "repeat" in k:  # Remove the repeat prefix
            line = r.original
            # we add attribute for later
            r.first_word_for_repeat = first_word_of_prev_line

        if "pai" in k:
            npai = " ".join(r.pai)
            aluno.pai = npai
            # print(f'pn${npai}')
            if "mae" in k:
                nmae = " ".join(r.mae)
                aluno.mae = nmae
                # print(f'mn${nmae}')

        # we can have 'section' and 'fname' in the same line
        # so we need to test for both separetly
        if "section" in k:
            # print()
            # print('[Section] Section ', r['section'])
            section = r["section"]
            # Note that we have a section followed by no field lines
            # we need to avoid the previous field to "continue" in
            # the new section, e.g.
            #   Faculdade:
            #   Matrícula(s):
            #   Cânones 1558.10.01 a 1559.05.31

            fname = ""
            line_parsed = True

        if "fname" in k:
            line_parsed = True
            previous_fname = fname  # save the last fname
            fname = r["fname"]
            fvalue = r["fvalue"]
            if len(fname.split()) > 3:
                # long field name, probably error
                # we take the first word and push the line to value
                fvalue = fname + ": " + fvalue
                fname = fname.split()[0]

            if fname == "Nome":
                aluno.nome = fvalue
            elif fname == "Data inicial":
                try:
                    aluno.unit_date_inicial = DateUtility(fvalue)
                except ValueError:
                    aluno.unit_date_inicial = DateUtility("")
            elif fname == "Data final:":
                try:
                    aluno.unit_date_final = DateUtility(fvalue)
                except ValueError:
                    aluno.unit_date_final = DateUtility("")
            elif fname == "idem":
                fname = previous_fname

            if "matrícula" in fname.lower() or "matricula" in fname.lower():
                section = "Matrículas"

            if "exames" in fname.lower():
                section = "Exames"

            fname, fvalue, line_is_just_date = process_field(
                r, section, fname, fvalue, aluno
            )
            if "idem" in k:  # line contain another value
                fvalue = r["idem"]
                fname, fvalue, line_is_just_date = process_field(
                    r, section, fname, fvalue, aluno
                )

        # line contains only a date, we repeat the last field
        elif "day" in k or "day1" in k:
            line_parsed = True
            du = DateUtility(r)
            fvalue = du.original
            fname, fvalue, line_is_just_date = process_field(
                r, section, fname, fvalue, aluno
            )
            # du = date_utility(r)
            # print(f'[date]    {section} >> {fname}: {du} %{du.original}')
            # if line_is_just_date:
            # print(f'ls${fname}/{normal_date}%{original_date}/data={normal_date}')
            #   person.include(ls(fname,(du.value,None,du.original),data=du.short))
            # else:
            # print( f'ls${fname}/{fvalue}/data={normal_date}')
            #  person.include(ls(fname,du.original,data=du.short))
        elif "blank" in k:
            line_parsed = True
            section = ""
            fname = ""
        elif "nomatch" in k:  # no match
            if not fname > "":
                fname = "*no-field-line*"
            fvalue = line.strip()
            fname, fvalue, line_is_just_date = process_field(
                r, section, fname, fvalue, aluno
            )
            line_parsed = True

        if not line_is_just_date:  # save the first word for repeating values
            if len(fvalue.split()) > 0:
                first_word_of_prev_line = fvalue.split()[0]
    # finished processing lines, extract information
    aluno.extract()
    return aluno


# keep a counter for file names
letter_counter = {}


def row_to_kgroup(row):
    """Check type of row and call adequate converter

    The export contains a single SSR record,
    an UI record for each letter of the alphabet
    an D record for each student record

    """
    description_level = row["DescriptionLevel"]
    if description_level == "SSR":
        return row_to_ksource(row)
    elif description_level == "UI":
        return row_to_klista(row)
    elif description_level == "D":
        return row_to_n(row, atrs=False)


def row_to_ksource(row, atrs=False):
    description_level = row["DescriptionLevel"]
    assert description_level == "SSR", "Description level SSR expected!"
    group_name = "source"
    unit_title = row["UnitTitle"]
    reference = row["CompleteUnitId"]
    gid = row["\ufeffID"]
    unit_date_initial = row["UnitDateInitial"]
    unit_date_final = row["UnitDateFinal"]
    data = unit_date_initial + ":" + unit_date_final
    scope_content = row["ScopeContent"]
    arrangement = row["Arrangement"]
    url = "http://pesquisa.auc.uc.pt/details?id=" + row["\ufeffID"]
    obs = (
        "Âmbito e conteúdo"
        + nl
        + nl
        + scope_content
        + nl
        + nl
        + "Sistema de organização"
        + nl
        + nl
        + arrangement
        + nl
        + nl
        + "URL: "
        + url
    )

    # get the sequential number for this id
    snumber = letter_counter.get(gid, 0)
    snumber = snumber + 1
    letter_counter[gid] = snumber
    # set id of fonte
    fonte_id = f"lista-{gid}-{snumber:05}"  # later we override this id with one derived from the letter

    gt = fonte(
        fonte_id,
        tipo="UC-AUC-ficheiro-alunos",
        data=data,
        loc="Arquivo da Universidade de Coimbra",
        ref=reference,
        obs=obs,
    )
    exclude_from_atrs = [
        "\ufeffID",
        "RepositoryCode",
        "UnitTitle",
        "UnitDateInitial",
        "UnitDateFinal",
        "DescriptionLevel",
        "ScopeContent",
        "Arrangement",
        "Creator",
        "Created",
        "Username",
        "Processinfo",
    ]
    if atrs:
        for a, v in row.items():
            if v > " " and a not in exclude_from_atrs:
                gt.include(atr("xauc-" + a, v))
    return gt


def row_to_klista(row, reference_date="2020-02-11", atrs=False):
    unit_id = row["UnitId"]
    repository_code = row["RepositoryCode"]

    letra = unit_id
    # get the sequential number for this letter
    snumber = letter_counter.get(letra, 0)
    snumber = snumber + 1
    letter_counter[letra] = snumber
    gid = f"alunos-{letra}-{snumber:05}"

    unit_title = row["UnitTitle"]
    unitDateInitial = row["UnitDateInitial"]
    unitDateFinal = row["UnitDateFinal"]
    data = unitDateInitial + ":" + unitDateFinal
    reference = row["CompleteUnitId"]

    year = reference_date[0:4]
    month = reference_date[5:7]
    day = reference_date[8:10]
    l = lista(
        gid,
        dia=day,
        tipo="lista-de-alunos",
        mes=month,
        ano=year,
        data=reference_date,
        loc=unit_id,
    )
    exclude_from_atrs = [
        "RepositoryCode",
        "UnitTitle",
        "UnitDateInitial",
        "UnitDateFinal",
        "Creator",
        "Created",
        "Username",
        "Processinfo",
    ]
    if atrs:
        for a, v in row.items():
            if v > " " and a not in exclude_from_atrs:
                l.include(atr("xauc-" + a, v))
    return l


def row_to_n(row, atrs=False, direct_import=False) -> n:

    # create the Aluno record to hold information to be processed
    pdate = None

    if "ProcessInfoDate" in row.keys():
        pdate = row["ProcessInfoDate"]
    elif "PublicationDate" in row.keys():
        pdate = row["PublicationDate"]

    if pdate is not None:
        record_date = datetime.strptime(pdate, "%d/%m/%Y %H:%M:%S")
        rds = record_date.strftime("%Y-%m-%d")
    else:
        rds = "0000-00-00"

    row_id = row["\ufeffID"]
    # this allows a break point to be made at a specific record
    if row_id == "140436":
        break_point_here = True  # set the break point in your debugger

    aluno = Aluno(
        row["\ufeffID"],
        row["CompleteUnitId"],
        row["UnitTitle"].strip(),
        row["UnitDateInitial"],
        row["UnitDateFinal"],
        record_date,
        "https://pesquisa.auc.uc.pt/details?id=" + row["\ufeffID"],
    )

    aluno.bio_hist = row["BiogHist"]
    aluno.scope_content = row["ScopeContent"]

    # process the information in BioHist and ScopeContent
    process_bioreg(aluno)
    # map the result to a Kleio person group
    p = map_aluno_kperson(aluno)
    if direct_import:
        if len(p.includes("referido")) > 0:
            pai = p.includes("referido")[0]
            pai.sex = "m"
            if len(p.includes("referida")) > 0:
                mae = p.includes("referida")[0]
                mae.sex = "f"

    # p.dots.maes[0].id

    if atrs:
        exclude_from_atrs = [
            "\ufeffID",
            "UnitTitle",
            "UnitDateInitial",
            "UnitDateFinal",
            "BiogHist",
            "ScopeContent",
            "Creator",
            "Created",
            "Username",
            "Processinfo",
        ]
        for a, v in row.items():
            if v > " " and a not in exclude_from_atrs:
                p.include(atr("xauc-" + a, v))
    return p


def export_alumni_source(
    sources_dir: str, kleio_group: kleio, testing=False, direct_import=False
):
    """Export the kleio_group with alumni information

    If direct_import is True the kleio_group will be directly inserted
    in a database using the Session variable in scope. If False then
    a text file in Kleio notation will be produced

    The file name and necessary sub directories are calculated from the kleio_group.
    We assume that all the students in the group were filled under the same last name
    initial letter ("A","B",...) and this letter is stored as the loc element of the group `lista`

    The file name will be the same as the id of the group source (fonte).
    The sub directory will be the initial of the last name of the students in this file.

    :param sources_dir: a path to destination directory
    :param kleio_group: a `kleio` object with enclosed `fonte`,`lista` and `n` records.
    :param testing: If true outputs to the terminal instead of file
    :param direct_import: If true data will be directly imported to database
                          associated with global variable Session and no Kleio
                          file will be generated.
    :return: None

    """
    First = 0
    Last = -1

    fontes = kleio_group.includes(group=KSource)
    assert len(fontes) == 1, "Grupo kleio must contain only one source (fonte)"
    fs: fonte = fontes[0]
    listas = fs.includes(group=KAct)
    assert len(listas) == 1, "Source group must contain only one list (lista)"

    lis: lista = listas[First]
    letra = lis.loc.core

    alunos = lis.includes(group=KPerson)
    if len(alunos) == 0:
        # Empty file, nothing to export
        print("Empty file, nothing to export")
        return

    aluno1 = alunos[First]
    aluno2 = alunos[Last]
    id1 = aluno1.id
    id2 = aluno2.id
    nome1 = aluno1.nome
    nome2 = aluno2.nome

    # get the sequential number for this letter
    snumber = letter_counter.get(letra, 0)

    # set id of fonte
    fs["id"] = f"lista-{letra}-{snumber:05}"

    # set obs of list from student names
    lis["obs"] = f"de {nome1.core}/{id1} até {nome2.core}/{id2}"

    if direct_import:
        if not testing:
            with Session() as session:
                fs["kleiofile"] = "direct_import:" + fs.id.core
                print("Starting to import into database", fs.id, datetime.now())
                PomSomMapper.store_KGroup(fs, session)
        else:
            print("Testing. Database import skipped")
    else:
        path = os.path.join(sources_dir, letra)
        filename = os.path.join(path, f"{fs.id.core}.cli")
        try:
            os.makedirs(path, exist_ok=True)
        except FileExistsError as error:
            # print(f'Error when creating directory at path {path}',error)
            pass
        if not testing:
            with open(filename, "w", encoding="utf-8") as cli:
                print("Starting to write to file ", filename, datetime.now())
                cli.write(kleio_group.to_kleio())
                print("Finish writing to file", datetime.now())
        else:
            print("Testing. would write to", filename)
            print(kleio_group.to_kleio()[0 : 64 * 1024])
            print("   ... (test, output truncated) ")  # we print just a few


def import_auc_alumni(
    csv_file: str,
    dest_dir: str = "",
    db_connection: str = None,
    max_rows_to_process=500,
    batch=0,
    testing=False,
    echo_row=False,
):

    with open(csv_file) as csvfile:
        direct_import = False
        db: TimelinkDatabase = None
        # ensure the directory exists otherwise sqlalchemy fails.
        if dest_dir > "":
            Path(dest_dir).mkdir(parents=True, exist_ok=True)
        if db_connection and db_connection > " ":
            direct_import = True
            db = TimelinkDatabase(db_url=db_connection)
            try:
                Session.configure(bind=db.get_engine())
            except Exception as e:
                raise ("Could not configure session", e)

        finish = False
        ncount = 0
        rcount = 0
        sources_dir = dest_dir
        show_SSR_atrs = False
        show_UI_atrs = False
        show_D_atrs = False

        kleio_file = None
        f = None
        l = None

        file_modified = time.gmtime(os.path.getmtime(csv_file))
        file_reference_date = time.strftime("%Y-%m-%d %H:%M", file_modified)
        # See https://docs.python.org/3/library/csv.html
        auc_ficheiro = csv.DictReader(csvfile, delimiter=";")
        Aluno.collect_errata(config.path_to_errata)
        for row in auc_ficheiro:
            rcount = rcount + 1
            description_level = row["DescriptionLevel"]

            if echo_row:
                print("-------------------------------")
                for k, v in row.items():
                    if v > "":
                        print(f"{k} = {v}")
            if description_level == "SSR":
                if kleio_file is not None:  # if more than one SSR we start new file
                    print("-- New SSR: writing current batch to file or database")
                    print("--      id:", kleio_file.id)
                    export_alumni_source(
                        sources_dir,
                        kleio_file,
                        testing=testing,
                        direct_import=direct_import,
                    )

                kleio_file = kleio(
                    "gacto2.str",
                    obs=f"Generated from Archeevo export file:  {csv_file} dated {file_reference_date}",
                )
                f = row_to_ksource(row, atrs=show_SSR_atrs)
                kleio_file.include(f)
                # we save clean copy to generate multiple files
                f_row = deepcopy(row)
            elif description_level == "UI":
                if l is not None:
                    print("-- NEW UI: writing current batch to file or database")
                    print("--  fonte:", f.id)
                    print("--  lista:", l.loc)
                    print("--  aluno:", aluno.nome)
                    export_alumni_source(
                        sources_dir,
                        kleio_file,
                        testing=testing,
                        direct_import=direct_import,
                    )
                    # start new kleio file
                    kleio_file = kleio("gacto2.str")
                    # we recover source info
                    f = row_to_ksource(f_row, atrs=show_UI_atrs)
                    kleio_file.include(f)
                l = row_to_klista(row, atrs=show_UI_atrs)
                f.include(l)
                l_bak = deepcopy(row)
            elif description_level == "D":
                aluno: n = row_to_n(row, atrs=show_D_atrs, direct_import=direct_import)

                if direct_import:
                    aluno.rel("function-in-act", "n", "", l.id, "")
                    if len(aluno.includes("referido")) > 0:
                        pai = aluno.includes("referido")[0]
                        pai.rel("function-in-act", "pai", "", l.id, "")
                    if len(aluno.includes("referida")) > 0:
                        mae = aluno.includes("referida")[0]
                        mae.rel("function-in-act", "mae", "", l.id, "")

                l.include(aluno)

                ncount = ncount + 1
                if ncount > batch:
                    print(
                        "-- Number of records per batch reached, new batch generated.",
                        batch,
                        f.id,
                        aluno.nome,
                    )
                    export_alumni_source(
                        sources_dir,
                        kleio_file,
                        testing=testing,
                        direct_import=direct_import,
                    )
                    kleio_file = kleio("gacto2.str")
                    # we recover source info
                    f = row_to_ksource(f_row, atrs=show_SSR_atrs)
                    # we avoid repeating the long obs
                    f.obs = KElement("obs", None, None, None)
                    kleio_file.include(f)
                    # we recover list information
                    l = row_to_klista(l_bak, file_reference_date, show_UI_atrs)
                    f.include(l)
                    ncount = 0  # we recount
            if max_rows_to_process > 0 and rcount >= max_rows_to_process:
                print("-- New batch: maximum number of processed rows reached")
                print("-- TERMINATING PROCESSING")
                print("--  fonte:", f.id)
                print("--  lista:", l.loc)
                print("--  aluno:", aluno.nome)
                export_alumni_source(
                    sources_dir,
                    kleio_file,
                    testing=testing,
                    direct_import=direct_import,
                )
                finish = True
                break
                # create_kleio_file_for_alumni('../sources/',kleio_file)
            else:
                if rcount % 100 == 0:
                    print("Rows processed:", rcount)

    if not finish:  # loop run out of rows, output remaining
        print("-- End of CSV File reached, last batch generated")
        print("--  fonte:", f.id)
        print("--  lista:", l.loc)
        print("--  aluno:", aluno.nome)
        export_alumni_source(
            sources_dir, kleio_file, testing=testing, direct_import=direct_import
        )
        return rcount
