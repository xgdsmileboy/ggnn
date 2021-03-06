#!/usr/bin/env python
# coding=utf-8

import io
import os
import sys
import csv

# train_APIReplacement_Mkdir_0.json_result_valid.txt
keys = ['acc', 'prec', 'recall', 'f1']

def parse(f, dic):
	with open(f, 'r') as f:
		csv_reader = csv.reader(f, delimiter='\t')
		next(csv_reader)
		for row in csv_reader:
			epoch = int(row[0])
			# fname = row[1]
			# loss = float(row[2])

			accs = float(row[3])
			append(dic['acc'], epoch, accs)

			prec = float(row[4])
			append(dic['prec'], epoch, prec)

			recall = float(row[5])
			append(dic['recall'], epoch, recall)

			f1 = float(row[6])
			append(dic['f1'], epoch, f1)

			# speed = float(row[7])
			

def append(dic, key, value):
	if key not in dic:
		dic[key] = [value]
	else :
		dic[key].append(value)

def compute_best(dic, name):
	epoch = 0
	best_avg = 0
	for key, value in dic[name].items():
		avg = sum(value) / len(value)
		if avg > best_avg:
			epoch = key
			best_avg = avg
	return best_avg, epoch


if __name__ == '__main__':
	if len(sys.argv) < 3:
		print('Please input API path like "APIReplacement Mkdir"')
	else:
		dic = {}
		for key in keys:
			dic[key] = {}

		folder = sys.argv[1]
		api = sys.argv[2]
		base = os.path.join("./logs", "{}_{}".format(folder, api))
		for i in range(5):
			f = os.path.join(base, 'train_{}_{}_{}.json_result_valid.txt'.format(folder, api, i))
			parse(f, dic)
		with open(os.path.join(base, 'best.txt'), 'w') as f:
			for key in keys:
				best, epoch = compute_best(dic, key)
				f.write("Best {} : {}\tEpoch : {}\n".format(key, best, epoch))
		
