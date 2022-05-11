"""
:module: ucalumni

Support code for analysis of the University of Coimbra alumni database.

:Contains:
    Generation of kleio source files from Archeevo export data
    Grammars for parsing text fields in the original catalog (BioNote,ScopeContent)
    Data massaging support for analysis of import process
    Examples of using the database for analysis of: student population, faculties, cohorts,
    geographic origin, institucional relations

(c) Joaquim Carvalho, MIT LICENSE

"""

from ucalumni.importer import import_auc_alumni