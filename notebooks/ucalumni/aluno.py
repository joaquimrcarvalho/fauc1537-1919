"""
(c) Joaquim Carvalho 2021.
MIT License, no warranties.
"""
from dataclasses import dataclass, field
from datetime import datetime
from logging import warning
from typing import ClassVar, List, Callable, Type, Union
from pathlib import Path
import re

from pyparsing import QuotedString
from markdownTable import markdownTable

from timelink.mhk.models import base # this setups the orm models
from timelink.mhk.models.base import Person
from timelink.mhk.models.db import TimelinkMHK

from ucalumni.config import Session
from ucalumni.grammar import DATELINE, DateUtility
from ucalumni.groups import atr
import ucalumni.fields


# Helper for abbreviations
def replace_with_abbrev(text: str, abrev_list: dict) -> str:
    """ Replace expressions with abbreviations
    
    Arg:
        text: text with expressions to be replaced

        abrev_list: dictionnary with expressions as keys
        and abbreviations as values

    Expression are regular expressions."""
    atext = text
    for expression, abrev in abrev_list.items():
        atext = re.sub(expression, abrev, atext)
    return atext

entry_abbrev: dict = {
    '[Rr]eprovado':'repr.',
    '[Aa]provado': 'apr.',
    ' com ': ' ',
    'valores': 'v.',
    '[Ll]ivro': 'liv.',
    '[Vv]oluntário': 'vol.',
    '[Ob]rigado': 'obr.',
    '[Oo]rdinário]': 'ord.',
    'Bacharel': 'bach.',
    'Cadeira': 'cad.',
    'Atos': 'at.',
    'Tomo': 't.',
    'Formatura': 'form.',
    'Licenciatura': 'lic.',
    'Doutor': 'dr.',
    'Mestre': 'mes.',
    'Faculdade inferida': 'f.inf.',
    'Faculdade corrigida': 'f.corr.',
}

# Helper to display content of fields in aluno records. Used in __str__ method of aluno
def markdown_table(table: list):
    """
    Generate a markdown table from list of data

    table: a list of dictionnaries row date, 
           where keys are column names.

    The table can be used for documentation and matches
    the style of the markdown previewer in Visual Studio Code

    For instance:

           notes_table = []

           for nota in aluno.notes: 
               notes_table.append({'N':nota.numero, 
                'section': nota.seccao, 
                'campo':nota.campo,
                'data':nota.data.value,
                'valor': nota.valor,
                'obs': nota.obs})

            mkd_table = markdowntable(notes_table)
    """
    if len(table) == 0:
        return('')

    mkd =  markdownTable(table).setParams(row_sep='topbottom',
                                          padding_weight='right',
                                          padding_width=2).getMarkdown()
    # we retouch the markdown to look good in VS Code
    lines = mkd.splitlines()
    vscode_style_table = ''
    for number, line in enumerate(lines):
        # first line is ```` ignore
        # second is +-------- ... -----+ put it aside
        if number == 0:
            pass
        elif number == 1 :
            header_sep_line = line
        elif number == 2:
            header = line 
            # we get the column separators positions
            sep_pos = [m.start() for m in re.finditer('\|',line)]
            s = list(header_sep_line)
            s[0] = '|'
            for pos in sep_pos:
                s[pos]='|'
            s[-1] = '|'
            header_sep_line = "".join(s)
            vscode_style_table = header + '\n' + header_sep_line + '\n'
        elif number == len(lines) -1:
            pass
        else:
            vscode_style_table = vscode_style_table + line + '\n'
    return vscode_style_table


@dataclass
class Instituta:
    """ Representa um inscrição em Instituta

    Members
    -------
    `data` : date of the matricula, class: ucalumni.grammar.DateUtility
    `obs` : observations

    NOTE: makes sense? could be a type of matrícula
    """
    data: DateUtility
    obs: str

    def __str__(self):
        return f'{self.data.value} {self.obs}'

