import threading
from errors import *
import pdb


class Column():
	def __init__(self, domain, default=None):
		"""
		adds a column to the schema
		if objects are stored already and no default is provided, this raises an Error
		domain: int/float/str/list of possible values
		default: function that maps a stored element to its meta attribute. If objects are added to a slicer, all columns which do not have a default must be specified
		"""
		self.attributes = {} # obj_id -> attribute
		self.default = default
		try:
			self.domain = [attribute for attribute in domain]
		except:
			self.domain = domain

	def validate_attribute(self, attribute):
		if isinstance(self.domain, list):
			if not attribute in domain:
				raise ValidatorError()

		if not isinstance(attribute, self.domain):
			raise ValidatorError()


	def add(self, obj, obj_id, attribute):
		if attribute is None:
			if self.default is None:
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

		return self.attributes[obj_id] == val

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

	def union(self, other):
		pass

	def unique(self):
		pass


class Slicer():
	# store objects, tag them, query all objects with certain tagged values
	def __init__(self, validator=lambda obj:True):
		self.validator = validator # validator: a function that takes an object, can be used to simulate strong typing (lamba obj: isinstance(obj, int))
		
		self.cols = {}
		self.add_col_lock = threading.Lock()

		self.data = [] # data will contain objects or Nones (deleted objects), Nones will be sorted out by eval()
		self.add_obj_lock = threading.Lock()

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
	@staticmethod
	def import_schema():
		pass

	def export_schema():
		pass

	def export_slice():
		pass

	def import_slice():
		pass

