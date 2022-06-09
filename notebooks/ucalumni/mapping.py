"""

Contains the functions that map the Aluno information into Kleio
groups (n,ls,pai,mae)

(c) Joaquim Carvalho 2021.
MIT License, no warranties.
"""
import datetime
import re
from typing import List

from ucalumni.groups import n, atr, ls, referido, referida, rel
from ucalumni.aluno import Aluno
from ucalumni.grammar import DateUtility

# regiter for mapper functions
Aluno.mappers = []


def list_search(lista: List, texto:str):
    """
    Returns list of matches of members of list in text

    >> re.findall('(frei|padre|abade)',"o frei abade de sinfães, padre João")
    >> ['frei', 'abade', 'padre']
    """
    # we ensure that longer matches come first
    lista_sorted = reversed(sorted(lista,key=len))
    regex = '('+'|'.join(lista_sorted)+')'
    return re.findall(regex,texto)


def map_aluno_kperson(aluno: Aluno) -> n:
    """
    Maps the information collected about the student into
    a kleio structure

    This is called by row_to_n

    :param aluno: a "Aluno" record after extractors did their job
    :return: a Kleio group representing the information in Aluno

    """
    p = n(aluno.nome, aluno.sexo, id=aluno.id,
          obs=aluno.obs)
    # fill in the metadata from the catalog record
    p.include(atr('código-de-referência', aluno.codref,data=aluno.get_record_date()))
    p.include(atr('data-do-registo', aluno.get_record_date(),data=aluno.get_record_date()))
    # p.include(atr('user_name', aluno.user_name,data=aluno.get_record_date()))
    # p.include(atr('creator', aluno.creator,data=aluno.get_record_date()))
    p.include(atr('url', aluno.url,data=aluno.get_record_date()))



    p.include(ls('uc-entrada', aluno.unit_date_inicial.value,
                 data=aluno.unit_date_inicial.value))
    p.include(ls('uc-saida', aluno.unit_date_final.value,
                 data=aluno.unit_date_final.value))
    ano_inicial, _mes, _dia = aluno.unit_date_inicial.date
    ano_final, _mes, _dia = aluno.unit_date_final.date
    if ano_inicial != '0000':
        p.include(ls('uc-entrada.ano', ano_inicial, data=aluno.unit_date_inicial.value))
    if ano_final != '0000':
        p.include(ls('uc-saida.ano', ano_final, data=aluno.unit_date_final.value))
    if aluno.erratum_diff is not None:
        p.include(atr('errata','diff',data=datetime.datetime.today().strftime('%Y-%m-%d'),obs=aluno.erratum_diff))
    try:
        for mapper in Aluno.mappers:
            mapper(aluno, p)
    except Exception as e:
        print(f"problem during mapping ({mapper.__name_}) of {aluno.id} {aluno.nome}")
        print(str(e))
        p.include(ls('*erro*', mapper.__name__,
                     data=datetime.date.today().strftime("%Y/%m/%d"),
                     obs=str(e)))

    return p


