import matplotlib.pyplot as plt
import os
import numpy as np
import flopy
import flopy.utils.binaryfile as bf
import flopy.utils.formattedfile as ff
import flopy.utils.reference  as srf
import shutil

fmain =r'C:\PEST_examples\fault_example' # main directory for all files

# specify modflow modeldirectory and load relevant model data 
mfdir = fmain +os.sep+'Model\modflow'
mdlname  = 'example' # name of modflow model  
mf           = flopy.modflow.Modflow.load(mfdir+os.sep+mdlname+ '.nam')               # import modflow object
hdobj = ff.FormattedHeadFile(mfdir+os.sep+mdlname+'.hds', precision = 'single') # import heads file as flopy object ( output from modflow)
hk = mf.lpf.hk.array # get hydraulic conductivity array (used for initial guess for parameters) 

Lx =sum(mf.dis.delr.array)
Ly =sum(mf.dis.delc.array)
xul = -Lx/2
yul = Ly/2
grid_ref = flopy.utils.reference.SpatialReference(delr=mf.dis.delr, delc=mf.dis.delc, lenuni=mf.dis.lenuni ,xul = xul,yul = yul)

## load pilot point data
fpath = fmain +os.sep+'Model\pilot_point_and_variogram_data.npy' # path to pilot point data
pp = np.load(fpath).flatten()[0]
nx = pp['nx']
ny = pp['ny']
n_pp = pp['nx']*pp['ny'] # number of pilot points





## use flopy to generate tempate file
pnames_raw = np.chararray([ny,nx],itemsize = 6) # just parameter name
params = [] # list of parameter objects of type flopy.pest.params.Params.

startvalue = 1*np.ones((ny,nx))
lbound = 0.01*np.ones((ny,nx))
ubound = 10*np.ones((ny,nx))

for i in np.arange(0,ny):
    for j in np.arange(0,nx):

        row = pp['r'][i,j]
        col = pp['c'][i,j]

        #print([row,col])
        name = 'hk'+str("{:02d}".format(row))+str("{:02d}".format(col))
        pnames_raw[i,j] = name
        # flopy param class for each parameter
        span = {'idx':(0,row,col)} # (lay,row,col) index for parameter 
        param = flopy.pest.params.Params('LPF','hk',parname = name,startvalue= startvalue[i,j], lbound = lbound[i,j], ubound= ubound[i,j], span = span) 
        params.append(param)                    
pnames_raw = pnames_raw.decode("utf-8")
tpl = flopy.pest.templatewriter.TemplateWriter(mf,params)
tpl.write_template()




###################
#### write instruction file
instruction = open(mdlname+'.ins','w')
delim = '@'
instruction.writelines('pif '+delim  +'\n')

# open .hds file, retrieve data and close file
file = open(mfdir+os.sep+mdlname+'.hdsraw', 'r')
hds = file.readlines()

#retrieve headers
nstp = mf.dis.nstp[0] # number of timesteps in model
hds_marker = hds[0][0:30]
file.close()


# define observation names (model output)
obsnames = np.chararray([ny,nx],itemsize = 9)
obsnames_raw = np.chararray([ny,nx],itemsize = 9)
for i in np.arange(0,ny):
    for j in np.arange(0,nx):
        row = pp['r'][i,j]
        col = pp['c'][i,j]
        
        name_raw = 'obs'+str("{:02d}".format(row))+str("{:02d}".format(col))
        obsnames_raw[i,j] = name_raw
        
        name = '['+name_raw+']'
        obsnames[i,j] = name
        
obsnames = obsnames.decode("utf-8")       
obsnames_raw = obsnames_raw.decode("utf-8") 

line_advance =  'l1' # number of lines to advance after each primary marker
width = 11 # number of spaces occupied by each head entry
primary_marker = delim + hds_marker +delim +'\n' # primary marker for identifying observations 
instruction.writelines(primary_marker)

for i in np.arange(0,ny):
    for j in np.arange(0,nx):
        obstxt = obsnames[i,j]+'7:15'
        line = ' '.join([line_advance,obstxt])
        instruction.writelines(line + ' \n')          
instruction.close()
        


## create control file
control = open(mdlname+'.pst','w')
delim = ' '
# write header
control.writelines('pcf \n')
## control data

# first line
control.writelines('* control data \n')
#second line
RSTFLE = 'norestart' # restart or norestart
PESTMODE = 'estimation' # mode

line = delim.join([RSTFLE,PESTMODE])
control.writelines(line+  '\n')

# third line
NPAR = n_pp # number of parameters
NOBS = n_pp # number of observations
NPARGP = 1 # number of parameter groups
NPRIOR = 0 # number of articles of prior information
NOBSGP = 1 # number of observation groups

