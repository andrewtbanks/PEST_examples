# write hyd file to hds raw file type
import numpy as np
import flopy
import os
fmain = 'C:\PEST_examples\pilot_points_tkreg_example'
# load model being used with PEST
mf_path      = fmain +os.sep+'Model'+os.sep+'modflow'
mf_modelname = 'example'
mf           = flopy.modflow.Modflow.load(mf_path+os.sep+mf_modelname+ '.nam')# import modflow object

# read hydmod output and convert to text file
hydlbl_len=20# length of hydmod labels
#print(hydlbl_len)
obsout = flopy.utils.observationfile.HydmodObs(mf_modelname+'.hyd.bin', verbose=True, hydlbl_len=hydlbl_len)
obsnames = obsout.get_obsnames()
heads_raw = []
data = obsout.get_data()
# create new file
file = open(mf_modelname+'.hdsraw', 'w')
# write header
header = 'HEADS OUTPUT FOR USE WITH PEST \n'
file.writelines(header)

for i,obs in enumerate(obsnames,0):
    #print(obs)

    #print(i)
    head = data[obs][-1] # get head  at final timestep and format 
    heads_raw.append(head)
    name = 'obs'+"{:02d}".format(i)
    line = name + r' '  + "{:02f}".format(head)+' \n'
    file.writelines(line)
file.close()
