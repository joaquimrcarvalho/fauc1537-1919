"""
:mod: `groups` -- Groups used for UC alumni processing
======================================================

.. module: groups
kleio
    Top level group for the file
fonte
    Portuguese Historical Source
list
    List of alumni in the file
auc
    The AUC original record, takes atr$ for individual values
n
    The alumnus / alumna
referido
    Father of the alumuns/alumna
referido
    Mother of the alumnus/alumna
ls,atr
    Attributes and life story (from KAtr)
    Attributes and life story (from KAtr)

.. moduleauthor: Joaquim Carvalho 2021.

MIT License, no warranties.
"""
from timelink.kleio.groups import KDate, KDay, KMonth,KYear, KType, KReplace, KName 
from timelink.kleio.groups import  KKleio, KSource, KAct, \
    KAbstraction, KPerson, KSex
from timelink.kleio.groups.kls import KLs
from timelink.kleio.groups.krelation import KRelation
from timelink.kleio.groups.katr import KAtr



KData = KDate.extend('data')
KAno = KYear.extend('ano')
KMes = KMonth.extend('mes')
KDia = KDay.extend('dia')
KSubstitui = KReplace.extend('substitui')
KThetype = KType('the_type')
KTipo = KThetype.extend('tipo')
KNome = KName.extend('nome')
KSexo = KSex.extend('sexo')


#/Users/jrc/develop/timelink-py/timelink/kleio/groups.py:1129: UserWarning: Created a KElement class for loc. Better to create explicit or provide  synonyms= in group creation.
#  warnings.warn(f"Created a KElement class for {arg}. "
#/Users/jrc/develop/timelink-py/timelink/kleio/groups.py:1129: UserWarning: Created a KElement class for ref. Better to create explicit or provide  synonyms= in group creation.
#  warnings.warn(f"Created a KElement class for {arg}. "
#/Users/jrc/develop/timelink-py/timelink/kleio/groups.py:1129: UserWarning: Created a KElement class for value. Better to create explicit or provide  synonyms= in group creation.
#  warnings.warn(f"Created a KElement class for {arg}. "
#/Users/jrc/develop/timelink-py/timelink/kleio/groups.py:1129: UserWarning: Created a KElement class for destname. Better to create explicit or provide  synonyms= in group creation.
#  warnings.warn(f"Created a KElement class for {arg}. "
#/Users/jrc/develop/timelink-py/timelink/kleio/groups.py:1129: UserWarning: Created a KElement class for destination. Better to create explicit or provide  synonyms= in group creation.


kleio = KKleio
fonte = KSource.extend(
    'fonte', also=['tipo', 'data', 'ano', 'substitui', 'loc', 
                    'ref', 'obs','kleiofile'])
lista = KAct.extend('lista', position=['id', 'dia', 'mes', 'ano'], guaranteed=[
    'id', 'ano', 'mes', 'dia'], also=['data', 'tipo', 'loc', 'obs'])
auc = KAbstraction.extend('auc', position=['name', ''], also=[
    'level', 'id'], guaranteed=['id'])
n = KPerson.extend('n', position=['nome', 'sexo'], guaranteed=[
    'id', 'nome', 'sexo'], also=['mesmo_que', 'obs'])
referido = KPerson.extend('referido', position=['nome','sexo'], guaranteed=[
    'id', 'nome'], also=['mesmo_que',  'obs'])
referida = KPerson.extend('referida', position=['nome','sexo'], guaranteed=[
    'id', 'nome'], also=['mesmo_que', 'obs'])
ls = KLs.extend('ls', position=['type', 'value', 'data'], also=['data', 'obs','entity'])
atr = KAtr.extend(
    'atr', position=['type', 'value', 'data'], also=['data', 'obs','entity'])
rel = KRelation.extend('rel', position=['type', 'value','destname','destination'],
            also=['origin','data'] )
n.allow_as_part(referido)
n.allow_as_part(referida)
