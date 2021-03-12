#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import nltk
import json
import html
import emoji
import random
import string
import requests

import jieba
import jieba.posseg as pseg

from bs4 import BeautifulSoup
from requests.utils import requote_uri
from EmojiPredictor import EmojiPredictor
from google.cloud import translate_v2 as translate
from TextProcessor import TextProcessor
from EmojiUtil import *

class CHNTextProcessor(TextProcessor):
    def __init__(self, emojiPredictor):
        super(TextProcessor, self).__init__()
        self.ep = emojiPredictor
        self.nopunc = str.maketrans('', '', string.punctuation)
        self.gsearchURL = "https://www.googleapis.com/customsearch/v1?key=insert_your_key_here"
        self.EMOJI_REGEXP = re.compile(_EMOJI_REGEXP)
        self.ep = emojiPredictor
        self.numemojis = 5
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
                
        #you need to put your own google api json here
        self.translate_client = translate.Client.from_service_account_json("gapiKey.json")

    def isCHN(self, text):
    	return re.search("[\u4e00-\u9FFF]", text)

    def processText(self, premessage, text):
        res = {"text":""}
        if text == None or len(text.strip()) == 0:
            return res

        textrim = text.lower().translate(self.nopunc).strip()
        if textrim in ['第一个表情','第1个表情'] :
            res['text'] = text
            res['selection'] = 0
        elif textrim in ['第二个表情', '第2个表情']:
            res['text'] = text
            res['selection'] = 1
        elif textrim in ['第三个表情', '第3个表情']:
            res['text'] = text
            res['selection'] = 2
        elif textrim in ['第四个表情','第4个表情']:
            res['text'] = text
            res['selection'] = 3
        elif textrim in ['第五个表情', '第5个表情', '最后一个表情']:
            res['text'] = text
            res['selection'] = 4
        if "selection" in res:
            return res

        #second check if there's instruction on "delete the emoji"
        #or like change the emoji into xxx emoji
        if textrim in ["删除表情", '删掉表情']:
            res["delete"] = -1
            res["text"] = text
        elif textrim.startswith("把表情改成"):
            query = textrim[5:].replace('表情','emoji')
            colorchange = False
            if '皮肤' in query or '色' in query:
                colorchange = True
            query = self.translateToEng(query)
            if colorchange:
                lastemoji = ''
                for match in self.EMOJI_REGEXP.finditer(premessage):
                    lastemoji = premessage[match.start():match.end()] 
                query = lastemoji+query
            emojis = self.getEmojiList(query, False)
            res["query"] = query
            res["text"] = text
            if len(emojis) == 0:
                res["change"] = ''
            else:
                res["change"] = emojis[0]
        if "change" in res or "delete" in res:
            return res

        if textrim in ["有什么表情",'有哪些表情']:
            res["show"] = 1
            return res

        x = re.search(r'给我.*?表情', text)
        if x:
            query = x[0][2:]
            if query[:2] == '一个':
                query = query[2:]
            if query[-3] == '的':
                query = query[:-3]
            else:
                query = query[:-2]
            query = self.translateToEng(query)
            res["text"] = text[:x.start()]
            emojis = self.getEmojiList(query, True)
            res["emojis"] = emojis
            res["query"] = x[0]
        elif '表情' in text:
            description = "" #插入xxx(description)表情 
            tmptext = text
            words = pseg.cut(text) 
            words = [[list(k)[0], list(k)[1]] for k in list(words)]
            insertidx = -1
            for i, item in enumerate(words):
                word, flag = item
                if word == '插入':
                    insertidx = i
                    continue
                elif word == '表情' and i > 0:
                    cur_pos = tmptext.find('表情')
                    if insertidx >= 0:
                        res["text"] += tmptext[:tmptext[:cur_pos].rfind('插入')]
                        if len(description) > 0:
                            if description[-1] == '的':
                                description = description[:-1]
                            emojis = self.getEmojiList(self.translateToEng(description), False)
                            if len(emojis) > 0:
                                res["text"] += emojis[0]
                        tmptext = tmptext[cur_pos+2:]
                        description = ''
                        insertidx = -1
                    else:
                        #checn xxx emoji, if xxx is noun/number
                        query_word = words[i-1]
                        if words[i-1][0] == '的' and i > 1:
                            query_word = words[i-2]
                        if query_word[1] in ['n', 'nz', 'ns', 'v', 'vn']:
                            #search for the emoji!
                            emojis = self.getEmojiList(self.translateToEng(query_word[0]), False)
                            if len(emojis) > 0:
                                res["text"] += tmptext[:tmptext.find(query_word[0])]+emojis[0]
                            else:
                                res["text"] += tmptext[:cur_pos+2]
                        else:
                            res["text"] += tmptext[:cur_pos+2]
                        tmptext = tmptext[cur_pos+2:]
                elif insertidx >= 0:
                    description += word
            res["text"]+=tmptext
        else:
            res["text"] = text
        if 'emojis' not in res: #and self.EMOJI_REGEXP.search(res["text"]) == None:
            inputext = premessage+' '+res["text"]
            inputext = self.translateToEng(inputext)
            # print("翻译： %s" % inputext)
            if len(inputext) > 0:
                predemojis = self.ep.getPredictedEmojis(' '.join(inputext.split()[-20:]))
                #get word emojis
                wordemojis = self.getWordEmojis(inputext, set(predemojis))
                res["emojis"] = predemojis[:3]
                # print ("pred: %s, word: %s" % (' '.join(predemojis), ' '.join(wordemojis)) )
                if len(wordemojis) < 2:
                    res["emojis"] = predemojis[:5-len(wordemojis)]
                res["emojis"] += wordemojis[:2]
        return res

    def translateToEng(self, text):
        # Text can also be a sequence of strings, in which case this method
        # will return a sequence of results for each text.
        result = self.translate_client.translate(
            text, target_language='en')
        # print(u'Text: {}'.format(result['input']))
        return html.unescape(result['translatedText'])


# print(tp.processText("", "我想要一只大象"))
# print(tp.processText("","这个不错给我一个酷酷的表情."))
# print(tp.processText("","这里的天气表情不错，我们可以出去晒太阳表情，还有运动保持好表情"))

