import sys,os
import argparse
import re
import optparse
sys.path.append('..')
import WZG_selector.DAS_filesearch as search
import json


parser = argparse.ArgumentParser(description='condor for postproc')
parser.add_argument('-f', dest='file', default='', help='json file input')
parser.add_argument('-isdata', dest='isdata', default=False,type=bool, help='json file input')
args = parser.parse_args()

with open(args.file, "r") as f:
	jsons = json.load(f)
	f.close()

initial_path = os.getcwd()
isdata = args.isdata

import glob
# Dataset Loop
for dataset in jsons:
	
	os.chdir(initial_path)


	if not isdata:

		if dataset['name'].startswith("/x5"):
			datasetname = 'WZG_2018'

		else:
			datasetname = dataset['name'].split('/')[9].split('_')[0] + '_' + dataset['year']

			if datasetname.startswith("GluGluToContinTo"):
				datasetname = 'ZZgg_2018'
	else:
		run_name  = dataset['name'].split('/')[8]
		data_name = dataset['name'].split('/')[9]
		year = dataset['year']
		
		datasetname = data_name + '_' + run_name + '_' + year
		

	

	os.system("mkdir -p "+datasetname+"/log")
	os.chdir(datasetname)

	flist = glob.glob(dataset['name'])
	i = 0
	for i,filepath in enumerate(flist):

		
		filename = filepath.split('/')[-1].split('_')[0]
		print("##"*20)
		print("dataset: ",datasetname)
		print("fname: ",filename)
		print("path: ",filepath)


		## -->>  submit.jds script
		with open ("submit_"+datasetname+"_file"+str(i)+"_"+filename+".jdl","w+") as f:
			f.write("universe \t = vanilla\n")
			f.write("executable \t = wrapper_"+datasetname+"_file"+str(i)+"_"+filename+".sh\n")
			f.write("error \t = log/"+datasetname+"_file"+str(i)+"_"+filename+".err\n")
			f.write("output \t = log/"+datasetname+"_file"+str(i)+"_"+filename+".output\n")
			f.write("log \t = log/"+datasetname+"_file"+str(i)+"_"+filename+".log\n\n")
			f.write("should_transfer_files \t = YES\n")
			f.write("when_to_transfer_output \t = ON_EXIT\n")
			f.write("queue 1")
		f.close()
		print "file",str(i),filename," submit code prepared" 




		## -->>  run scruipt
		with open ("wrapper_"+datasetname+"_file"+str(i)+"_"+filename+".sh","w+") as f:
			f.write("#!/bin/bash\n\n")

			# set path
			f.write("initial_path=${PWD}\n\n")
	
			# set CMSENV				
			f.write("export SCRAM_ARCH=slc7_amd64_gcc700\n")
			f.write("source /cvmfs/cms.cern.ch/cmsset_default.sh\n")
			f.write("cd /x5/cms/jwkim/gitdir/JWCorp/JW_analysis/NanoAODTool/CMSSW_10_6_19/src\n")
			f.write("eval `scramv1 runtime -sh`\n")
			f.write("echo $CMSSW_BASE\n\n")

			# set NanoAOD tool and run jobs
			f.write("cd PhysicsTools/NanoAODTools/nanoAOD-WVG/WZG_selector\n")
			f.write("python WZG_postproc.py -f "+filepath+"\n")
			f.write("cp *.root ${initial_path}")
			f.close()


		print "file",str(i),filename," shell prepared" 


		os.system("condor_submit submit_"+datasetname+"_file"+str(i)+"_"+filename+".jdl")
		print "file",str(i),filename," submitted\n" 


	print "total "+str(i)+" file(s) submitted\n" 
