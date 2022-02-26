# !/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Jonas De Paolis"
__version__ = "2022-02-26"

# general imports
import sys

# singleton pattern
class Singleton(type):
    
    _instances = {}
    
    def __call__(cls, *args, **kwargs):

        # only if there does not exist a class instance, create a new one
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)

        return cls._instances[cls]

# detailed version ---

class Logger(metaclass=Singleton):
    
    def __init__(self):
        """
        Redirect sys.stdout to a text file while maintaining the regular output.
        
        :param file_path:
            str, path to text file
        """
        
        # ...
        self.is_attached = False

    def attach(self, file_path):
        """
        Attach logger.
        """
        
        # ...
        if self.is_attached:
            print("(INFO) logger is attached already"); return
        
        # link sys.stdout to self.terminal (attach), open self.file
        self.terminal = sys.stdout
        self.file = open(file_path, "a+")

        # sys.stdout is redirected to self
        sys.stdout = self
        
        # ...
        print("(INFO) logger has been attached")
        self.is_attached = True
    
    def detach(self):
        """
        Detach logger.
        """
        
        # ...
        if not self.is_attached:
            print("(INFO) logger is detached already"); return
        
        # link self.terminal to sys.stdout (detach), close self.file
        sys.stdout = self.terminal
        self.file.close()
        
        # ...
        print("(INFO) logger has been detached")
        self.is_attached = False
        
    def write(self, message):
        """
        Write message to both channels.
        """
        
        # write each message to both output channels
        self.terminal.write(message)
        self.file.write(message)

    def flush(self):
        """
        Required only for compatibility reasons.
        """
        
        # ...
        pass

# shorthand version ---
    
def attach_logger(file_path):
    """
    Start logger.
    
    :param file_path:
        str, path to text file
    """
    
    Logger().attach(file_path)

def detach_logger():
    """
    Stop logger.
    """
    
    # file_path does not matter
    Logger().detach()


