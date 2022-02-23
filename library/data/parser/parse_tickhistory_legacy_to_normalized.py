# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# execute this script via terminal: python3 <path_to_this_file> --path <path_to_raw_data> (--nrows 1e6)

# TODO: provide built-in multi-threading
# TODO: fix datatable issues

import argparse
import datatable as dt
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None  # default="warn"
import time

DATETIME = "Date-Time"

def time_decorator(function):

    # wrapper fn
    def wrapper(*args, **kwargs):
        time_start = time.time()
        result = function(*args, **kwargs)
        print("{function_name} took {runtime} seconds to execute".format(
            function_name=function.__name__,
            runtime=time.time()-time_start,
        ))
        return result

    return wrapper

@time_decorator
def reconstruct_book(data:pd.DataFrame):
    """
    Efficiently reconstruct TRTH book. 

    :param data:
        pd.DataFrame, TRTH raw legacy data
    :return full:
        pd.DataFrame, TRTH normalized book data
    """

    # SPECIFY COLUMNS TO INCLUDE . . . . . . . . . . . . . . . . . . . . . . .

    # map 'FID Name' values to corresponding columns, all items in this dictionary will be considered
    MAPPING_FIDNAME_TO_COLUMN = {
        # exchange-recorded time in milliseconds, no date
        "TIMACT_MS": "EXCHANGE_TIME_IN_MILLISECONDS",
        # limit order book informatiom
        "BEST_BID1": "L1-BidPrice", 
        "BEST_BSIZ1": "L1-BidSize", 
        "NO_BIDORD1": "L1-BuyNo", 
        "BEST_ASK1": "L1-AskPrice", 
        "BEST_ASIZ1": "L1-AskSize", 
        "NO_ASKORD1": "L1-SellNo", 
        "BEST_BID2": "L2-BidPrice", 
        "BEST_BSIZ2": "L2-BidSize", 
        "NO_BIDORD2": "L2-BuyNo", 
        "BEST_ASK2": "L2-AskPrice", 
        "BEST_ASIZ2": "L2-AskSize", 
        "NO_ASKORD2": "L2-SellNo", 
        "BEST_BID3": "L3-BidPrice", 
        "BEST_BSIZ3": "L3-BidSize", 
        "NO_BIDORD3": "L3-BuyNo", 
        "BEST_ASK3": "L3-AskPrice", 
        "BEST_ASIZ3": "L3-AskSize", 
        "NO_ASKORD3": "L3-SellNo", 
        "BEST_BID4": "L4-BidPrice", 
        "BEST_BSIZ4": "L4-BidSize", 
        "NO_BIDORD4": "L4-BuyNo", 
        "BEST_ASK4": "L4-AskPrice", 
        "BEST_ASIZ4": "L4-AskSize", 
        "NO_ASKORD4": "L4-SellNo", 
        "BEST_BID5": "L5-BidPrice", 
        "BEST_BSIZ5": "L5-BidSize", 
        "NO_BIDORD5": "L5-BuyNo", 
        "BEST_ASK5": "L5-AskPrice", 
        "BEST_ASIZ5": "L5-AskSize", 
        "NO_ASKORD5": "L5-SellNo", 
        "BEST_BID6": "L6-BidPrice", 
        "BEST_BSIZ6": "L6-BidSize", 
        "NO_BIDORD6": "L6-BuyNo", 
        "BEST_ASK6": "L6-AskPrice", 
        "BEST_ASIZ6": "L6-AskSize", 
        "NO_ASKORD6": "L6-SellNo", 
        "BEST_BID7": "L7-BidPrice", 
        "BEST_BSIZ7": "L7-BidSize", 
        "NO_BIDORD7": "L7-BuyNo", 
        "BEST_ASK7": "L7-AskPrice", 
        "BEST_ASIZ7": "L7-AskSize", 
        "NO_ASKORD7": "L7-SellNo", 
        "BEST_BID8": "L8-BidPrice", 
        "BEST_BSIZ8": "L8-BidSize", 
        "NO_BIDORD8": "L8-BuyNo", 
        "BEST_ASK8": "L8-AskPrice", 
        "BEST_ASIZ8": "L8-AskSize", 
        "NO_ASKORD8": "L8-SellNo", 
        "BEST_BID9": "L9-BidPrice", 
        "BEST_BSIZ9": "L9-BidSize", 
        "NO_BIDORD9": "L9-BuyNo", 
        "BEST_ASK9": "L9-AskPrice", 
        "BEST_ASIZ9": "L9-AskSize", 
        "NO_ASKORD9": "L9-SellNo", 
        "BEST_BID10": "L10-BidPrice", 
        "BEST_BSZ10": "L10-BidSize", 
        "NO_BIDRD10": "L10-BuyNo", 
        "BEST_ASK10": "L10-AskPrice", 
        "BEST_ASZ10": "L10-AskSize", 
        "NO_ASKRD10": "L10-SellNo", 
    }
    
    # FILTER DATA TO INCLUDE ONLY TIMESTAMP OR RELEVANT FID . . . . . . . . . .
    
    # filter for relevant columns
    data = data[["#RIC", "Date-Time", "GMT Offset", "FID Name", "FID Value"]] # possibly omit 'GMT Offset' since 'Date-Time' is already displayed in UTC
    
    # filter for relevant rows that have (1) a timestamp, or (2) a 'FID Name' value listed in the dictionary keys
    has_timestamp = ~ data["Date-Time"].isna()
    has_fidname = data["FID Name"].isin(MAPPING_FIDNAME_TO_COLUMN.keys())
    data = data.loc[has_timestamp | has_fidname, :]
    
    # ...
    data = data.reset_index(drop=True) # IMPORTANT!
    
    # store information about relevant rows in filtered dataframe
    HAS_TIMESTAMP = ~ data["Date-Time"].isna()
    HAS_FIDNAME = ~ data["FID Name"].isna()
    HAS_FIDVALUE_NONE = data["FID Value"].isna()
    
    # special case: if 'FID Name' exists and 'FID Value' is NaN, set to 0
    data.loc[HAS_FIDNAME & HAS_FIDVALUE_NONE, "FID Value"] = 0 # use arbitrary placeholder
    
    """
    Disregarded 'FID Name' values are ...
    - TIMACT (obsolete),
    - BOOK_STATE, 
    - NO_BIDMMKR, NO_BIDMKR{2-9}, NO_BIDMK10 -> identical to NO_BIDORD{1-9}, NO_BIDRD10
    - NO_ASKMMKR, NO_ASKMKR{2-9}, NO_ASKMK10 -> identical to NO_ASKORD{1-9}, NO_ASKRD10
    - ...
    """
    
    # TRANSFORM (1): MAP FID NAMES TO COLUMNS AND FID VALUES TO ROWS . . . . . 

    # create FID dataframe, set all values per row to the corresponding value in RAW['FID Value']
    book = pd.DataFrame({col: data["FID Value"] 
        for fidname, col in MAPPING_FIDNAME_TO_COLUMN.items()
    })
    
    """
    data                                          book
    -----------------------------------------     --------------------------------
    Date-Time    ...     FID Name   FID Value     col_1   col_2   col_3   ...
    2021-01-01           NaN        NaN           NaN     NaN     NaN             <- UPDATE STATE
    2021-01-01           Test_1     123           123     123     123
    2021-01-01           Test_2     234           234     234     234
    2021-01-01           Test_3     345           345     345     345
    2021-01-02           NaN        NaN           NaN     NaN     NaN             <- UPDATE STATE
    2021-01-02           Test_1     123.1         123.1   123.1   123.1
    3032-02-02           Test_3     345.1         345.1   345.1   345.1
    ...

    Assume mapping ('Test_1' -> 'col_1'), ('Test_2' -> 'col_2'), etc.
    """
    
    # TRANSFORM (2): CREATE MASK THAT PLACES FID VALUES IN MATCHING POSITIONS .

    # repeat 'FID Name' (matching each column) vertically across all rows
    mask_layer_a = pd.DataFrame({col: pd.Series([fidname]).repeat(len(data.index)) 
        for fidname, col in MAPPING_FIDNAME_TO_COLUMN.items()
    }).reset_index(drop=True)
    
    # repeat 'FID Name' horizontally across all columns
    mask_layer_b = pd.DataFrame({col: data["FID Name"] 
        for fidname, col in MAPPING_FIDNAME_TO_COLUMN.items()
    }).reset_index(drop=True)
    
    # set mask to True where 'FID Name' values align
    mask = (mask_layer_a == mask_layer_b)
    # apply book_mask, set NaN where values_mask is False
    book = book.where(mask, np.nan) 

    """
    data                                          book
    -----------------------------------------     --------------------------------
    Date-Time    ...     FID Name   FID Value     col_1   col_2   col_3   ...
    2021-01-01           NaN        NaN           NaN     NaN     NaN             <- UPDATE STATE
    2021-01-01           Test_1     123           123     NaN     NaN
    2021-01-01           Test_2     234           NaN     234     NaN
    2021-01-01           Test_3     345           NaN     NaN     345
    2021-01-02           NaN        NaN           NaN     NaN     NaN             <- UPDATE STATE
    2021-01-02           Test_1     123.1         123.1   NaN     NaN
    3032-02-02           Test_3     345.1         NaN     NaN     345.1
    ...
    
    Generate sparse matrix where each FID Value is assigned to its corresponding column. 
    """
    
    # TRANSFORM (3): PROJECT FID VALUES BACK ONTO AGGREGATE ROW . . . . . . . .

    # set NaN in UPDATE STATE to token 'E' (empty)
    book.loc[HAS_TIMESTAMP, :] = "E"
    # backward-fill
    book = book.fillna(method="bfill")
    
    """
    data                                          book
    -----------------------------------------     --------------------------------
    Date-Time    ...     FID Name   FID Value     col_1   col_2   col_3   ...
    2021-01-01           NaN        NaN           E       E       E               <- UPDATE STATE
    2021-01-01           Test_1     123           123     234     345             <- AGGREGATE ROW
    2021-01-01           Test_2     234           E       234     345
    2021-01-01           Test_3     345           E       E       345
    2021-01-02           NaN        NaN           E       E       E               <- UPDATE STATE
    2021-01-02           Test_1     123.1         123.1   NaN     345.1           <- AGGREGATE ROW
    3032-02-02           Test_3     345.1         NaN     NaN     345.1
    ...

    Use backward-fill so that the first row after each UPDATE STATE is now an AGGREGATE ROW
    of all FID Values updated at a given timestep (UPDATE STATE).
    """
    
    # TRANSFORM (4): PROJECT AGGREGATE ROW BACK ONTO UPDATE STATE . . . . . . .

    # set token 'E' in UPDATE STATE to NaN
    book.loc[HAS_TIMESTAMP, :] = np.nan    
    # backward-fill
    book = book.fillna(method="bfill")

    """
    data                                          book
    -----------------------------------------     --------------------------------
    Date-Time    ...     FID Name   FID Value     col_1   col_2   col_3   ...
    2021-01-01           NaN        NaN           123     234     345             <- UPDATE STATE
    2021-01-01           Test_1     123           123     234     345             <- AGGREGATE ROW
    2021-01-01           Test_2     234           E       234     345
    2021-01-01           Test_3     345           E       E       345
    2021-01-02           NaN        NaN           123.1   E       345.1           <- UPDATE STATE
    2021-01-02           Test       123.1         123.1   E       345.1           <- AGGREGATE ROW
    3032-02-02           Test_3     345.1         E       E       345.1
    ...

    Use backward-fill to move AGGREGATE ROW one step up to the UPDATE STATE.
    """
    
    # TRANSFORM (5): FILTER ALL ROWS EXCEPT UPDATE STATE . . . . . . . . . . .

    # filter rows to include only rows of type UPDATE STATE
    book = book.loc[HAS_TIMESTAMP, :]    

    """
    data                                          book
    -----------------------------------------     --------------------------------
    Date-Time    ...     FID Name   FID Value     col_1   col_2   col_3   ...
    2021-01-01           NaN        NaN           123     234     345             <- UPDATE STATE
    2021-01-02           NaN        NaN           123.1   E       345.1           <- UPDATE STATE
    ...

    Filter all rows that are not of type UPDATE STATE.
    """
    
    # TRANSFORM (6): FORWARD-FILL MISSINGS . . . . . . . . . . . . . . . . . .
    
    # replace token 'E' in UPDATE STATE with NaN
    book = book.replace({"E": np.nan})
    # forward-fill unchanged values with previous value
    book = book.fillna(method="ffill")    

    """
    data                                          book
    -----------------------------------------     --------------------------------
    Date-Time    ...     FID Name   FID Value     col_1   col_2   col_3   ...
    2021-01-01           NaN        NaN           123     234     345             <- CURRENT STATE
    2021-01-02           NaN        NaN           123.1   234     345.1           <- CURRENT STATE
    ...

    Use forward-fill to combine rows of type UPDATE STATE to the corresponding CURRENT STATE.
    """
    
    # MERGE DATA & BOOK COLUMNS . . . . . . . . . . . . . . . . . . . . . . . .

    # filter data rows to include only those of type UPDATE STATE
    data = data.loc[HAS_TIMESTAMP, :]
    # extract subset of relevant data columns, add information on 'Type' (so we know that we built this file!)
    data_subset = data[["#RIC", "Date-Time", "GMT Offset"]]
    data_subset["Type"] = "Reconstructed LL2"
    # merge columns of data_subset ('Date-Time', 'GMT Offset', ...) and book ('Date-Time-Exch', ...)
    full = pd.concat([data_subset, book], axis=1)    

    """
    full
    -----------------------------------------------------
    Date-Time    ...     col_1   col_2   col_3   ...
    2021-01-01           123     234     345
    2021-01-02           123     234     345  
    ...

    Concatenate data_subset and book dataframe to full dataframe. 
    """
    
    # ADD EXCHANGE-BASED TIMESTAMP . . . . . . . . . . . . . . . . . . . . . .
    
    # remove rows with missing timestamp (sometimes happens when value for TIMACT_MS is missing)
    has_timestamp_exch = ~ full["EXCHANGE_TIME_IN_MILLISECONDS"].isna()
    full = full.loc[has_timestamp_exch, :]

    # add 'Date-Time-Exch' (integer-based, in milliseconds)
    date = full["Date-Time"].dt.normalize() # normalize() removes time from timestamp
    time_delta = pd.to_timedelta(full["EXCHANGE_TIME_IN_MILLISECONDS"].astype(int), unit="milliseconds")
    full["Date-Time-Exch"] = date + time_delta

    # make timestamp columns timezone-unaware
    full["Date-Time"] = pd.DatetimeIndex(full["Date-Time"]).tz_localize(None)
    full["Date-Time-Exch"] = pd.DatetimeIndex(full["Date-Time-Exch"]).tz_localize(None)

    # drop obsolete exchange time information
    full = full.drop(["EXCHANGE_TIME_IN_MILLISECONDS"], axis=1)

    """
    full
    ----------------------------------------------------------------------
    Date-Time    Date-Time-Exch   ...     col_1   col_2   col_3   ...
    2021-01-01   2021-01-01               123     234     345
    2021-01-02   2021-01-02               123     234     345  
    ...

    Include both 'Date-Time' (Refinitiv-recorded) 'Date-Time-Exch' (exchange-recorded) timestamp. 
    """
    
    # POST-PROCESS BOOK . . . . . . . . . . . . . . . . . . . . . . . . . . . .
    
    # columns -61 to -1 are book, -0 is 'Date-Time-Exch'
    cols_book = list(full.columns[-61:-1]) 
    # include 'Date-Time-Exch' in cols_base
    cols_base = ["#RIC", "Type", "Date-Time", "Date-Time-Exch", "GMT Offset"] 
    # ensure desired column order
    full = full[cols_base + cols_book]
    
    # remove duplicate book states (sometimes happens in original data)
    cols_book_changed = full[cols_book].shift(-1) != full[cols_book] # use .shift(-1) to keep last
    full = full.loc[cols_book_changed.any(axis=1), :] # keep rows if there has been any change
    
    # stringify 'GMT Offset' column as in the beginning
    full["GMT Offset"] = (full["GMT Offset"]
        .astype(int)
        .apply(lambda x: f"+{x}" if x >= 0 else f"{x}")
    )
    
    # fill remaining NaN values with 0
    full = full.fillna(value=0)
    
    # ensure integer datatype for 'size' and 'no' columns
    int_cols = [col for col in full.columns 
        if any(substring in col.lower() for substring in ["size", "no"])
    ]
    full[int_cols] = full[int_cols].astype(int)
    
    # ensure float datatype for 'price' columns
    float_cols = [col for col in full.columns 
        if "price" in col.lower()
    ]
    full[float_cols] = full[float_cols].astype(float)

    # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

    return full

