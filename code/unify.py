import csv
import os
import string

import data
from annot import DocAnnotation
from article_parser import ArticleParser


def generate_bag_of_words(root, output_file='/tmp/debate_sentences.csv'):
    orig_data = os.path.join(root, 'data', 'downloaded')
    corenlp_annot = os.path.join(root, 'data', 'corenlp_annot')
    doc_dir = os.path.join(root, 'data', 'downloaded')
    corenlp = os.path.join(root, 'corenlp')
    ap = ArticleParser(orig_data, corenlp_annot, doc_dir, corenlp, '3.3.1')
    ap.process_all()

    writer = csv.writer(open(output_file, 'w'))
    fields = ['year', 'debate_number', 'doc_id', 'publication', 'byline']
    writer.writerow(fields + ['party', 'text'])

    max_field_size = 30000

    n_unicode_errors = 0
    for doc in ap.docs:
        year, debate, doc_id = [int(doc[x]) for x in 
                                ['year', 'debate_number', 'doc_id']]
        annot = DocAnnotation(corenlp_annot, year, debate, doc_id)
        
        parties = data.candidates[year].keys()
        all_types = parties + ['none', 'multiple']
        sents_by_cand = {x: [] for x in all_types}

        for sent in annot.doc.sents:
            mentions = [party for party in parties 
                        if sent in annot.candidate_mentions[party]]
            # Only sentences that mention exactly one candidate
            if len(mentions) == 0:
                cand = 'none'
            elif len(mentions) == 1:
                cand = mentions[0]
            else:
                cand = 'multiple'
            sents_by_cand[cand].append(sent)

        for cand in all_types:
            as_str = []
            for sent in sents_by_cand[cand]:
                try:
                    as_str.append(str(sent))
                except UnicodeEncodeError:
                    n_unicode_errors += 1

            text = ' '.join(as_str)
            values = [doc.get(field, 'n/a') for field in fields]
            row = values + [cand]
            for i in range(0, len(text), max_field_size):
                row.append(text[i:i+max_field_size])
            writer.writerow(row)

    print '%d Unicode errors' % n_unicode_errors
