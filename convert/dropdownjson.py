import pandas as pd
import json

def create_json(location = "data/csv/expl.csv", out = "data/json/expl/expl.json"):
    df = pd.DataFrame.from_csv(location)
    JSON = {}
    for group in df["Group"]:
        JSON[group] = json.loads(df[df['Group'] == group].T.to_json())
    with open(out, 'w') as f:
        json.dump(JSON, f)
        return "DONE!"

print create_json()