@dataclass
class Matricula:
    """ Represents an inscription "matrícula"

    Members
    -------

    `ambito`: what is the inscription in: Cânones, Curso Jurídico, 1ª ano do Curso Jurídico
    `tipo`: the type, one of: faculdade, ano, curso, classe
    `modalidade`: obrigado ou ordinário 
    `data` : date of the matricula, class: ucalumni.grammar.DateUtility
    `obs` : observations

    """

    ambito: str  # object of the inscription
    tipo: str # type of the inscription Faculdade, curso, classe
    modalidade: str # obrigatório ou ordinário
    data: DateUtility
    obs: str


@dataclass
class Grau:
    """ Representa um grau
    nome
        nome do grau, str
    ambito
        Faculdade, curso, str
    data
        tipo :class:`DateUtility`
    obs
        any note
    """
    nome: str
    ambito: str
    data: DateUtility
    obs: str


@dataclass
class Exame:
    """ Representa a informação de um exame
    ambito
        course or degree
    data
        DateUtility
    resultado
        Result of the exame
    obs
    """
    ambito: str  # cadeira, curso, grau
    data: DateUtility
    resultado: str
    obs: str


@dataclass
class Prova:
    """ Corresponds to entries like: 'Provou cursar... provou residir"""
    ambito: atr  # cursar, residir
    data: DateUtility
    obs: str


@dataclass
class Nota:
    """ Information not processed in a precise form.
     Extractors work the information in the Nota list and
     move it to specific fields and lists.

     numero
        sequential number by creation order
     seccao
        the section name of the information
     campo
        the field name
     valor
        the value of the field
    data
        the date, :class:`DateUtility`
    obs
        any observation on the value
    processed
        if True this note was already processed by an extractor

     """
    numero: int
    seccao: str
    campo: str
    valor: str
    data: DateUtility
    obs: str
    processed: bool = field(init=False, default=False)
    fname_inferred: bool = field(init=False,default=False) # field name can be inferred from previous line
    fvalue_is_date: bool = field(init=False,default=False)

    @property
    def fvalue_contains_date(self):
        """
        Return true if the value of this note contains a date
        """
        l = list(DATELINE.scanString(self.valor))
        if len(l) > 0:
            return True
        else:
            return False

    def __str__(self):
        return f"{self.numero:02d} [{self.processed}] {self.seccao} : {self.campo} : {self.data.value} : {self.valor} | obs: {self.obs}"


def get_aluno_from_db(id :str, db :TimelinkMHK=None)-> Type["Aluno"]:
    """ Get a aluno record from database by id
    
    Returns original information of a 'aluno' record from
    a Timelink/MHK database.

    The following attributes are set:

        * id
        * coderef
        * nome
        * unit_date_inicial
        * unit_date_final
        * process_info_date (time of database access)
        * scope_content (with the obs field in the db which is = BioHist+ScopeContent)
        * obs (same as scope_content)

    Assumes that a Session variable exists in scope associated 
        with a Timelink/MHk database. 

    A common pattern is:
        from ucalumni import Session
        db = TimelinkMHK(db_main_db)
        Session.configure(bind=db.engine())

        my_aluno = get_aluno_from_db('140337')
    
        See  https://docs.sqlalchemy.org/en/14/orm/session_basics.html

    """
    if db is not None:
        Session.configure(bind=db.get_engine())
    with Session() as session:
        case = session.get(Person, id)
        obs = case.obs
        name = case.name
        code_ref = [atr.the_value for atr in case.attributes if atr.the_type == 'código-de-referência'][0]
        start_date = [atr.the_value for atr in case.attributes if atr.the_type == 'uc-entrada'][0]
        end_date = [atr.the_value for atr in case.attributes if atr.the_type == 'uc-saida'][0]
        data_do_registo = [atr.the_value for atr in case.attributes if atr.the_type == 'data-do-registo'][0]
        aluno = Aluno(
            id,
            code_ref,
            name,
            start_date,
            end_date,
            datetime.now(),  # fake we store it in ls
            "http://pesquisa.auc.uc.pt/details?id=" + id,
            )
        aluno.bio_hist = ""
        aluno.scope_content = str(obs).replace('"""', "")  # it includes the bio_hist
        aluno.obs = f'# DB LOAD\n{case.obs}'
    return(aluno)


