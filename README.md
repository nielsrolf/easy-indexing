# Organize your data

When I wrote my bachelor thesis, I generated a lot of data that I needed to analyse, and it all got a huge mess.
It got a mess because all the different data was associated with partly the same, partly different attributes, and I needed to aggregate data with certain attributes, and did so by transofrming Python dicts in a not too systematic way. I don't want to loose time because of this again, and try to create a structured way to store, query and aggregate my data.

This shall be achieved by using a somewhat SQL like way to make queries, where each "line of a table" is an arbitrary object, and the queryable table schema is stored apart from the data.

Compared to SQL, this thing has the following differences:
- tables can be created dynamically
- stores objects that are in RAM already
- queries are for meta attributes of objects rather than object properties themselves
- queries are not evaulated in a perfomance optimized way, it is only thought for a more convenient data access

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

# What comes next
I want to add:
- retrieve all meta data for an object
- Import, export
- Set operations

If someone wants to use this too, it makes me so happy that I will try to add the features you need :)