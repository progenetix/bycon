## LinkML Schema

#### Requirements

```
pip3 install linkml
```

#### Procedure

The LinkML schemas first have to be converted into their JSON Schema representation by running e.g.

```
gen-json-schema Publication.yaml > Publication.json
```

The read & instantiate then is slightly different from the normal schema processing, e.g.:

```
pub_p = path.join( pkg_path, "schemas", "ProgenetixLinkML", "Publication.json#/$defs/Publication/properties")
root_def = RefDict(pub_p)
exclude_keys = [ "format", "examples", "_id" ]
e_p_s = materialize(root_def, exclude_keys = exclude_keys)
```

