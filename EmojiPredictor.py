# -*- coding: utf-8 -*-

""" Use torchMoji to predict emojis from a single text input
"""

from __future__ import print_function, division, unicode_literals
import json
import csv
import argparse

import numpy as np
import emoji

import requests
from requests.utils import requote_uri

from torchmoji.sentence_tokenizer import SentenceTokenizer
from torchmoji.model_def import torchmoji_emojis

# Emoji map in emoji_overview.png
EMOJIS = ":joy: :unamused: :weary: :sob: :heart_eyes: \
:pensive: :ok_hand: :blush: :heart: :smirk: \
:grin: :notes: :flushed: :100: :sleeping: \
:relieved: :relaxed: :raised_hands: :two_hearts: :expressionless: \
:sweat_smile: :pray: :confused: :kissing_heart: :heartbeat: \
:neutral_face: :information_desk_person: :disappointed: :see_no_evil: :tired_face: \
:v: :sunglasses: :rage: :thumbsup: :cry: \
:sleepy: :yum: :triumph: :hand: :mask: \
:clap: :eyes: :gun: :persevere: :smiling_imp: \
:sweat: :broken_heart: :yellow_heart: :musical_note: :speak_no_evil: \
:wink: :skull: :confounded: :smile: :stuck_out_tongue_winking_eye: \
:angry: :no_good: :muscle: :facepunch: :purple_heart: \
:sparkling_heart: :blue_heart: :grimacing: :sparkles:".split(' ')

VOCAB_PATH = "torchmoji/vocabulary.json"
PRETRAINED_PATH = "torchmoji/pytorch_model.bin"

def top_elements(array, k):
    ind = np.argpartition(array, -k)[-k:]
    return ind[np.argsort(array[ind])][::-1]

class EmojiPredictor(object):
    def __init__(self):
        # Tokenizing using dictionary
        with open(VOCAB_PATH, 'r') as f:
            vocabulary = json.load(f)
        self.st = SentenceTokenizer(vocabulary, 30)
        # Loading model
        self.model = torchmoji_emojis(PRETRAINED_PATH)
        # Running predictions
        self.dangoURL = "https://emoji.getdango.com/api/emoji?q="

    def getPredictedEmojis(self, text):
        api_response = ''
        try:
            #turned out that Dango has stopped the api service. 
            #we might just use the deepmoji model
            r= requests.get("https://emoji.getdango.com/api/emoji",
                    params={"q": text})
            api_response = json.loads(r.text)
        except:
            pass

        if 'results' in api_response:
            res = [item['text'] for item in api_response['results']]
            if len(res) < 5:
                extraemojis = self.localPredict(text)
                for k in extraemojis:
                    if k not in res:
                        res.append(k)
                    if len(res) == 5:
                        return res
            else:
                return res[:5]
        else:
            return self.localPredict(text)

    def localPredict(self, text):
        tokenized, _, _ = self.st.tokenize_sentences([text.lower()])
        # Get sentence probability
        prob = self.model(tokenized)[0]
        # Top emoji id
        emoji_ids = top_elements(prob, 6)
        np.setdiff1d(emoji_ids,[42])
        if len(emoji_ids) > 5:
            emoji_ids = emoji_ids[:5]
        # map to emojis
        emojis = map(lambda x: EMOJIS[x], emoji_ids)
        return emoji.emojize(' '.join(emojis), use_aliases=True).split()