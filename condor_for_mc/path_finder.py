
import sys,os
import argparse
import re
import optparse
sys.path.append('..')
import WZG_selector.DAS_filesearch as search
import json


parser = argparse.ArgumentParser(description='condor for postproc')
parser.add_argument('-f', dest='file', default='', help='json file input')
args = parser.parse_args()

with open(args.file, "r") as f:
	jsons = json.load(f)
	f.close()

initial_path = os.getcwd()


import glob
# Dataset Loop
for dataset in jsons:
	
	os.chdir(initial_path)


	## data/MC type setting
	isdata=False # initilize isdata 
	period='B' # initialize period
	if dataset['type'] !='MC':
		isdata=True

	# MC case
	if not isdata:

		# Private signal case
		if dataset['name'].startswith("/x5/cms/jwkim/store/2018/wza_UL18_sum.root"):
			datasetname = 'WZG_2018'

		# General case
		else:
			datasetname = dataset['name'].split('/')[6].split('_')[0] + '_' + dataset['year']
			
	# Data case
	else:
		run_name    = dataset['name'].split('/')[5]
		data_name   = dataset['name'].split('/')[6]
		period      = run_name[7]
		datasetname = data_name + '_' + run_name
	


	flist = glob.glob(dataset['name'])
	for i,filepath in enumerate(flist):
		
		filename = filepath.split('/')[-1].split('_')[0]
		print("##"*20)
		print("dataset: ",datasetname)
		print("fname: ",filename)
		print("path: ",filepath)
		print("print: ",period)
		
		if i>1:
			break;