vals = [NPAR,NOBS,NPARGP,NPRIOR,NOBSGP]
vals = [str(item) for item in vals]
line = delim.join(vals)
control.writelines(line+  '\n')

# fourth line
NTPLFLE = 1 # number of model input files which contain parameters
NINSFLE = 1 # number of instruction files (one for each model output file containing model-generated observations)
PRECIS = 'single' # output precision 
DPOINT = 'point' # decimal place representation (nopoint omits redundant decimils - not reccomended)
NUMCOM = 1 #controls how PEST takes derivatives (set to 1 normally)
JACFILE = 0 #controls how PEST takes derivatives (set to 0 normally)
MESSFILE = 0 #controls how PEST takes derivatives (set to 0 normally)

vals = [NTPLFLE,NINSFLE,PRECIS, DPOINT, NUMCOM, JACFILE, MESSFILE]
vals = [str(item) for item in vals]
line = delim.join(vals)
control.writelines(line+  '\n')

#fifth line
RLAMBDA1 = 10.0 # initial value of marquet lambda (10.0 appropriate in most cases - rasie if normal matrix is singular)
RLAMFAC = 2.0 # factory by which marquet lambda is adjusted by PEST (2.0 works good, so does -3)
PHIRATSUF = 0.3 # something.. (pg 93 of pdf)
PHIREDLAM = 0.01 # objective function precision -- choose between (0.01 and 0.05)
NUMLAM = 5 # upper limit of number of lambdas that PEST will test (5-10 works, closer to 10 usually)
JACUPDATE = 0 # number of Broydean updates -- how often jacobian is updated during second part of PEST iteration (workds well sometimes, and not well other times)
LAMFORGIVE = 'lamforgive'
DERFORGIVE = 'derforgive'

vals = [RLAMBDA1,  RLAMFAC, PHIRATSUF, PHIREDLAM, NUMLAM, JACUPDATE, LAMFORGIVE, DERFORGIVE]
vals = [str(item) for item in vals]
line = delim.join(vals)
control.writelines(line+  '\n')

#sixth line
RELPARMAX = 10# (percent)maximum relative change a parameter is allowed to undergo between optimization iterations
FACPARMAX = 10#maximum factor change that a parameter is allowed to undergo
#ABSPARMAX = #maximum absolute change that parameters assigned to change-group N are allowed to undergo - not needed if no prameters are designated as absolute limited in the "parameter data" section
FACORIG = 0.001 # must be greater than zero, helps with obj fcn imnimization convergence 
IBOUNDSTICK = 4 # will glue a parameter to its upper/lower bound if it stays there after n iterations (2-4 is a good choice) - OMIT USUALLY
vals = [RELPARMAX,FACPARMAX,FACORIG,IBOUNDSTICK]
vals = [str(item) for item in vals]
line = delim.join(vals)
control.writelines(line+  '\n')
# seventh line
PHIREDSWH = 0.1
control.writelines(str(PHIREDSWH)+  '\n')

#eigth line
NPOTMAX = 50 # maximum number of iterations for optimization
PHIREDSTP = 0.005 # convergence tolerence for optimization
NPHISTP = 4 # minimum number of optimization iterations
NPHINORED = 3 # terminate optimization if n iterations have not lowered the objective function
RELPARSTP = 0.005 #If the magnitude of the maximum relative parameter change between iterations is less than RELPARSTP over NRELPAR successive iterations, PEST will cease execution.
NRELPAR = 4 # see above
#PHISTOPTHRESH = 0 # cease execution if obj function falls below this value at any time
vals = [NPOTMAX, PHIREDSTP, NPHISTP, NPHINORED, RELPARSTP, NRELPAR]
vals = [str(item) for item in vals]
line = delim.join(vals)
control.writelines(line+  '\n')

#ninth line
ICOV = 0 # 0 means not record, 1 means record
ICOR = 0 # 0 means not record, 1 means record
IEIG = 0 # 0 means not record, 1 means record
vals = [ICOV,ICOR,IEIG]
vals = [str(item) for item in vals]
line = delim.join(vals)
control.writelines(line+  '\n')

