import csv

import pandas as pd
import corenlp

import data

class DocAnnotation(object):

    def __init__(self, d, year, debate, doc_id):
        filename = '%s_%s_%03d.txt.xml' % (year, debate, doc_id)
        self.doc = corenlp.Document(os.path.join(d, filename))
        self.year, self.debate, self.doc_id = year, debate, doc_id
        self.find_candidate_mentions()

    def find_candidate_mentions(self):
        can = data.candidates[self.year]
        self.candidate_mentions = {party: set() for party in data.parties}
        for chain in self.doc.mention_chains:
            for party, name in can.items():
                if any(name in t.lem for t in chain.mention_heads):
                    for t in chain.mention_heads:
                        self.candidate_mentions[party].add(t.sent)

    def sentences_csv_file(self, output_file, empty=False):
        with open(output_file, 'w') as handle:
            writer = csv.writer(handle)
            writer.writerow(['id', 'sentence', 'dem', 'rep', 'other'])
            for sent_id, sent in enumerate(self.doc.sents):
                mentions = [('X' if not empty and
                             sent in self.candidate_mentions[party] else '')
                            for party in parties]
                writer.writerow([str(sent_id), str(sent)] + mentions)


def create_sentence_annot_files(d):
    f = open(os.path.join(d, 'sent_annot', 'doc_list.csv'), 'rU')
    reader = csv.DictReader(f)
    for rec in reader:
        try:
            doc = DocAnnotation(os.path.join(d, 'corenlp_annot'),
                                int(rec['year']), int(rec['debate']),
                                int(rec['doc_id']))
        except IOError, exc:
            print exc
            continue
        filename = '%s_%s_%03d' % (rec['year'], rec['debate'],
                                   int(rec['doc_id']))
        out_filename = os.path.join(d, 'sent_annot', filename + '.csv')
        doc.sentences_csv_file(out_filename)


def compare_all_annot_to_hand(d):
    f = open(os.path.join(d, 'sent_annot', 'doc_list.csv'), 'rU')
    reader = csv.DictReader(f)
    dicts = []
    for rec in reader:
        doc = DocAnnotation(os.path.join(d, 'corenlp_annot'),
                            int(rec['year']), int(rec['debate']),
                            int(rec['doc_id']))
        filename = '%s_%s_%03d.final.csv' % (rec['year'], rec['debate'], 
                                             int(rec['doc_id']))
        filename = os.path.join(d, 'hand_annot', filename)
        try:
            hand_annot = list(csv.DictReader(open(filename, 'rU')))
        except IOError, exc:
            print exc
            continue

        assert len(doc.doc.sents) == len(hand_annot)
        for nlp_sent, hand_sent in zip(doc.doc.sents, hand_annot):
            shared = dict(year=rec['year'],
                          debate=rec['debate'],
                          doc_id=rec['doc_id'],
                          sentence=hand_sent['sentence'],
                          id=hand_sent['id'])
            for party in data.parties:
                dic = shared.copy()
                dic['party'] = party
                nlp = 'T' if nlp_sent in doc.candidate_mentions[party] else 'F'
                dic['nlp'] = nlp
                dic['hand'] = hand_sent.get(party, 'N/A')
                dicts.append(dic)

    columns = ['year', 'debate', 'doc_id', 'id', 'party', 'nlp', 'sentence']
    return pd.DataFrame.from_records(dicts, columns=columns)
