# Notebooks

This folder contains Jupyter notebooks that interact with the MHK/Timelink database to process data in forms not available using the web interface.

To be able to run notebooks you need to install the Python VSCode extension and a Python interpreter on the current machine.

## Install the Python extension and the Python interpreter

To install the Python extension check https://marketplace.visualstudio.com/items?itemName=ms-python.python

## Install aditional packages for timelink-mhk interaction

In addition to the base instalation of Python, some specific packages are needed
to interact with ``timelink-mhk``. The packages handle sql queries, reading MHK
configuration files, and various auxiliary functions.

To install the required packages open the terminal in VSCode: Command+j or menu `Terminal` -> `New terminal`

Type 
    ``pip install -r notebooks/requirements.txt``


# Optional packages

Data analysis with Pandas

    ``pip install pandas``


## References

* https://pypi.org/project/ipython-sql/
* https://pypi.org/project/python-dotenv/
* https://pypi.org/project/mysql-connector-python/
* https://pandas.pydata.org
* https://ipywidgets.readthedocs.io/en/latest/index.html