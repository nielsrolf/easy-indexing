# What's this?
This provides a data structure called `Slicer` that let's you store data with some meta data, and then query for that meta data. It also allows to save and load the data, and use common schemas for different `Slicer`s.
Features:
- Store data in a Slicer
- Define the meta data schema for a slicer
- Define dependencies between the schema of different slicers
- Query for subsets of the data
- Retrieve all meta data for an object
- Iterate over query results and the meta data
- Save and load slicers, including the schema and the data

# Installation
Right now, there is no clean way to install only this module because it uses another self written module which is not included here. Instead, my whole Python setup must be installed, which can be found in another repo of mine. I will soon provide a more convenient an clean way to install this cia pip.

-----------------------------------------------------------

# What comes next
I want to add:
- add metadata for existing objects if default is provided
- Set operations (union, distinct, ...)

If someone wants to use this too, it makes me so happy that I will try to add the features you need :)

# Notes
- When exporting/importing: the domain of a column must support dumping, and export+import should be hash invariant (after ex- and import, the attributes must be recognized)

-----------------------------------------------------------

# Organize your data

When I wrote my bachelor thesis, I generated a lot of data that I needed to analyse, and it all got a huge mess.
It got a mess because all the different data was associated with partly the same, partly different attributes, and I needed to aggregate data with certain attributes, and did so by transofrming Python dicts in a not too systematic way. I don't want to loose time because of this again, and try to create a structured way to store, query and aggregate my data.

This shall be achieved by using a somewhat SQL like way to make queries, where each "line of a table" is an arbitrary object, and the queryable table schema is stored apart from the data.

Compared to SQL, this thing has the following differences:
- tables can be created dynamically
- stores objects that are in RAM already
- queries are for meta attributes of objects rather than object properties themselves
- queries are not evaulated in a perfomance optimized way, it is only thought for a more convenient data access

# Example Code
To get an idea what this is for, a look on some sample code might help. If it doesn't help, just ignore itm it is explained later

```Python
def get_slicer():
	# create two slicers to store the results, which use a shared schema
	try:
		accuracies = Slicer().open(experiment_id+"/results/accuracies")
	except Slicer.NotFound:
		accuracies = Slicer()
		accuracies.add_col("sample_size", Column())
		accuracies.add_col("teacher", Column(["mlp", "cnn"], default=lambda config: config["a_name"]))
		accuracies.add_col("students", Column(["mlp", "cnn"], default=lambda config: config["a_name"]))
		accuracies.add_col("teach_method", Column(["zbab", "deeptaylor"]))

	schema = accuracies.schema()
	schema.subscribe(accuracies) # make sure future changes on schema will by synced with accuracies

	try:
		activations = Slicer().open(experiment_id+"/results/accuracies")
	except Slicer.NotFound:
		activations = Slicer()
	schema.subscribe(activations) # bind this slicer to the same schema

	return schema, accuracies, activations

def train_students(teacher):
	...

	schema, accuracies, activations = get_slicer()

	# generate some data to store
	for sample_size in [10, 40, 160, 640, 2560, 10000]:
		for student_id in range(5):
			...
			test_acc = student.nn.sess.run(student.nn.accuracy, feed_dict=student_data.test_dict())
			accuracies.add(
				test_acc,
				sample_size=sample_size,
				teacher=teacher_config,
				students=student_config,
				teach_method=teach_method
				)
		
	accuracies.save(experiment_id+"/results/accuracies")
```

# Test
`python -m unittest -v test`

# Example use case
Assume you profile pictures in a normalized size, and the following meta data: sex, age, origin country, color of hair
If the objects and thair attributes are stored in a slicer, it is very easy to caluclate the mean or variance images of:
- German and English women who are older than 20 years
- black hair colored children
- black or brown hair colored men
- ...

# Data structures
## ObjectSlicer
The root data structure:
- has the schema: mapping from names to column objects
- can store objects
- is queryable, and returns a slice

## Slice
- Comes from a slicer
- Lazy evaluation subset of the objects of its slicer
- Can be chained

## Column
- describes a meta attribute of an object
- has a domain: numerical, string or list
- keeps track of what party of the domain are actually filled, with the `.__call__()` method
- column instances will be called property
- the value of an property will be called attribute

# Making queries
A slicer or a slice can be queried, returning a new slice. Slices can be evaluated to a list of values.
A slice is a definition of a subset of the slicer that the slice belongs to.
The subset definition uses the columns of the root slicer: the basic elements are:
- property = value -> only objects, where obj.attribute=value
- property = func(attribute) -> only object, where func(attribute) == True
- property = [val1, val2] -> only  objects, where obj.attribute is one of property=val1, property=val2 evaluate to True
## AND
`slicer.get(property1=v1, property2=v2)`: for different columns
- chaining `slicer.get(property1=[v1, w1]).get(property2=v2).get(property1=[v1, u1])`: for different or the same properties
## OR
Can be realized by `slicer.get(property1=[v1, w1])`: it's like (`property1=v1 OR property1=w1`)