def get_and_process_aluno(id, db: TimelinkMHK=None)-> Type["Aluno"]:
    """
    Fetch the FA original information of
    a student and extract the information
    using current algorithm

    Does not take into account the "errata"

    """
    aluno = get_aluno_from_db(id, db)
    aluno.process()
    return aluno

@dataclass
class Aluno:
    """Information about a UC student. Holds information as it
    is processed from catalog records.

    Objects of this class are created with the metadata from the original
    catalog. Then a number of extraction functions try to fetch the rest
    of the information from the text fields BioHist and ScopeContent.
    The content of BioHist and Scope content, as well as some pre-processing
    of anotations in names,are processed by extraction functions.

    The extraction functions must have the following signature: `fextractor(aluno: Aluno)`.

    Extractor functions are called by order in the `extractors`class variable.
    They should process the notes list and set to True note.processed variable
    when the note requires no further processing after extraction.

    See README_ucalumni.md for details on structure of the information
    to be extracted

    `param id`
        a six digit number, taken from the catalog.
    `param codref`
        reference code in the original catalog e.g. "PT/AUC/ELU/UC-AUC/B/001-001/B/003305"
    `param nome`
        str, name of the student as in the catalog, might differ after processing because of name annotations
    `param unit_date_inicial`
        earliest reference in the sources
    `param unit_date_final`
        latest reference in the sourcexs
    `param data_registo`
        date of the last change to the catalog record (?) class: `datetime.datetime`
    `param url`
        str, link to the record in the online catalog
    `param id``
        str, a six digit number, taken from the catalog.
    `param codref``
         reference code in the original catalog e.g. "PT/AUC/ELU/UC-AUC/B/001-001/B/003305"
    `param nome` str, name of the student as in the catalog, might differ after processing because of name annotations
    `param data_registo` 
        `datetime.datetime` date of the last change to the catalog record (?)
    `param unit_date_inicial` earliest reference in the sources, str
    `param unit_date_final` latest reference in the sources, str
    `param url` str, link to the record in the online catalog

    """
    # Fields set by the metadata on the original record
    id: str
    codref: str
    nome: str  # UnitTile in the record metadata
    unit_date_inicial: Type[Union[str, DateUtility]]
    unit_date_final: Type[Union[str, DateUtility]]
    process_info_date: datetime = datetime.now()
    url: str = None
    # From here onwards optional fields in __init__
    # BioHist, includes place of birth and parents
    bio_hist: str = field(init=False, compare=False)
    # ScopeContent, includes academic record
    scope_content: str = field(init=False, compare=False)
    # errata: class variable with list of id of existing errata records
    # see Aluno.collect_errata(path)
    errata: ClassVar[str] = field(init=False, compare=False,default=None)
    # Erratum: information which corrects the original 
    #  archeevo record. If not None or empty will be used
    #  to extract information, superseeding original record. 
    erratum: str = field(init=False, compare=False,default=None)
    erratum_diff: str = field(init=False, compare=False,default=None)
    # Fields set by the extraction functions
    pnome: str = field(init=False, compare=False,default=None)
    apelido: str = field(init=False, compare=False,default=None)
    sexo: str = field(init=False, compare=False, default='m')
                        # the final value for faculdade, after aplication of checks 
    faculdade: List[str] = field(init=False, compare=False, default_factory=list)
                        # the original value for the field "faculdade", if any
    faculdade_original: str = field(init=False, compare=False, default=None)
                        # Error message related to faculdade 
    faculdade_problem: str = field(init=False,compare=False,default=None) 
                        # detail on problem with faculdade
    faculdade_strange: str = field(init=False,compare=False,default=None) 
                        # something strange like Direito changed to Teologia
    faculdade_problem_obs: str = field(init=False,compare=False, default=None)
    nome_final: str = field(init=False,
                            compare=False)  # name after processing eventual annotations
    nota_nome: str = field(init=False,
                           compare=False,
                           default=None)  # texto of annotation in name, if any
    vide: str = field(init=False, compare=False, default=None)
    #: cut=vide is cut from name, rep=vide replaces name, add=vide adds to name
    vide_type: str = field(init=False, compare=False, default=None)
    vide_target: str = field(init=False, compare=False, default=None)

    pai: str = field(init=False, compare=False, default=None)
    mae: str = field(init=False, compare=False, default=None)
    familia: str = field(init=False,
                         compare=False,
                         default=None)  # sometines "paternidade" has a title or family name

    naturalidade: str = field(init=False, compare=False,default=None)
    colegio: str = field(init=False, compare=False, default=None)
    titulo: str = field(init=False, compare=False)  # dom, frei, padre
    universidade: str = field(init=False,
                              compare=False,default=None)  # references to other universities
    ordem: list[str] = field(init=False, compare=False,default_factory=list)  # religious orders

    matriculas: list[Matricula] = field(init=False, compare=False,
                                        default_factory=list)
    graus: list[Grau] = field(init=False, compare=False, default_factory=list)
    exames: list[Exame] = field(init=False, compare=False,
                                default_factory=list)
    provas: list[Prova] = field(init=False, compare=False,
                                default_factory=list)
    notas: list[Nota] = field(init=False, compare=False, default_factory=list)
    notas_index: dict[str, str] = field(init=False, compare=False,
                                        default_factory=dict)

    instituta: list[Instituta] = field(init=False, compare=False, default_factory=list)
 
    obs: str = field(init=False, compare=False,default="")

    # list of extraction functions
    extractors: ClassVar[List[Callable]] = []


    # return the date in which this record was edit (from the export file)
    def get_record_date(self):
        return self.process_info_date.strftime("%Y-%m-%d")

    @classmethod
    def from_db(cls,id: str) -> Type["Aluno"]:
        return get_aluno_from_db(id)

    @classmethod
    def collect_errata(cls,path_to_errata: str):
        """Collects errata files into Aluno.errata
        
        From `path_to_errata` and subdirectories collects files
        with name pattern [0-9]*.[tT][xX][tT] e.g. 165656.txt

        Sets Aluno.errata (class property) to a dictionnary where 
        the keys are the file names with no extension (Aluno ids)
        and the value is a tuple (file_name, path, relative, absolute)

        """

        result = list(Path(path_to_errata).rglob("[0-9]*.[tT][xX][tT]"))
        files = [ {'id':s.stem.split(" ")[0],'file_name':s.name,'path_relative':str(s.relative_to(path_to_errata).parent),'path':str(s),'path_absolute':str(s.resolve())} for s in result]
        cls.errata = {}
        for f in files:
            id = f['id']
            cls.errata[id] = (
                f['file_name'],   
                f['path'],
                f['path_relative'],
                f['path_absolute'])

    def check_errata(self):
        """ Check if aluno has an errata record

        If so set the content of aluno.erratum to the errata record
        Erratum wil be used by aluno.process() as source for extracting
        information.

        """
        if Aluno.errata is None:
            # not sure about this, complexifies too much
            #  warning("calling check_errata without calling Aluno.collect_errata(path) first")
            return
        if self.id in Aluno.errata.keys():
            (file_name, file_path,rel ,abs ) = Aluno.errata[self.id]
            with open(file_path) as f:
                 self.erratum = f.read()


    @classmethod
    def add_extractor(cls, extractor: Callable):
        """
        Add an extractor
        :param extractor: a function tha
        :return: class: `Aluno`
        """
        cls.extractors.append(extractor)
        return cls

    @classmethod
    def remove_extractor(cls, extractor: Callable):
        cls.extractors.remove(extractor)
        return cls

    def process(self):
        """
        Process the BioReg and ScopeContent into notes and other fields.
        """
        ucalumni.fields.process_bioreg(self)

    def extract(self):
        """
        Calls in order all the functions in the `extractors` list.

        :return: None
        """
        # print("Number of extractors: ",len(self.extractors))
        if len(self.extractors) == 0:
            raise TypeError("Aluno.extract is being called but not extractors were added. Must import ucalumni.extractors module after uc.alumni.aluno")
        for extractor in self.extractors:
            extractor(self)

    def add_nota(self, seccao: str, campo: str, valor: str, data: DateUtility,
                 obs: str, fname_inferred = False,fvalue_is_date = False):
        """
        Adds a note to the list of notes of this Aluno.
        Also creates or updates self.notes_index[seccao][campo] adding
        (valor,data,obs) to the current list under seccao/campo.

        :param seccao: the section of the note, a str
        :param campo:  the campo of the note, a str
        :param valor:  the valor of the note, a str
        :param data:  the historical date of the valor, :class:`DateUtility`
        :param obs: an observation, str
        :return: None
        """

        this_note = Nota(len(self.notas)+1, seccao, campo, valor, data, obs)
        this_note.fname_inferred = fname_inferred
        this_note.fvalue_is_date = fvalue_is_date
        self.notas.append(this_note)
        if seccao not in self.notas_index.keys():
            self.notas_index[seccao] = {campo: [(valor, data, obs)]}
        elif campo not in self.notas_index[seccao].keys():
            self.notas_index[seccao][campo] = [(valor, data, obs)]
        else:
            if self.notas_index[seccao][campo] is None:
                self.notas_index[seccao][campo] = []
            else:
                l: list = self.notas_index[seccao][campo]
                l.append((valor, data, obs))
                self.notas_index[seccao][campo] = l
        return self

    def get_unprocessed_note(self):
        """ Returns an unprocessed note. Used by extractors
        to fetch notes that need processing.

        Extractors process notes and flag then as processed if the
        information needs no further processing as a note.

        Not all extractors set the processed flag to true, because
         the same note can provide information for different extractors
         """
        for nota in [n for n in self.notas if not n.processed]:
            yield nota

    def print_notes(self):
            [print(f'{str(nota.numero).zfill(2)} {nota.seccao:12} {nota.campo:24} {nota.valor:12} {nota.data.value:20} {nota.obs}') for nota in self.notas]
   
    def __str__(self):
        r = f"# {self.id} {self.nome}\n\n"
        r = r + f'## Original\n```{self.obs}\n```\n'
        if self.erratum_diff is not None and self.erratum_diff > '':
            r = r+f'\n### Erratum:\n.....................\n{self.erratum_diff}\n......................\n'

        if len(self.extractors) == 0:
            return r

            
        r = r + "## Inferences:\n"
        r = r + f'* id:{self.id}\n'
        r = r + f'* Nome: {self.nome}\n'\
            +f'* Data inicial:{str(self.unit_date_inicial)}\n'\
            +f'* Data final: {str(self.unit_date_final)}\n'\
            +f'* Codigo de referência: {self.codref}\n'

        if self.vide is not None:
            r = r + f'\n* Vide {self.vide}'
            r = r + f'\n* Tipo de vide {self.vide_type}'
            r = r + f'\n* Nome destino vide {self.vide_target}'
        if self.colegio is not None:
            r = f'{r}* Colégio {self.colegio}\n'


        mkdtable: list = []

        # Notas
        mkdtable.clear()
        nota: Nota
        for  nota in self.notas:
            mkdtable.append({'N':nota.numero, 
                'proc': nota.processed,
                'section': nota.seccao, 
                'campo':nota.campo,
                'data':nota.data.value,
                'valor': nota.valor,
                'obs': nota.obs})
        table = markdown_table(mkdtable)
        r = r + '\n### Notes (sections and fields from the record):\n' + table
        # Faculdade
        if self.faculdade is not None:
            for fac,data,obs in self.faculdade:
                r = r + f'### Faculdade: {fac} {data} {obs}\n'
            r = r + f'* Faculdade problema: {self.faculdade_problem} ({self.faculdade_problem_obs})\n'
            fac_org = self.faculdade_original
            if fac_org is not None and fac_org > '':
                r = r + f'* Faculdade original: {self.faculdade_original}\n'

        if self.instituta is not None:
            for inst in self.instituta:
                r = r + f'### Instituta {inst.data} {inst.obs}\n'
            

        # Matrículas
        mkdtable.clear()
        matricula: Matricula
        for matricula in self.matriculas:
            mkdtable.append({
                'âmbito':matricula.ambito,
                'tipo':matricula.tipo,
                'modalidade':matricula.modalidade,
                'data':matricula.data,
                'obs':matricula.obs})
        table = markdown_table(mkdtable)        
        r = r + '\n### Matrículas:\n' + table

        # Exames
        mkdtable.clear()
        exame: Exame
        for exame in self.exames:
            mkdtable.append({
                'âmbito':exame.ambito,
                'resumo':exame.resultado,
                'data':exame.data,
                'obs':exame.obs})
        table = markdown_table(mkdtable)        
        r = r + '\n### Exames:\n' + table

        # Graus
        mkdtable.clear()
        grau: Grau
        for grau in self.graus:
            mkdtable.append({
                'nome':grau.nome,
                'data':grau.data,
                'obs':grau.obs})
        table = markdown_table(mkdtable)        
        r = r + '\n### Graus:\n' + table

        return r + '\n'

        
    def as_entry(self):
        """ Format aluno as dictionnary entry"""
        r = f'[{self.id}] {self.nome}'
        if self.faculdade is not None:
            r=f'{r}.'
            for fac,data,obs in self.faculdade:
                r = f'{r} {fac}'
                if obs is not None and obs.strip() != fac.strip():
                    r = f'{r} ({obs})'

        if self.unit_date_inicial.value > '0000-00-00':
            r = f'{r}, {self.unit_date_inicial.value[0:4]}:{self.unit_date_final.value[0:4]}.'
        if self.pai is not None:
            r = f'{r}\nF. {self.pai}'
        if self.mae is not None:
            r = f'{r} e {self.mae}'
        if self.familia is not None:
            r = f'{r}.\nF. {self.familia}'
        
        if self.naturalidade is not None:
            r = f'{r}. N. {self.naturalidade}'

        if self.colegio is not None:
            r = f'{r}. {self.colegio}'         
            if self.nota != self.colegio:
                r = f'{r} ({self.nota})' 
            r=f'{r}.'

        matricula: Matricula
        if len(self.matriculas) > 0:
            r=f'{r}.\nMatr. '
            comma = ''
            for matricula in self.matriculas:
                r = f'{r}{comma} {matricula.data}'
                if len(self.faculdade) == 1 and matricula.ambito == self.faculdade[0][0]:
                    pass
                else:
                    r = f'{r} ({matricula.ambito})'
                comma = ','
            r=f'{r}.'

        exame: Exame
        if len(self.exames) > 0:
            r=f'{r}\nEx. '
            comma = ''
            for exame in self.exames:
                ex = f'{exame.data}: {exame.ambito} {exame.resultado} {exame.obs}'
                r = f'{r}{comma} {ex.strip()}'
                comma = ";"
            r=f'{r}.'

        grau: Grau
        if len(self.graus) > 0:
            r=f'{r}.\nG. '
            comma = ''
            for grau in self.graus:

                gr = f'{grau.nome} {grau.data}'
                r = f'{r}{comma} {gr.strip()}'
                comma = ","
            r=f'{r}.'

        return replace_with_abbrev(r,entry_abbrev)

        
