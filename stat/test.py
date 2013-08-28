'''
Created on Jul 31, 2013

@author: openstack
'''
import os

def list_dir(dir):
    os.listdir(dir)
    
list_dir('/opt/stack')