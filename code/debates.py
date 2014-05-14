import csv
import os
import re

header_re = re.compile(r'(?P<doc_id>\d+) of (?P<total_docs>\d+) DOCUMENTS\n+')
fields = ['byline', 'section', 'length', 'dateline', 'load-date',
          'language', 'graphic', 'publication-type', 'acc-no',
          'journal-code', 'document-type']
additional_fields = ['year', 'debate_number', 'publication', 'date', 'title',
                     'text']


class ArticleParser(object):

    def __init__(self):
        self.docs = []

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


dirname = os.path.expanduser('~/Dropbox/Debate Coding/data/txt')
def process_all_presidential_debates(dirname):
    ap = ArticleParser()
    for filename in os.listdir(dirname):
        if filename[0] == '.':
            continue
        base, ext = os.path.splitext(filename)
        year, _, _, debate_number = base.split()
        ap.process_file(os.path.join(dirname, filename), 
                        {'year': year, 'debate_number': debate_number})
    return ap
