# services/clean.py
"""
THE CLEANER — transforms messy raw data into analysis-ready data
"""
from typing import Dict,List,Tuple,Any
import pandas as pd
import re

def clean_dataframe(df:pd.DataFrame)-> Tuple[pd.DataFrame,Dict[str,Any]]:
    '''
    cleaning the dataframe anf return cleaned_df and and its report 
    '''
    # a report for original data
    
    report:Dict[str,Any] ={
        'original_shape' :{'Rows':len(df),'Columns':len(df.columns)},
    }
    df = df.copy() # never change/mutate teh original data -- 

    #  ---  Normalise column names  --------
    original_cols = list(df.columns)
    df.columns = (
        pd.Series(df.columns.astype(str))
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
        .str.replace(r"[^\w\s]", "", regex=True)
    )
    renamed = {o:n for o,n in zip(original_cols,df.columns) if str(o).strip() !=n}
    if renamed:
        _record(report,
                f'Renamed {len(renamed)} columns to snake_case',
                {"type": "rename", "count": len(renamed), "mapping": renamed}
        )
    #    --- Strip string whitespace ----
    objt_cols = df.select_dtypes(include='object').columns.tolist()
    strip_count = 0
    for cols in objt_cols:
        initial = df[cols].copy()
        df[cols] = df[cols].str.strip() if isinstance(str,df[cols]) else df[cols]
        strip_count += (initial !=df[cols]).sum()
    if strip_count:
        _record(report,
                f"Stripped whitespace from {strip_count} cells across {len(objt_cols)} text columns",
                {"type": "strip_whitespace", "cells_changed": int(strip_count)})

















def _record(report:dict,message:str,details:dict)->None:
    report[message] = details