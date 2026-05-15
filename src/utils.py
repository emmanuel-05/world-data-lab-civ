## src/utils.py

import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE_DIR, "data", "civ")
EXTERNAL = os.path.join(BASE_DIR, "data", "external")

def load_all_data():
    """Charge tous les fichiers CSV du projet en un dictionnaire de DataFrames."""
    files = {
        "inactive":    "inactive.csv",
        "student":     "student.csv",
        "unemployed":  "unemployed.csv",
        "formality":   "formality.csv",
        "sector":      "sector.csv",
        "sector_ur":   "sector_ur.csv",
        "employed_ur": "employed_ur.csv",
    }
    return {
        k: pd.read_csv(
            os.path.join(RAW, v),
            dtype={
                'ccode':   'category',
                'gender':  'category',
                'year':    'int16',
                'age':     'int8',      
                'age_group': 'category', 
                'status':  'category', 
                'geo':     'category',  
                'edu_ilo': 'category',   # niveaux d'éducation
            }
        )
        for k, v in files.items()
    }

def load_external_data():
    """Charge les données externes (ONU, Banque Mondiale, etc.)"""
    return {
        "demographics": pd.read_csv(
            os.path.join(EXTERNAL, "demographics_clean_civ.csv")
        )
    }

def filter_civ(dfs):
    """Filtre tous les DataFrames pour la Côte d'Ivoire (CIV)."""
    filtered = {}
    for key, df in dfs.items():
        country_col = next(
            (c for c in df.columns if c.lower() in ['ccode', 'country', 'iso', 'code']),
            None
        )
        if country_col:
            filtered[key] = df[df[country_col].astype(str) == "CIV"].copy()
        else:
            filtered[key] = df.copy()
    return filtered


def filter_youth(dfs, max_age=24):
    """
        max_age=24 → définition ILO strict (15-24)
        max_age=35 → définition AYEC élargie (15-35)
    """
    result = {}
    for key, df in dfs.items():
        d = df.copy()
        if 'age_group' in d.columns:
            if max_age == 24:
                d = d[d['age_group'].astype(str) == '15-24'].reset_index(drop=True)
            elif max_age == 35:
                d = d[d['age_group'].astype(str).isin(['15-24', '25-34'])].reset_index(drop=True)
        if 'age' in d.columns:
            d = d[d['age'].astype(int) <= max_age].reset_index(drop=True)
        result[key] = d
    return result


def harmonize_gender(dfs):
    """Harmonise la casse de la colonne gender dans tous les DataFrames."""
    for df in dfs.values():
        if 'gender' in df.columns:
            df['gender'] = df['gender'].str.capitalize()
    return dfs