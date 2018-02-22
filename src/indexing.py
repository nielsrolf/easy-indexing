import threading, os
from .errors import *
import utils
import pdb
import pprint


class Column():
	def __init__(self, domain=None, default=lambda obj:None, name="Column"):
		"""
		adds a column to the schema
		if objects are stored already and no default is provided, this raises an Error
		domain: int/float/str/list of possible values; None for all
		default: function that maps a stored element to its meta attribute. If objects are added to a slicer, all columns which do not have a default must be specified
		"""
		self.attributes = {} # obj_id -> attribute
		self.default = default
		try:
			self.domain = [attribute for attribute in domain]
		except:
			self.domain = domain

	def copy(self):
		# copies schema, not content
		return Column(domain=self.domain, default=self.default)

	def validate_attribute(self, attribute):
		if self.domain is None: return

		if isinstance(self.domain, list):
			if not attribute in domain:
				raise ValidatorError()

		if not isinstance(attribute, self.domain):
			raise ValidatorError()

	def add(self, obj, obj_id, attribute):
		if attribute is None:
			if self.default is not None:
				attribute = self.default(obj)
			else:
				raise PropertyError("{} has no default, and but {} is tried to be stored without a value".format(type(self), obj))
		self.attributes[obj_id] = attribute

	def check(self, obj_id, val):
		# check if ob_id has attribut val, val evals to True or one element of val evals to true
		if isinstance(val, list):
			for v in val:
				if self.check(obj_id, v): return True
			return False

		if callable(val):
			try:
				assert(val(self.attributes[obj_id])==True)
				return True
			except AssertionError:
				return False

		default = None if val is not None else 1
		return self.attributes.get(obj_id, default) == val

	def save(self, export_dir): # save column type
		utils.mkdir(export_dir)
		utils.pickle_single(export_dir+"/domain", self.domain)

	def open(self, import_dir):
		self.domain = utils.load_single(import_dir+"/domain")
		return self

	def save_metadata(self, export_dir): # save metadata of stored objects
		utils.mkdir(export_dir)
		utils.pickle_single(export_dir+"/metadata", self.attributes)

	def open_metadata(self, import_dir):
		self.attributes = utils.load_single(import_dir+"/metadata")
		return self

	def __call__(self):
		# return domain list, i.e. list of all existing entries
		return list(self.attributes.values())

class Slice():
	def __init__(self,
		parent,
		slicer,
		**properties):

		self.properties = properties
		self.parent = parent
		self.slicer = slicer

	def get(self,  **properties):
		# returns slice
		# the values of properties can either be items or lists
		# it shall be possible to query like this: slicer.get(col1=v1).get(col2=v2).get(col3=v3, col4=v4).eval()
		return Slice(parent=self,
			slicer=self.slicer,
			**properties)

	def check_obj(self, obj_id, obj):
		for col_name, val in self.properties.items():
			if not self.slicer.cols[col_name].check(obj_id, val):
				return False
		return True

	def all(self):
		# returns a obj_id->obj dict
		super_set = self.parent.all()
		return [item for item in super_set if self.check_obj(*item)]

	def eval(self):
		# returns a list
		return [obj for obj_id, obj in self.all()]

	def serialize(self, serialize_obj=True):
		self.ids = [obj_id for obj_id, obj in self.all()]
		return [self.slicer.get_obj_meta(id, serialize_obj) for id in self.ids]

	def first(self):
		return self.all()[0][1] # [1] because all[0] -> obj_id, obj

	def only(self):
		entries = self.all()
		assert len(entries)==1, "Slice has more than one entry: properties: {} \n Entries: {}".format(self.properties, self.serialize())
		return entries[0][1]

	def union(self, other):
		pass

	def unique(self):
		pass

	def __iter__(self):
		return SliceIterator(self)

class SliceIterator():
	def __init__(self, s):
		self.slice = s
		self.iter_id = -1
		self.iter_items = s.all()

	def __iter__(self):
		return self

	def __next__(self):
		self.iter_id += 1
		try:
			obj_id, obj = self.iter_items[self.iter_id]
		except IndexError:
			raise StopIteration()
		return self.slice.slicer.get_obj_meta(obj_id, False)["meta"], obj


