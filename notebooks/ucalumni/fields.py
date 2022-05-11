""" Fields 
Code to process lines into fields
(c) Joaquim Carvalho 2021.
MIT License, no warranties.
"""
from os import linesep as nl

import difflib as dl
from pyparsing import ParseResults

from ucalumni.grammar import BIOLINE, preserve_original, DateUtility, scan_date
from ucalumni.aluno import Aluno


def break_lines_with_repetitions(original_lines: str):
    # some entries have multiple values separated by ";" and " e "
    # e.g. Provas de curso - Instituta 1.1.1563 até 31.07.1564; Código 1.02.1565 até 24.07.1565; Leis 15.06.1565 até 0.0.1566; 1.1.1566 até 31.05.1567; desde Fevereiro 1568 até 31.07.1568 e desde
    #    Setembro de 1568 até 24.06.1569; 8.12.1570 até 31.01.1571; 1.1.1571 até 1572
    # We break them in separate lines, preceded with # to indicate continuation

    new_lines = []
    for line in original_lines.splitlines():
        if len(line) == 0 or line[0] == '#':  # line is a comment, do not break
            new_lines.extend([line])
        else:
            repetitions = line.split(';')
            if len(repetitions) > 1:  # this was a line with repetitions
                i = 1
                for rep in repetitions:
                    for rep3 in rep.split(" e "):
                        new_lines.extend([rep3])
                        i = i + 1
            else:
                new_lines.extend(repetitions)

    return nl.join(new_lines)

def ignore_in_diff(line: str):
    """ Flag line as not relevant in diff

    Used with difflib for recording errata processing
    """
    if len(line.strip()) == 0:
        return True
    elif line.strip().startswith('#'):
        return True
    else:
        return False

