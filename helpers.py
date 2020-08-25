#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Helper functions and nltk-based NLP classes and utiities """

import os
import subprocess
import re
from collections import deque


FEMININE_TITLES = (
    "Chairwoman",
    "Councilwoman",
    "Congresswoman",
    "Countess",
    "Dame",
    "Empress",
    "Lady",
    "Mrs",
    "Mrs.",
    "Miss",
    "Miss.",
    "Ms",
    "Ms.",
    "Mme",
    "Mme.",
    "Madam",
    "Madame",
    "Mother",
    "Princess",
    "Queen",
    "Sister",
)

MASCULINE_TITLES = (
    "Archduke",
    "Ayatollah",
    "Count",
    "Emperor",
    "Father",
    "Imam",
    "King",
    "Lord",
    "Master",
    "Mr",
    "Mr.",
    "Prince",
    "Sir",
)

GENERIC_TITLES = (
    "Admiral",
    "Apostle",
    "Archbishop",
    "Bishop",
    "Captain",
    "Cardinal",
    "Chairman",
    "Chancellor",
    "Chef",
    "Chief",
    "Colonel",
    "Commissioner",
    "Councillor",
    "Councilman",
    "Congressman",
    "Corporal",
    "Deacon",
    "Doctor",
    "Dr.",
    "Dr",
    "Elder",
    "General",
    "Governor",
    "Gov.",
    "Gov",
    "Governor-General",
    "Justice",
    "Mahatma",
    "Major",
    "Mayor",
    "Minister",
    "Nurse",
    "Ombudsman",
    "Pastor",
    "Pharaoh",
    "Pope",
    "President",
    "Professor",
    "Prof.",
    "Prof",
    "Rabbi",
    "Reverend",
    "Representative",
    "Rep",
    "Rep.",
    "Saint",
    "Secretary",
    "Senator",
    "Sen.",
    "Sen",
    "Sergeant",
    "Sultan",
    "Swami",
)

PRESIDENTIOSITUDE = (
    "17 Time Winner of the Q-Anonopiac Popularity Pole",
    "Adored Dispicable",
    "Beloved Orange Dumpling",
    "Chaste Keeper of American Great-Againness",
    "Chief Scientist of the United States",
    "Chosen One",
    "Delightful Fellow",
    "Elected Leader of the Free World",
    "Engorged Effigy of Himself",
    "First Citizen of the Flies",
    "Friend to the Obsequious",
    "Friend to the Downtrodden and the White",
    "Friend to Mankind",
    "God Most High",
    "God King",
    "Grand Wizard of the USA",
    "His Royal Highness",
    "Inspirer of Adoration and Dispair",
    "Jingoistic Ringleader on High",
    "Kindness and Compassion Incarnate",
    "Lord of All Three Branches",
    "Most High King",
    "Our Overlord and Savior",
    "Paragon of Truthiness",
    "President of the United States",
    "President of the United States of America",
    "Quite High IQ Person",
    "Rex Devi Felis",
    "Right Man for the Nut Job",
    "Simply the Best President Ever",
    "Super Stable Genius",
    "The Great and Powerful",
    "The Toast of Tyrants",
    "The Suseptible but Invulnerable",
    "The Unimpeachable",
    "Unabashed Racialist",
    "Very High IQ Person Indeed",
    "Wastern Civilization's Most Impressive Puppet",
)


def kill_firefox():

    """ Indescriminately kill all running firefox processes """

    process = subprocess.Popen(["ps", "-A"], stdout=subprocess.PIPE)
    output, error = process.communicate()
    for line in output.splitlines():
        if "firefox" in str(line):
            pid = int(line.split(None, 1)[0])
            os.kill(pid, 9)
    if error:
        print(error)


def find_duplicates(my_list):

    """Return list of duplicated items in a list """

    a_list = sorted(my_list)
    b_list = sorted(set(my_list))
    c_list = []
    if len(a_list) == len(b_list):
        return c_list
    while a_list:
        dee = a_list.pop()
        if dee in a_list:
            c_list.append(dee)

    return sorted(set(c_list))


def fix_double_quotes(input_string):

    """Balance quotation marks using utf-8 curlys """

    lsquote = b"\xe2\x80\x98".decode("utf-8")
    apos = b"\xe2\x80\x99".decode("utf-8")
    ldquote = b"\xe2\x80\x9c".decode("utf-8")
    rdquote = b"\xe2\x80\x9d".decode("utf-8")
    text = input_string
    quoted = ""
    warn = ""
    pat = r'"|{}|{}|{}'.format(ldquote, rdquote, "['" + lsquote + apos + "]{2}")
    matches = deque(re.finditer(pat, text))
    parity = 0

    while matches:
        # look for pairs from left to right
        match = matches.popleft()
        copy, text = text[: match.end()], text[match.end() :]
        repl = [ldquote, rdquote][parity]
        copy = re.sub(r"{}".format(match[0]), repl, copy)
        quoted += copy
        parity = (parity + 1) % 2

    quoted += text

    if parity:
        warn = "Unmatched double quote"
        print("{}: {}".format(warn, quoted))
        quoted += rdquote

    return quoted


def irreg_inflect(lemma, context):

    """ Return the inflected form for the given context: (tense,number,person) """

    itable = {}
    itable["be"] = [
        [["am", "are", "is"], ["are", "are", "are"]],
        [["was", "were", "was"], ["were", "were", "were"]],
    ]
    itable["do"] = [
        [["do", "do", "does"], ["do", "do", "do"]],
        [["did", "did", "did"], ["did", "did", "did"]],
    ]
    itable["have"] = [
        [["have", "have", "has"], ["have", "have", "have"]],
        [["had", "had", "had"], ["had", "had", "had"]],
    ]
    itable["say"] = [
        [["say", "say", "says"], ["say", "say", "say"]],
        [["said", "said", "said"], ["said", "said", "said"]],
    ]

    tense, number, person = context

    return itable[lemma][tense][number][person]


# if __name__ == "__main__":
# """ run unit tests  """
# import unittest
# from tests import TestPersonChunker
# from tests import TestPersonScanner
# unittest.main()

# conflation = load_conflation()
# pass