def chunkwise_reconstruct_book(data:pd.DataFrame):
    
    # determine breaking points by day
    series = data["Date-Time"].fillna(method="ffill").dt.day # processing by the hour would raise problems with forward-fill
    change = series.shift(1) != series    
    change_index = np.append(np.flatnonzero(change), len(series.index))
    # get (start, end) tuples
    change_index_list = [(change_index[i-1], change_index[i]) 
        for i in range(1, len(change_index))
    ]
    
    # process chunk by chunk to save memory
    chunk_list = []    
    for i, (start_index, end_index) in enumerate(change_index_list, 1):
        
        print("process chunk {}".format(i))
        chunk = data.iloc[start_index:end_index]
        chunk_list.append(reconstruct_book(chunk))
    
    # concatenate
    data = pd.concat(chunk_list, axis=0)
    
    return data

@time_decorator
def load_df(path:str, nrows=None): # as .csv(.gz)

    # parse nrows string to support both input of form "1000" and "1e3"
    if nrows is not None:
        nrows = int(float(nrows))
    
    # load df using datatable (multi-threaded!), then transform to pandas
    df = dt.fread(path, max_nrows=nrows, verbose=False,
        fill=True, # fill missing fields (happens in RAW LEGACY data)
        na_strings=[""], # make datatable.fread parse empty strings as NaNs
    ).to_pandas()
    
    # load df using pandas (single-threaded!)
    # df_cols = pd.read_csv(path, nrows=1).columns # peek at column names
    # df = pd.read_csv(path, nrows=nrows,
    #     names=df_cols, header=0, # ensure that all columns are identical per row
    #     na_values=[""], # make pd.read_csv parse empty strings as NaNs
    # )
    
    # parse datetime using pandas
    df[DATETIME] = pd.to_datetime(df[DATETIME])

    return df

@time_decorator
def save_df(df:pd.DataFrame, path:str): # as .csv(.gz)

    # datatable: fast, but may cause error!
    dt.Frame(df).to_csv(path=path, compression="gzip")
    
    # pandas: reliable but slow
    # df.to_csv(path, compression="gzip", index=False)

# ...
if __name__ == "__main__":
    
    # instantiate argument parser
    parser = argparse.ArgumentParser("reconstruct_book")
    parser.add_argument("--path", type=str, help="specify filepath", default="...")
    parser.add_argument("--nrows", type=str, help="number of rows to read", default=None)

    # parse args
    args = parser.parse_args()

    # load df
    path_load = args.path # "./test_files/DB_Raw.csv" 
    data = load_df(path_load, nrows=args.nrows)
    
    # reconstruct book
    print("start reconstructing LL2 data ...")
    data = chunkwise_reconstruct_book(data) # data = reconstruct_book(data)
    print("... done reconstructing LL2 data")

    # save df into same directory
    path_save = path_load.replace(".csv.gz", "_reconstructed.csv.gz")
    save_df(data, path_save)


