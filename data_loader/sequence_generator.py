# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import concurrent
import numpy as np
import os
import pandas as pd

# setup logger, use WARNING (default), DEBUG (debugging)
import logging
logging.basicConfig(level=logging.WARNING) 

# cache_property requires python 3.8 or later
# from functools import cached_property

class SequenceGenerator:

    def __init__(
        self,
        source_directory:str, source_directory_filter:list,
        num_threads:int, max_workers:int, # threading args
        chunk_shuffle:bool, chunk_size:int, batch_shuffle:bool, batch_size:int, # generator args
        pipeline, # pipeline args
        num_steps:int, sample_rate:int, # sequence args
        seed:int=42, # seed args
    ):
        """
        Input generator that implements an end-to-end process for multi-threaded
        loading and processing of time-series data, and that yields batches of
        sequential input data.
        
        This generator can be iterated over multiple times.

        Specific arguments:
        
        :param source_directory:
            str, reference to directory containing .csv files

        Standard arguments:
        
        :param num_threads:
            int, number of chunks to be processed in parallel threads
        :param max_workers:
            int/None, maximum number of workers to be used
        :param chunk_shuffle:
            bool, shuffle order in which chunks are loaded into memory
        :param chunk_size:
            int, number of data points per chunk
        :param batch_shuffle:
            bool, shuffle samples at the cost of performance
        :param batch_size:
            int, number of samples per batch
        :param num_steps:
            int, number of steps per sequence
        :param sample_rate:
            int, rate at which to sample, default is 1
        :param seed:
            int, seed for reproducibility in np.random operations
        
        :param pipeline:
            dict, pipeline arguments
        """
        
        # source arguments
        self.source_list = None
        self.length_list = None
        self.source_setup(source_directory, source_directory_filter)
        
        # threading arguments
        self.num_threads = num_threads
        self.max_workers = max_workers
        self.thread_setup(self.max_workers)
        
        # generator arguments
        self.chunk_shuffle = bool(chunk_shuffle)
        self.chunk_size = int(chunk_size)
        self.batch_shuffle = bool(batch_shuffle)
        self.batch_size = int(batch_size)
        
        # pipeline arguments
        self.pipeline = pipeline
        
        # sequence arguments
        self.num_steps = int(num_steps)
        self.sample_rate = int(sample_rate)
        
        # seed arguments
        self.seed = seed
        
    # setup routines . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 
    
    def source_setup(self, source_directory:str, source_directory_filter:list):
        """
        Parse source based on file system and set the attributes required to
        access data, that is source_list and length_list. 
        
        :param source_directory:
            str, source directory
        :param source_directory_filter:
            str, substrings used to filter paths
        """
        
        # from local directory: '/Volumes/.../<folder>/train'
        if os.path.isdir(source_directory):
            self.path_list = [os.path.join(source_directory, x)
                for x in os.listdir(source_directory) if not x.startswith(".")]
        # from unknown source: ...
        else:
            raise ValueError(f"Unable to identify source '{source_directory}'.")
            
        # ...
        if source_directory_filter:
            self.path_list = [path for path in self.path_list
                if any([stock in path for stock in source_directory_filter])
            ]
            
        # keep list of sources and related length information
        self.source_list = [pd.HDFStore(path) for path 
            in self.path_list
        ] # source list
        self.length_list = [source.get_storer("df").shape[0] for source 
            in self.source_list
        ] # source length list

        # close all sources manually
        [source.close() for source in self.source_list]
    
    def thread_setup(self, max_workers:int):
        """
        If not yet existent, instantiate THREAD_POOL. 
        
        IMPORTANT: When run on vCPUs in the cloud, max_workers must be set to 
        1 as otherwise there are problems with parallel reading of hdf5 files. 
        
        :param max_workers:
            int/None, maximum number of workers to be used
        """
        
        # ...
        if not hasattr(self.__class__, "THREAD_POOL"):
            self.__class__.THREAD_POOL = concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers # limited to 1 in cloud environment
            )

    # indexers . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
    
    # @cached_property 
    def set_chunk_indexer(self):
        """
        Chunk indexer that can be used to shuffle load chunks from a set of
        file paths, thereby allowing for heterogenous input data.
        
        This property is cached and must first be deleted in order to be
        updated. An update is necessary when the upper_bound for a given path
        is changed in `self.meta_list`.
        """
        
        # all possible (file_index, line_index) combinations
        indexer = [(source, offset)
            for source in range(len(self.source_list))
            for offset in range(0, self.length_list[source], self.chunk_size)
        ]
        indexer = np.array(indexer)
        
        # if shuffling is enabled: shuffle indexer
        if self.chunk_shuffle:
            indexer = np.random.permutation(indexer) 
        
        # set attribute
        self.chunk_indexer = indexer

    # TODO: to be used with cached_property
    def chunk_indexer_reset(self):
        """
        Reset cached_property by deleting chunk_indexer.
        """
        
        # ...
        del self.chunk_indexer
    
    # @cached_property 
    def set_batch_indexer(self):
        """
        Batch indexer that can be used to shuffle samples, also allowing to
        remove samples in case a flag is provided.
        
        This property is cached and must first be deleted in order to be
        updated.
        """

        # if flag is provided: identify flagged indices >= offset
        if self.flag is not None:
            flagged = np.arange(-self.num_steps, self.num_steps+1)[None, :] + \
                np.flatnonzero(self.flag)[:, None] # broadcasting
            flagged = np.unique(flagged) # remove duplicates
            flagged = flagged[flagged >= self.num_steps] # start from offset
        # else: empty np.ndarray
        else:
            flagged = np.empty((0,))
        
        # extend flagged indices to (0,) + flagged + (length,)
        flagged = np.insert(flagged, 0, 0)
        flagged = np.insert(flagged, flagged.shape[0], self.x.shape[0])
        
        # if shuffling is disabled: keep sequential indices to use slicing
        if not self.batch_shuffle:
            # find (start, end) tuple per batch in between flagged indices
            indexer = [(
                np.arange(flagged[i], flagged[i+1] - self.batch_size,
                    self.batch_size)[None, :] + \
                np.arange(0, self.batch_size * 2,
                    self.batch_size)[:, None]).T
                for i in np.arange(flagged.size - 1)
            ]
            # ...
            indexer = np.concatenate(indexer, axis=0)
            # return indexer as list of slice objects -> FAST
            indexer = [
                slice(start, end) for (start, end) in indexer.astype(int)
            ]
        # else: shuffle indices to use fancy-indexing
        else:
            # exclude flagged indices
            indexer = np.setdiff1d(
                np.arange(self.x.shape[0]), flagged)
            # shuffle indexer
            indexer = np.random.permutation(indexer)
            # return indexer as 2-dimensional np.ndarray -> SLOW
            surplus = indexer.size % self.batch_size
            indexer = indexer[:-surplus].reshape(-1, self.batch_size)

        # sanity check
        if not len(indexer) > 0:
            logging.debug(f"total samples per chunk are less than batch_size")
        
        # set attribute
        self.batch_indexer = indexer

    # TODO: to be used with cached_property
    def batch_indexer_reset(self):
        """
        Reset cached_property by deleting batch_indexer.
        """
        
        # ...
        del self.batch_indexer

    # get chunk . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
    
    def thread_submit(f):
        """
        Submit method call to thread_pool executor that allows for training on
        the main thread to continue while loading the next chunk in parallel.
        
        https://docs.python.org/3/library/concurrent.futures.html
        """
        
        # ...
        def wrapper(self, *args, **kwargs):
            return self.__class__.THREAD_POOL.submit(f, self, *args, **kwargs)
        
        return wrapper

    @thread_submit
    def thread(self, chunk_index:int):
        """
        Run thread to process a single chunk of data. Each thread must return a
        chunk, that is either an instance of `concurrent.futures.Future` or
        None.
        
        :param chunk_index:
            int, position at which to read parameters from chunk_indexer
        :return chunk:
            concurrent.futures.Future, thread reference
        """
        
        # read source and offset
        source, offset = self.chunk_indexer[chunk_index]
        # (re-)open file
        self.source_list[source].open()
        # load chunk
        chunk = self.source_list[source].select(**{
            "key": "df", # default key
            "start": offset,
            "stop": offset + self.chunk_size,
            # "auto_close": True, # instead of pd.HDFStore.close()
        })
        # close file to release memory
        self.source_list[source].close()
        # transform chunk
        chunk = self.pipeline(chunk)

        # ...
        logging.debug(f"thread {chunk_index} finished processing")
        
        return chunk
    
    def get_chunk(self):
        """
        Get chunk future instances. This method is triggered as soon as previous
        chunk_pool is updated.
        
        :return chunk_pool:
            list, contains multiple concurrent.futures.Future instances
        """
            
        # get chunk_index_queue
        chunk_index_queue = [self.chunk_index + i for i 
            in range(self.num_threads)
        ]
        # ensure that chunk_index does not exceed chunk_indexer length
        chunk_index_queue = [chunk_index for chunk_index 
            in chunk_index_queue if chunk_index < len(self.chunk_indexer)
        ]
        # if queue is not empty, update global chunk_index attribute
        if len(chunk_index_queue) > 0:
            self.chunk_index = chunk_index_queue[-1] + 1
        
        # initiate futures
        chunk_pool = [
            self.thread(chunk_index) for chunk_index in chunk_index_queue
        ]
            
        return chunk_pool
        
    # set chunk . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
    
    def set_x(self, array:np.ndarray):
        """
        Build data. Use sequence view based on np.stride_tricks, i.e. without 
        causing an expensive copy. In terms of access, note that contiguous 
        slicing will be very fast, whereas non-contiguous fancy-indexing will 
        cause a copy and therefore should be avoided.
        
        continuous slicing # FAST
            sequencer = Sequencer(num_steps, sample_rate)
            view = sequencer.transform(array)
            fast_slice = view[0:100]
        non-continuous fancy-indexing # SLOW
            ...
            slow_fancy = view[[5,15,35,75,85]]
        
        https://scipy-cookbook.readthedocs.io/items/ViewsVsCopies.html
        https://mentat.za.net/numpy/numpy_advanced_slides/

        Use numpy stride_tricks to generate sequences, with strides denoting
        the number of bytes of memory that must be skipped to progress to the
        next item along a certain dimension.
        
        :param array:
             np.ndarray, input array of arbitrary dimensions
        :return array:
            np.ndarray, output array with index range 0..(n-num_steps)
        """
    
        # add 2 output dimensions
        output_dim_0 = (array.shape[0] - self.num_steps - 1) // self.sample_rate
        output_dim_1 = self.num_steps
        output_shape = (output_dim_0 + 1, output_dim_1,) + array.shape[1:]

        # add 1 stride dimension
        stride_dim_0 = (array.strides[0] * self.sample_rate,)
        stride_shape = stride_dim_0 + array.strides

        # apply stride_tricks to avoid copy
        as_strided = np.lib.stride_tricks.as_strided
        array = as_strided(array, output_shape, stride_shape)

        # ...
        self.x = array 

    def set_y(self, array:np.ndarray):
        """
        Build targets.

        :param array:
            np.ndarray, output array with index range num_steps..n
        """

        self.y = array[self.num_steps::self.sample_rate]

    def set_flag(self, array:np.ndarray):
        """
        Build flag.

        :param array:
            np.ndarray, output array with index range num_steps..n
        """

        self.flag = array[self.num_steps::self.sample_rate]
    
    def set_chunk(self, chunk_pool:list):
        """
        Set chunk future results. This method is triggered as soon as previous
        chunk_pool is exhausted.
        
        :param chunk_pool:
            list, contains multiple concurrent.futures.Future instances
        """
        
        # if chunk_pool is empty, set exhausted flag and exit method
        if not len(chunk_pool) > 0:
            self.EXHAUSTED = True; return
        
        # compute results
        chunk_pool = [
            chunk.result() for chunk in chunk_pool
        ]
        # merge results
        x, y, flag = [
            np.vstack(array) for array in zip(*chunk_pool)
        ]

        # update data x as a sequence
        self.set_x(x)
        self.set_y(y)
        self.set_flag(flag)

        # logging
        logging.debug(f"all attributes are set, start training ...")
    
    # generator loop . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 
    
    def __iter__(self):
        """
        Generate batches from chunk, reset chunk when exhausted.
        
        :yield batch:
            tuple, (data, targets) model input
        """
        
        # reset seed everytime that generator is restarted
        np.random.seed(self.seed)

        # set chunk_indexer
        self.set_chunk_indexer() # self.chunk_indexer_reset() 

        # set chunk & batch index
        self.EXHAUSTED = False # flag is set in self.set_chunk
        self.chunk_index = 0
        self.batch_index = 0

        # get and set initial chunk, set batch_indexer
        chunk = self.get_chunk()
        self.set_chunk(chunk)
        self.set_batch_indexer()
        
        while not self.EXHAUSTED:
            
            # if batch_indexer contains at least one batch, yield batch
            if len(self.batch_indexer) > 0:
                batch = self.batch_indexer[self.batch_index]
                yield self.x[batch], self.y[batch]
            
            # if initial batch: get next chunk
            if self.batch_index == 0:
                chunk = self.get_chunk()
            # if last batch: set next chunk
            if self.batch_index >= len(self.batch_indexer) - 1:
                self.set_chunk(chunk) 
                self.set_batch_indexer() # self.batch_indexer_reset()
            
            # handle batch_index
            if self.batch_index >= len(self.batch_indexer) - 1:
                self.batch_index = 0
            else:
                self.batch_index = self.batch_index + 1
                
        # GENERATOR IS EXHAUSTED ---
            
    def __next__(self):
        return self


