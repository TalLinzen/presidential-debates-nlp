import csv

import corenlp

class DocAnnotation(object):

    def __init__(self, filename):
        self.doc = corenlp.Document(filename)

    def sentences_csv_file(self, output_file):
        with open(output_file, 'w') as handle:
            writer = csv.writer(handle)
            writer.writerow(['id', 'sentence', 'dem', 'rep'])
            for sent_id, sent in enumerate(self.doc.sents):
                writer.writerow([str(sent_id), str(sent), '', ''])

def create_sentence_annot_files(d):
    f = open(os.path.join(d, 'sent_annot', 'doc_list.csv'))
    reader = csv.DictReader(f)
    for rec in reader:
        filename = '%s_%s_%03d' % (rec['year'], rec['debate'], 
                                   int(rec['doc_id']))
        try:
            doc = DocAnnotation(os.path.join(d, 'corenlp_annot', 
                                             filename + '.txt.xml'))
        except IOError, exc:
            print exc
            continue
        out_filename = os.path.join(d, 'sent_annot', filename + '.csv')
        doc.sentences_csv_file(out_filename)

