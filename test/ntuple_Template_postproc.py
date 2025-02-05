#!/usr/bin/env python
import os, sys
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True
from importlib import import_module
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.modules.common.countHistogramsModule import countHistogramsProducer
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetHelperRun2       import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.PrefireCorr import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.puWeightProducer import *

from ntuple_Template_Module import * 

import argparse
import re
import optparse

import time
time_begin = time.time()

parser = argparse.ArgumentParser(description='fake photon CR full template production')
parser.add_argument('-f', dest='file', default='', help='File input. In local mode it will be the filepath. In condor mode it will be the dataset name')
parser.add_argument('-m', dest='mode', default='local', help='runmode local/condor')
parser.add_argument('-y', dest='year', default='2018', help='year')
parser.add_argument('-d', dest='isdata',action='store_true',default=False)
parser.add_argument('-p', dest='period',default="B", help="Run period, only work for data")
parser.add_argument('-s', dest='preskim',default='', help="preskim json input")
args = parser.parse_args()

# print ("mode: ", args.mode)
# print ("input file: ", args.file)


if args.isdata:
    if args.year == '2018':
        jetmetCorrector = createJMECorrector(isMC=False, dataYear="UL2018", runPeriod=args.period, metBranchName="MET")
    if args.year == '2017':
        jetmetCorrector = createJMECorrector(isMC=False, dataYear="UL2017", runPeriod=args.period, metBranchName="MET")
    if args.year == '2016':
        jetmetCorrector = createJMECorrector(isMC=False, dataYear="UL2016", runPeriod=args.period, metBranchName="MET")
    if args.year == '2016_PreVFP':
        jetmetCorrector = createJMECorrector(isMC=False, dataYear="UL2016_PreVFP", runPeriod=args.period, metBranchName="MET")
    Modules = [countHistogramsProducer(),first_Template_Module(),jetmetCorrector()]
else:
    if args.year == '2018':
        jetmetCorrector = createJMECorrector(isMC=True, dataYear="UL2018", jesUncert="Total", metBranchName="MET", splitJER=False, applyHEMfix=True)
        Modules = [countHistogramsProducer(),first_Template_Module(),jetmetCorrector(),puWeight_2018()]
    if args.year == '2017':
        jetmetCorrector = createJMECorrector(isMC=True, dataYear="UL2017", jesUncert="Total", metBranchName="MET", splitJER=False)
        Modules = [countHistogramsProducer(),PrefCorr(),first_Template_Module(),jetmetCorrector(),puWeight_2017()]
    if args.year == '2016':
        jetmetCorrector = createJMECorrector(isMC=True, dataYear="UL2016", jesUncert="Total", metBranchName="MET", splitJER=False)
        Modules = [countHistogramsProducer(),PrefCorr(),first_Template_Module(),jetmetCorrector(),puWeight_2016()]
    if args.year == '2016_PreVFP':
        jetmetCorrector = createJMECorrector(isMC=True, dataYear="UL2016_PreVFP", jesUncert="Total", metBranchName="MET", splitJER=False)
        Modules = [countHistogramsProducer(),PrefCorr(),first_Template_Module(),jetmetCorrector(),puWeight_2016()]

if args.file:

    infilelist = []
    jsoninput = None
    fwkjobreport = False

    if args.mode == 'condor':
        import DAS_filesearch as search
        infilelist.append(search.getValidSite(args.file)+args.file) 
    else:
        infilelist = [args.file]

else:

    from PhysicsTools.NanoAODTools.postprocessing.framework.crabhelper import inputFiles,runsAndLumis
    infilelist = inputFiles()
    jsoninput = runsAndLumis()
    fwkjobreport = True

if args.preskim:
    from preselect_help import preselect_json_load
    preselection = preselect_json_load(args.preskim)
else:
    preselection = None

# if args.data and args.year=='2018' and args.period=='D' and ('MuonEG' in infilelist):
if True:
    print 'special treatment for MuonEG_Run2018D'
    import FWCore.PythonUtilities.LumiList as LumiList
    import FWCore.ParameterSet.Config as cms

    lumisToProcess = cms.untracked.VLuminosityBlockRange( LumiList.LumiList(filename="./Cert_314472-325175_13TeV_Legacy2018_Collisions18_JSON.txt").getCMSSWString().split(',') )
    # print lumisToProcess

    runsAndLumis_special = {}
    for l in lumisToProcess:
        if "-" in l:
            start, stop = l.split("-")
            rstart, lstart = start.split(":")
            rstop, lstop = stop.split(":")
        else:
            rstart, lstart = l.split(":")
            rstop, lstop = l.split(":")
        if rstart != rstop:
            raise Exception(
                "Cannot convert '%s' to runs and lumis json format" % l)
        if rstart not in runsAndLumis_special:
            runsAndLumis_special[rstart] = []
        runsAndLumis_special[rstart].append([int(lstart), int(lstop)])
    jsoninput = runsAndLumis_special

p=PostProcessor(".",infilelist,
                branchsel="keep_and_drop.txt",
                cut=preselection,
                modules=Modules,
                justcount=False,
                noOut=False,
                fwkJobReport=fwkjobreport, 
                jsonInput=jsoninput, 
                provenance=True,
                outputbranchsel="output_branch_selection.txt",
                )
p.run()

time_end = time.time()
# print "time cost: ", time_end-time_begin, " sec"