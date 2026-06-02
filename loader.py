import pandas as pd

def load_excel(path):

    df = pd.read_excel(path)

    df.columns = [x.strip() for x in df.columns]

    return df