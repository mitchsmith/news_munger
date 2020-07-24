import sys
import os
import re
import random
import datetime
import time
import json
import spacy
import lemminflect
from spacy.lang.en import English
from spacy.tokens import Doc, Span, Token
from spacy.matcher import Matcher
from collections import deque
from itertools import islice
nlp = spacy.load("en_core_web_md")

try:
    Doc.set_extension("title", default=None)
    Doc.set_extension("byline", default=None)
    Doc.set_extension("timestamp", default=None)
    Doc.set_extension("dateline", default=None)
    Doc.set_extension("people", default=None)
except ValueError:
    # Reloading pickled
    pass


def find_mungeable_sentences(documents):
    # Fetch all sentence roots
    s_roots = []
    [s_roots.extend([s.root for s in d.sents]) for d in catalog.documents]
    # list all lemmas occurring more than once as sentence roots
    root_lemmas = find_duplicates([r.lemma_ for r in s_roots])
    # locate sentences with identical root lemmas by document and sentence index
    sentences = {k:[] for k in root_lemmas}
    for i, d in enumerate(catalog.documents):
        for j, s in enumerate(d.sents):
            if s.root.lemma_ in root_lemmas:
                sentences[s.root.lemma_].append((i, j))
    return sentences

   


"""
say_swaps = {}
for tup in sentences['say']:
    sent = next(islice(catalog.documents[tup[0]].sents, tup[1], None))
    root = sent.root
    k = tuple([c.dep_ for c in root.children])
    if k in say_swappable:
        try:    
            say_swaps[k].append(tup)
        except KeyError:
            say_swaps[k] = [tup]

for k in say_swaps.keys():
    for d, s in say_swaps[k]:
        sent = next(islice(catalog.documents[d].sents, s, None))
        print(sent.text_with_ws)
        print([c.orth_ for c in sent.root.children])
    print("\n")
    


# print the available sentences

for lemma in sentences.keys():
    print(lemma)
    for tup in sentences[lemma]:
        print(next(islice(catalog.documents[tup[0]].sents, tup[1], None)))
    print("\n***\n")

# split, swap and rejoin on root the first 2 sents

for lemma in sentences.keys():
    print(lemma)
    swaps = []
    for tup in sentences[lemma][:3]:
        swaps.append(next(islice(catalog.documents[tup[0]].sents, tup[1], None)))

    print(
            "".join([
                    swaps[0][:swaps[0].root.i - swaps[0].start + 1].text_with_ws,
                    swaps[1][swaps[1].root.i - swaps[1].start + 1:].text_with_ws
                    ])
           )
    print(
            "".join([
                    swaps[1][:swaps[1].root.i - swaps[1].start + 1].text_with_ws,
                    swaps[0][swaps[0].root.i - swaps[0].start + 1:].text_with_ws
                    ])
            )
    print([c for c in swaps[0].root.children])
    print([c for c in swaps[1].root.children])

    print("\n***\n")


# get the list of tokens that make up a child's subtree
[t for t in [c for c in next(islice(catalog.documents[5].sents, 27, None)).root.children][3
].subtree]







# Don't include s inital, punct or proper nouns
def approved_pivots(t):
    return [
        p
        for p
        in t
        if p.dep_ != "punct"
        and p.pos_ != "PROPN"
        and not p.is_sent_start
        ]

roots = {k:[] for k in (s.root.lemma_ for s in catalog.documents[11].sents)}
{k:roots[k].extend(list(v)) for (k,v) in ((s.root.lemma_, s.root.children) for s in catalog
.documents[11].sents)}
roots

[
    approved_pivots(s.root.children)
    for s
    in catalog.documents[11].sents
    if len(approved_pivots(s.root.children)) > 1
]

"""

