# Utilities for interacting with pandas 
#
# IDEAS:
#    baptisms=function_to_df( function='n',       
#                               act_tpe='bap',
#                               column_name='child', # instead of function
#                               person_info=True, # adds function_name, function_sex, 
#                                                 #  columns
#                               dates_in=(after,before),  
#                               name_like = name of person with function
#                               more_funcs=['pn','mn','ppn','mpn','pmn','mmn'],....)

from distutils.log import warn
from sqlalchemy import MetaData, engine, Table,select, not_, func, and_, desc
import pandas as pd
from matplotlib import cm, colors
from IPython.display import display

from timelink.mhk.models import base  # noqa
from timelink.mhk.models.db import TimelinkMHK
from timelink.mhk.models.person import Person
from timelinknb.config import Session
from timelinknb import get_attribute_table, get_nattribute_table, get_person_table
import timelinknb.config as conf

def remove_particles(name, particles=None):
    if particles is None:
        particles = ("de","da","e","das","dos","do")

    return " ".join([n for n in name.split() if n not in particles])

def name_to_df(name,db: TimelinkMHK=None, similar=False, sql_echo=False ):
    """ name_to_df return df of people with a matching name

Args:
    name = name to search for
    similar = if true will strip particles and insert a wild card %
              between name components with an extra one at the end
    """
    # We try to use an existing connection and table introspection
    # to avoid extra parameters and going to database too much
    dbsystem: TimelinkMHK = None
    if db is not None:
        dbsystem = db
    elif conf.TIMELINK_DBSYSTEM is not None:
        dbsystem = conf.TIMELINK_DBSYSTEM
    else:
        raise(Exception("must call get_mhk_db(conn_string) to set up a database connection before or specify previously openned database with db="))

    if similar:
        name_particles = remove_particles(name).split(" ")
        name_like = '%'.join(name_particles)
        name_like = name_like+'%'
    else:
        name_like = name
    
    ptable = get_person_table(dbsystem)

    stmt = select(ptable.c.id, ptable.c.name, ptable.c.sex, ptable.c.obs).where(ptable.c.name.like(name_like))
    
    if sql_echo:
        print(stmt)

    with Session() as session:
        records = session.execute(stmt)
        df =  pd.DataFrame.from_records(records.columns('id','name','sex','obs'),index=['id'],columns=['id','name','sex','obs'])
        if df.iloc[0].count() == 0:
            df = None  #  nothing found we 
    return df


    