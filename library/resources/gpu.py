# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# general imports
import os

# TODO: to make the GpuManager more robust, include both fields "FB Memory Usage > Used" and "Temperature > GPU Current Temp"
# TODO: include XML parser to work with `nvidia-smi -x -q` command
# TODO: support different types of gpus (A100, RTX 3090, ...)
# TODO: support fractional gpus in MIG mode

# settings
GPU_COUNT = 2

class Singleton(type):
    
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        """
        Silently prevent class instantiation if, for a given kernel, one class 
        instance already exists. 
        
        :param cls:
            ..., reference to the class that is to be instantiated
        """
        
        # ...
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        
        return cls._instances[cls]

class GpuManager(metaclass=Singleton):
    
    def __init__(self, framework=None):
        """
        Expose available gpus upon request for use within the given kernel, 
        avoiding any resource conflicts between multiple users. 
        
        IMPORTANT INFORMATION:

        Once the deep learning framework has seen the gpus, it cannot unsee 
        them - it is therefore necessary to (1) FIRST expose only the 
        requested or available gpus, and (2) THEN inform the deep learning 
        framework about their existence. 
        
        Therefore, before running the GpuManager, restart the kernel. 
        
        USAGE:
        
        >>> from gpu import GpuManager
        >>> gpu_manager = GpuManager()
        >>> gpu_manager.request_gpus(1)
        
        :param framework:
            str, either 'tensorflow' or 'pytorch'
        """

        # attributes
        self.framework = framework

        # status
        self.num_enabled = 0

    def request_gpus(self, num_requested=None): 
        """
        Handle user request for gpus.

        :param num_requested:
            int, number of gpus requested, default is None
        """

        # should gpus already be enabled, return 
        if self.num_enabled:
            print("(INFO) remember to restart the kernel before requesting gpus!")
            return self.num_enabled

        # screen available gpus
        num_available, gpuid_list = self._get_gpus(gpuid_filter=[])

        # if no number has been requested, ask user for input
        if not num_requested:
            while not num_requested in range(num_available + 1):
                num_requested = int(input("(ENTER) number of gpus requested:"))

        # expose min(available, requested) gpus to the requesting user
        if num_requested <= num_available:
            num_enabled = self._set_gpus(gpuid_list[:num_requested])
        # ...
        else:
            num_enabled = self._set_gpus(gpuid_list[:num_available])

        # ensure visibility with regard to deep learning framework
        if self.framework == "tensorflow":
            assert num_enabled == tensorflow_gpu_count(), \
                "(INFO) tensorFlow cannot see the correct number of gpus ..."
        # ...
        elif self.framework == "pytorch":
            assert num_enabled == pytorch_gpu_count(), \
                "(INFO) pytorch cannot see the correct number of gpus ..."
        # ...
        else:
            pass
        
        # if asserts have run through, assume that gpus are enabled
        self.num_enabled = num_enabled

        return self.num_enabled

    def _get_gpus(self, gpuid_filter=[]):
        """
        Identify available gpus by parsing the output of the nvidia-smi 
        command. To be considered available, a device must at that time be 
        idle, that is, the nvidia-smi command must yield ...

        - gpu utilization: 0%
        - gpu memory: 0%

        :param gpuid_filter:
            list, filter results by this list of gpuid numbers
        """

        # if we use a gpuid filter, run sanity check
        if gpuid_filter:
            assert all(x in range(GPU_COUNT) for x in gpuid_filter), \
                "(INFO) gpuid filter contains values outside of the possible range"
        # else, set gpuid filter to include all possible gpuid values
        else:
            gpuid_filter=list(range(GPU_COUNT))

        # parse the entire nvidia-smi command line output
        output = os.popen("nvidia-smi -q --id={gpuid_string}".format(
            gpuid_string=",".join(map(str, gpuid_filter)), 
        )).read()

        # get gpu utilization
        gpu_util = [parsed_line for parsed_line in output.split("\n") 
            if "gpu" in parsed_line.lower() and parsed_line.endswith("%")
        ]
        # get memory utilization
        mem_util = [parsed_line for parsed_line in output.split("\n") 
            if "memory" in parsed_line.lower() and parsed_line.endswith("%")
        ]
        # TODO: get gpu memory
        # TODO: get gpu temperature

        # helper function to determine if idle, that is, 0% utilization
        idle = lambda parsed_line: not [int(x) for x in parsed_line.split() 
            if x.isdigit()
        ][0] > 0

        # append all available gpus to gpuid_list
        gpuid_list = []
        for gpuid, gpu_line, mem_line in zip(gpuid_filter, gpu_util, mem_util):
            if idle(gpu_line) and idle(mem_line):
                gpuid_list.append(gpuid)

        # ...
        num_available = len(gpuid_list)

        return num_available, gpuid_list

    def _set_gpus(self, gpuid_list):
        """
        Expose min(num_request, num_available) gpus to the requesting user by 
        setting the CUDA_VISIBLE_DEVICES environment variable accordingly. 
        Note that this environment variable will be seen only from within the
        given kernel, not across multiple kernels!
        
        :param gpuid_list:
            list, expose gpus for the listed gpuid numbers
        """

        # default visibility, all gpus are hidden from user
        os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

        # update visibility, exposing only the gpus represented by gpuid_list
        gpuid_string = ",".join(map(str, gpuid_list))
        os.environ["CUDA_VISIBLE_DEVICES"] = gpuid_string

        # ...
        num_enabled = len(gpuid_list)

        return num_enabled
    
# helper functions ...

def tensorflow_gpu_count():
    """
    Test the number of gpus seen by TensorFlow. 
    """

    # ...
    from tensorflow.python.client.device_lib import list_local_devices
    return len(list_local_devices()) - 1 # do not count cpu

def pytorch_gpu_count():
    """
    Test the number of gpus seen by PyTorch. 
    """

    # ...
    from torch.cuda import device_count
    return device_count()