##parameter groups
# first line
control.writelines('* parameter groups \n')
#second line (Parameter group 1)
PARGPNME = 'hk' # parameter group name (one for each parameter group)
INCTYP = 'relative' # type of increment used for forward-difference calculation of derivatives (“relative”, “absolute” or “rel_to_max”.)
DERINC = 0.01 # value of increment for INCTYP
DERINCLB = 0.0 #lower bound  on parameter increments; this lower bound is the same for all group members
FORCEN  ='switch' #- 'switch' best -- 'always_2' # “always_3 “always_5' -- finite differencing type for param- _n is number of midel runs per adjustable parameter - switch uses 5 pointmethod when obj fcn is close to minimum for better performance
DERINCMUL = 1.5 #increase the value of the increment  used for forward difference derivatives calculation (1-2 ususlly works)
DERMTHD = 'parabolic' #which three-point derivative method to use “parabolic”, “best_fit” or “outside_pts” (parabolic normally best)
vals = [PARGPNME, INCTYP, DERINC, DERINCLB, FORCEN, DERINCMUL, DERMTHD]
vals = [str(item) for item in vals]
line = delim.join(vals)
control.writelines(line+  '\n')

# parameter data
#first line
control.writelines('* parameter data \n')

#First part - one line for each estmiated parameter - -Lines 2-NPAR+2
#for par in np.arange(0,NPAR):
for i in np.arange(0,ny):
    for j in np.arange(0,nx):
        PARNME = pnames_raw[i,j] # parameter name
        PARTRANS = 'none' # 'fixed','tied','log' (log can help inversion alot if parameter doesnt take zero or negative values)
        PARCHGLIM = 'relative' # designate whether an adjustable parameter is relative-limited, factor-limited or absolute-limited
        PARVAL1 = 5# Initial parameter value # hk[0,i,j]
        PARLBND = 0.0001 # parameter lower bound
        PARUBND = 50 # parameter upper bound
        PARGP = 'hk' # name of parameter group param belongs to
        SCALE = 1.0 # parameter scale
        OFFSET = 0.0 # paramter offset
        DERCOM = 1 # not sure exactly what this is (pg 121 of pdf)

        vals = [PARNME, PARTRANS, PARCHGLIM, PARVAL1, PARLBND, PARUBND, PARGP,SCALE,OFFSET,DERCOM]
        vals = [str(item) for item in vals]
        line = delim.join(vals)
        control.writelines(line+  '\n')
# second part - one line for each tied parameter
# no tied parameters here



#observation groups
#first line
control.writelines('* observation groups \n')
# second line  (one line for each observation group or prior information group)
OBGNME = 'heads' # observarion group name
control.writelines(OBGNME +' \n')
# no prior information here

#observation data
#first line
control.writelines('* observation data \n')

# one line for each observation listed in the in the PEST instruction file
# Get observations (heads) from TRUTH corresponding to each cell int the MODFLOW model
#true_hds = hdobj_truth.get_data(totim = 2000)
measured_hds = np.zeros([ny,nx], dtype = float)# measured TRUTH heads at each cell on MODFLOW MODEL

# get x,y centroid for each cell in truth and MODFLOW model
##xct = grid_ref_truth.get_xcenter_array()+ xul
##yct = grid_ref_truth.get_ycenter_array()- yul
##Xt,Yt = np.meshgrid(xct,yct)
##
##xc = grid_ref.get_xcenter_array()+ xul
##yc = grid_ref.get_ycenter_array()- yul
##X,Y = np.meshgrid(xc,yc)

# get measurment value for each MODFLOW model cell
for i in np.arange(0,ny):
    for j in np.arange(0,nx):
        measured_hds[i,j] = pp['head'][i,j]
        OBSNME = obsnames_raw[i,j]  # name of observation variable
        OBSVAL = '{:.2f}'.format(round(measured_hds[i,j],7))  # field or lab measurment corresponding to observaation variable (for obj fun)
        WEIGHT = 1
        OBSGNME = 'heads'

        vals = [OBSNME, OBSVAL, WEIGHT, OBSGNME]
        vals = [str(item) for item in vals]
        line = delim.join(vals)
        control.writelines(line+  '\n')


#Model command line
#first line
control.writelines('* model command line \n')
# second line (once for each NUMCOM command lines)
fpath = fmain +os.sep
COMLINE = fpath +r'Model\modflow\run_model'
control.writelines(COMLINE+  '\n')
#Model input/output
#first line
control.writelines('* model input/output \n')
# one line for each template file 
TEMPFLE = fpath +'pest\example.lpf.tpl' # name of template file 
INFLE = fpath +'Model\modflow\example.lpf' #name of model input file corresponding to template file
vals = [TEMPFLE, INFLE]
vals = [str(item) for item in vals]
line = delim.join(vals)
control.writelines(line+  '\n')

# one line for each instruction file
INSFLE = fpath +'pest\example.ins'# name of instruction file
OUTFLE = fpath +'Model\modflow\example.hdsraw'#name of model output file corresponding to template file
vals = [INSFLE, OUTFLE]
vals = [str(item) for item in vals]
line = delim.join(vals)
control.writelines(line+  '\n')

control.close()

