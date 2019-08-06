import sys
import os
import io
import csv
import json
import ast
import re
from operator import add
from random import shuffle
from random import sample

# filter patterns with given pattern
# this is only used for API replace
def filter(feature_file_name, pattern):
    filtered = []
    print(feature_file_name)
    csv.field_size_limit(sys.maxsize)
    with open(feature_file_name, 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter='\t')
        header = next(csv_reader, None)
        line_count = 0
        # tokens\ttags\tRepAPI\tRetAPI\tBodyAPI\tfile\tline
        for row in csv_reader:
            # seq = row[0] # json string for gnn tokens
            # tags = set(row[1].split(',')) # separated with ',' when there are more than one
            repAPI = row[2] # with the form of API1::API2
            # retAPI = set(row[3].split(',')) # separated with ',' when there are more than one
            # bodyAPI = row[4] # separated with ',' when there are more than one
            # fname = row[5] # absolute file name of the pattern
            # line = int(row[6]) # line number
            if repAPI == pattern:
                filtered.append(row)
    return filtered

# load pre-trained word embedding
def load_embedding():
    dic = {}
    with open('embeddings.txt', 'r') as f:
        for line in f.readlines():
            tokens = line.split('\t')
            dic[tokens[0].rstrip()] = [float(value) for value in tokens[1].split()]
    return dic

# embed a list of tokens, and sum embeddings
def embed_token_list(dic, token_list):
    feature_sum = [0] * len(dic['UNK'])
    # print(token_list)
    # print('before', feature_sum)
    for token in token_list:
        if token in dic :
            feature_sum = list( map(add, feature_sum, dic[token]) )
        else :
            print(token, 'not')
    if sum(feature_sum) == 0 :
        feature_sum = dic['UNK']
    # print('after', feature_sum)
    return feature_sum

# split token into words according to camel case
def word_split(token):
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', token)
    return [m.group(0).lower() for m in matches]

# embed a string, which may be a camel case
def embed_string(dic, string, default_value):
    features = embed_token_list(dic, word_split(string.encode("utf-8")))
    if features == None :
        features = embed_token_list(dic, word_split(default_value))
    if features == None :
        print('should not!')
        features = dic['UNK']
    return features

# embed value type info
def embed_type(dic, type_str, default_value):
    # need to preprocess type info, e.g., java.util.List<java.lang.String> -> List
    index = type_str.find('<')
    if index > 0:
        type_str = type_str[:index]
    type_str = type_str[type_str.rfind('.') + 1:]
    return embed_string(dic, type_str, default_value)
    

default_value_map = {'kind': 'UnknownNode', 'op': 'UnknownUse', 'type': 'UnknownType', 'api': 'UnknownAPI'}

# embed features
def embedding(features):
    dic = load_embedding()
    converted = []
    for row in features:
        seq = row[0]
        obj = json.loads(seq) # {
                              #     "targets": [int,int],
                              #     "graph":[[int, int, int], []],
                              #     "node_features":[[Str, Str, Str, Str], []]
                              # }
        convertedFeature = {}
        for key, value in obj.items():
            if key == 'node_features':
                items = []
                for item in value:
                    comb_feature = []
                    comb_feature.extend(embed_string(dic, item[0], default_value_map['kind']))
                    comb_feature.extend(embed_string(dic, item[1], default_value_map['op']))
                    comb_feature.extend(embed_type(dic, item[2], default_value_map['type']))
                    comb_feature.extend(embed_string(dic, item[3], default_value_map['api']))
                    items.append(comb_feature)
                convertedFeature[key] = items
            else :
                convertedFeature[key] = value
        # convertedFeature['API'] = row[2]
        converted.append(convertedFeature)
    return converted

def split_list(a_list):
    shuffle(a_list)
    cut = len(a_list)//5
    return a_list[:cut], a_list[cut:]

if __name__ == '__main__' :
    pattern = 'java.util.Date.getTime()::java.lang.System.currentTimeMillis()'
    path = './embed/APIReplacement/DateGetTime'# + sys.argv[1]
    files = ['correct.txt', 'wrong.txt']
    
    converted_string = []

    for f in files:
        filtered = filter(os.path.join(path, f), pattern)
        converted = embedding(filtered)
        converted_string.extend([str(ast.literal_eval(json.dumps(item))).replace("'", "\"") for item in converted])
    
    for i in range(5):
        test, train_valid = split_list(converted_string)
        valid, train = split_list(train_valid)
        with open(os.path.join(path, 'train_{}.json'.format(i)), 'w') as f:
            f.write('[{}]'.format(','.join(train)))
        with open(os.path.join(path, 'valid_{}.json'.format(i)), 'w') as f:
            f.write('[{}]'.format(','.join(valid)))
        with open(os.path.join(path, 'test_{}.json'.format(i)), 'w') as f:
            f.write('[{}]'.format(','.join(test)))