class Corpse():
    
    """ """

    def __init__(self, catalog, *args, **kwargs):
        self.catalog = catalog
        self.sentences = []
        self.fragments = []
        self.used = []
        self.title = None
        self.topic_sentence = None
        self.current_focus = None
        self.current_doc_index = None
        self.current_sentence = None
        self.current_pivot = None

    
    def begin(self):

        """
        select the first inital sentence containg the focus (Person)
        entity, or selct the shortest topic sentence.
        """
        self.fragments = []
        sentences = []
        pivots = []
        used = None
        self.current_focus = sorted(
                self.catalog.people,
                key=lambda p: len(p.appears_in),
                reverse=True
                )[0]
        print(self.current_focus)
        
        for d_tup in (
                    (n, self.catalog.documents[n])
                    for n
                    in self.current_focus.appears_in
                    if (n, 1) not in (t[:2] for t in self.used)
                    ):
            sentences.append((d_tup[0], 1, next(islice(d_tup[1].sents, 1)).as_doc()))

        self.topic_sentence = sentences[random.randrange(len(sentences))]
        self.current_sentence = self.topic_sentence
        self.current_doc_index = self.topic_sentence[0]
        pivots = self.find_pivots()
        print("Pivots: {}".format(pivots))
        if not pivots:
            #self.used.append(self.current_sentence)
            print("No usable pivots: Beginning again . . .")
            self.begin()
        else:
            self.complete_next_sentence(pivots)


    def find_pivots(self):
        return [
                c 
                for
                c
                in next(islice(self.current_sentence[2].sents, 0, None)).root.children
                if c.dep_ != "punct"
                and c.pos_ not in ["PROPN", "NOUN"]
                and not c.is_sent_start
                ]
        
        
    def paired_sentence(self):
        sentence = None
        count = 0
        while not sentence and count < 3:
            d = random.randrange(len(self.catalog.documents))
            sents = []
            for i, sent in enumerate(self.catalog.documents[d].sents):
                if self.current_pivot.lemma_ in (
                        c.lemma_ for c in sent.root.children
                        ) and (d, i) not in (
                                s[:2] for s in self.used
                                ):
                    
                    sents.append((d, i, sent.as_doc()))
            
            if sents:
                sentence = sents[random.randrange(len(sents))]
            else:
                pivots = self.find_pivots()
                self.current_pivot = pivots[random.randrange(len(pivots))]
                count += 1
                print(count)
        return sentence
    
    def complete_next_sentence(self, pivots):
        print(pivots)
        self.current_pivot = pivots[random.randrange(len(pivots))]
        print("using: {} up to {}".format(self.current_sentence, self.current_pivot))
        self.used.append(self.current_sentence)
        s = next(islice(self.current_sentence[2].sents, 0, None))
        self.fragments.append(
                s[:self.current_pivot.i - s.start + 1]
                )

        next_sentence = self.paired_sentence()
        if next_sentence:
            pivot = [
                    t.i
                    for
                    t in
                    next(islice(next_sentence[2].sents, 0, None)).root.children
                    if t.lemma_ == self.current_pivot.lemma_
                ][0]
            fragment = next_sentence[2][pivot+1:]
            self.fragments.append(fragment)
            self.current_sentence = next_sentence
            self.used.append(self.current_sentence)
            self.sentences.append(nlp("".join([f.text_with_ws for f in self.fragments])))
            #self.fragments = []
        else:
            self.generate_next_sentence()


    def generate_next_sentence(self):
        
        self.fragments = []
        pivots = []
        if len(self.sentences) % 2 == 1:
            d, s = self.used[random.randrange(len(self.used))][:2]
        else:
            d = self.current_focus.appears_in[
                    random.randrange(len(self.current_focus.appears_in))
                    ]
            s = random.randrange(
                    len([s for s in self.catalog.documents[d].sents])
                )
        
        while (d, s) in ((sent[:2]) for sent in self.used):
            s = random.randrange(
                    len([s for s in self.catalog.documents[d].sents]))

        self.current_sentence = (d, s, next(islice(
            self.catalog.documents[d].sents,
            s,
            None)).as_doc())

        pivots = self.find_pivots()
        
        if not pivots:
            self.generate_next_sentence()
        else:
            self.used.append(self.current_sentence)
            self.complete_next_sentence(pivots)
       
    def conclude(self):
        d = self.topic_sentence[0]
        self.current_sentence = ((
                d,
                -1,
                [sent for sent in self.catalog.documents[d].sents][-1].as_doc()
                ))
        pivots = self.find_pivots()
        self.complete_next_sentence(pivots)
        

            
    def current_state(self):
        print("sentences: {}".format(self.sentences))
        print("current_focus: {}".format(self.current_focus.name))
        print("current_sentence: {}".format(self.current_sentence))
        print("current_pivot: {}".format(self.current_pivot))
        print("current_doc_index: {}".format(self.current_doc_index))
        print("fragments: {}".format(self.fragments))
        print("used: {}".format(self.used))
        print("# used: {}".format(len(self.used)))


    def __repr__(self):
        return "<ExquisiteCorpse: {}>".format(self.name)

       
        


