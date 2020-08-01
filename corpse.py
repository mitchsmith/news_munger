#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from munger import *

## Classes ##


class MadLib(Munger):
    
    """  """

    def build(self):
        pass
        

    def __repr__(self):
        return "<MadLib: {}>".format(self.headline)


class ExquisiteCorpse(Munger):
    
    """  """

    def build(self):
        pass
    
    def munge_sayings(self, sentences):
        print("Munging Sayings:")
        for sentence in sentences:
            if sentence[3][0].tag_ == "``":
                # begins with a quotation
                pattern = re.compile(r"^(“)([^”]+)([,\.]”)(.*)$")
                tmp = nlp(pattern.sub(r"\2.", sentence[3].text))
                s = next(islice(tmp.sents, 0, None))
                repl = self.munge_on_roots((None, None, s.root.lemma_, s))
                if type(repl) == Doc:
                    new = pattern.sub(r"\1{}\3\4".format(repl), sentence[3].text_with_ws)
                    return new
            else:
                lefts = []
                rights = []
                for right in sentence[3].root.rights:
                    rights.extend([t for t in right.children])
                if rights[0].tag_ == "``":
                    try:
                        end = [t.tag_ for t in rights[1:]].index("``")
                        tmp = nlp("".join([t.text_with_ws for t in rights[1:end]]))
                        s = next(islice(tmp.sents, 0, None))
                        pattern = re.compile(r"^(“)([^”]+)([,\.]”)(.*)$")
                        repl = self.munge_on_roots((None, None, s.root.lemma_, s))
                        if type(repl) == Doc:
                            new = pattern.sub(r"\1{}\3\4".format(repl),
                                    sentence[3].text_with_ws
                                    )
                        return new

                    except ValueError:
                        pass
                
                sentence = []
                while type(sentence) == list:
                    sentence = self.munge_on_roots(
                            sentences[random.randrange(len(sentences))]
                            )
                    sentences = sentence
                        
                return sentence
        
        return sentences
    
    
    def munge_beings(self, sentences):
        print("Munging Beings:")
        sentence = sentences[random.randrange(len(sentences))][3]
        text = sentence.text_with_ws
        for left in sentence.root.lefts:
            if left.dep_ != 'punct':
                orig = "".join([t.text_with_ws for t in left.subtree])
                alternates = self._be_children['left'][left.dep_]
        alt = alternates[random.randrange(len(alternates))]
        repl = "".join([t.text_with_ws for t in alt[2]])
        if not repl:
            repl = " "
        repl = " {}".format(repl)
        text = re.sub(orig, repl, text)
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\s([,;?!.])", r"\1", text)
        for right in sentence.root.rights:
            if right.dep_ != 'punct':
                orig = "".join([t.text_with_ws for t in right.subtree])
                alternates = self._be_children['right'][right.dep_]
        alt = alternates[random.randrange(len(alternates))]
        repl = "".join([t.text_with_ws for t in alt[2]])
        if not repl:
            repl = " "
        repl = " {}".format(repl)
        text = re.sub(orig, repl, text)
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\s([,;?!.])", r"\1", text)
        text =  re.sub(r"(\w)( but )", r"\1 and ", text)
        text = re.sub(r"^\s+", "", text)
        sentence = nlp(text)

        return sentence
    
    
    def munge_children(self, sentences):
        if sentences[1][2] == "be":
            return self.munge_beings(sentences)
        
        return self.munge_sayings(sentences)
        
        
    def __repr__(self):
        return "<ExquisiteCorpse: {}>".format(self.headline)



