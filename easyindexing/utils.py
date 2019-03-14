import collections
import numpy as np
import math
import pickle
import os

def mkdir(directory):
	if not os.path.exists(directory):
		os.makedirs(directory)


# -------------------------------------
# save and restore
# -------------------------------------

def pickle_name(export_dir, key): # pickle riiiick
	return "{}/{}.pkl".format(export_dir, key)

def pickle_single(export_dir, data):
	mkdir(export_dir)
	with open(export_dir+"/obj.pkl", 'wb') as f:
		pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
	return data

def load_single(import_dir, data=None): # data is ignored, but i dont know what breaks if i remove it
	with open(import_dir+"/obj.pkl", 'rb') as f:
		obj = pickle.load(f)
	return obj

