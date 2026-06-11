# services/ingest.py

# what i need to read CSV , EXCEL , SQL , xml  

import io
import pandas as pd
import xml.etree.ElementTree as ET
from typing import Dict


def ingest(read:bytes, filename:str)-> Dict[str,pd.DataFrame]:
    '''
    Reading the  raw data file and converting into `Dictionary`,
    choosing Dictionary because of excel , that may have multiple sheets .
    can also handle  the other type of file easily .   
    '''
    # extracting the extension name
    ext = filename.split('.')[-1].strip().lower()

    if ext =="csv":
        df = _read_csv(read)
        return {'main':df}
    elif ext in ('xlsx','xls'):
        df = _read_excel(read)
        return df
    elif ext == 'xml':
        df = _read_xml(read)
        return {'main':df}
    elif ext == 'sql':
        df = _read_sql(read)
        return df
    else:
        raise ValueError(f'Unsupported file type: .{ext}')
        

# file workers
def _read_csv(content:bytes)->pd.DataFrame:
    '''
    reading CSV file 
    '''
    for enc in ['utf-8','latin-1','cp1252']:
        try:
            __read_csv__ = pd.read_csv(
                filepath_or_buffer=io.BytesIO(content),
                sep=None,
                encoding=enc,
                engine='python',
                on_bad_lines='skip' #skip bad lines without raising or warning when they are encountered.
            )
        except UnicodeDecodeError :
            # using continue , for skiping the encoding that do not support the given/current csv file.
            continue
    raise ValueError(f"Unable to decode CSV using supported encodings : {' , '.join(enc)}")

def _read_excel(content:bytes)->Dict[str,pd.DataFrame]:
    '''
    Read all sheets from an Excel workbook.
    because many excel data like lookups, summary and more are in separate sheets
    '''
    xl_files = pd.ExcelFile(io.BytesIO(content))
    # due to multiple sheets we need a dict than need to be return
    multiple_sheets = {}
    for sheet_name in xl_files.sheet_names:
        df = xl_files.parse(sheet_name)
        if not df.empty:
            # cleaning the sheet name
            clean_sheet_name = sheet_name.strip().replace(" ","_").lower()
            multiple_sheets[clean_sheet_name] = df
    return multiple_sheets if multiple_sheets else {'main':pd.DataFrame()}


def _read_xml(content:bytes)->pd.DataFrame:
    '''
        Parse XML into a flat DataFrame.

        using two `APPROACHES`
        1) using the pandas (pd.read_xml())
        2) manual Xml parsing (note:- i had took some help of AI)
    
    '''
    try:
        return pd.read_xml(io.BytesIO(content))
    
    except Exception:
        pass # use for switch on manual method
    # Manual approach
    root = ET.fromstring(content.decode(encoding='utf-8',errors='ignore'))
    records =[]
    for child in root:
        record = dict(child.attrib)
        for elems in child:
            record[elems.tag] = elems.text # for values
        if record:
            records.append(record)
    if not record:
        raise ValueError('Could not extract tabular data from XML structure')
    return pd.DataFrame(record)
            

        

def _read_sql():
    '''
    work in progress
    '''
    pass

