# flake8: noqa: E501
""" Treatment of place names in the UC Alumni dataset. """
import pandas as pd

PLACE_NAME_INFO_FILE = 'inferences/places/gngc_names_geocoded.csv'
PLACE_NAME_INFO_DF = None


def load_place_name_info(file: str = PLACE_NAME_INFO_FILE):
    """ Load the place name info from the CSV file. """
    return pd.read_csv(file, dtype={'geonamesid': str})


def get_place_info(place_name: str, place_info: pd.DataFrame = None,
                   name_field: str = 'name'):
    """ Get the place name information.

    Args:
        place_name (str): The name of the place.
        change_list (pd.DataFrame): The DataFrame with the information.
        name_field (str): The name of the field with the place name (deafult=name).

    Returns:
        dict: A dictionary with the place name information.
    """
    if place_info is None:
        place_info = PLACE_NAME_INFO_DF

    row = place_info[place_info[name_field] == place_name]
    # make a dict with the row values
    if row.empty:
        return {}
    else:
        # generate a dict with a key fo each column and value of the row
        return dict(row.iloc[0])

if PLACE_NAME_INFO_DF is None and PLACE_NAME_INFO_FILE is not None:
    try:
        PLACE_NAME_INFO_DF = pd.read_csv(PLACE_NAME_INFO_FILE)
    except ValueError as error:
        print(error)
        PLACE_NAME_INFO_DF = None

