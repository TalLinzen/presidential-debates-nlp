import csv
import os
import re
import subprocess

import data
from annot import DocAnnotation

header_re = re.compile(r'(?P<doc_id>\d+) of (?P<total_docs>\d+) DOCUMENTS[\r\n]+')
fields = ['byline', 'section', 'length', 'dateline', 'load-date',
          'language', 'graphic', 'publication-type', 'acc-no',
          'journal-code', 'document-type']
additional_fields = ['year', 'debate_number', 'doc_id', 'publication',
                     'date', 'title', 'text', 'total_docs']


class ArticleParser(object):
    '''
    ap = ArticleParser(os.path.expanduser('~/Dropbox/Debate Coding/data/txt'),
                       os.path.expanduser('~/Dropbox/debates/data/corenlp_annot'),
                       os.path.expanduser('~/Dropbox/debates/data/documents'),
                       os.path.expanduser('~/Dropbox/debates/corenlp'), '3.3.1')
    ap.load()
    if CoreNLP hasn't been run yet:
        ap.dump_to_dir()
        ap.run_corenlp()
    ap.final_output(output_filename)
    '''

    def __init__(self, docs_dir, annotations_dir, doc_text_dir,
                 corenlp_dir, corenlp_version):
        self.docs = []
        self.docs_dir = docs_dir
        self.annotations_dir = annotations_dir
        self.doc_text_dir = doc_text_dir
        self.corenlp_dir = corenlp_dir
        self.corenlp_version = corenlp_version

    def process_body(self, body):
        doc = {}
        body = body.replace('\r\n', '\n')
        sections = body.split('\n\n')
        doc['publication'] = sections[0]
        doc['date'] = sections[1]
        doc['title'] = sections[2]

        text_candidates = []
        for section in sections[3:]:
            colon_split = section.split(':', 1)
            if len(colon_split) > 1 and colon_split[0].lower() in fields:
                doc[colon_split[0].lower()] = colon_split[1].strip()
            else:
                text_candidates.append(section)

        max_len = max(len(x) for x in text_candidates)
        doc['text'] = [x for x in text_candidates if len(x) == max_len][0]

        return doc

    def post_process_doc(self, doc):
        '''
        Hack to fix inconsistencies in presidential debate date
        '''
        if re.search(r'\d{4}', doc['date']) is None:
            doc['date'], doc['title'] = doc['title'], doc['date']

    def process_file(self, filename, metadata={}):
        raw = open(filename).read()
        matches = re.split(header_re, raw)[1:]
        assert len(matches) % 3 == 0
        for i in range(0, len(matches), 3): 
            doc = metadata.copy()
            doc['doc_id'], doc['total_docs'], body = matches[i:i+3]
            doc.update(self.process_body(body))
            self.post_process_doc(doc)
            self.docs.append(doc)

    def dump_to_dir(self):
        '''
        Dump all files one by one 
        '''
        if not os.path.exists(self.doc_text_dir):
            os.mkdir(self.doc_text_dir)

        filenames = []
        for doc in self.docs:
            filename = '%s_%s_%03d.txt' % (doc['year'], doc['debate_number'],
                                           int(doc['doc_id']))
            full_filename = os.path.join(self.doc_text_dir, filename)
            filenames.append(full_filename)
            with open(full_filename, 'w') as handle:
                handle.write(doc['text'])

        file_list_name = os.path.join(self.doc_text_dir, 'file_list.txt')
        with open(file_list_name, 'w') as handle:
            handle.write('\n'.join(filenames))

    def run_corenlp(self):
        '''
        dirname: path to temporary files created by dump_to_dir.
        corenlpdir: path to Stanford CoreNLP.
        '''
        if not os.path.exists(self.annotations_dir):
            os.mkdir(self.annotations_dir)

        file_list = os.path.join(self.doc_text_dir, 'file_list.txt')
        cwd = os.getcwd()
        os.chdir(self.corenlp_dir)

        try:
            command = 'java -cp stanford-corenlp-%s.jar:stanford-corenlp-%s-models.jar:xom.jar:joda-time.jar:jollyday.jar:ejml-0.23.jari -Xmx2g edu.stanford.nlp.pipeline.StanfordCoreNLP -annotators tokenize,ssplit,pos,lemma,ner,parse,dcoref -filelist %s -outputDirectory %s' % (self.corenlp_version, self.corenlp_version, file_list, self.annotations_dir)
            subprocess.call(command.split())
        finally:
            os.chdir(cwd)

    def alldoc_csv(self, filename='/tmp/tmp.csv'):
        '''
        Create a CSV file with all doc metadata and 100 first characters of 
        each document
        '''
        writer = csv.writer(open(filename, 'w'))
        all_fields = additional_fields + fields
        writer.writerow(all_fields)
        for doc in self.docs:
            writer.writerow([doc.get(field, '')[:100] for field in all_fields])

    def load(self):
        for filename in os.listdir(self.docs_dir):
            if filename[0] == '.':
                continue
            base, ext = os.path.splitext(filename)
            year, _, _, debate_number = base.split()
            self.process_file(os.path.join(self.docs_dir, filename), 
                              {'year': year, 'debate_number': debate_number})

    def final_output(self, output_file='/tmp/debate_sentences.csv'):
        writer = csv.writer(open(output_file, 'w'))
        fields = ['year', 'debate_number', 'doc_id', 'publication', 'byline']
        writer.writerow(fields + ['party', 'text'])

        max_field_size = 30000

        n_unicode_errors = 0
        for doc in self.docs:
            year, debate, doc_id = [int(doc[x]) for x in 
                                    ['year', 'debate_number', 'doc_id']]
            annot = DocAnnotation(self.annotations_dir, year, debate, doc_id)
            
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
