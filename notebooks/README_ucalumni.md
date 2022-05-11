**[EN]** 
# UC Alumni: processing the alumni records at the Arquivo da Universidade de Coimbra

    > This file only exists in English

## Scope

This directory contains Jupyter notebooks that can process information from the
online catalog of alumni of the University of Coimbra and extract data in
a format suitable for statistical, prosopographical and network analysis.


The alumni records at the Arquivo da Universidade de Coimbra consist of over 100,000 records, 
from 1537 to 1913. 

A catalog is available at http://pesquisa.auc.uc.pt/details?id=264605. It includes a description of how the information was collected (in Portuguese). A more complete guide for researchers, by Ana Maria Bandeira, is available online: https://www.uc.pt/auc/orientacoes/UC_GuiaPercursoAcademico.pdf


The catalog packs most of the relevant information about each student in a 
couple of texts fields. 

To be useful the information needs to be mapped into a structured database.
We use the `Timelink` data model to create a database which allows for 
many interesting analysis of the alumni information. 

This document gives an overview of the format of the alumni records in the 
original online catalog and the process of conversion to `Timelink` format. 


## The online catalog

The online catalog transcribes the content of the card records, which were produced
between 1940 a 1950. The online catalog is managed by the `archeevo` 
software (https://www.keep.pt/en/produts/archeevo-archival-management-software/). 
An export of the contents of catalog in `csv` format was done in February 2020,
and a new one in February 2022.

The information follows the ISAD(G) model. The catalog corresponds to a "Sub-series" (ISAD level: SSR). The Sub-series is divided in "units of installation" corresponding to the letters A to Z (level: UI). Each unit of installation contains the students whose last name starts with the corresponding letter, in alphabetical order of last name.

The export file contains a first row with the SSR record, one row for each letter of the alphabet (no entry for "Y"), and a row for each student.

## The export format

The rows corresponding to student information contain the following relevant columns 
(additional columns, not shown bellow, contain control information ):

        -------------------------------
        ID = 140339
        DescriptionLevel = D
        CompleteUnitId = PT/AUC/ELU/UC-AUC/B/001-001/A/000003
        UnitId = 000003
        RepositoryCode = AUC
        CountryCode = PT
        UnitTitle = Jerónimo Rodrigues Abegão
        UnitDateInitial = 1732-10-01
        UnitDateFinal = 1746-06-15
        UnitDateInitialCertainty = True
        UnitDateFinalCertainty = True
        AllowUnitDatesInference = False
        AllowExtentsInference = False
        Repository = Arquivo da Universidade de Coimbra
        Producer = Universidade de Coimbra
        BiogHist = Filiação: Jerónimo Rodrigues Abegão
        Naturalidade: Portalegre
        ScopeContent = Faculdade: Cânones

        Matrícula(s): 01.10.1733
        01.10.1734
        01.10.1735
        01.10.1736
        01.10.1737
        01.10.1738
        01.10.1741
        01.10.1745
        Instituta: 01.10.1732
        Bacharel: 12.04.1742, Atos e Graus 80, fl. 104 v.
        Formatura: 15.06.1746

        Outras informações: Tirou as cartas com o nome Jerónimo de Faria Vidal, Atos e Graus 80, fl. 104 v.

For analytical purposes the relevant fields are 
* UnitTitle = Name of student, which can contain a note on status (priest, college of residence, etc...) and a " vide " note, which is a cross reference to another record, sometimes circular (for instance: 127765, 211625).
* UnitDateInitial = first date on the record
* UnitDateFinal = last date on the record
* BiogHist = contains place of birth ("naturalidade") and can include parents names (mostly father name).
* ScopeContent = contains the academic record, with different types of information in semi structured way, such as  "Faculdade", "Matrícula(s))", "Exames", information on degrees and a generic "Outras Informações". 

Extracting structured information from "ScopeContent" is the main challenge of processing the catalog. 

Names of students and "BioHist" are comparatively simple to handle, even if the 
notes to the names included between parenthesis require some processing.

The field "ScopeContent" has many variations in structure and the same type of information is
recorded in different styles.

The rest of this document details how the information is processed. 

## The target data model

In order to generate a usable representation of the catalog it is necessary to map the information
in the catalog to fields in a database. 

We use the database structure defined by `Timelink` in which each person is represented by a 
variable set of _attributes_ and _relations_. 

`Timelink`  _attributes_ will store the 
academic information while _relations_ store the family relations are recorded in `BioHist` field.


This is done through the intermediate step of generating text files in `kleio` notation. \
The `kleio` files are then imported into a `timelink` database.

A direct import to the `timelink` database is also possible, skipping the generation of data
files,

See
* [How to process an export file from the original catalog](000-convert-catalog.ipynb)


## Names

We extract the first name and family name. For the family name we generate entries for the various combinations.

    nome : Amadeu Aarão Pereira Pinto dos Santos
    nome.primeiro : Amadeu
    nome.apelido : Aarão Pereira Pinto dos Santos
    nome.apelido : Pereira Pinto dos Santos
    nome.apelido : Pinto dos Santos
    nome.apelido : Santos

## Names notes

Student names can have annotations in the name itself, between parentesis:

* D. (dom),  prefix for noble people, also "Barão", "Visconte", "Marquês"
* Padre = Priest
* Frei  = Friar, normally followed by the name of the Order, with many variations
* Colegial ou Colégio = The college of the student, followed by the name of the college.
* Lente = Lecturer
* various professions: impressor, ourives, "mestre" 

The text between parentesis is added as the attribute "nota", with 9975 occurences so far.

Most frequence notes are:


| Note                                            | Count |
:-----------------------------------------------: | :--------------: |
| padre                                           |            5810 |
| D.                                              |             639 |
| padre frei religioso de Nossa Senhora do Carmo  |              97 |
| padre frei religioso de São Bernardo            |              94 |
| frei monge de São Bento                         |              90 |
| padre frei religioso de Nossa Senhora da Graça  |              85 |
| frei                                            |              78 |
| frei monge de São Bernardo                      |              78 |
| padre frei religioso de São Bento               |              68 |
| frei religioso de São Bento                     |              67 |
| frei religioso de São Bernardo                  |              66 |
| frei religioso de Nossa Senhora da Graça        |              56 |
| frei religioso da Ordem de Cristo               |              56 |
| padre frei religioso de São Domingos            |              53 |
| frei religioso de São Domingos                  |              50 |


## Attributes derived from name notes

From the information in name notes the following information is extacted:

### Colégio

If the name note contains "colégio", "colegio" or "colegial" the name of the 
college is extracted as follows:

* Non relevant words and ponctuation are removed from the note: 
        * padre reitor padres frei monge eremita d. religioso colegial porcionista familiar da de do dos das
* "São" is replaced by "S."
* The resulting expression is scanned for a match is predefined college names:


            if "Graça" in colegio:
                colegio = "Colégio Graça"
            elif "Pedro" in colegio:
                colegio = "Colégio S.Pedro"
            elif "João" in colegio or "Evangelista" in colegio or "Lóios" in colegio:
                colegio = "Colégio S.João Evangelista"
            elif "Trindade" in colegio:
                colegio = "Colégio Trindade"
            elif "Boaventura" in colegio:
                colegio = "Colégio S.Boaventura"
            elif "Paulo" in colegio:
                colegio = "Colégio S.Paulo"
            elif "Militar" in colegio:
                colegio = "Colégio Ordens Militares"
            elif "Rita" in colegio:
                colegio = "Colégio Santa Rita"
            elif "Bernard" in colegio:
                colegio = "Colégio S.Bernardo"
            aluno.colegio = colegio

Note that if no match is found the original note minus irrelevant words and ponctuation is used.
 
 A total of 275 references to "colégio" were collected:



| Colégio                      | Count               |
| :--------------------------: | :-----------------: |
| Colégio Ordens Militares     |                  88 |
| Colégio S.Pedro              |                  55 |
| Colégio S.Paulo              |                  51 |
| Colégio Graça                |                  25 |
| Colégio S.João Evangelista   |                  15 |
| colégio Jesus                |                  10 |
| colégio Carmo                |                   5 |
| Colégio S.Bernardo           |                   4 |
| colégio S.Tomás              |                   3 |
| Colégio Real                 |                   3 |
| colégio S.Bento              |                   3 |
| colégio S.Tomar              |                   2 |
| Colégio Trindade             |                   2 |
| militares                    |                   2 |
| Colégio Santa Rita           |                   2 |
| colégio Cristo               |                   1 |
| colégio Loios                |                   1 |
| colégio Ciências Naturais    |                   1 |
| Colégio S.Boaventura         |                   1 |
| colégio S. pedro             |                   1 |

### Ordem Religiosa

A dictionary of patterns is used. If more than one match occurs the longest match is kept.

To see the current list of patterns check `notebooks/ordem_religiosa_clean.ipynb`.

**São Domingos (Dominicanos)**

We have taken the reference to "São Tomás" as meaning "Colégio de S.Tomás", which was the Dominican college at Coimbra from 1543.
So the note " (frei religioso de São Tomás)" is interpreted as indicating a member of the order of São Domingos. This is clear in the case of https://pesquisa.auc.uc.pt/details?id=242679 where a double note appears: "Jerónimo Mesquita (padre frei de São Tomas) (São Domingos)"


**Santo Agostinho**

The expression "agostinho" is particularly difficult because there are several different branches:

* Cónegos regrantes de Santo Agostinho (Santa Cruz monastery)
* Ordem dos Agostinhos de Nossa Senhora da Graça (Colégio da Graça)
* Ordem dos Agostinho descalços (Colégio de Santa Rita)

See Azevedo, C.A.M. (2011) Ordem dos Eremitas de Santo Agostinho em Portugal: 1256-1834. Lisboa: Centro de Estudos de História Religiosa (História religiosa, 8).

See also the following note in record [217564](https://pesquisa.auc.uc.pt/details?id=217564)

> Outras informações: Conforme os Atos é referido como: Frei Domingos de Santo Agostinho, Frei Domingos Eremita de Santo Agostinho ou Frei Domingos do Colégio da Graça. Foi feita a interpretação como sendo o mesmo.


## Remissions 



## "Naturalidade" (place of birth)



## "Filiação"   



## Dates



## Informations prefixed with field names

Most information in the notes is tagged in the format "FIELD:VALUE" 

e.g.  

    Faculdade: Cânones
    Matrícula(s): 15.10.1661
    Instituta: 10.10.1660
    Naturalidade: Castelo de Vide

But in some cases the expression before ":" can be long and introduce unnecessary variability:

        Provou ter o tempo necessário para Bacharel em Artes: 10.02.1550

Another pattern introduces a two level structure where the form "HEADER:" precedes a series of lines in "FIELD:VALUE" format:

        Exames: 8ª cadeira: 8.07.1912, Aprovado com 14 valores, Atos n.º 28, fl. 10v.
            9ª cadeira: 22.07.1913, Aprovado com 13 valores, Atos n.º 29, fl. 63
            10ª cadeira: 14.08.1912, Aprovado com 13 valores, Atos n.º 28, fl. 150 v.
            11ª cadeira: 24.06.1912, Aprovado com 14 valores, Atos n.º 28, fl. 195 v.
            16ª cadeira: 28.1.1914, Aprovado com 12 valores, Atos n.º 42, fl. 37 v.
            17ª cadeira: 17.07.1912, Aprovado com 13 valores, Atos n.º 41, fl. 105
            18ª cadeira: 9.07.1913, Aprovado com 14 valores, Atos n.º 42, fl. 131
            19ª cadeira: 9.1.1913, Reprovado, Atos n.º 42, fl. 204 v., idem: 31.1.1914, Atos n.º 42, fl. 22


Sometimes we get an extra label in the same line:

        4º e Grau de Bacharel: 03.07.1888, Reprovado, Atos n.º 29, fl. 134, idem: 12.07.1889, Aprovado Simpliciter, Atos n.º 30, fl. 94 v.
        
Note the `idem` which means repeating the previous field, in this case: "4º e Grau de Bacharel".

## Handling variations and inconsistencies in field names

To handle the variation in the notation the following rules are used:

**Rule #1 Field names are signaled by ":" or " - "**

Field names are inferred from "field:value" or "field - value". The value part is the 
sequence after ":" or " - " until the end of the line (except when subsequent rules apply).

**Rule #2 Lines with more than one field name denote sections**

        Exames: 8ª cadeira: 8.07.1912, Aprovado com 14 valores, Atos n.º 28, fl. 10v.

"Exames" is considered a section header and "8ª cadeira" the field name

**Rule #3: Lines with just a field name are considered section header**

            Outras informações:
            Provas de curso: 1.1.1573 até 28.07.1574
            1.1.1574 até 17.05.1575
            1.1.1575 até 1576
            1.1.1577 até 18.05.1578
            1.1.1578 até 13.02.1579
            1ª Tentativa: 10.01.1578
            1º Princípio: 15.1.1579
            2º Princípio: 17.1.1579
            4º Princípio: 1.12.1579

"Outras informações" is considered the section header. 

**Rule #4: A line with no field is considered a new value for the last detected field**

        Código e Leis: 01.10.1567 até 31.05.1568
        01.10.1568 até 30.04.1569
        15.10.1570 até 30.04.1571

Example

           Id: 140714
            Id: 205781
            Código de referência: PT/AUC/ELU/UC-AUC/B/001-001/P/000051

            Nome        : Antonio Luís da Costa Pacheco
            Data inicial: 1767-10-01
            Data final  : 1772-10-00
            Filiação:
            Naturalidade: Coimbra
            Faculdade: Medicina

            Matrícula(s): 01.10.1767
            01.10.1768
            01.10.1769
            01.10.1770
            10.12.1772
            2º ano 10.1772
            Matemática, 04.11.1774 (obrigado)
            Cânones 01.10.1766
            01.10.1765
            01.10.1764

            Instituta: 01.10.1769

            Bacharel em artes 16.06.1768
            Licenciado 17.06.1768
            1ª Tentativa 14.05.1771
            2ª 25.05.1771, Atos n.º 105, fl. 144


Is processed as


id:127987 António Cabral 1665-10-15 : 1666-10-10

|N   |section      |campo                 |data        |valor                                            |obs                                              |
|----|-------------|----------------------|------------|-------------------------------------------------|-------------------------------------------------|
|1   |*nosection*  |Id                    |1279-00-00  |127987                                           |                                                 |
|2   |*nosection*  |Código de referência  |0000-00-00  |PT/AUC/ELU/UC-AUC/B/001-001/C/000067             |                                                 |
|3   |*nosection*  |Nome                  |1665-10-15  |António Cabral (frei religioso de São Bernardo)  |                                                 |
|4   |*nosection*  |Data inicial          |1665-10-15  |1665-10-15                                       |1665-10-15                                       |
|5   |*nosection*  |Data final            |1666-10-10  |1666-10-10                                       |1666-10-10                                       |
|6   |*nosection*  |Faculdade             |1665-10-15  |Teologia                                         |                                                 |
|7   |Matrículas   |Matrícula(s)          |1665-10-15  |1665-10-15                                       |15.10.1665                                       |
|8   |Matrículas   |Matrícula(s)          |1666-10-01  |01.10.1666 (ordinário)                           |                                                 |
|9   |*nosection*  |Provas                |1669-01-28  |1669-01-28                                       |28.01.1669                                       |
|10  |*nosection*  |Provas                |1669-01-30  |1669-01-30                                       |30.01.1669                                       |
|11  |*nosection*  |Provas                |1669-02-06  |1669-02-06                                       |06.02.1669                                       |
|12  |*nosection*  |Formatura             |1669-02-15  |1669-02-15                                       |15.02.1669                                       |
|13  |*nosection*  |Formatura             |1669-02-15  |1669-02-15                                       |15.02.1669                                       |
|14  |*nosection*  |Augustiniana          |1669-07-05  |1669-07-05                                       |05.07.1669                                       |
|15  |*nosection*  |Quodlibetus           |1669-01-22  |1669-01-22                                       |22.01.1669                                       |
|16  |*nosection*  |Exame Privado         |1669-07-30  |1669-07-30                                       |30.07.1669                                       |
|17  |*nosection*  |Vésperas              |1669-10-12  |1669-10-12                                       |12.10.1669                                       |
|18  |*nosection*  |Doutor                |1669-10-13  |1669-10-13                                       |13.10.1669                                       |
|19  |nome         |nota                  |1665-10-15  |frei religioso de São Bernardo                   |António Cabral (frei religioso de São Bernardo)  |









## Important fields

### Faculdade

* See [QA for faculdade](031-instituta_qa.ipynb)
* See [Inferences for faculdade](035-faculdades.ipynb)

Mostly contains a single name of a Faculdade (school) of the University. 

But some students have more than one Faculdade recorded explicitly:

        (Fernão de Abreu id: 140714)

        Faculdade: Teologia / Cânones
        Matrícula(s): Teologia: 1616/10/06
        1617/10/13
        Cânones: 1618/10/15
        1619/10/15
        1621/10/21
        1622/10/19
        Instituta: 1618/12/08.
        Bacharel em Cânones: 1623/07/12
        Formatura: 1623/07/19
 
        (Lopo de Abreu id: 141025)
        Faculdade: Cânones / Leis
        Matrícula(s):
        Instituta:
        Bacharel em Leis: 1572/07/12
        Formatura: 1575/11/11
        Licenciado:
        Doutor:
        Outras informações:
        Provas de curso: Cânones: 21.10.1566 até 22.06.1567
        Código e Leis: 01.10.1567 até 31.05.1568
        01.10.1568 até 30.04.1569
        15.10.1570 até 30.04.1571
        08.10.1571 até 15.06.1572
        18.10.1572 até 18.06.1573
        28.10.1573 até 28.06.1574
        Conclusões do 8º ano: 11.11.1575

When there is no value recorded in the "Faculdade:" field, the programme tries to
infer from other information in the record. The process can generate more than one
"faculdade" per given student. 

In different periods attendance of some "faculdades" was required as part of the curriculum
of other "faculdades". Before 1772 to enter the faculties of Theology and Medicine it was necessary
to be a bachelor in Arts, and so either enroll in the Faculty of Arts or obtain an equivalence 
of prior studies outside the university (for instance in colleges).

After 1772 all students, irrespective of the area of study, should do introductory courses at the Faculty of Mathematics and Philosophy for two years, and only then continue to the school where they would receive their degree. In this context the first enrollments occur in the faculty of Mathematics or Philosophy despite the students going on to study Civil or Canon Law, Medicine or Theology. Note that some students did go on to graduate in Mathematics or Philosophy as their first choice

The algorithm tries to infer the Faculdade if the corresponding field is empty and corrects the value 
if is was not in compliance of the academic rules of precedence.

Many errors occur during the periods of transition: when a student entered the university before a
major reformation and exited after new rules were in place. 

### Matrícula (inscription)

Information about inscriptions is one of the most varied and difficult to process. 

In its simplest form it is just a series of dates:

        Id: 139883
        Faculdade: Cânones
        Matrícula(s):01.10.1586
        01.10.1587
        04.01.1588
        10.02.1590

Some have tags for faculdade in the middle of the dates:

        Matrícula(s): Matemática 0.1.1792 (ordinário)
        Filosofia: 29.1.1792 (obrigado)
        3.1.1793
        13.1.1795
        Direito: 18.1.1793
        4.1.1794
        Leis: 3.1.1795
        4.1.1796
        4.1.1797


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

Errors due to misunderstanding of the rules:

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


### Instituta 

We only take fields the value of which contain a date. Some records have spurious punctuation content in this field
(e.g. https://pesquisa.auc.uc.pt/details?id=140367)


## Information inferred independently of fields

### Degrees

Between 1700 and 1771 the mean duration of obtaining the "bacharel" degree was 7,2. Fonseca, F.T. da (2000) ‘A dimensão pedagógica da reforma de 1772: alguns aspectos’, in O Marquês de Pombal e a Universidade. Coimbra: Imprensa da Universidade de Coimbra, pp. 43–68. doi:http://dx.doi.org/10.14195/978-989-26-0373-5_2., p.51




## Install required packages and libraries 

The normal requirements for running Timelink notebooks were expanded for this
specific application. Be sure to install all the required software as follows:

Open a terminal in VS Code and type

        pip install -r notebooks/requirements.txt 


## References

ipython sql extension (allows usage of %sql in notebook cells): https://pypi.org/project/ipython-sql/
ISAD(G): https://www.ica.org/sites/default/files/CBPS_2000_Guidelines_ISAD%28G%29_Second-edition_EN.pdf
