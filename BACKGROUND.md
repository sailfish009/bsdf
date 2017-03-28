# Background

This is a quick overview of the history and argumentation for this format.

## History

### SSDF

Around 2011 I developed a
[file format called SSDF](https://bitbucket.org/almarklein/ssdf), suited
for storing hierachical data, similar to JSON, but with support for
`nan` and `inf`. It also supports nd-arrays, via base64 encoding and zlib
compression.

I've used this in several (scientific) projects (e.g. its used in the
[Pyzo IDE](http://github.com/pyzo/pyzo) to store config data. Its dependency
on Numpy was at some point made optional.

Although it does serve its purpose, its not terribly good for large
binary datasets. I also kept coming back in need of a format to send binary
data to/from JS, where compression is a problem.

### BSDF v1

At some point I developed a binary equivalent of SSDF that's fully compatible,
but stored binary data more effectively. Seemed sensible to me at the time,
but now it feels rather silly. It did work pretty well, but I hope that I am
its only user.

### ZON

My later opinion was that a format that is good at binary data can not also be
good at being a human readable config format. Therefore I created
[ZON](https://bitbucket.org/pyzo/pyzolib/src/tip/zon), which is
completely compatible with SSDF, except that it does not support binary data.

### BSDF v2

The current BSDF format is a new approach (not compatible with BSDF v1), which
takes more use-cases into account, yet is simple to implement.


## Other formats

### JSON

JSON did not do it for me:

* No `nan` or `inf`, come on!
* No support for binary data or nd-arrays (base64 is a compromise that I want to avoid).
* It's kind of human readable, but very verbose, and not easy to write
  (e.g. a comma after the last item in a list breaks it).


### Other formats from the JS ecosystem

I've looked at quite a few of them, but none made me happy, for various
reasons. Most seem rather web-oriented. Or adhere strictly to JSON
compat (e.g. no `nan`). None of these seemed to provide the flexibility
needed for the scientific stuff I was looking for.

* [ubjson](http://ubjson.org/) comes closests to my needs, and the format is
  quite similar. Data can actually be stored as typed arrays, but only for
  compact storage; in JS the data is unpacked in arrays again.
* [msgpack](http://msgpack.org/) is quite widely supported. It tries very badly
  to be compact, making it hard to implement, and slower. It does not have
  the support for typed arrays out of the box that we need.
* [bson](http://bsonspec.org/) also seemed very web-oriented.

### HDF5

HDF5 is quite popular, but there are also good reasons to avoid it, as e.g.
explained well in the ASDF paper. A summary:
    
* HDF5 is a complex spec and there is more or less just one
  implementation that actually works.
* The implementation sometimes has bugs or performance issue, but there
  are no alternatives.
* Not human readable, and no other tools for inspection except that one
  implementation.
* No proper mappings (dicts) and lists.

### ASDF

The [ASDF format](http://asdf-standard.readthedocs.io/en/latest/) has
goals that really resonate with me:

* intrinsic hierarchical structure
* human readable
* based on existing data format (yaml)
* support for references (also to external objects)
* efficient updating
* machine independent, structured data, ndarrays
* support for writing (and reading) streams
* explicit versioning
* explicit extensibility without interference
* support for validation with schemas

ASDF seems like a great format, but I did not use it because:
    
* Yaml is a rather ill defined format. I find confusing as a human, but
  it's also hard to parse, which is probably why the parser is so slow.
* I have doubts whether a human readable part inside a file that is
  further binary works well in practive. For inspection, sure. But if
  the text is edited, byte alignments can break.


## Why not a (partly) human readable format?

In SSDF I stored binary data in text via base64 encoding. This might work
for some cases. For many, perhaps. But for some cases you simply cannot
afford the compromise.

A format like ASDF solves the problem. Though editing such files can
be risky (and slow), and it makes the format more complex. Maybe its
worth it, but since ASDF was not suited for my needs, and I seemed to
be rolling something myself, I thought I'd better come up with something
simple, and not too similar to ASDF. I do want to make tooling to make
it easy to create human readable summaries of BSDF file contents.
