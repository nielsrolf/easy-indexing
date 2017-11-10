import unittest, shutil
import utils
from indexing import *
import pdb

class Content():
	def __init__(self, value=None):
		self.value = value
	def __str__(self): return "v:{}".format(self.value)
	def save(self, export_dir): utils.pickle_single(export_dir, self.value)
	def open(self, import_dir):
		self.value = utils.load_single(import_dir)
		return self
	def __eq__(self, other):
		return self.value==other.value

class SlicerTest(unittest.TestCase):
	def setUp(self):
		slicer = Slicer()

		# Define Schema
		slicer.add_col(name="numerical", col=Column(float))
		slicer.add_col(name="even", col=Column(bool))
		slicer.add_col(name="list_prop", col=Column(range(6)))

		# Test Schema
		self.assertTrue(slicer.numerical() == [])
		self.assertTrue(slicer.even() == [])
		self.assertTrue(slicer.list_prop() == [])
		self.assertTrue(slicer.list_prop.domain == list(range(6)))
		self.slicer = slicer
		#
		#def test_insert_data(self):
		#input("insert data")
		# Lists we want to retrieve as query results
		self.stored = []
		self.below_ten = []
		self.even = []
		self.even_l2 = []
		self.small_or_great = []
		# Insert data
		for lid in slicer.list_prop.domain:
			for nid in range(100):
				elem = Content(nid)
				
				self.stored.append(elem)
				if nid%2==0:
					self.even.append(elem)
				if nid < 10:
					self.below_ten.append(elem)
				if nid <10 or nid==99:
					self.small_or_great.append(elem)
				if nid%2==0 and lid==2:
					self.even_l2.append(elem)

				slicer.add(
					elem,
					numerical=nid,
					even=(nid%2==0),
					list_prop=lid)

	def test_get_all(self, slicer=None):
		if slicer is None: slicer = self.slicer
		self.assertTrue(slicer.get().eval() == self.stored)

	def test_get_even(self, slicer=None):
		if slicer is None: slicer = self.slicer
		self.assertTrue(slicer.get(even=True).eval() == self.even)

	def test_get_and_chained(self, slicer=None):
		if slicer is None: slicer = self.slicer
		self.assertTrue(slicer.get(even=True).get(list_prop=2).eval() == self.even_l2)

	def test_get_and_unchained(self, slicer=None):
		if slicer is None: slicer = self.slicer
		self.assertTrue(slicer.get(even=True, list_prop=2).eval() == self.even_l2)

	def test_get_or(self, slicer=None):
		if slicer is None: slicer = self.slicer
		self.assertTrue(self.small_or_great == slicer.get(numerical=[lambda x: x<10, 99]).eval())

	def test_export_schema(self):
		schema = self.slicer.schema()
		# all colums (names) exist and contain columns of the correct domain
		for col_name, col in self.slicer.cols.items():
			self.assertEqual(col.domain, schema.cols[col_name].domain)

	def test_subscribe_schema(self):
		schema = self.slicer.schema()
		copy = Slicer()
		schema.subscribe(copy)

		for col_name, col in self.slicer.cols.items():
			self.assertEqual(col.domain, copy.cols[col_name].domain)

		schema.add_col("added", Column())
		self.assertEqual(schema.cols["added"].domain, copy.cols["added"].domain)
		try:
			a = self.slicer.cols["added"]
			raise Exception("Column 'added' should not exist in slicer, but does")
		except KeyError: pass

		schema.subscribe(self.slicer)
		self.assertEqual(schema.cols["added"].domain, self.slicer.cols["added"].domain)

	def test_save_open_schema(self):
		self.slicer.save(".temp")
		copy = Slicer().open(".temp", Content)
		for col_name, col in self.slicer.cols.items():
			self.assertEqual(col.domain, copy.cols[col_name].domain)

	def test_save_open_objects(self):
		self.slicer.save(".temp")
		copy = Slicer().open(".temp", Content)
		self.test_get_all(copy)
		self.test_get_even(copy)
		self.test_get_and_chained(copy)
		self.test_get_and_unchained(copy)
		self.test_get_or(copy)

	def tearDown(self):
		shutil.rmtree(".temp", ignore_errors=True)

if __name__ == '__main__':
	unittest.main()


