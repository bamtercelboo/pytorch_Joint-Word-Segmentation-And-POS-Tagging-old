# coding=utf-8
import torch
import random
import collections
from loaddata.common import sep, app, nullkey, paddingkey, unkkey
import hyperparams as hy
torch.manual_seed(hy.seed_num)
random.seed(hy.seed_num)


"""
  Create alphabet by train/dev/test data
"""


class Create_Alphabet():
    def __init__(self, min_freq=1):

        self.min_freq = min_freq

        self.word_state = collections.OrderedDict()
        self.char_state = collections.OrderedDict()
        self.bichar_state = collections.OrderedDict()
        self.pos_state = collections.OrderedDict()

        self.word_alphabet = Alphabet(min_freq=min_freq)
        self.char_alphabet = Alphabet(min_freq=min_freq)
        self.bichar_alphabet = Alphabet(min_freq=min_freq)
        # pos min_freq = 1, not cut
        self.pos_alphabet = Alphabet(min_freq=1)
        self.label_alphabet = Alphabet(min_freq=min_freq)

        # unkid
        self.word_UnkkID = None
        self.char_UnkID = None
        self.bichar_UnkID = None
        self.pos_UnkID = None

        # paddingid
        self.word_PaddingID = None
        self.char_PaddingID = None
        self.bichar_PaddingID = None
        self.pos_PaddingID = None

        self.appID = None
        self.sepID = None

    def createAlphabet(self, train_data=None, dev_data=None, test_data=None, debug_index=-1):
        print("create Alphabet start...... ! ")
        # handle the data whether to fine_tune
        assert train_data is not None
        datasets = []
        datasets.extend(train_data)
        print("the length of train data {}".format(len(datasets)))
        if dev_data is not None:
            print("the length of dev data {}".format(len(dev_data)))
            datasets.extend(dev_data)
        if test_data is not None:
            print("the length of test data {}".format(len(test_data)))
            datasets.extend(test_data)
        print("the length of data that create Alphabet {}".format(len(datasets)))
        # create the word Alphabet
        for index, data in enumerate(datasets):
            # word
            for word in data.words:
                if word not in self.word_state:
                    self.word_state[word] = 1
                else:
                    self.word_state[word] += 1
            # char
            for char in data.chars:
                if char not in self.char_state:
                    self.char_state[char] = 1
                else:
                    self.char_state[char] += 1
            # bichar_left
            for bichar in data.bichars_left:
                if bichar not in self.bichar_state:
                    self.bichar_state[bichar] = 1
                else:
                    self.bichar_state[bichar] += 1
            bichar = data.bichars_right[-1]
            if bichar not in self.bichar_state:
                self.bichar_state[bichar] = 1
            else:
                self.bichar_state[bichar] += 1
            # label pos
            for pos in data.pos:
                if pos not in self.pos_state:
                    self.pos_state[pos] = 1
                else:
                    self.pos_state[pos] += 1
            # copy with the gold "SEP#PN"
            for gold in data.gold:
                self.label_alphabet.loadWord2idAndId2Word(gold)

            # copy with the seq/app/unkkey/nullkey/paddingkey
            self.word_state[unkkey] = self.min_freq + 1
            self.word_state[paddingkey] = self.min_freq + 1
            self.char_state[unkkey] = self.min_freq + 1
            self.char_state[paddingkey] = self.min_freq + 1
            self.bichar_state[unkkey] = self.min_freq + 1
            self.bichar_state[paddingkey] = self.min_freq + 1
            self.pos_state[unkkey] = 1
            self.pos_state[paddingkey] = 1

            if index == debug_index:
                # only some sentence for debug
                print(self.word_state, "************************")
                print(self.char_state, "*************************")
                print(self.bichar_state, "*************************")
                print(self.pos_state, "*************************")
                print(self.label_alphabet.words2id)
                break

        # create the id2words and words2id
        self.word_alphabet.initialWord2idAndId2Word(self.word_state)
        self.char_alphabet.initialWord2idAndId2Word(self.char_state)
        self.bichar_alphabet.initialWord2idAndId2Word(self.bichar_state)
        self.pos_alphabet.initialWord2idAndId2Word(self.pos_state)

        # copy with the unkID
        self.word_UnkkID = self.word_alphabet.loadWord2idAndId2Word(unkkey)
        self.char_UnkID = self.char_alphabet.loadWord2idAndId2Word(unkkey)
        self.bichar_UnkID = self.bichar_alphabet.loadWord2idAndId2Word(unkkey)
        self.pos_UnkID = self.pos_alphabet.loadWord2idAndId2Word(unkkey)

        # copy with the PaddingID
        self.word_PaddingID = self.word_alphabet.loadWord2idAndId2Word(paddingkey)
        self.char_PaddingID = self.char_alphabet.loadWord2idAndId2Word(paddingkey)
        self.bichar_PaddingID = self.bichar_alphabet.loadWord2idAndId2Word(paddingkey)
        self.pos_PaddingID = self.pos_alphabet.loadWord2idAndId2Word(paddingkey)

        # copy the app seq ID
        self.appID = self.label_alphabet.loadWord2idAndId2Word(app)
        self.sepID =self.label_alphabet.loadWord2idAndId2Word(sep)
        # print(self.appID)
        # print(self.sepID)
        # print(self.word_alphabet.id2words)
        # print(self.word_alphabet.id2words[self.word_UnkkID])
        # print(self.word_UnkkID)
        # print(self.word_alphabet.id2words[self.word_PaddingID])
        # print(self.word_PaddingID)


class Alphabet():
    def __init__(self, min_freq=1):
        self.id2words = []
        self.words2id = collections.OrderedDict()
        self.word2id_id = 0
        self.m_size = 0
        self.min_freq = min_freq

    def initialWord2idAndId2Word(self, data):
        for key in data:
            if data[key] >= self.min_freq:
                Alphabet.loadWord2idAndId2Word(self, key)

    # def loadWord2idAndId2Word(self, string):
    #     if string in self.words2id:
    #         return self.words2id[string]
    #     new_id = self.word2id_id
    #     self.id2words.append(string)
    #     self.words2id[string] = new_id
    #     self.word2id_id += 1
    #     self.m_size = self.word2id_id

    def loadWord2idAndId2Word(self, string):
        if string in self.words2id:
            return self.words2id[string]
        else:
            new_id = self.word2id_id
            self.id2words.append(string)
            self.words2id[string] = new_id
            self.word2id_id += 1
            self.m_size = self.word2id_id
        return new_id

    def from_id(self, qid, defineStr = ''):
        if int(qid) < 0 or self.m_size <= qid:
            return defineStr
        else:
            return self.id2words[qid]

