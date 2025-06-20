# This contains global values and configurations
from sqlalchemy.orm import Session, sessionmaker

# Various shared information
#
# Connection strings for SQLite databases
sqlite_main_db = "sqlite:///../database/sqlite3/fauc.db?check_same_thread=False"
sqlite_test_db = "sqlite:///notebooks/ucalumni/tests/db/ucalumni.db?check_same_thread=False"

# Main db name in Mysql
mysql_main_db = 'ucalumni'
mysql_test_db = 'ucalumni_test'

# this is where the notebooks will come for a db
default_db = ('sqlite','fauc.db')
default_db_url = sqlite_main_db

# To share a Session do, in each module:
# from ucalumni.config import Session

Session = sessionmaker()


# Paths
path_to_errata = 'database/errata'

