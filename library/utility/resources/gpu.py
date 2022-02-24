# !/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Jonas De Paolis"
__version__ = "2022-02-23"

# open issues
# TODO: support different types of gpus (A100, RTX 3090, ...)
# TODO: support fractional gpus in MIG mode

# general imports
import os
import xml.etree.ElementTree

# settings
GPU_COUNT = 2

# detailed version ---

# ensure that there may exist only a single class instance
class Singleton(type):
    
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        
        return cls._instances[cls]

class GPUManager(metaclass=Singleton):
    
    def __init__(self):
        """
        Expose available gpus upon request for use within the given kernel,
        avoiding any resource conflicts between multiple users.

        IMPORTANT: Once the deep learning framework has seen the gpus, it
        cannot unsee them - it is therefore necessary to (1) FIRST expose only
        the requested or available gpus, and (2) THEN inform the deep learning
        framework about their existence.
        
        Therefore, before running the GPUManager, restart the kernel and put
        the following lines at the very top of your program ...
        
        from gpu import GPUManager
        gpu_manager = GPUManager()
        gpu_manager.request_gpu(num_requested=1)
        
        Alternatively, you may also use the shorthand version ...
        
        request_gpu(num_requested=1)
        """
        
        # set default visibility, being that all gpus are hidden from the user
        os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
        
        # suppress tf logger
        os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
        
        # status
        self._num_available = None
        self._num_requested = None
        self._num_enabled = 0

    @property
    def num_available(self):
        return self._num_available if self._num_requested else len(self._get_gpu())

    @property
    def num_requested(self):
        return self._num_requested
    
    @property
    def num_enabled(self):
        return self._num_enabled
    
    def request_gpu(self, num_requested=1, type_requested="a100"):
        """
        Handle user request for gpus.
        
        :param num_requested:
            int, the number of gpus requested by the user
        :param type_requested:
            list, gpuid values out of which the request a gpu
        """

        # ...
        assert isinstance(num_requested, int), \
            "(ERROR) num_requested must be an integer value, you provided value {value} with dtype {dtype}".format(
                value=num_requested,
                dtype=type(num_requested),
            )

        # report num_enabled (should request have already been made)
        if self._num_requested:
            print("(INFO) you already received {num_enabled} gpu(s)".format(
                num_enabled=self._num_enabled,
            ))
            return self._num_enabled

        # screen gpu(s) of the given type_requested that are available
        gpuid_list = self._get_gpu(gpuid_list=[])
        num_available = len(gpuid_list)

        # expose min(available, requested) gpu(s) to the requesting user
        if num_requested <= num_available:
            num_enabled = self._set_gpu(gpuid_list[:num_requested])
        # ...
        else:
            num_enabled = self._set_gpu(gpuid_list[:num_available])

        # set attributes only after the request has gone through
        self._num_requested = num_requested
        self._num_enabled = num_enabled
        self._num_available = num_available - num_enabled
        
        # report num_enabled
        print("(INFO) you requested {num_requested} and received {num_enabled} gpu(s)".format(
            num_requested=num_requested,
            num_enabled=num_enabled,
        ))
        return self._num_enabled
    
    def _get_gpu(self, gpuid_list=[]):
        """
        Identify available gpus by parsing the output of the `nvidia-smi -x -q`
        command. To be considered available, a device must be idle, that is,
        the nvidia-smi command must yield values that are not larger than the
        following thresholds ...

        - gpu utilization: 0 %
        - gpu temperature: 30 C
        - memory utilization: 0 %
        - memory usage: 500 MiB
        
        For more details on the `nvidia-smi` command, refer to ...
        https://developer.download.nvidia.com/compute/DCGM/docs/nvidia-smi-367.38.pdf

        :param gpuid_list:
            list, filter results by this list of gpuid numbers, default is []
        """

        # if we provide a gpuid_list, run sanity check
        if gpuid_list:
            assert all(x in range(GPU_COUNT) for x in gpuid_list), \
                "(INFO) gpuid filter contains values outside of the possible range"
        # else, let gpuid_list include all possible gpuid values
        else:
            gpuid_list=list(range(GPU_COUNT))

        # get the entire nvidia-smi command line output as xml_string
        xml_string = os.popen("nvidia-smi -x -q --id={gpuid_string}".format(
            gpuid_string=",".join(map(str, gpuid_list)),
        )).read()
        
        # parse xml_string into xml_parsed
        xml_parsed = xml.etree.ElementTree.fromstring(xml_string)
        gpu_list = xml_parsed.findall("gpu")
        
        # ...
        assert len(gpu_list) == len(gpuid_list)
        
        # ...
        test_list = [
            
            # check utilization.gpu_util, GPU_UTIL_THRESHOLD: 0 %
            lambda gpu: not int(gpu.find("utilization").find("gpu_util")
                .text.split(" ")[0]
            ) > 0,
            
            # check temperature.gpu_temp, GPU_TEMP_THRESHOLD: 30 C
            lambda gpu: not int(gpu.find("temperature").find("gpu_temp")
                .text.split(" ")[0]
            ) > 30,
            
            # check utilization.memory_util, MEM_UTIL_THRESHOLD: 0 %
            lambda gpu: not int(gpu.find("utilization").find("memory_util")
                .text.split(" ")[0]
            ) > 0,
            
            # check fb_memory_usage.used, MEM_USAGE_THRESHOLD: 500 MiB
            lambda gpu: not int(gpu.find("fb_memory_usage").find("used")
                .text.split(" ")[0]
            ) > 500,
        
        ]
        
        # if any test for a gpuid has failed, remove gpuid from gpuid_list
        for gpuid in gpuid_list.copy(): # iterate over copy!
            if not all([test_fun(gpu_list[gpuid]) for test_fun in test_list]):
                gpuid_list.remove(gpuid)
        
        return gpuid_list
    
    def _set_gpu(self, gpuid_list):
        """
        Expose min(num_request, num_available) gpus to the requesting user by
        setting the CUDA_VISIBLE_DEVICES environment variable accordingly.
        Note that this environment variable will be seen only from within the
        given kernel, not across multiple kernels!
        
        :param gpuid_list:
            list, expose gpus corresponding to the listed gpuid numbers
        """

        # set updated visibility, expose only the gpus included in gpuid_list
        gpuid_string = ",".join(map(str, gpuid_list))
        os.environ["CUDA_VISIBLE_DEVICES"] = gpuid_string
        
        # block gpus by loading small tf.constant onto device
        self._block_gpu(gpuid_list)
        
        return len(gpuid_list)
    
    def _block_gpu(self, gpuid_list):
        """
        Block gpus by loading small tf.constant onto each device in gpuid_list.
        This will take 570 MiB on each device.
        
        :param gpuid_list:
            list, block gpus corresponding to the listed gpuid numbers
        """
        
        # import
        import tensorflow as tf
        
        # load small tf.constant onto each device in gpuid_list
        for gpuid in gpuid_list:
            with tf.device(f"/gpu:{gpuid}"):
                _ = tf.constant(42) # will take 570 MiB
    
    @property
    def tensorflow_gpu_count(self):
        """
        Test the number of gpus seen by TensorFlow, this will be possible only
        after a request has been made.
        
        Note that we put the import only within the scope of this method as we
        do not know whether the framework is installed on system.
        """
        
        # import
        from tensorflow.python.client.device_lib import list_local_devices
        
        # expose gpu(s) to the framework, do this only request has been made
        if self._num_requested:
            return len(list_local_devices()) - 1 # do not count cpu
        # ...
        else:
            return None
    
    @property
    def pytorch_gpu_count(self):
        """
        Test the number of gpus seen by PyTorch, this will be possible only
        after a request has been made.
        
        Note that we put the import only within the scope of this method as we
        do not know whether the framework is installed on system.
        """
    
        # import
        from torch.cuda import device_count
    
        # expose gpu(s) to the framework, do this only request has been made
        if self._num_requested:
            return device_count()
        # ...
        else:
            return None
        
    # TODO
    def monitor_gpu(self, gpuid_list):
        """
        Run real-time monitoring of each device in gpuid_list.
        
        :param gpuid_list:
            list, monitor gpus corresponding to the listed gpuid numbers
        """
        
        # ...
        raise NotImplementedError

# shorthand version ---

def request_gpu(num_requested=1):
    """
    Shorthand version for `GPUManager.request_gpu()` that may be used if a
    user does not require more detailed information.
    
    :param num_requested:
        int, number of gpus requested by the user, default is 1
    """
    
    # there can be only a single GPUManager instance (singleton pattern)
    num_enabled = GPUManager().request_gpu(
        num_requested=num_requested,
    )
    
    return num_enabled


