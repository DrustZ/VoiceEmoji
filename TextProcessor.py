#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import nltk
import json
import emoji
import random
import string
import requests
from bs4 import BeautifulSoup
from requests.utils import requote_uri
from EmojiPredictor import EmojiPredictor
from EmojiUtil import *

class TextProcessor(object):
    """docstring for TextProcessor"""
    def __init__(self, emojiPredictor):
        super(TextProcessor, self).__init__()
        self.nopunc = str.maketrans('', '', string.punctuation)
        self.numemojis = 5
        
        #you need to create your own google search url from the api console. This one is not guaranteed to work
        self.gsearchURL = "https://www.googleapis.com/customsearch/v1?key=insert_your_key_here"
        self.EMOJI_REGEXP = re.compile(_EMOJI_REGEXP)
        self.ep = emojiPredictor
        self.emojidict = json.load(open('emojis.json', encoding="utf-8"))
        self.emojikeywords = {}
        for k,v in self.emojidict.items():
            if v['category'] == 'flags':
                continue
            emoji = v['char']
            keys = v['keywords']
            keys.append(k)
            for key in keys:
                if key not in self.emojikeywords:
                    self.emojikeywords[key] = []
                self.emojikeywords[key].append(emoji)

    def processText(self, premessage, text):
        res = {"text":""}
        if text == None or len(text.strip()) == 0:
            return res
        tlowertrim = text.lower().translate(self.nopunc).strip()
        last_three_words = ' '.join(tlowertrim.split()[-3:])
        #first check if it's a emoji selection task
        if 'the first emoji' == last_three_words:
            res["text"] = ' '.join(text.split()[:-3]) + ' '
            res["selection"] = 0
        elif 'the second emoji' == last_three_words:
            res["text"] = ' '.join(text.split()[:-3]) + ' '
            res["selection"] = 1
        elif 'the third emoji' == last_three_words:
            res["text"] = ' '.join(text.split()[:-3]) + ' '
            res["selection"] = 2
        elif 'the fourth emoji' == last_three_words:
            res["text"] = ' '.join(text.split()[:-3]) + ' '
            res["selection"] = 3
        elif last_three_words in ['the fifth emoji', 'the last emoji']:
            res["text"] = ' '.join(text.split()[:-3]) + ' '
            res["selection"] = 4
        if "selection" in res:
            return res

        #second check if there's instruction on "delete the emoji"
        #or like change the emoji into xxx emoji
        if re.match("^(remove|delete)( the)? emoji", tlowertrim):
            res["delete"] = -1
        elif tlowertrim.startswith("change the emoji to "):
            query = ' '.join(tlowertrim.split()[4:])
            if 'color' in query or 'skin' in query:
                lastemoji = ''
                for match in self.EMOJI_REGEXP.finditer(premessage):
                    lastemoji = premessage[match.start():match.end()] 
                query = lastemoji+query
            
            emojis = self.getEmojiList(query, False)
            res["query"] = query
            if emojis == None or len(emojis) == 0:
                res["change"] = ''
            else:
                res["change"] = emojis[0]
        if "change" in res or "delete" in res:
            return res

        if tlowertrim == "read emojis":
            res["show"] = 1
            return res

        #For emoji input, first search if there's instruction
        x = re.search(r'emoji search .*?emoji', text.lower())
        if x:
            query = ' '.join(x[0].split()[2:])
            #no punc in the query
            if query.translate(self.nopunc) == query:
                #query process
                res["text"] = text[:x.start()].rstrip()
                emojis = self.getEmojiList(query, True)
                res["emojis"] = emojis
                res["query"] = x[0]
                res["text"] = text[:x.start()]
        elif 'emoji' in text.lower():
            description = ""
            insertidx = -1
            tmptext = text.lower()
            tokens = nltk.word_tokenize(tmptext)
            tags = nltk.pos_tag(tokens)
            for i, tag in enumerate(tags):
                if tag[0].lower() == 'insert':
                    insertidx = i
                    continue
                elif tag[0].lower() == 'emoji' and i > 0:
                    cur_pos = tmptext.find('emoji')
                    if insertidx >= 0:
                        res["text"] += tmptext[:tmptext[:cur_pos].rfind('insert')]
                        if len(description) > 0:
                            emojis = self.getEmojiList(description +'emoji', False)
                            if emojis != None and len(emojis) > 0:
                                res["text"] += emojis[0]
                        tmptext = tmptext[cur_pos+6:]
                        description = ''
                        insertidx = -1
                    else:
                        #checn xxx emoji, if xxx is noun/number
                        if tags[i-1][1] in ['NN', 'CD', 'NNS', 'NNP', 'VBG', 'VB']:
                            #search for the emoji!
                            emojis = self.getEmojiList(tags[i-1][0]+' emoji', False)
                            if emojis != None and len(emojis) > 0:
                                res["text"] += ' '.join(tmptext[:cur_pos].split()[:-1])+' '+emojis[0]+' '
                            else:
                                res["text"] += tmptext[:cur_pos+6]   
                        else:
                            res["text"] += tmptext[:cur_pos+6]
                        tmptext = tmptext[cur_pos+6:]
                elif insertidx >= 0:
                    description += tag[0].lower()+' '
            res["text"]+=tmptext
        else:
            res["text"] = text
        if 'emojis' not in res: #and self.EMOJI_REGEXP.search(res["text"]) == None:
            #predict semantic
            inputext = premessage+' '+res["text"]
            predemojis = self.ep.getPredictedEmojis(' '.join(inputext.split()[-20:]))
            #get word emojis
            wordemojis = self.getWordEmojis(res['text'], set(predemojis))
            res["emojis"] = predemojis[:3]
            # print ("pred: %s, word: %s" % (' '.join(predemojis), ' '.join(wordemojis)) )
            if len(wordemojis) < 2:
                res["emojis"] = predemojis[:5-len(wordemojis)]
            res["emojis"] += wordemojis[:2]
        if len(res['text']) > 0:
            res['text'] += ' '
        return res

    def getWordEmojis(self, text, predemojis):
        emojis = []
        words = text.lower().split()
        for w in words[::-1]:
            if len(w) > 3 and w in self.emojikeywords:
                candidates = list(set(self.emojikeywords[w]) - predemojis)
                if len(candidates) == 0:
                    continue
                emojis.append(random.choice(candidates))
        return emojis

    def getEmojiList(self, query, moreEmojis=False):
        print("Query: %s" % query.translate(self.nopunc).replace(' ', '+'))

        r = requests.get(self.gsearchURL+query.translate(self.nopunc).replace(' ', '+'))#+requote_uri(query))
        urls = []
        emojis = []
        searchRes = r.json()
        queryitems = []
        if 'items' not in searchRes:
            return []

        for item in searchRes['items']:
            if item['link'].startswith('https://emojipedia.org/search/?q'):
                queryitems.append(item['link'])
            else:
                segs = list(filter(len, item['link'].split('/')))
                #official emoji pages only have three slashes
                if len(segs) != 3:
                    continue
                metatag = item['pagemap']['metatags']
                if len(metatag) > 0 and 'og:title' in metatag[0]:
                    emojires = self.EMOJI_REGEXP.search(metatag[0]['og:title'])
                    if emojires and emojires not in emojis:
                        emojis.append(emojires[0])
                        urls.append(item['link'])

        for item in queryitems:
            res = self.getSearchListEmojis(item, emojis)
            emojis += res[0]
            urls += res[1]

        if len(emojis) == 0:
            return None
        #if not enough and we need more, we crawl related emojis
        if len(emojis) < self.numemojis and moreEmojis:
            moremojis = self.getRelatedEmojis(urls[0])
            idx = 0
            for memoji in moremojis:
                if memoji not in emojis:
                    emojis.append(memoji)
        #remove duplicate
        seen = set()
        seen_add = seen.add
        emojis = [x for x in emojis if not (x in seen or seen_add(x))]
        if emojis == None:
            emojis = []
        print (emojis)
        return emojis

    #get emojis from urls like https://emojipedia.org/search/?q=, 
    #the defaut search emoji pages of emojipedia
    def getSearchListEmojis(self, url, emojiset):
        emojis = []
        urls = []
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        elist = soup.select_one('.search-results')
        for itm in elist.findChildren('li'): 
            emojires = self.EMOJI_REGEXP.search(list(itm.select_one('.emoji').strings)[0])
            if not emojires or emojires in emojiset:
                continue
            emojis.append(emojires[0])
            urls.append("https://emojipedia.org"+itm.find('a')['href'])
        return [emojis, urls]


    #get emojis from emoji page of emojipedia
    def getRelatedEmojis(self, url):
        r = requests.get(url)
        # print("searching ... %s" % url)
        extra_emojis = []
        soup = BeautifulSoup(r.text, "html.parser")
        lst = soup.select("article > h1")
        if len(lst) == 0:
            return []
        elif len(list(soup.select("article > h1")[0].strings)) == 0:
            return []
        cur_emoji_desc = list(soup.select("article > h1")[0].strings)[-1]\
        .lower().strip().split()
        elist = soup.find('h2', text="See also").find_next("ul")
        for itm in elist.findChildren('li'): 
            moji = list(itm.strings)[0]
            moji_desc = list(itm.strings)[-1].lower()
            common_words = 0
            for w in cur_emoji_desc:
                if w in moji_desc:
                    common_words += 1
            extra_emojis.append([-common_words, moji])
        extra_emojis = sorted(extra_emojis)
        if len(extra_emojis) > 0:
            return [itm[1] for itm in extra_emojis]
        return []

# tp = TextProcessor(EmojiPredictor())
# print(tp.processText("","give me a sex emoji"))
# print(tp.processText("do you remember? ","yeah! I got in on time"))
# print(tp.processText("","test this sentence slash fast emoji."))
# print(tp.processText("test this sentence slash fast emoji haha"))
# print(tp.processText("","test this sentence give me a cool hat emoji"))
# print(tp.processText("test this sentence give me a fast emoji hehe"))
# print(tp.processText("test ","this car emoji sentenc a fast this cat emoji sentenc a fast this cap emoji sentenc a fast emoji"))
# print(tp.processText("test this sentence car emoji haha"))

