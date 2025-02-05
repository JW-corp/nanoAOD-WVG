import sys,os
import ROOT
import json
import argparse
import pandas as pd
from decimal import Decimal

parser = argparse.ArgumentParser(description='prepare combined cards')
parser.add_argument('-f', dest='file', default='./combine.json', help='input json with configuration')
args = parser.parse_args()

def GetHist(file, variable, process):
    hist = file.Get(str(process + '_' + variable))
    hist.SetDirectory(0)
    return hist

def auto_cal(file, variable, process, uncertainty, bin):

    cal_unc = 1.0

    if 'JES' in uncertainty:
        
        JES_nominal = file.Get(str(process + '_' + variable)).GetBinContent(bin)
        JES_up = file.Get(str(process + '_' + variable + '_JESup')).GetBinContent(bin)
        JES_down = file.Get(str(process + '_' + variable + '_JESdown')).GetBinContent(bin)
        if JES_nominal == 0:
            print 'JES_nominal equals zero in: ', file, process, variable, ' bin: ', bin
            cal_unc = 1
        else:
            cal_unc = 1 + (max(abs(JES_up-JES_nominal), abs(JES_down-JES_nominal)) / JES_nominal)
        return Decimal(cal_unc).quantize(Decimal("0.001"), rounding="ROUND_HALF_UP")
    
    elif 'JER' in uncertainty:
        
        JER_nominal = file.Get(str(process + '_' + variable)).GetBinContent(bin)
        JER_up = file.Get(str(process + '_' + variable + '_JERup')).GetBinContent(bin)
        JER_down = file.Get(str(process + '_' + variable + '_JERdown')).GetBinContent(bin)
        if JER_nominal == 0:
            print 'JER_nominal equals zero in: ', file, process, variable, ' bin: ', bin
            cal_unc = 1
        else:
            cal_unc = 1 + (max(abs(JER_up-JER_nominal), abs(JER_down-JER_nominal)) / JER_nominal)
        return Decimal(cal_unc).quantize(Decimal("0.001"), rounding="ROUND_HALF_UP")

    elif 'stat' in uncertainty:
        stat_unc = file.Get(str(process + '_' + variable)).GetBinError(bin)
        nominal = file.Get(str(process + '_' + variable)).GetBinContent(bin)
        if nominal == 0:
            print 'stat counts equals zero in: ', file, process, variable, ' bin: ', bin
            cal_unc = 1
        else:
            cal_unc = 1 + abs(stat_unc/nominal)
        return Decimal(cal_unc).quantize(Decimal("0.001"), rounding="ROUND_HALF_UP")

    else:
        print "Unknown nuissance parameters: ", uncertainty, " ,Set to 1.0"
        return 1.0

if __name__ == '__main__':

    with open(args.file, "r") as f:
        jsons = json.load(f)
        f.close()
    imax = jsons['utils']['imax']
    tag = jsons['utils']['tag']
    variable = jsons['utils']['variable']

    for region in jsons['regions']:

        # Get All Process
        df = pd.read_csv(jsons['regions'][region]['csv'])
        processes = []
        for process in df.columns:
            # skip type and uncertainty columns
            if ('type' in process) or ('uncertainty' in process):
                continue
            processes.append(process)
        print "processes: ", processes, "\n"

        # Get all histogram
        file_region = ROOT.TFile.Open(jsons['regions'][region]['name'] + '_' + str(tag) + '.root', 'READ')
        hist_region = {}
        for process in processes:
            hist_region[process] = GetHist(file_region, variable, process)
        hist_region['data'] = GetHist(file_region, variable, 'data')
        
        print 'preparing cards for: ', str(jsons['regions'][region]['name'] + '_' + str(tag))
        path_region = str('cards_' + jsons['regions'][region]['name'] + '_' + str(tag))
        if not os.path.exists(path_region):
            os.mkdir(path_region)

        for bin in range(1, jsons['utils']['bins']+1):
            bin_content = jsons['regions'][region]['name'] + '_' + variable + '_bin' + str(bin)
            with open(path_region + '/card_' + bin_content + '.txt', 'w+') as f:
                f.write('imax \t' + str(imax) + '\tnumber of channels\n')
                f.write('jmax \t' + str(len(df.columns)-2-imax) + '\tnumber of bkgs\n')
                f.write('kmax \t' + str(len(df.index)) + '\tnumber of NPs\n')
                f.write('----------------\n')

                f.write('bin \t' + bin_content + '\n')
                if 'SR' in region:
                    # f.write('observation\t' + str(0) + '\n')
                    observation = Decimal(sum([hist_region[process].GetBinContent(bin) for process in processes])).quantize(Decimal("0.001"), rounding="ROUND_HALF_UP")
                    f.write('observation\t' + str(observation) + '\n')
                else:
                    observation = Decimal(sum([hist_region[process].GetBinContent(bin) for process in processes])).quantize(Decimal("0.001"), rounding="ROUND_HALF_UP")
                    f.write('observation\t' + str(observation) + '\n')
                    # f.write('observation\t' + str(hist_region['data'].GetBinContent(bin)) + '\n')
                f.write('----------------\n')

                print_length_1 = 15
                for unc in df.iloc[:,0]:
                    print_length_1 = max(print_length_1, len(str(unc))+10+len("t_enriched"))

                print_length_2 = 15
                f.write('bin'.ljust(print_length_2,' '))
                f.write(' '.ljust(print_length_2,' '))
                for process in processes:
                    print_length_2 = max(print_length_2, len(str(process))+1) 
                    f.write(bin_content.ljust(max(print_length_2,len(bin_content))+1,' '))
                f.write('\n')

                f.write('process'.ljust(print_length_1,' '))
                f.write(' '.ljust(print_length_1,' '))
                for process in processes:
                    f.write(process.ljust(print_length_2, ' '))
                f.write('\n')

                f.write('process'.ljust(print_length_1,' '))
                f.write(' '.ljust(print_length_1,' '))
                for i in range(len(processes)):
                    f.write(str(i).ljust(print_length_2,' '))
                f.write('\n')

                f.write('rate'.ljust(print_length_1,' '))
                f.write(' '.ljust(print_length_1,' '))
                for process in processes:
                    rate = Decimal(hist_region[process].GetBinContent(bin)).quantize(Decimal("0.001"), rounding="ROUND_HALF_UP")
                    if rate < 0:
                        print region, process, bin, "rate < 0, set to 0"
                        f.write(str(0.00).ljust(print_length_2, ' '))
                    else:   
                        f.write(str(rate).ljust(print_length_2, ' '))
                f.write('\n')
                f.write('----------------\n')

                for row in df.index:
                    # print uncertainty source 
                    if "stat" in str(df.iloc[row,0]):
                        f.write((str(jsons["regions"][region]["name"]) + '_' + str(df.iloc[row,0])+"_bin"+str(bin)).ljust(print_length_1,' '))
                    else:
                        f.write(str(df.iloc[row,0]).ljust(print_length_1,' '))
                    # print uncertainty type
                    f.write(str(df.iloc[row,1]).ljust(print_length_1,' '))
                    # cal and print rest
                    for i in range(len(df.iloc[row,2:])):
                        para = df.iloc[row,i+2]
                        if str(para) == 'nan':
                            f.write('-'.ljust(print_length_2,' '))
                        elif str(para) != 'auto_cal':
                            f.write(str(para).ljust(print_length_2,' '))
                        elif str(para) == 'auto_cal':
                            f.write(str(auto_cal(file_region, variable, processes[i], str(df.iloc[row,0]), bin)).ljust(print_length_2,' '))
                    f.write('\n')


                pass
        file_region.Close()

