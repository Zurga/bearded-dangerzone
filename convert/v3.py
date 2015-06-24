#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import operator
import json
import csv
import glob
import os


def get_vars(csvfile):
    """
    Returns a dictionary of correct variables for a specific year.
    """
    with open(csvfile, "rbU") as f:
        reader = csv.reader(f, delimiter=';')
        return {row[0]: row[1] for row in reader}


# Dictionary of correct variables for all years.
variables = {os.path.basename(fn)[:-4]: get_vars(fn)
             for fn in glob.glob('data/csv/vars/*')
             if not fn.endswith("~")}

# Dict of all provinces and their codes.
provinces = {"Groningen": 20, "Friesland": 21, "Drenthe": 22,
             "Overijssel": 23, "Flevoland": 24, "Gelderland": 25,
             "Utrecht": 26, "Noord-Holland": 27, "Zuid-Holland": 28,
             "Zeeland": 29, "Noord-Brabant": 30, "Limburg": 31}


def list_columns(year, location):
    """
    Returns all columns of a specific year.csv file.
    This file is identical to the .xls file provided by the CBS,
    but is converted to CSV format.
    """
    return sorted(pd.DataFrame.from_csv(location +
                                        str(year) + ".csv").columns)


def get_countrydata(JSON):
    minimum = min((JSON[province]["__provdata"]["min"]
                   for province in JSON.keys()), key=lambda x: x[2])

    maximum = max((JSON[province]["__provdata"]["max"]
                   for province in JSON.keys()), key=lambda x: x[2])

    average = np.mean([JSON[province]["__provdata"]["avg"]
                       for province in JSON.keys()])

    return {"min": minimum,
            "max": maximum,
            "avg": average}


def get_json(var, variables, provinces, years, location="data/csv/"):
    """
    Returns a json string per item,
    in which the data for the given years is included.

    var: string
    variables: nested dictionary
    provinces: list of Dutch provinces
    years: tuple -> ints
    location: string

    E.g.

    > get_json("aantal_mannen", variables, provinces, (2010, 2014))
>>> {'2010': {'Drenthe':  { u'Aa en Hunze': 12685,
                u'Assen': 32605,
                ...
                },
                'Flevoland': {u'Almere': 93510,
                                u'Dronten': 20185,
                    ...
                            }
                },

        '2011': {...
    }
"""

    JSON = {}

    # For each year provided in the years tuple parameter...
    for year in xrange(years[0], years[1] + 1):
        # Create a new entry in the JSON dict.

        year = str(year)
        JSON[year] = {}

        # Retrieve correct variable names.
        item = variables[var][year]
        areades = variables["regioaanduiding"][year]
        index = variables["regionaam"][year]
        mannen = variables["aantal_mannen"][year]
        vrouwen = variables["aantal_vrouwen"][year]
        data = pd.DataFrame.from_csv(location + year + ".csv")

        # Lower all input and all columns
        # (CBS uses multicase for its columns throughout the years).
        item, areades = item.lower(), areades.lower()
        index = index.lower()
        data.columns = map(str.lower, data.columns)

        # First select only all gemeentes,
        # then filter based on given item and index.
        # This will be for all gemeentes in all provinces.

        if var != "aantal_mannen" and var != "aantal_vrouwen":
            root = data[(data[areades] == 'Gemeente') |
                        (data[areades] == 'G')].filter(
                            [item, index, mannen, vrouwen])

            root["inwoners"] = root[mannen] + root[vrouwen]

        else:
            if var == "aantal_mannen":
                root = data[(data[areades] == 'Gemeente') |
                            (data[areades] == 'G')].filter(
                                [item, index, vrouwen])

                root["inwoners"] = root[item] + root[vrouwen]

            elif var == "aantal_vrouwen":
                root = data[(data[areades] == 'Gemeente') |
                            (data[areades] == 'G')].filter(
                                [item, index, mannen])

                root["inwoners"] = root[mannen] + root[item]

        # Remove rows which contain no data (notice the ~)
        rootx = root[~root[item].isin(['x', '-'])]

        
        # If 'probleemvars', multiply by 100
        if var == "gemiddelde_huishoudensgrootte"\
                or var == "personenautos_per_huishouden":
            rootx[item] = rootx[item].apply(
                lambda x: float(x.replace(',', '.'))*100)

        # DataFrame consisting of Gemeente,Provincie data.
        # Foor 2004 and 2005, assuming data is equal to 2006 data,
        # because of nonexistence of data for these years.
        try:
            gemprov = pd.DataFrame.from_csv(location +
                                            "gemprov/" + year + ".csv")
        except Exception as e:
            print(e)
            gemprov = pd.DataFrame.from_csv(location +
                                            "gemprov/2006.csv")

        # For each province in the provinces list parameter...
        for prov in provinces:
            # Create a list of Gemeentes in currently iterated province.
            gem = list(gemprov[(gemprov["PROVINCIE"] == prov)]
                       .filter(["GEMEENTE"]).T.columns)

            # Filter root based on this list.
            branch = root[(root[index].isin(gem))].set_index([index])
            branchx = rootx[(rootx[index].isin(gem))].set_index([index])

            # Lowercase all Gemeente names.
            branch.index = branch.index.str.lower()
            branchx.index = branchx.index.str.lower()

            # Min, max, average for each province.
            bd = branch[item].to_dict()
            dfdict = {k: int(v) for k, v in branchx[item].to_dict().items()}
            minimum = min(dfdict.items(), key = lambda x: x[1])
            maximum = max(dfdict.items(), key = lambda x: x[1])
            average = np.mean(dfdict.values())
            countrydata = {
                "__provdata":
                {"min": [provinces[prov],
                         minimum[0], minimum[1]],
                 "max": [provinces[prov],
                         maximum[0], maximum[1]],
                 "avg": average,
                 "inw": (branch["inwoners"]).to_dict()
                 }
            }

            bd.update(countrydata)

            # Write to JSON dictionary.
            JSON[year][prov] = json.loads(json.dumps(bd))

        # Min, max, average for whole country
        JSON[year]["__countrydata"] = get_countrydata(JSON[year])

    return JSON


