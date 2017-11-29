# coding=utf-8
from loaddata.common import paddingkey
import torch.nn
import torch.nn as nn
import  torch.nn.functional as F
from torch.autograd import Variable
import torch.nn.init as init
import numpy as np
import random
import time
import hyperparams as hy
torch.manual_seed(hy.seed_num)
random.seed(hy.seed_num)

"""
    sequence to sequence Encode model
"""


class Encoder_WordLstm(nn.Module):

    def __init__(self, args):
        print("Encoder model --- LSTMCELL")
        super(Encoder_WordLstm, self).__init__()
        self.args = args

        # random
        self.char_embed = nn.Embedding(self.args.embed_char_num, self.args.embed_char_dim, sparse=False)
        for index in range(self.args.embed_char_dim):
            self.char_embed.weight.data[self.args.create_alphabet.char_PaddingID][index] = 0
        self.char_embed.weight.requires_grad = True

        self.bichar_embed = nn.Embedding(self.args.embed_bichar_num, self.args.embed_bichar_dim, sparse=False)
        for index in range(self.args.embed_bichar_dim):
            self.bichar_embed.weight.data[self.args.create_alphabet.bichar_PaddingID][index] = 0
        self.bichar_embed.weight.requires_grad = True

        # fix the word embedding
        self.static_char_embed = nn.Embedding(self.args.static_embed_char_num, self.args.embed_char_dim, sparse=False)
        init.uniform(self.static_char_embed.weight, a=-np.sqrt(3 / self.args.embed_char_dim),
                     b=np.sqrt(3 / self.args.embed_char_dim))
        self.static_bichar_embed = nn.Embedding(self.args.static_embed_bichar_num, self.args.embed_bichar_dim, sparse=True)
        init.uniform(self.static_bichar_embed.weight, a=-np.sqrt(3 / self.args.embed_bichar_dim),
                     b=np.sqrt(3 / self.args.embed_bichar_dim))

        # load external word embedding
        if args.char_Embedding is True:
            print("char_Embedding")
            pretrained_char_weight = np.array(args.pre_char_word_vecs)
            self.static_char_embed.weight.data.copy_(torch.from_numpy(pretrained_char_weight))
            for index in range(self.args.embed_char_dim):
                self.static_char_embed.weight.data[self.args.create_static_alphabet.char_PaddingID][index] = 0
            self.static_char_embed.weight.requires_grad = False

        if args.bichar_Embedding is True:
            print("bichar_Embedding")
            pretrained_bichar_weight = np.array(args.pre_bichar_word_vecs)
            self.static_bichar_embed.weight.data.copy_(torch.from_numpy(pretrained_bichar_weight))
            # print(self.static_bichar_embed.weight.data[self.args.create_static_alphabet.bichar_PaddingID])
            # print(self.static_bichar_embed.weight.data[self.args.create_static_alphabet.bichar_UnkID])
            for index in range(self.args.embed_bichar_dim):
                self.static_bichar_embed.weight.data[self.args.create_static_alphabet.bichar_PaddingID][index] = 0
            self.static_bichar_embed.weight.requires_grad = False

        self.lstm_left = nn.LSTMCell(input_size=self.args.hidden_size, hidden_size=self.args.rnn_hidden_dim, bias=True)
        self.lstm_right = nn.LSTMCell(input_size=self.args.hidden_size, hidden_size=self.args.rnn_hidden_dim, bias=True)

        # init lstm weight and bias
        init.xavier_uniform(self.lstm_left.weight_ih)
        init.xavier_uniform(self.lstm_left.weight_hh)
        init.xavier_uniform(self.lstm_right.weight_ih)
        init.xavier_uniform(self.lstm_right.weight_hh)
        value = np.sqrt(6 / (self.args.rnn_hidden_dim + 1))
        self.lstm_left.bias_hh.data.uniform_(-value, value)
        self.lstm_left.bias_ih.data.uniform_(-value, value)
        self.lstm_right.bias_hh.data.uniform_(-value, value)
        self.lstm_right.bias_ih.data.uniform_(-value, value)

        self.hidden_l = self.init_hidden_cell(self.args.batch_size)
        self.hidden_r = self.init_hidden_cell(self.args.batch_size)

        self.dropout = nn.Dropout(self.args.dropout)
        self.dropout_embed = nn.Dropout(self.args.dropout_embed)

        self.input_dim = (self.args.embed_char_dim + self.args.embed_bichar_dim) * 2
        if self.args.use_cuda is True:
            self.liner = nn.Linear(in_features=self.input_dim, out_features=self.args.hidden_size, bias=True).cuda()
        else:
            self.liner = nn.Linear(in_features=self.input_dim, out_features=self.args.hidden_size, bias=True)

        # init linear
        init.xavier_uniform(self.liner.weight)
        init_linear_value = np.sqrt(6 / (self.args.hidden_size + 1))
        self.liner.bias.data.uniform_(-init_linear_value, init_linear_value)

    def init_hidden_cell(self, batch_size=1):
        # the first is the hidden h
        # the second is the cell  c
        if self.args.use_cuda is True:
            return (Variable(torch.zeros(batch_size, self.args.rnn_hidden_dim)).cuda(),
                    Variable(torch.zeros(batch_size, self.args.rnn_hidden_dim)).cuda())
        else:
            return (Variable(torch.zeros(batch_size, self.args.rnn_hidden_dim)),
                    Variable(torch.zeros(batch_size, self.args.rnn_hidden_dim)))

    def init_cell_hidden(self, batch=1):
        if self.args.use_cuda is True:
            return (torch.autograd.Variable(torch.zeros(batch, self.args.rnn_hidden_dim)).cuda(),
                    torch.autograd.Variable(torch.zeros(batch, self.args.rnn_hidden_dim)).cuda())
        else:
            return (torch.autograd.Variable(torch.zeros(batch, self.args.rnn_hidden_dim)),
                    torch.autograd.Variable(torch.zeros(batch, self.args.rnn_hidden_dim)))

    # @time
    def forward(self, features):
        batch_length = features.batch_length
        char_features_num = features.static_char_features.size(1)

        char_features = self.char_embed(features.char_features)
        bichar_left_features = self.bichar_embed(features.bichar_left_features)
        bichar_right_features = self.bichar_embed(features.bichar_right_features)

        # fix the word embedding
        static_char_features = self.static_char_embed(features.static_char_features)
        static_bichar_l_features = self.static_bichar_embed(features.static_bichar_left_features)
        static_bichar_r_features = self.static_bichar_embed(features.static_bichar_right_features)

        # dropout
        char_features = self.dropout_embed(char_features)
        bichar_left_features = self.dropout_embed(bichar_left_features)
        bichar_right_features = self.dropout_embed(bichar_right_features)
        static_char_features = self.dropout_embed(static_char_features)
        static_bichar_l_features = self.dropout_embed(static_bichar_l_features)
        static_bichar_r_features = self.dropout_embed(static_bichar_r_features)

        # left concat
        left_concat = torch.cat((char_features, static_char_features, bichar_left_features, static_bichar_l_features), 2)
        # right concat
        right_concat = torch.cat((char_features, static_char_features, bichar_right_features, static_bichar_r_features), 2)

        # non-linear
        left_concat_non_linear = self.dropout(F.tanh(self.liner(left_concat)))
        left_concat_input = left_concat_non_linear.permute(1, 0, 2)

        right_concat_non_linear = self.dropout(F.tanh(self.liner(right_concat)))
        right_concat_input = right_concat_non_linear.permute(1, 0, 2)

        # # init hidden cell
        # self.hidden = self.init_hidden_cell(batch_size=batch_length)
        # left_lstm_output, _ = self.lstm_left(left_concat_input)

        left_h, left_c = self.init_cell_hidden(batch_length)
        left_lstm_output = []
        for idx in range(char_features_num):
            left_h, left_c = self.lstm_left(left_concat_input[idx], (left_h, left_c))
            left_h = self.dropout(left_h)
            left_lstm_output.append(left_h.view(batch_length, 1, self.args.rnn_hidden_dim))
        left_lstm_output = torch.cat(left_lstm_output, 1)

        # self.hidden_r = self.init_hidden_cell(batch_length)
        right_h, right_c = self.init_cell_hidden(batch_length)
        right_lstm_output = []
        for idx in reversed(range(char_features_num)):
            right_h, right_c = self.lstm_right(right_concat_input[idx], (right_h, right_c))
            right_h = self.dropout(right_h)
            right_lstm_output.insert(0, right_h.view(batch_length, 1, self.args.rnn_hidden_dim))
        right_lstm_output = torch.cat(right_lstm_output, 1)

        encoder_output = torch.cat((left_lstm_output, right_lstm_output), 2)

        return encoder_output


