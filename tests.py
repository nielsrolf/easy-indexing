import unittest
from indexing import *
import pdb

class Content():
	def __init__(self, value):
		self.value = value
	def __str__(self): return "v:{}".format(self.value)

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

	def test_get_all(self):
		self.assertTrue(self.slicer.get().eval() == self.stored)

	def test_get_even(self):
		self.assertTrue(self.slicer.get(even=True).eval() == self.even)

	def test_get_and_chained(self):
		self.assertTrue(self.slicer.get(even=True).get(list_prop=2).eval() == self.even_l2)

	def test_get_and_unchained(self):
		self.assertTrue(self.slicer.get(even=True, list_prop=2).eval() == self.even_l2)

	def test_get_or(self):
		self.assertTrue(self.small_or_great == self.slicer.get(numerical=[lambda x: x<10, 99]).eval())

if __name__ == '__main__':
	unittest.main()