class ExquisiteCorpse():
    """  """
    def __init__(self, name=None, *args, **kwargs):
        self.name = name
        self.sentences = []
        self.fragments = []
        self.used = []
        self.title = None
        self.topic_sentence = None
        self.current_doc_index = None
        self.current_sentence = None
        self.current_subj = None
        self.current_comp = None
        self.current_pivot = None
        self.preserve = None
        if "docs" in kwargs.keys():
            pass
        elif not self.catalog.people:
            self.catalog.collect_people()
        self.focus = sorted(
                catalog.people,
                key=lambda p: len(p.appears_in),
                reverse=True
                )[0]
        print(self.focus)
    
    def begin(self):

        """
        select the first inital sentence containg the focus (Person)
        entity, or selct the shortest topic sentence.
        """

        sentences = []
        used = None
        for d_tup in ((n, catalog.documents[n]) for n in self.focus.appears_in):
            sentences.append((d_tup[0], 1, next(islice(d_tup[1].sents, 1)).as_doc()))
            self.current_doc_index = d_tup[0]

        print(sentences)
        
        for sent in sentences:
            if self.fragments:
                break
            for p in (e for e in sent[2].ents if e.label_ == "PERSON"):
                if p.text in self.focus.aka:
                    self.topic_sentence = sent
                    self.current_sentence = sent
                    self.used.append(sent)
                    # idx = next(islice(self.topic_sentence[1].sents, 1)).root.i + 1
                    preserve = (p.start, p.end, p.text, p.root.dep_)
                    self.current_pivot = [t for t
                          in next(islice(sent[2].sents, 1)).root.rights
                          ][0]
                    idx = self.current_pivot.i
                    if p.end > idx:
                        self.fragments.append(self.topic_sentence[2][idx:])
                    else:
                        self.fragments.append(self.topic_sentence[2][:idx+1])
                    break
                
        if not self.current_sentence:
            self.current_sentence = sorted(sentences, key=lambda s: len(s[2]))[0]

        pattern = [{"LEMMA": self.current_pivot.lemma_}]
        matcher = Matcher(nlp.vocab)
        matcher.add("PivotPoint", [pattern], None)
        for index, doc in (
                    (n, catalog.documents[n])
                    for n
                    in self.focus.appears_in
                    if n != self.current_sentence[0]
                    ):
            for i, sent in enumerate(doc.sents):
                try:
                    mid, lidx, ridx = matcher(sent)[0]
                    if mid:
                        self.fragments.append(sent.as_doc()[lidx:])
                        self.current_doc_index = index
                        used = (index, i, sent)
                        break
                except:
                    continue
            
            if len(self.fragments) >= 2:
                new_sent = nlp(
                        "".join(
                                [
                                self.fragments[0].text_with_ws,
                                self.fragments[1][1:].text_with_ws
                                ]
                               )
                        )
                self.sentences.append(self.fix_pronouns(new_sent))
                self.used.append(used)
                self.current_sentence = used
                break

    
    def fix_pronouns(self, doc):
        return doc
    
    def choose_next_document(self):
        
        peeps = [p for p in catalog.people if p.wikidata]
        refocus = sorted([
                    person
                    for person
                    in catalog.people
                    if person.name != self.focus.name
                ],
                key=lambda p: len(p.appears_in),
                reverse=True
                )[random.randrange(len(peeps))]
        self.focus = refocus
        
        choices = [
                n
                for n
                in self.focus.appears_in
                if n
                not in [s[0] for s in self.used]
                ]
        if len(choices):
            self.current_doc_index = choices[random.randrange(len(choices))]
        else:
            self.current_doc_index = random.randrange(len(catalog.documents))

        return catalog.documents[self.current_doc_index]


    def choose_next_sentence(self, dindex=None, sindex=None):
        if len(self.sentences) >= 8:
            # Need to include failsafe here?
            pass 
        
        self.fragments = []
        if dindex:
            self.current_doc_index = dindex
            doc = catalog.documents[dindex]
        else:
            # self.current_doc_index = self.current_sentence[0]
            doc = self.choose_next_document()

        if sindex:
            self.current_sentence = (sindex, next(islice(doc.sents, sindex, None)))
        else:
            for i, s in enumerate(doc.sents):
                p = [
                        e for e in s.ents
                        if e and e.label_ == "PERSON"
                        and e.text not in self.focus.aka
                        ]
                if p:
                    if self.used[0] == self.current_doc_index and self.used[1] == i:
                        continue
                    #try:
                    #    self.focus = next(islice(
                    #        (name for name in catalog.people if p.text in name.aka),
                    #        0,
                    #        None
                    #        ))
                    #except:
                    #    pass
                    self.current_sentence = (self.current_doc_index, i, s)
                    self.used.append(self.current_sentence)
                    break
        
        children = [
                c for c
                #in next(islice(
                #    catalog.documents[self.current_doc_index].sents,
                #    self.current_sentence[0],
                #    None
                #    )).root.children
                in self.current_sentence[2].root.children
                if c.dep_ != 'punct'
                and c.pos_ != 'PROPN'
                ]
        try:
            self.current_pivot = children[random.randrange(1, len(children))]
            self.fragments.append(
                    self.current_sentence[2][:
                        self.current_pivot.i - self.current_sentence[2].start + 1
                        ]
                    )
        except ValueError:
            print("skipping {}".format(self.current_sentence))
            self.current_doc_index = (self.current_doc_index + 1) % len(catalog.documents)
            self.choose_next_sentence(dindex=self.current_doc_index)
    
    def complete_next_sentence(self):
        sentences = []
        for doc in (
                (n, catalog.documents[n])
                for n
                in self.focus.appears_in
                if n != self.current_doc_index
                ):
            for i, sentence in enumerate(doc[1].sents):
                print(doc[0], i)
                #try:
                pivots = [
                    (t.i - sentence.start, t)
                    for t 
                    in sentence
                    if t.lemma_ == self.current_pivot.lemma_
                    and t.head.dep_ == "ROOT"
                    ]
                if self.current_pivot.lemma_ in (p[1].lemma_ for p in pivots):
                    sentences.append(
                                        {
                                        "d": doc[0],
                                        "i": i,
                                        "pivots": pivots, 
                                        "sentence": sentence, 
                                        "rank": 0,
                                        }
                                    )
        
        
        try:
            fragment = next(islice(
                (s['sentence'][s['pivots'][-1][0]+1:] for s in sentences),
                random.randrange(len(sentences)),
                None
                ))
            self.fragments.append(fragment)
            self.sentences.append(
                    nlp("".join([f.text_with_ws for f in self.fragments]))
                    )
        except ValueError:
            #self.current_pivot = corpse.current_sentence[1].root
            #cut = (corpse.current_sentence[1].root.i 
            #        - corpse.current_sentence[1].start
            #        + 1
            #        ) 
            #
            #self.fragments = [self.current_sentence[1][:cut]]
            self.fragments = []
            self.used = self.used[:-1]
            self.choose_next_sentence()
            self.complete_next_sentence()
        
        sentences = []
        self.fragments = []

        #return sentences
    
    def current_state(self):
        print("sentences: {}".format(self.sentences))
        print("current_sentence: {}".format(self.current_sentence))
        print("current_pivot: {}".format(self.current_pivot))
        print("current_doc_index: {}".format(self.current_doc_index))
        print("fragments: {}".format(self.fragments))
        print("used: {}".format(self.used))
        print("# used: {}".format(len(self.used)))


    def __repr__(self):
        return "<ExquisiteCorpse: {}>".format(self.name)



