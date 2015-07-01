#
# Copyright (c) 2015 nexB Inc. and others. All rights reserved.
# http://nexb.com and https://github.com/nexB/scancode-toolkit/
# The ScanCode software is licensed under the Apache License version 2.0.
# Data generated with ScanCode require an acknowledgment.
# ScanCode is a trademark of nexB Inc.
#
# You may not use this software except in compliance with the License.
# You may obtain a copy of the License at: http://apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#
# When you publish or redistribute any data created with ScanCode or any ScanCode
# derivative work, you must accompany this data with the following acknowledgment:
#
#  Generated with ScanCode and provided on an "AS IS" BASIS, WITHOUT WARRANTIES
#  OR CONDITIONS OF ANY KIND, either express or implied. No content created from
#  ScanCode should be considered or used as legal advice. Consult an Attorney
#  for any legal advice.
#  ScanCode is a free software code scanning tool from nexB Inc. and others.
#  Visit https://github.com/nexB/scancode-toolkit/ for support and download.

from __future__ import absolute_import, print_function


import os
import codecs

from commoncode.testcase import FileBasedTesting

from textcode import analysis
from textcode.analysis import Token
from textcode.analysis import text_lines

from licensedcode import index


class TestIndexBasedDetection(FileBasedTesting):
    test_data_dir = os.path.join(os.path.dirname(__file__), 'data')

    def test_merge_positions(self):
        pos1 = Token(start=58, end=58, start_line=8, start_char=52, end_line=8, end_char=59)
        pos2 = Token(start=63, end=64, start_line=23, start_char=12, end_line=53, end_char=23)
        expected = Token(start=58, end=64, start_line=8, start_char=52, end_line=53, end_char=23)
        tst = index.merge_positions([pos2, pos1])
        assert expected == tst

    def test_merge_aligned_positions(self):
        pos11 = Token(start=58, end=58, start_line=8, start_char=52, end_line=8, end_char=59)
        pos12 = Token(start=63, end=64, start_line=23, start_char=12, end_line=53, end_char=23)

        pos21 = Token(start=12, end=24, start_line=12, start_char=52, end_line=12, end_char=59)
        pos22 = Token(start=15, end=35, start_line=45, start_char=12, end_line=54, end_char=36)

        expected = (
            Token(start=58, end=64, start_line=8, start_char=52, end_line=53, end_char=23),
            Token(start=12, end=35, start_line=12, start_char=52, end_line=54, end_char=36)
        )

        tst = index.merge_aligned_positions([(pos11, pos21,), (pos12, pos22,)])
        assert expected == tst

    def get_test_docs(self, base, subset=None):
        base = self.get_test_loc(base, copy=True)
        for docid in os.listdir(base):
            if (subset and docid in subset) or not subset:
                yield docid, text_lines(location=os.path.join(base, docid))

    def test_Index_index_many_unigrams(self):
        test_docs = self.get_test_docs('index/bsd', ['bsd-new', 'bsd-no-mod'])
        idx = index.Index(ngram_len=1)
        idx._index_many(test_docs)
        unigrams_index = idx.indexes[1]

        assert 212 == idx.get_tokens_count('bsd-new')
        assert 233 == idx.get_tokens_count('bsd-no-mod')
        assert 138 == len(unigrams_index)

        pos = Token(start=61, end=61, start_line=8, start_char=52, end_line=8, end_char=59, value=(u'minimum',))
        expected_posting = ('bsd-no-mod', [pos],)
        assert expected_posting == unigrams_index[('minimum',)].items()[0]

    def test_Index_index_one_unigrams(self):
        test_docs = self.get_test_docs('index/bsd', ['bsd-new', 'bsd-no-mod'])
        idx = index.Index(ngram_len=1)
        for docid, doc in test_docs:
            idx.index_one(docid, doc)
        unigrams_index = idx.indexes[1]

        assert 212 == idx.get_tokens_count('bsd-new')
        assert 233 == idx.get_tokens_count('bsd-no-mod')
        assert 138 == len(unigrams_index)

        pos = Token(start=61, end=61, start_line=8, start_char=52,
                    end_line=8, end_char=59, value=(u'minimum',))
        expected_posting = ('bsd-no-mod', [pos],)
        assert expected_posting == unigrams_index[('minimum',)].items()[0]

    def test_Index_index_one_trigrams_no_templates(self):
        test_docs = self.get_test_docs('index/bsd', ['bsd-new', 'bsd-no-mod'])
        idx = index.Index(ngram_len=3)

        for docid, doc in test_docs:
            idx.index_one(docid, doc)

        indexes = [(idx.indexes[1], 0,),
                   (idx.indexes[2], 0,),
                   (idx.indexes[3], 280,)]
        for idxi, expected_len in indexes:
            assert expected_len == len(idxi)

        assert 212 == idx.get_tokens_count('bsd-new')
        assert 233 == idx.get_tokens_count('bsd-no-mod')

    def test_Index_index_one_trigrams_with_templates(self):
        test_docs = self.get_test_docs('index/bsd_templates2')
        idx = index.Index(ngram_len=3)
        for docid, doc in test_docs:
            idx.index_one(docid, doc, template=True)
        indexes = [
            (idx.indexes[1], 2,),
            (idx.indexes[2], 5,),
            (idx.indexes[3], 267,)
        ]

        for idxi, expected_len in indexes:
            assert expected_len == len(idxi)

        assert 210 == idx.get_tokens_count('bsd-new')
        assert 231 == idx.get_tokens_count('bsd-no-mod')

    def get_test_index(self, docs, ngram_len=3, template=False):
        idx = index.Index(ngram_len)
        idx._index_many(docs, template)
        return idx

    def test_Index_match_simple(self):
        test_docs = self.get_test_docs('index/bsd')
        idx = self.get_test_index(test_docs, ngram_len=1)
        test_doc = self.get_test_loc('index/querysimple')
        expected = {
            'bsd-new':
                [(Token(start=0, start_line=0, start_char=0, end_line=6, end_char=753, end=211),
                  Token(start=0, start_line=4, start_char=0, end_line=12, end_char=607, end=211))
                ],
            'bsd-no-mod':
                [(Token(start=0, start_line=0, start_char=0, end_line=0, end_char=49, end=7),
                  Token(start=0, start_line=4, start_char=0, end_line=4, end_char=49, end=7))
                ],
            'bsd-original':
                [(Token(start=0, start_line=0, start_char=0, end_line=0, end_char=9, end=0),
                  Token(start=29, start_line=6, start_char=59, end_line=6, end_char=68, end=29)
                 ),
                 (Token(start=0, start_line=0, start_char=0, end_line=0, end_char=9, end=0),
                  Token(start=47, start_line=7, start_char=62, end_line=7, end_char=71, end=47)
                 ),
                 (Token(start=0, start_line=0, start_char=0, end_line=0, end_char=9, end=0),
                  Token(start=103, start_line=10, start_char=33, end_line=10, end_char=42, end=103)
                 ),
                 (Token(start=0, start_line=0, start_char=0, end_line=0, end_char=9, end=0),
                  Token(start=137, start_line=12, start_char=117, end_line=12, end_char=126, end=137)
                 )
                ],
            'bsd-original-uc':
                [(Token(start=0, start_line=0, start_char=0, end_line=0, end_char=9, end=0),
                  Token(start=29, start_line=6, start_char=59, end_line=6, end_char=68, end=29)),
                 (Token(start=0, start_line=0, start_char=0, end_line=0, end_char=9, end=0),
                  Token(start=47, start_line=7, start_char=62, end_line=7, end_char=71, end=47)),
                 (Token(start=0, start_line=0, start_char=0, end_line=0, end_char=9, end=0),
                  Token(start=103, start_line=10, start_char=33, end_line=10, end_char=42, end=103)),
                 (Token(start=0, start_line=0, start_char=0, end_line=0, end_char=9, end=0),
                  Token(start=137, start_line=12, start_char=117, end_line=12, end_char=126, end=137))
                ],
            'bsd-simplified':
                [(Token(start=0, start_line=0, start_char=3, end_line=7, end_char=73, end=67),
                  Token(start=0, start_line=4, start_char=0, end_line=7, end_char=207, end=67))
                 ]
        }

        test = dict(idx.match(test_doc, perfect=False))
        for k, val in test.items():
            assert expected[k] == val

    def test_Index_match_unigrams_perfect(self):
        test_docs = self.get_test_docs('index/bsd')
        idx = self.get_test_index(test_docs, ngram_len=1, template=False)
        test_qdoc = self.get_test_loc('index/queryperfect')

        expected = {
            'bsd-new': [
                (Token(start=0, start_line=0, start_char=0, end_line=6, end_char=753, end=212),
                 Token(start=0, start_line=5, start_char=0, end_line=11, end_char=753, end=212))
            ]
        }

        test = dict(idx.match(text_lines(test_qdoc), perfect=True))

        self.assertNotEqual({}, test)
        for k, val in test.items():
            assert expected[k] == val

        with codecs.open(test_qdoc, encoding='utf-8') as td:
            actual = td.read().splitlines(True)
            expected = u''.join(actual[5:-2])[:-2]
            query_match_pos = test['bsd-new'][0][-1]
            tst = analysis.doc_subset(text_lines(location=test_qdoc), query_match_pos)
            tst = u''.join(tst)
            assert expected == tst

    def test_Index_match_ngrams_perfect_minimalist(self):
        idoc = ['name is joker, name is joker']
        idx = index.Index(ngram_len=3)
        idx.index_one('tst', text_lines(idoc), template=False)

        qdoc = ['Hi my name is joker, name is joker yes.']
        expected = {
            'tst': [
                (Token(start=0, start_line=0, start_char=0, end_line=0, end_char=28, end=5),
                 Token(start=2, start_line=0, start_char=6, end_line=0, end_char=34, end=7))
            ]
        }
        test = dict(idx.match(qdoc, perfect=True))

        self.assertNotEqual({}, test)
        for k, val in test.items():
            assert expected[k] == val

    def test_Index_match_ngrams_perfect_single_idoc_in_index_minimal(self):
        test_docs = self.get_test_docs('index/mini')
        idx = self.get_test_index(test_docs, ngram_len=3, template=False)
        test_qdoc = self.get_test_loc('index/queryperfect-mini')

        expected = {
            'bsd-new': [
                (Token(start=0, start_line=0, start_char=0, end_line=0, end_char=94, end=13),
                 Token(start=1, start_line=2, start_char=0, end_line=2, end_char=94, end=14))
            ]
        }
        test = dict(idx.match(text_lines(test_qdoc), perfect=True))

        self.assertNotEqual({}, test)
        for k, val in test.items():
            assert expected[k] == val

    def test_Index_match_ngrams_templates_perfect_minimalist(self):
        idoc = ['name is joker, {{}} name is joker']
        idx = index.Index(ngram_len=3)
        idx.index_one('tst', text_lines(idoc), template=True)

        qdoc = ['Hi my name is joker the joker name is joker yes.']
        expected = {
            'tst': [
                (Token(start=0, start_line=0, start_char=0, end_line=0, end_char=33, end=5),
                 Token(start=2, start_line=0, start_char=6, end_line=0, end_char=43, end=9))
            ]
        }
        test = dict(idx.match(text_lines(qdoc), perfect=True))

        self.assertNotEqual({}, test)
        for k, val in test.items():
            assert expected[k] == val

    def test_Index_match_ngrams_template_perfect_multi_idoc_in_index(self):
        test_docs = self.get_test_docs('index/bsd_templates')
        idx = self.get_test_index(test_docs, ngram_len=3, template=True)
        test_qdoc = self.get_test_loc('index/queryperfect_single_template')

        expected = {
            'bsd-new':[
                 (Token(start=0, start_line=0, start_char=0, end_line=6, end_char=753, end=210),
                  Token(start=4, start_line=5, start_char=0, end_line=11, end_char=753, end=216))
            ]
        }

        test = dict(idx.match(text_lines(test_qdoc), perfect=True))

        self.assertNotEqual({}, test)
        for k, val in test.items():
            assert expected[k] == val