def mapper_nomes_notes(aluno: Aluno, p: n):
    ano = aluno.unit_date_inicial.date.year
    ## check information that was appended to the name between parentesis
    if getattr(aluno, 'nota', None) is not None:
        nota_ao_nome = aluno.nota
        lsn = ls('nome-nota',
                 nota_ao_nome.strip(),
                 aluno.unit_date_inicial.value)
        p.include(lsn)
        titulos = "d\\.,frei,padre,abade,arcediago,barão,"\
        "beneficiado,bispo,capelão,chantre,cónego,"\
        "lente , lente,marquês,monge,porcionista,presbítero,"\
        "visconde"
        titulos_lista = titulos.split(",")
        hits = list_search(titulos_lista,nota_ao_nome.lower())
        for titulo in hits:
            if "D." in titulo:
                p.include(ls('titulo', 'dom', aluno.unit_date_inicial.value),)
            elif titulo == 'padre':
                p.include(ls('padre', 'sim', aluno.unit_date_inicial.value,obs=nota_ao_nome))
            else:
                p.include(ls('titulo', titulo.strip(), aluno.unit_date_inicial.value,obs=nota_ao_nome))
        ## this assumes colegio extractor was run
        if hasattr(aluno,'colegio') and getattr(aluno, 'colegio', None) is not None :
            p.include(ls('colegio', aluno.colegio, aluno.unit_date_inicial.value,obs=nota_ao_nome))
        if hasattr(aluno,'colegial') and getattr(aluno, 'colegial', None) is not None :
            p.include(ls('colegial', aluno.colegial, aluno.unit_date_inicial.value,obs=nota_ao_nome))
        ## this assume ordem extractor was run
        if hasattr(aluno,'ordem') and getattr(aluno, 'ordem', None) is not None :
            for ordem in aluno.ordem:
                p.include(ls('ordem-religiosa', ordem, aluno.unit_date_inicial.value,obs=nota_ao_nome))


    if getattr(aluno, 'vide', None) is not None:
        p.include(ls('nome-vide', aluno.vide, aluno.unit_date_inicial.value))
        if aluno.vide_target is not None:
            p.include(ls('nome', aluno.vide_target, aluno.unit_date_inicial.value,obs=f"{aluno.nome}, vide {aluno.vide}"))
           
    p.include(ls('nome', aluno.nome, aluno.unit_date_inicial.value))
    # p.include(ls('nome.ano', ano+'.'+aluno.nome, aluno.unit_date_inicial.value))
    p.include(ls('nome-primeiro', aluno.pnome, aluno.unit_date_inicial.value))
    # p.include(ls('nome.primeiro.ano', ano+'.'+aluno.pnome, aluno.unit_date_inicial.value))
    apelidos = aluno.nome.split()[1:]
    particles = ['de','do','da','dos','das','e']
    for i in range(len(apelidos)):
        if apelidos[i] not in particles:
            p.include(ls('nome-apelido', " ".join(apelidos[i:]), aluno.unit_date_inicial.value))
    # p.include(ls('nome.apelido.ano', ano+'.'+aluno.apelido, aluno.unit_date_inicial.value))

    id_pai = None
    if getattr(aluno, 'pai', None) is not None:
        relation = "filho" if aluno.sexo == 'm' else "filha"
        id=aluno.id+'-pai'
        id_pai = id
        p.include(referido(aluno.pai, 'm',id=id))
        p.include(rel("parentesco",relation, aluno.pai,id,data=aluno.unit_date_inicial.value))
        p.include(ls('nome-pai',aluno.pai, data=aluno.unit_date_inicial.value))
    if getattr(aluno, 'mae', None) is not None:
        id=aluno.id+'-mae'
        mae = referida(aluno.mae,'f', id=id)
        p.include(mae)
        p.include(rel("parentesco",relation,aluno.mae,id,data=aluno.unit_date_inicial.value))
        mae.include(rel("parentesco", 'mulher', aluno.pai, id_pai,data=aluno.unit_date_inicial.value))
        p.include(ls('nome-mae',aluno.mae, data=aluno.unit_date_inicial.value))

Aluno.mappers.append(mapper_nomes_notes)



def mapper_naturalidade(aluno: Aluno, p: n):
    if getattr(aluno, 'naturalidade', None) is not None:
        ano, _mes, _dia = aluno.unit_date_inicial.date

        nat = aluno.naturalidade.replace("/",",")
        nat = nat.replace(".","")
        nat = nat.replace(" - ",",")
        # Sometimes geografical context is between parentesis
        if len(nat) > 0 and nat[0] == '(':
            nat = nat.replace("(","")
            nat = nat.replace(")",",")
        if len(nat) > 0 and nat[-1] == ')':
            nat = nat.replace("(",",")
            nat = nat.replace(")","")
        nat = nat.strip(" ?,")
        partes = nat.split(",")
        nat_better = ", ".join([p.strip() for p in partes])
        if len(partes) > 0:
            if len(partes)>1:
                obs = aluno.naturalidade
            else:
                obs = None
            for loc in partes:
                if loc > ' ':
                    loc = loc.strip(" ?")
                    # strip "hoje"
                    loc = loc[loc.startswith("hoje") and len("hoje"):]
                    p.include(ls('nome-geografico',
                                 loc,
                                 aluno.unit_date_inicial.value,
                                 obs=obs))
                    if ano != '0000':
                        p.include(ls('nome-geografico.ano',
                                    loc + '.' + ano,
                                    aluno.unit_date_inicial.value,
                                    obs=obs))
        obs=None
        if nat_better != aluno.naturalidade.strip():
            obs = f"{aluno.naturalidade}"
            aluno.naturalidade=nat_better

        lsn = ls('naturalidade',
                 aluno.naturalidade.strip(),
                 aluno.unit_date_inicial.value,
                 obs=obs)
        p.include(lsn)
        lsfa = ls('naturalidade.ano', aluno.naturalidade.strip() + '.' + ano,
                  aluno.unit_date_inicial.value)
        p.include(lsfa)


