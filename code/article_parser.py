import csv
import os
import re
import subprocess

header_re = re.compile(r'(?P<doc_id>\d+) of (?P<total_docs>\d+) DOCUMENTS\n+')
fields = ['byline', 'section', 'length', 'dateline', 'load-date',
          'language', 'graphic', 'publication-type', 'acc-no',
          'journal-code', 'document-type']
additional_fields = ['year', 'debate_number', 'doc_id', 'publication',
                     'date', 'title', 'text', 'total_docs']


class ArticleParser(object):

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

    def process_all(self):
        for filename in os.listdir(self.docs_dir):
            if filename[0] == '.':
                continue
            base, ext = os.path.splitext(filename)
            year, _, _, debate_number = base.split()
            self.process_file(os.path.join(self.docs_dir, filename), 
                              {'year': year, 'debate_number': debate_number})
