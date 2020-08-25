## NCIt Neoplasm Core files

The NCIt mappings represent the data from the [NCI Thesaurus Neoplasm Core OBO edition](https://github.com/NCI-Thesaurus/thesaurus-obo-edition/wiki/Downloads#neoplasm-core):

* neoplasm-core.owl
  - the source OWL file from the repository
  - processed semi-automatically, by extracting codes & labels of the whole
  Neoplasm tree from root `NCIT:C3262` & saving as separate text files, then
  fusing & exporting using the [pgx_create_NCIT_tree.py](../../bin/pgx_create_NCIT_tree.py)
  script
```
Neoplasm (NCIT:C3262)
	Neoplasm by Site (NCIT:C3263)
		Genitourinary System Neoplasm (NCIT:C156482)
			Benign Genitourinary System Neoplasm (NCIT:C156483)
			...
```
* ncit-neoplasm-tree-codes.txt
  - the "tree indented" codes extracted from the `neoplasm-core.owlneoplasm-core.owl` file
* ncit-neoplasm-tree-labels.txt
  - the labels from the OWL file
* hierarchies.
  - a `__label__ (__code__)`, hierarchically indented file, created by the script
  - uses the format from the original NCIt resource site (but adds the prefix)
* labels.tsv
  - code - tab - label
  - single representation off all individual codes
