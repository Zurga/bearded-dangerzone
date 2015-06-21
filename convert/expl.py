import pandas as pd
import json
import sys

reload(sys)  
sys.setdefaultencoding('utf8')

def json_to_csv(inp = "data/expl.json", oup = "data/expl.csv"):
    x = {}
    expl = json.loads(open(inp).read())

    for group in expl:
        x.update(expl[group])

    df = pd.DataFrame.from_dict(x)
    df.T.to_csv(oup)
    return "File %s written." % oup

def csv_to_json(inp = "data/expl.csv", oup = "data/expl.json", grouped = True):
    df = pd.DataFrame.from_csv(inp, sep=';')
    if grouped:
        x = {}
        for group in set(df["Group"].values):
            x[group] = {}
            for var in set(df[df["Group"] == group].index):
                x[group][var] = df.loc[var].to_dict()
	
    with open(oup, 'w') as f:
        json.dump(json.loads(json.dumps(x, ensure_ascii=False)), f, sort_keys=True)
    
    return "File %s written." % oup
    
print csv_to_json()