Aluno.mappers.append(mapper_naturalidade)


def map_faculdade(aluno: Aluno, p: n):
    for faculdade, data, obs in aluno.faculdade:
        lsf = ls('faculdade', faculdade.strip(), data.value, obs=obs)
        p.include(lsf)
        if data.is_range:
            ano, _mes, _dia, _ano2, _mes2, _dia2 = data.date
        else:
            ano, _mes, _dia = data.date
        lsfa = ls('faculdade.ano', faculdade.strip() + '.' + ano, data.value,
                  obs=obs)
        p.include(lsfa)
    if aluno.faculdade_original is not None and aluno.faculdade_original > '':
        lsfo = ls('faculdade-original',aluno.faculdade_original.strip(), aluno.unit_date_inicial)
    problem = aluno.faculdade_problem
    problem_obs = aluno.faculdade_problem_obs
    if problem is not None and problem > '':
        today = DateUtility(datetime.datetime.today().strftime('%Y-%m-%d'))
        lsp = atr('nota-processamento', problem, today, obs=problem_obs)
        p.include(lsp)
        if aluno.faculdade_original is not None and aluno.faculdade_original > '':
            lsfo = ls('faculdade-original',aluno.faculdade_original.strip(), aluno.unit_date_inicial)
            p.include(lsfo)
        if aluno.faculdade_strange is not None and aluno.faculdade_strange > '':
            lsfstr = ls('nota-processamento','Faculdade corrigida, combinação incomum', today,obs=aluno.faculdade_strange)
            p.include(lsfstr)           


Aluno.mappers.append(map_faculdade)


def map_matriculas(aluno: Aluno, p: n):
    for matricula in aluno.matriculas:
        the_type = f'matricula-{matricula.tipo}'
        lsm = ls(the_type, matricula.ambito.strip(),
                 matricula.data.value,
                 obs=matricula.obs)
        p.include(lsm)
        if matricula.data.is_range:
            ano, _mes, _dia, _ano2, _mes2, _dia2 = matricula.data.date
        else:
            ano, _mes, _dia = matricula.data.date
        lsm2 = ls(the_type+'.ano', matricula.ambito.strip() + '.' + ano,
                  matricula.data.value,
                  obs=matricula.obs)
        p.include(lsm2)
        if matricula.modalidade > '': # obrigado, ordinário, voluntário
            lsm3 = ls(f'{the_type}.{matricula.modalidade}', f'{matricula.ambito.strip()}',
            matricula.data.value,
            obs=matricula.obs)
            p.include(lsm3)
            lsm4 = ls(f'{the_type}.{matricula.modalidade}'+'.ano', matricula.ambito.strip() + '.' + ano,
            matricula.data.value,
            obs=matricula.obs)  
            p.include(lsm4)         


Aluno.mappers.append(map_matriculas)


def map_graus(aluno: Aluno, p: n):
    for grau in aluno.graus:
        lsg = ls('grau', grau.nome.strip(), grau.data.value, obs=grau.obs)
        p.include(lsg)
        if grau.data.is_range:
            ano, _mes, _dia, _ano2, _mes2, _dia2 = grau.data.date
        else:
            ano, _mes, _dia = grau.data.date
        lsm2 = ls('grau.ano', grau.nome.strip() + '.' + ano,
                  grau.data,
                  obs=grau.obs)
        p.include(lsm2)


Aluno.mappers.append(map_graus)


def map_exames(aluno: Aluno, p: n):
    for exame in aluno.exames:
        lse = ls('exame', exame.ambito, exame.data.value, obs=exame.resultado+" "+exame.obs)
        p.include(lse)


Aluno.mappers.append(map_exames)

def map_instituta(aluno: Aluno, p: n):
    for instituta in aluno.instituta:
        lsm = ls('instituta',instituta.data.value,
                 instituta.data,
                 obs=instituta.obs)
        p.include(lsm)
        if instituta.data.is_range:
            ano, _mes, _dia, _ano2, _mes2, _dia2 = instituta.data.date
        else:
            ano, _mes, _dia = instituta.data.date
        lsm2 = ls('instituta.ano', ano,
                  instituta.data,
                  obs=instituta.obs)
        p.include(lsm2)


Aluno.mappers.append(map_instituta)