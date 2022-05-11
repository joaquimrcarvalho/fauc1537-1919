# script to call the import command from the command line
#
# In the root directory of the repository do:
# python notebooks/import-alumni.py --help

from ucalumni.cli import app

if __name__ == "__main__":
    app()