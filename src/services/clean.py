# services/clean.py
"""
THE CLEANER — transforms messy raw data into analysis-ready data.

⭐ this code will be improve very soon !


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



def clean_dataframe(df:pd.DataFrame)-> Tuple[pd.DataFrame,Dict[str,Any]]:
    '''
    cleaning the dataframe anf return cleaned_df and and its report 
    '''
    # a report for original data
    df = df.copy() # never change/mutate the original data -- 
    report = create_report(df)
    df = Normalise_column(df,report)
    df = strip_string(df,report)
    df = drop_empty(df,report)
    df = coerce_numeric(df,report)
    df = parse_date(df,report)
    df = impute_missing(df,report)
    df = remove_duplicates(df,report)

    final_report_ = final_report(df,report)

    return df, report

    
def create_report(df)->Dict[str,Any]:
    report:Dict[str,Any] ={
    'original_shape' :{'Rows':len(df),'Columns':len(df.columns)},
    'operations' : [],
    'summary':[]
    }
    return report
   

    #  ---  Normalise column names  --------
def Normalise_column(df:pd.DataFrame,report:dict)->pd.DataFrame:
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
    
    return df    
    
    #    --- Strip string whitespace ----
def strip_string(df:pd.DataFrame,report:dict)->pd.DataFrame:

    objt_cols = df.select_dtypes(include='object').columns.tolist()
    strip_count = 0
    for cols in objt_cols:
        initial  = df[cols].copy()
        df[cols] = df[cols].str.strip() if hasattr(df[cols],"str") else df[cols]
        strip_count += (initial != df[cols]).sum()
    if strip_count:
        _record(report, f"Stripped whitespace from {strip_count} cells across {len(objt_cols)} text columns",
                {"type": "strip_whitespace", "cells_changed": int(strip_count)})

    return df
        


    #    ----  Drop fully empty rows & columns  ------
def drop_empty(df:pd.DataFrame,report:dict)->pd.DataFrame:
    initial_shape = df.shape
                # droping the rows and columns which are filled with full of NAN/Null 
    df = df.dropna(how="all").dropna(axis=1,how="all") # axis 0 for Operations move down vertically and axis 1 for Operations move across horizontally
    dropped_rows = initial_shape[0] - df.shape[0]
    dropped_cols = initial_shape[1] - df.shape[1]
    if dropped_rows or dropped_cols:
        _record(report, f"Removed {dropped_rows} fully-empty rows and {dropped_cols} empty columns",
                {"type": "drop_empty", "rows_dropped": dropped_rows, "cols_dropped": dropped_cols})

    return df


    #    ----   Coerce numeric strings --------
def coerce_numeric(df:pd.DataFrame,report:dict)->pd.DataFrame:
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
    return df



    #    ----    Parse date columns  --------
def parse_date(df:pd.DataFrame,report:dict)->pd.DataFrame:
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
            if not_null > 0 and success/not_null >= 0.75:
                df[col] = parsed
                _record(report, f"Parsed '{col}' as datetime",
                        {"type": "parse_datetime", "column": col})
        except ValueError:
            continue 

    return df

        #  ----   Impute missing values --------
def impute_missing(df:pd.DataFrame,report:dict)->pd.DataFrame:
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
        
    return df



        #  ---- Remove duplicates  ------
def remove_duplicates(df:pd.DataFrame,report:dict)->pd.DataFrame:
    dup_count = int(df.duplicated().sum())
    df = df.drop_duplicates()
    if dup_count:
        _record(report, f"Removed {dup_count} duplicate rows",
                {"type": "dedup", "duplicates_removed": dup_count})
        
    return df
        
        #  ---- Final report --------
def final_report(df:pd.DataFrame,report:dict)->Dict[str,Any]:
    report['summary'].append({
            'final_steps' : {"rows": len(df), "cols": len(df.columns)},
            'dtypes':{col: str(dtype) for col, dtype in df.dtypes.items()}
        })





#  ----  report maker -----------
def _record(report:dict,message:str,details:dict)->None:
    report["operations"].append({
        'message':message,
        'details':details
    })

