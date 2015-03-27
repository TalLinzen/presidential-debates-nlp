## Code to run Stanford CoreNLP on LexisNexis data for US presidential debates

Dependencies:

```bash
pip install nltk
pip install pandas
```

Requires nltk 3 and up. Includes a slightly modified version of the Python corenlp package.
Usage:

```python
ap = ArticleParser(os.path.expanduser('~/Dropbox/Debate Coding/data/txt'),
                   os.path.expanduser('~/Dropbox/debates/data/corenlp_annot'),
                   os.path.expanduser('~/Dropbox/debates/data/documents'),
                   os.path.expanduser('~/Dropbox/debates/corenlp'), '3.3.1')
ap.load()
# run the following two lines if CoreNLP hasn't been run yet:
ap.dump_to_dir()
ap.run_corenlp()
ap.final_output(output_filename)
```

