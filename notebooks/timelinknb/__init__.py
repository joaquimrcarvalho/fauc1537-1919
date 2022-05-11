"""
:module: timelinknb

Utilities and shared variables for using timelink inside notebooks

:Contains:
    Utilities for acessing timelink from Jupyter notebooks

(c) Joaquim Carvalho, MIT LICENSE

"""
import datetime
import socket
from pathlib import Path

from sqlalchemy import MetaData, Table, engine
from sqlalchemy.orm import declarative_base, sessionmaker

from timelink.mhk.utilities import get_dbnames, get_connection_string, get_engine
from timelink.mhk.models import base  # noqa
from timelink.mhk.models.person import Person
from timelink.mhk.models.db import TimelinkDB
import timelinknb.config as conf
from timelinknb.config import Session

current_time = datetime.datetime.now()
current_machine = socket.gethostname()
sqlite_databases = [f.stem for f in list(Path('../database/sqlite3/').rglob('*.db'))]
mhk_databases = get_dbnames()

def get_mhk_db(db_name,**extra_args) -> TimelinkDB: 
    """ Create a connection to a Timelink/MHK database
    
    Creates a connection to the database db_name, 
    using the parameters of the current MHK instalation.

    The resulting dbsystem oject is stored in global variable
    TIMELINK_DBSYSTEM

    """

    connection_string = get_connection_string(db_name)
    conf.TIMELINK_CONNSTRING = connection_string # share it with other modules
    db = TimelinkDB(connection_string,**extra_args)
    conf.TIMELINK_DBSYSTEM = db # share it
    conf.Session.configure(bind=db.get_engine())
    return db


def get_nattribute_table(db: TimelinkDB=None):
    """ Return the nattribute view.

    Returns a sqlalchemy table linked to the nattributes view of MHK databases
    This views joins the talbe "persons" and the table "attributes" providing attribute
    values with person names and sex.


            create view nattributes as
            select `p`.`id`        AS `id`,
                `p`.`name`      AS `name`,
                `p`.`sex`       AS `sex`,
                `a`.`the_type`  AS `the_type`,
                `a`.`the_value` AS `the_value`,
                `a`.`the_date`  AS `the_date`,
                `p`.`obs`       AS `pobs`,
                `a`.`obs`       AS `aobs`
            from `attributes` `a`
                join `persons` `p`
            where (`a`.`entity` = `p`.`id`);


    The column id contains the id of the person/object, not of the attribute
    """
    if db is not None:
        dbsystem = db
    elif conf.TIMELINK_DBSYSTEM is not None:
        dbsystem = conf.TIMELINK_DBSYSTEM
    else:
        raise(Exception("must specify database with db="))
    if conf.TIMELINK_NATTRIBUTES is None:
        eng: engine = dbsystem.get_engine()
        metadata: MetaData = dbsystem.get_metadata()
        attr=Table('nattributes', metadata, autoload_with=eng)
        conf.TIMELINK_NATTRIBUTES = attr
    else:
        attr = conf.TIMELINK_NATTRIBUTES   
    return attr   


def get_attribute_table(db: TimelinkDB=None):
    """ Return the attribute table.

    Returns a sqlalchemy table linked to the attributes table of MHK databases

            id        varchar(64)    not null  primary key,
            entity    varchar(64)    null,
            the_type  varchar(512)   null,
            the_value varchar(1024)  null,
            the_date  varchar(24)    null,
            obs       varchar(16000) null

    The column id contains the id of the attribute and the column entity the id
    of the person/object to which the attribute is related
    """
    if db is not None:
        dbsystem = db
    elif conf.TIMELINK_DBSYSTEM is not None:
        dbsystem = conf.TIMELINK_DBSYSTEM
    else:
        raise(Exception("must specify database with db="))
    if conf.TIMELINK_ATTRIBUTES is None:
        eng: engine = dbsystem.get_engine()
        metadata: MetaData = dbsystem.get_metadata()
        attr=Table('attributes', metadata, autoload_with=eng)
        conf.TIMELINK_ATTRIBUTES = attr
    else:
        attr = conf.TIMELINK_ATTRIBUTES  
    return attr



def get_relations_table(db: TimelinkDB=None):
    """ Return the relations table.

    Returns a sqlalchemy table linked to the relations table of MHK databases


            id          varchar(64)    not null primary key,
            origin      varchar(64)    null,
            destination varchar(64)    null,
            the_date    varchar(24)    null,
            the_type    varchar(32)    null,
            the_value   varchar(256)   null,
            obs         varchar(16000) null

    """
    if db is not None:
        dbsystem = db
    elif conf.TIMELINK_DBSYSTEM is not None:
        dbsystem = conf.TIMELINK_DBSYSTEM
    else:
        raise(Exception("must specify database with db="))
    if conf.TIMELINK_RELATIONS is None:
        eng: engine = dbsystem.get_engine()
        metadata: MetaData = dbsystem.get_metadata()
        rels=Table('relations', metadata, autoload_with=eng)
        conf.TIMELINK_RELATIONS = rels
    else:
        rels = conf.TIMELINK_RELATIONS  
    return rels



def get_nfuncs_view(db: TimelinkDB=None):
    """ Return the nfuncs (named functions) table.

    Returns a sqlalchemy table linked to the nfuncs view of MHK databases

        create view nfuncs as
            select `r`.`origin`    AS `id`,
                `p`.`name`      AS `name`,
                `r`.`the_value` AS `func`,
                `a`.`id`        AS `id_act`,
                `a`.`the_type`  AS `act_type`,
                `a`.`the_date`  AS `act_date`
            from `ucalumni`.`relations` `r`
                    `persons` `p`
                    join `acts` `a`
            where ((`r`.`the_type` = 'function-in-act') and
                (`r`.`destination` = `a`.`id`) and (`r`.`origin` = `p`.`id`));

    """
    if db is not None:
        dbsystem = db
    elif conf.TIMELINK_DBSYSTEM is not None:
        dbsystem = conf.TIMELINK_DBSYSTEM
    else:
        raise(Exception("must specify database with db="))
    if conf.TIMELINK_NFUNCS is None:
        eng: engine = dbsystem.get_engine()
        metadata: MetaData = dbsystem.get_metadata()
        nfuncs=Table('nfuncs', metadata, autoload_with=eng)
        conf.TIMELINK_NFUNCS = nfuncs
    else:
        nfuncs = conf.TIMELINK_NFUNCS  
    return nfuncs
    """
    
    """





def get_person(id:str=None, sql_echo:bool=False)-> Person:
    """
    Fetch a person from the database
    """
    if id is None:
        raise(Exception("Error, id needed"))
    p:Person = Session().get(Person,id)
    return p

def pperson(id:str):
    """Prints a person in kleio notation"""
    print(get_person(id=id).to_kleio())


print("Timelink utilities for Jupyter notebooks loaded!")