def get_tree_json(var, variables, provinces, years, location="data/csv/"):
    """
    Generates a json file in tree format.
    """
    JSON = {"name": var,
            "children": []}

    # For each year provided in the years tuple parameter...
    for year in xrange(years[0], years[1] + 1):
        # Create a new entry in the JSON dict.

        year = str(year)
        yeardict = {"name": year,
                    "children": []}
        # Retrieve correct variable names.
        item = variables[var][year]
        areades = variables["regioaanduiding"][year]
        index = variables["regionaam"][year]
        data = pd.DataFrame.from_csv(location + year + ".csv")

        # Lower all input and all columns
        # (CBS uses multicase for its columns throughout the years).
        item, areades = item.lower(), areades.lower()
        index = index.lower()
        data.columns = map(str.lower, data.columns)

        # First select only all gemeentes,
        # then filter based on given item and index.
        # This will be for all gemeentes in all provinces.
        root = data[(data[areades] == 'Gemeente') |
                    (data[areades] == 'G')].filter([item, index])

        # If var is float, multiply by 100.
        if var == "gemiddelde_huishoudensgrootte" \
                or var == "personenautos_per_huishouden":
            root[item] = root[item].apply(
                lambda x: float(x.replace(',', '.'))*100 if x != "x" else 'x')

        # DataFrame consisting of Gemeente,Provincie data.
        # Foor 2004 and 2005, assuming data is equal to 2006 data,
        # because of nonexistence of data for these years.
        try:
            gemprov = pd.DataFrame.from_csv(location +
                                            "gemprov/" + year + ".csv")
        except Exception as e:
            print(e)
            gemprov = pd.DataFrame.from_csv(location +
                                            "gemprov/2006.csv")

        for prov in provinces:
            provdict = {"name": prov,
                        "children": []}
            # Create a list of Gemeentes in currently iterated province.
            gemeentes = list(gemprov[(gemprov["PROVINCIE"] == prov)]
                             .filter(["GEMEENTE"]).T.columns)

            for gem in gemeentes:
                gem = gem.lower()
                # Filter root based on this list.
                branch = root[(root[index].isin(gemeentes))].set_index([index])
                # Lowercase all Gemeente names.

                branch.index = branch.index.str.lower()

                gemdict = {"name": gem,
                           "value": branch.T[gem].values[0]}
                provdict["children"].append(gemdict)
            yeardict["children"].append(provdict)
        JSON["children"].append(yeardict)
    return JSON


def write_json(variables, tree=False, inp_dir_prefix='',
               outdir='data/json/'):
    """
    Writes JSON to data/json/. If tree is set to true it returns a tree list
    """
    broken_var = ["aantal_ao_uitkering", "aantal_geboorte",
                  "meest_voorkomende_postcode", "buurtcode",
                  "personen_ao_uitkering_totaal", "regionaam",
                  "woningvoorraad_aantal", "regioaanduiding", "gemeentecode"]

    for var in variables:
        if var not in broken_var:
            print("Currently writing %s.json.") % var
            if tree:
                filename = outdir + "tree_" + var + ".json"
                with open(filename, 'w') as f:
                    json.dump(get_tree_json(var, variables, provinces,
                                            (2006, 2014),
                                            location=inp_dir_prefix +
                                            "data/csv/"), f)
            else:
                filename = outdir + var + ".json"
                with open(filename, 'w') as f:
                    json.dump(get_json(var, variables, provinces,
                                       (2006, 2014), location=inp_dir_prefix
                                       + "data/csv/"), f)


if __name__ == "__main__":
    print "MAIN WEETJE"