def process_bioreg(aluno: Aluno) -> Aluno:
    """ Pre process the information in BioHist and ScopeContent

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
        aluno.scope_content = aluno.scope_content.replace(chr(29),' ')
    if "#29;" in aluno.scope_content:
        aluno.scope_content = aluno.scope_content.replace("#29;",' ')
    bioreg = aluno.bio_hist + nl + aluno.scope_content
    aluno.check_errata()
    if aluno.erratum is not None:
        # we make a note of the change
        original = [f'{line}\n' for line in bioreg.splitlines() if line.strip()>' ']
        changed = [f'{line}\n' for line in aluno.erratum.splitlines() if line.strip()>' ']
        diff_items = dl.unified_diff(original,
                              changed,
                              fromfile='original',
                              tofile='errata',
                              )
        aluno.erratum_diff = ''.join(diff_items)
        aluno.bio_hist = ''
        bioreg = aluno.erratum

    # we add the original information to aluno.obs
    if hasattr(aluno,"obs") and aluno.obs.startswith("# DB LOAD"):
        # if this record was loaded from db then it is ready
        aluno.obs = aluno.scope_content
    if aluno.erratum is not None:
        # if this record was changed by erratum, use the erratum and diff note
        aluno.obs = f'# Errata\n{aluno.erratum}\n'
    # if at this point there is no aluno.obs build one
    if aluno.obs is None or aluno.obs == '':
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
    except:
        aluno.unit_date_inicial = DateUtility('')
    try:
        aluno.unit_date_final = DateUtility(udf)
    except:
        aluno.unit_date_final = DateUtility('')

    section = ''
    line_is_just_date = False
    fname = ''
    fvalue = ''
    nbioreg = break_lines_with_repetitions(
        bioreg)  # we join again with new lines and '#'
    first_word_of_prev_line = ''
    BIOLINE.setParseAction(preserve_original)
    line_number = 0
    for line in nbioreg.splitlines():
        #if len(line.strip()) == 0:
        #    line = '# Empty line'
        if len(line.strip())> 0 and line.strip()[0] == '#':
            continue            # we treat lines starting with # as comments
        line_number = line_number + 1
        line_parsed = False
        # print('Line: ',line)
        r = BIOLINE.parseString(line)
        # print(r.dump())
        k = r.asDict().keys()
        if 'repeat' in k:  # Remove the repeat prefix
            line = r.original
            # we add attribute for later
            r.first_word_for_repeat = first_word_of_prev_line

        if 'pai' in k:
            npai = " ".join(r.pai)
            aluno.pai = npai
            # print(f'pn${npai}')
            if 'mae' in k:
                nmae = " ".join(r.mae)
                aluno.mae = nmae
                # print(f'mn${nmae}')

        # we can have 'section' and 'fname' in the same line
        # so we need to test for both separetly
        if 'section' in k:
            # print()
            # print('[Section] Section ', r['section'])
            section = r['section']
            # Note that we have a section followed by no field lines
            # we need to avoid the previous field to "continue" in
            # the new section, e.g.
            #   Faculdade:
            #   Matrícula(s):
            #   Cânones 1558.10.01 a 1559.05.31
             
            fname = ''   
            line_parsed = True


        if 'fname' in k:
            line_parsed = True
            previous_fname = fname  # save the last fname
            fname = r["fname"].strip()
            fvalue = r["fvalue"].strip()
           
            if len(fname.split()) > 3:
                # long field name, more than 3 words, probably error
                # 
                # we take the first word and push the line to value
                fvalue = fname + ": " + fvalue
                fname = fname.split()[0]

            if fname == 'Nome':
                aluno.nome = fvalue
            elif fname == 'Data inicial':
                try:
                    aluno.unit_date_inicial = DateUtility(fvalue)
                except:
                    aluno.unit_date_inicial = DateUtility('')
            elif fname == 'Data final:':
                try:
                    aluno.unit_date_final = DateUtility(fvalue)
                except:
                    aluno.unit_date_final = DateUtility('')
            elif fname == 'idem':
                fname = previous_fname

            if "matrícula" in fname.lower() or "matricula" in fname.lower():
                section = "Matrículas"

            if "exames" in fname.lower():
                section = "Exames"

            fname, fvalue, line_is_just_date = process_field(r,
                                                             section,
                                                             fname,
                                                             fvalue,
                                                             aluno)
            if 'idem' in k:  # line contain another value
                fvalue = r["idem"]
                fname, fvalue, line_is_just_date = process_field(r,
                                                                 section,
                                                                 fname,
                                                                 fvalue,
                                                                 aluno)

        # line contains only a date, we repeat the last field
        elif 'day' in k or 'day1' in k:
            line_parsed = True
            du = DateUtility(r)
            fvalue = du.original
            fname, fvalue, line_is_just_date = process_field(r,
                                                             section,
                                                             fname,
                                                             fvalue,
                                                             aluno)
            # du = date_utility(r)
            # print(f'[date]    {section} >> {fname}: {du} %{du.original}')
            # if line_is_just_date:
            # print(f'ls${fname}/{normal_date}%{original_date}/data={normal_date}')
            #   person.include(ls(fname,(du.value,None,du.original),data=du.short))
            # else:
            # print( f'ls${fname}/{fvalue}/data={normal_date}')
            #  person.include(ls(fname,du.original,data=du.short))
        elif 'blank' in k:
            line_parsed = True
            section = ''
            fname = ''
        elif 'nomatch' in k:  # no match
            if not fname > '':
                fname = '*no-field-line*'
            fvalue = line.strip()
            fname, fvalue, line_is_just_date = \
                process_field(r,
                                section,
                                fname,
                                fvalue,
                                aluno)
            line_parsed = True

        if not line_is_just_date:  # save the first word for repeating values
            if len(fvalue.split()) > 0:
                first_word_of_prev_line = fvalue.split()[0]
    # finished processing lines, extract information
    aluno.extract()
    return aluno


def process_field(pr: ParseResults, section: str, fname: str, fvalue: str,
        aluno: Aluno):
    """ Processes section, field and value. Adds information to `Aluno`.

    :param pr: `parseResults`  of the current line
    :param section: field name (normally from tokens)
    :param fname: field value (normally from tokens)
    :param fvalue: name of section, if one was detected before
    :param aluno: current student record
    :type aluno: class: ucalumni.importer.Aluno
    :return: fname,fvalue, fvalue_is_date (True if fvalue is a date_expression)

    Extracts date if present in field value, for Notes.
    Can change fname and fvalue according to context and specific rules.
    If fvalue is a date or date range then it is replaced by a normalized
    date and fvalue_is_date flag is returned
    """

    obs = ''
    
    default_date = aluno.unit_date_inicial

    k = pr.asDict().keys()
    
    if 'provas' in k:
        fname = 'provas'
        
    
    fvalue_is_date = False

    if fvalue > '':
        ls_date = default_date
        fvalue_is_date = False
        any_date_found = False
        # Check is field value contains an usable date
        d = scan_date(fvalue)
        if d is not None:
            ls_date = d
            if d.date_only:
                if 'repeat' in k:
                    fvalue = pr.first_word_for_repeat + ' ' + d.original
                    fvalue_is_date = False
                else:
                    fvalue_is_date = True
                    fvalue = d.value
                    obs = d.original_date
            any_date_found = True

        if section == '':
            sname = '*nosection*'
        else:
            sname = section
        fname_inferred = 'nomatch' in k
        aluno.add_nota(sname.strip(), 
                        fname.strip(), 
                        fvalue, 
                        ls_date, 
                        obs,
                        fname_inferred=fname_inferred,
                        fvalue_is_date=fvalue_is_date)

        if any_date_found:
            pass
    else:
        pass
    return fname, fvalue, fvalue_is_date
