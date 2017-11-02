# coding=utf-8

import os
import re
import torch
import shutil
import random
import unicodedata
from loaddata.Alphabet import Create_Alphabet
from loaddata.Instance import instance
from loaddata.common import sep, app, paddingkey, unkkey, nullkey
# fix the random seed
import hyperparams as hy
torch.manual_seed(hy.seed_num)
random.seed(hy.seed_num)


class load_data():

    def __init__(self):
        print("load data for train/dev/test")
        self.debug_index = 10

    def clean_str(self, string):
        """
        Tokenization/string cleaning for all datasets except for SST.
        Original taken from https://github.com/yoonkim/CNN_sentence/blob/master/process_data.py
        """
        string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)
        string = re.sub(r"\'s", " \'s", string)
        string = re.sub(r"\'ve", " \'ve", string)
        string = re.sub(r"n\'t", " n\'t", string)
        string = re.sub(r"\'re", " \'re", string)
        string = re.sub(r"\'d", " \'d", string)
        string = re.sub(r"\'ll", " \'ll", string)
        string = re.sub(r",", " , ", string)
        string = re.sub(r"!", " ! ", string)
        string = re.sub(r"\(", " \( ", string)
        string = re.sub(r"\)", " \) ", string)
        string = re.sub(r"\?", " \? ", string)
        string = re.sub(r"\s{2,}", " ", string)
        return string.strip()

    def loaddate(self, path, shuffle=False):
        print("loading {} data......".format(path))
        assert path is not None
        insts = []
        with open(path, encoding="UTF-8") as f:
            lines = f.readlines()
            for index, line in enumerate(lines):
                # copy with "/n"
                line = unicodedata.normalize('NFKC', line.strip())
                # init instance
                inst = instance()
                line = line.split(" ")
                count = 0
                for word_pos in line:
                    # segment the word and pos in line
                    word, _, label = word_pos.partition("_")
                    word_length = len(word)
                    inst.words.append(word)
                    inst.gold_seg.append("[" + str(count) + "," + str(count + word_length) + "]")
                    inst.gold_pos.append("[" + str(count) + "," + str(count + word_length) + "]" + label)
                    count += word_length
                    for i in range(word_length):
                        char = word[i]
                        # print(char)
                        inst.chars.append(char)
                        if i == 0:
                            inst.gold.append(sep + "#" + label)
                            inst.pos.append(label)
                        else:
                            inst.gold.append(app)
                char_number = len(inst.chars)
                for i in range(char_number):
                    # copy with the left bichars
                    if i is 0:
                        inst.bichars_left.append(nullkey + inst.chars[i])
                    else:
                        inst.bichars_left.append(inst.chars[i - 1] + inst.chars[i])
                    # copy with the right bichars
                    if i == char_number - 1:
                        inst.bichars_right.append(inst.chars[i] + nullkey)
                    else:
                        inst.bichars_right.append(inst.chars[i] + inst.chars[i + 1])
                # char/word size
                inst.chars_size = len(inst.chars)
                inst.words_size = len(inst.words)
                inst.bichars_size = len(inst.bichars_left)
                inst.gold_size = len(inst.gold)
                # add one inst that represent one sentence into the list
                insts.append(inst)
                if index == self.debug_index:
                    break
        if shuffle is True:
            print("shuffle tha data......")
            random.shuffle(insts)
        # return all sentence in data
        # print(insts[-1].words)
        return insts


if __name__ == "__main__":
    print("Test dataloader........")
    load_data = load_data()
    train_data = load_data.loaddate("../pos_test_data/train.ctb60.pos.hwc", shuffle=True)
    dev_data = load_data.loaddate("../pos_test_data/dev.ctb60.pos.hwc", shuffle=True)
    test_data = load_data.loaddate("../pos_test_data/test.ctb60.pos.hwc", shuffle=True)
    create_alphabet = Create_Alphabet(min_freq=1)
    create_alphabet.createAlphabet(train_data=train_data, dev_data=dev_data, test_data=test_data, debug_index=-1)
    # load_data.loaddate("../pos_test_data/test.ctb60.pos.hwc")
