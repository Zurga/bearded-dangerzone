#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import json
import csv
import glob
import os


def list_columns(year, location):
	"""
	Returns all columns of a specific year.csv file.
	This file is identical to the .xls file provided by the CBS,
	but is converted to CSV format.
	"""
	return sorted(pd.DataFrame.from_csv(location + \
					str(year) + ".csv").columns)

def get_vars(csvfile):
    """
    Returns a dictionary of correct variables for a specific year.
    """
    with open(csvfile, "rbU") as f:
        reader = reader=csv.reader(f, delimiter=';')
        return {row[0]:row[1] for row in reader}

# Dictionary of correct variables for all years.
variables = {os.path.basename(fn)[:-4]: get_vars(fn)
				for fn in glob.glob('data/csv/vars/*')
				if not fn.endswith("~")}

# List of all provinces.
provinces = ["Groningen", "Friesland", "Drenthe", "Overijssel",
            "Flevoland", "Gelderland", "Utrecht", "Noord-Holland",
             "Zuid-Holland", "Zeeland", "Noord-Brabant", "Limburg"]

def get_json(var, variables, provinces, years, location = "data/csv/"):
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

        # DataFrame consisting of Gemeente,Provincie data.
        # Foor 2004 and 2005, assuming data is equal to 2006 data,
        # because of nonexistence of data for these years.
        try:
            gemprov = pd.DataFrame.from_csv(location +
                                            "gemprov/" + year + ".csv")
        except Exception as e:
            gemprov = pd.DataFrame.from_csv(location +
                                            "gemprov/2006.csv")

        # For each province in the provinces list parameter...
        for prov in provinces:
            # Create a list of Gemeentes in currently iterated province.
            gem = list(gemprov[(gemprov["PROVINCIE"] == prov)]
                       .filter(["GEMEENTE"]).T.columns)

            # Filter root based on this list.
            branch = root[(root[index].isin(gem))].set_index([index])

            # Lowercase all Gemeente names.
            branch.index = branch.index.str.lower()

            # Write to JSON dictionary.
            JSON[year][prov] = json.loads(branch[item].to_json())

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

        # DataFrame consisting of Gemeente,Provincie data.
        # Foor 2004 and 2005, assuming data is equal to 2006 data,
        # because of nonexistence of data for these years.
        try:
            gemprov = pd.DataFrame.from_csv(location +
                                            "gemprov/" + year + ".csv")
        except Exception as e:
            print e
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



        # For each province in the provinces list parameter...
    return JSON



def write_json(variables, tree=False, inp_dir_prefix= '',
               outdir='data/json/'):
    """
    Writes JSON to data/json/. If tree is set to true it returns a tree list
    """
    broken_var = ["aantal_ao_uitkering", "aantal_geboorte",
                  "meest_voorkomende_postcode", "buurtcode",
                  "personen_ao_uitkering_totaal", "regionaam",
                  "woningvoorraad_aantal", "regioaanduiding","gemeentecode"]

    for var in variables:
        if not var in broken_var:
            print("Currently writing %s.json.")  % var
            if tree:
                filename = outdir + "tree_" + var + ".json"
                with open(filename, 'w') as f:
                    json.dump(get_tree_json(var, variables, provinces, \
                    (2006, 2014), location=inp_dir_prefix + "data/csv/"), f)
            else:
                filename = outdir + var + ".json"
                with open(filename, 'w') as f:
                    json.dump(get_json(var, variables, provinces, \
                    (2006, 2014), location=inp_dir_prefix + "data/csv/"), f)


if __name__ == "__main__":
    print(write_json(variables))
