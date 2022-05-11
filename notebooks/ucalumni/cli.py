"""
:mod: `cli` -- Command line interface to ucalumni
=================================================

.. module: cli

For
(c) Joaquim Carvalho 2021.
MIT License, no warranties.
"""

# cli interface
# we use Typer https://typer.tiangolo.com
import typer
from ucalumni.importer import import_auc_alumni
from ucalumni.aluno import Aluno
from ucalumni import extractors
from ucalumni import mapping

app = typer.Typer()


@app.command()
def import_alumni(
        csv_file: str =
        typer.Argument(...,
                       help='path of the csv file exported from Archeevo'),
        dest_dir: str =
        typer.Argument(...,
                       help="Destination directory for generated files and databases"),
        db_connection: str=
        typer.Option("", prompt="Database connection string (blank for no direct import)?",
                        help="SQLAlchemy connection string if direct import is desired, leave blank if not. "
                        "If a connection string is provided no Kleio files are generated."),
        rows: int =
        typer.Option(0, 
                     help='max number of rows to processed (0 for all)'),
        batch: int = 
        typer.Option(500,
                     
                     help='Number of records per file or database insert'),
        
        dryrun: bool =
        typer.Option(False,
                     help='output to terminal, do not create files'),
        echo: bool =
        typer.Option(False,
                     help='echo the information in each row of the export file'),
        skip_until_id: str =
        typer.Option(None,help="Skip until id (inclusive)")             
                     
                     ):
    """
    Generate kleio source files for alumni records exported from
    AUC catalog (Archeevo)
    """
    import_auc_alumni(csv_file,
                      dest_dir,
                      db_connection,
                      rows,
                      batch,
                      dryrun,
                      echo)

    typer.echo('Import finished.')


if __name__ == "__main__":
    app()
