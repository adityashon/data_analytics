# services/clean.py
"""
THE CLEANER — transforms messy raw data into analysis-ready data.


Logic Flow:-
    Normalize columns
    ↓
    Strip strings
    ↓
    Remove empty rows
    ↓
    Convert numbers
    ↓
    Convert dates
    ↓
    Handle missing values
    ↓
    Remove duplicates
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
        'operations' : []
    }
    df = df.copy() # never change/mutate the original data -- 

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
        initial  = df[cols].copy()
        df[cols] = df[cols].str.strip() if hasattr(df[cols],"str") else df[cols]
        strip_count += (initial != df[cols]).sum()
    if strip_count:
        _record(report, f"Stripped whitespace from {strip_count} cells across {len(objt_cols)} text columns",
                {"type": "strip_whitespace", "cells_changed": int(strip_count)})
        


    #    ----  Drop fully empty rows & columns  ------

    initial_shape = df.shape
                # droping the rows and columns which are filled with full of NAN/Null 
    df = df.dropna(how="all").dropna(axis=1,how="all") # axis 0 for Operations move down vertically and axis 1 for Operations move across horizontally
    dropped_rows = initial_shape[0] - df.shape[0]
    dropped_cols = initial_shape[1] - df.shape[1]
    if dropped_rows or dropped_cols:
        _record(report, f"Removed {dropped_rows} fully-empty rows and {dropped_cols} empty columns",
                {"type": "drop_empty", "rows_dropped": dropped_rows, "cols_dropped": dropped_cols})




    #    ----   Coerce numeric strings --------
    '''
    CSVs store everything as text. "42.5" as a string can't be averaged.
    STRATEGY: only convert if 75%+ of the non-null values look numeric. (stratagy taken by AI 😅)
    '''
    num_col = df.select_dtypes(include='object').columns
    for col in num_col:
        changed = pd.to_numeric(df[col],errors='coerce')
        not_null = df[col].notna().sum()
        success = changed.notna().sum()
        if not_null > 0 and success /not_null >=0.75:
            df[col] = changed
            _record(report, f"Converted '{col}' from text to numeric",
                    {"type": "coerce_numeric", "column": col, "success_rate": round(success / not_null, 2)})




    #    ----    Parse date columns  --------
    '''
    Same STRATEGY is following also in date
    '''
    date_col = df.select_dtypes(include='object').columns
    for col in date_col:
        parsed = pd.Series(dtype='object') # safety 
        try:
            parsed = pd.to_datetime(df[col],errors="coerce")
            not_null = df[col].notna().sum()
            success = parsed.notna().sum()
            if not_null >0 and success/not_null >= 0.75:
                df[col] = parsed
                _record(report, f"Parsed '{col}' as datetime",
                        {"type": "parse_datetime", "column": col})
        except ValueError:
            continue 



        #  ----   Impute missing values --------
        '''
        Numeric columns → fill with MEDIAN (robust to outliers, unlike mean)
        Categorical columns → fill with MODE (most common value)
        '''

    total_missing = int(df.isnull().sum().sum())
    imputed_cols :list[str] =[]
    for col in df.select_dtypes(include='number').columns:
        if df[col].isnull().any():
            df[col] = df[col].fillna(df[col].median())
            imputed_cols.append(col)

    for  col in df.select_dtypes(include='object').columns:
        if df[col].isnull().any():
            vals = df[col].mode()
            fill_val  = vals.iloc[0] if len(vals) > 0 else "Unknown" 
            df[col] = df[col].fillna(fill_val)
            imputed_cols.append(col)

    if total_missing > 0:
        _record(report, f"Imputed {total_missing} missing values (median for numbers, mode for text)",
                {"type": "impute", "total_missing": total_missing, "columns_affected": imputed_cols})
        




        #  ---- Remove duplicates  ------
    dup_count = int(df.duplicated().sum())
    df = df.drop_duplicates()
    if dup_count:
        _record(report, f"Removed {dup_count} duplicate rows",
                {"type": "dedup", "duplicates_removed": dup_count})
        

        
        
        #  ---- Final report --------
    report['operations'].append({
            'final_steps' : {"rows": len(df), "cols": len(df.columns)},
            'dtypes':{col: str(dtype) for col, dtype in df.dtypes.items()}
        })
    return df, report




#  ----  report maker -----------
def _record(report:dict,message:str,details:dict)->None:
    report["operations"].append({
        'message':message,
        'details':details
    })