class Schema():
	# this class is used to transfer and share schemas between different Slicers
	def __init__(self, cols):
		self.cols = {col_name: cols[col_name].copy() for col_name in cols}
		self.subscriptions = []
		self.add_col_lock = threading.Lock()

	def subscribe(self, *slicers):
		# adds copies of added columns to all subscribed slicers, does not copy columns from slicers to this

		for slicer in slicers:
			self.subscriptions.append(slicer)
			for col_name, col in self.cols.items():
				if col_name in slicer.cols:
					if slicer.cols[col_name].domain == col.domain: continue
					else: raise Exception("schema got a new subscription, but slicer column '{}' doesn't match schema column '{}'".format(col_name, col_name))
				slicer.add_col(col_name, col.copy())

	def add_col(self, name, col):
		with self.add_col_lock:
			if name in self.cols:
				raise Exception("Column {} already exists".format(name))
			self.cols[name] = col
			self.__dict__[name] = col

		for sub in self.subscriptions:
			sub.add_col(name, col.copy())

	def save(self, export_dir):
		utils.mkdir(export_dir)
		for col_name, col in self.cols.items():
			col.save(export_dir+"/"+col_name)

	def open(self, import_dir):
		for col_name in os.listdir(import_dir):
			self.cols[col_name] = Column().open(import_dir+"/"+col_name)
		return self

class Slicer():
	# store objects, tag them, query all objects with certain tagged values
	def __init__(self, cols = None, validator=lambda obj:True):
		self.validator = validator # validator: a function that takes an object, can be used to simulate strong typing (lamba obj: isinstance(obj, int))
		
		self.cols = cols if cols is not None else {}
		self.add_col_lock = threading.Lock()

		self.data = [] # data will contain objects or Nones (deleted objects), Nones will be sorted out by eval()
		self.add_obj_lock = threading.Lock()

		self.pp = pprint.PrettyPrinter(indent=4).pprint

	def col(self, name):
		return self.cols[self.col_names[name]]

	# Schema API
	def add_col(self, name, col):
		with self.add_col_lock:
			if name in self.cols:
				raise Exception("Column {} already exists".format(name))
			self.cols[name] = col
			self.__dict__[name] = col
		
	# Storage and query API

	def add(self, obj, **properties):
		# properties: lict of colname -> colvalue
		try:
			assert(self.validator(obj)==True)
		except:
			raise ValidatorError()

		with self.add_obj_lock:
			obj_id = len(self.data)
			self.data.append(obj)
		try:
			for col_name, col in self.cols.items():
				col.add(obj, obj_id, properties.get(col_name, None))
		except Exception as e: # something went wrong when inserting obj, delete it
			self.data[obj_id] = None
			raise e

	def get_obj_meta(self, id, serialize_obj=True):
		meta = {"id": id,
			"meta": {col_name: self.cols[col_name].attributes.get(id, None) for col_name in self.cols}
		}
		if serialize_obj:
			meta["obj"] = self.data[id]
		return meta

	def serialize(self, serialize_obj=True):
		return [self.get_obj_meta(id, serialize_obj) for id in range(len(self.data))]

	def inspect(self, serialize_obj=True):
		self.pp(self.serialize(serialize_obj))

	def all(self):
		return [(obj_id, obj) for obj_id, obj in zip(range(len(self.data)), self.data)]

	def get(self, **properties):
		return Slice(parent=self,
			slicer=self,
			**properties)

	def merge(self, other):
		# permanently import all objects from other
		pass

	def clean(self):
		# permanently delete multiple occuerncies
		pass

	# Export / Import
	def schema(self): # export schema
		# returns a schema_object, which has a .save(export_dir)
		return Schema(self.cols)

	# import schema: schema.subscribe(self)

	def save(self, export_dir):
		"""
		Saves like this:
		export_path
			/schema : schema files
			/meta
				/:column name
					column.attributes
			/objects
				/:object_id : object files
		If the stored objects have a .save(), this will be used, otherwise uses utils.pickle_alot
		"""
		utils.mkdir(export_dir)
		self.schema().save(export_dir+"/schema")

		for col_name, col in self.cols.items():
			col.save_metadata(export_dir+"/meta/"+col_name)

		for obj_id, obj in enumerate(self.data):
			try:
				obj.save(export_dir+"/objects/"+str(obj_id))
			except AttributeError:
				utils.pickle_single(export_dir+"/objects/"+str(obj_id), obj)

	def open(self, import_dir, ObjClass=None):
		self.schema().open(import_dir+"/schema").subscribe(self)

		for col_name, col in self.cols.items():
			col.open_metadata(import_dir+"/meta/"+col_name)

		obj_id = 0
		while True:
			try: # if there is another unloaded object
				if ObjClass is None:
					self.data.append(
						utils.load_single(import_dir+"/objects/"+str(obj_id)))
				else:
					obj = ObjClass()
					obj.open((import_dir+"/objects/"+str(obj_id)))
					self.data.append(obj)

				obj_id += 1
			except FileNotFoundError: break
		return self

	def __iter__(self):
		return self.get().__iter__()
