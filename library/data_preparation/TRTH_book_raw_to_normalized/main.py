#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul 24 14:24:50 2021

@author: jonasdepaolis
"""

import os
import random

DIRECTORY = "/Volumes/HDD_8TB/_READ_ONLY/TRTH_EUROSTOXX_50_BOOK/_original_raw_legacy"
COMMAND = "python3 /Users/jonasdepaolis/Dropbox/GitHub/_quant-utils/preparation/TRTH_book_raw_to_normalized/TRTH_book_raw_to_normalized_v20210722.py --path {path}"

file_list = sorted(os.listdir(DIRECTORY), reverse=False)
#random.shuffle(file_list)

for file in file_list:
    
    path = os.path.join(DIRECTORY, file)
    
    if file.startswith((".", "_")):
        continue
    if "reconstructed" in file:
        continue
    if file.replace(".csv.gz", "_reconstructed.csv.gz") in os.listdir(DIRECTORY): # check CURRENT state of directory
        continue
    
    print(f"> process {path}")
        
    os.system(COMMAND.format(path=path))




"""

NUM_THREADS = 4

for i in range(0, len(file_list), NUM_THREADS):
    
    # ...
    path_list_parallel = []
    for j in range(i, i + NUM_THREADS):
        path_list_parallel.append(path_list[j])
    
    # submit to thread_pool ...
    for path in path_list_parallel:
        thread_pool.submit(..., path)
        
    # wait for results
    ....


"""

