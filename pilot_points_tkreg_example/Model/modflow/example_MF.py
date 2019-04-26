import numpy as np
import flopy
import sys
import os
import matplotlib.pyplot as plt
import shutil

def example1_Modflow(data):
    modelname = data['modelname']# 'example1'
    

    # Space discretization parameters
    ztop = 0 		# top elevation of aquifer
    zbot = -10 		# bottom elevation of aquifer
    nlay = 1 	        # number of layers 
##    nrow = 100 	        # n rows 
##    ncol = 25           # n cols
    
    Lx = 500 #length of domain in X dir
    Ly = 800 #length of domain in Y dir
    
    delr = (Lx/ncol)*np.ones([ncol,]) # row spacing
    delc = (Lx/ncol)*np.ones([nrow,]) # col spacing
    delv = (ztop - zbot) / nlay # layer spacing
    botm = np.linspace(ztop, zbot, nlay + 1) #top elevation of aquifer and bottom elevation of each layer 


    xul = -Lx/2 # x coordinate for upper left corner of grid
    yul =  Ly/2 # y coordinate for upper left corner of grid

    # Boundary Conditions
    ibound = np.ones((nlay, nrow, ncol), dtype=np.int32)
    ibound[:,0,:]  =   -1  # constant heads on N  border (val<0)
    ibound[:,-1,:] =   -1  # constant heads on S  border (val<0)
    #ibound[:,:,0]  =  -1  # constant heads on E  border (val<0)
    #ibound[:,:,-1] =  -1  # constant heads on W  border (val<0)
    hnoflo = 6666 # head at no flow boundaries (val=0)

    # specify initial heads
    strt = abs(ztop-zbot) * np.ones((nlay, nrow, ncol), dtype=np.float)
    strt[:,0,:] = 12 #  heads on N  border 
    strt[:,-1,:] = 10 #  heads on S  border

    # specify hydraulic conductivity field
    hk = data['hk']
    vka = 1.
    sy = 0.1
    ss = (10**-5)/abs(ztop - zbot)
    laytyp = 1 # 0= confined


    # Time discretization parameters
    nper = 1 # number of stress periods
    perlen = [20000] #length of each stress period (days)
    nstp = [25]# solver calls per stress period
    steady = [True] # Type (steady state or Transient) stress period type
    itmuni = 4 # time units 0 = undefined , 1= seconds, 2 = min , 3 = hours,  4 = days
    lenuni = 2 # length units 2 =  meters 

    # Flopy objects
    modelname = modelname
    mf = flopy.modflow.Modflow(modelname, exe_name='mf2005')
    dis = flopy.modflow.ModflowDis(mf, nlay = nlay, nrow = nrow, ncol = ncol, delr=delr, delc=delc,top=ztop, botm=botm[1:],
                                       nper=nper, perlen=perlen, nstp=nstp,steady=steady,
                                       itmuni = itmuni ,lenuni = lenuni,
                                       xul = xul, yul=yul )

    
    grid_ref = flopy.utils.reference.SpatialReference(delr=mf.dis.delr, delc=mf.dis.delc, lenuni=mf.dis.lenuni ,xul = xul,yul = yul)



    bas = flopy.modflow.ModflowBas(mf, ibound=ibound, strt=strt,hnoflo = hnoflo)
    lpf = flopy.modflow.ModflowLpf(mf, hk=hk, vka=vka, sy=sy, ss=ss, laytyp=laytyp,ipakcb=53)
    pcg = flopy.modflow.ModflowPcg(mf)

    # HYDMOD package for reporting heads only at select locations
    nhyd = data['pp']['nx']*data['pp']['ny'] # number of locations to report heads at
    ihydun = 1 # If ihydun is non-zero hydmod data will be saved
    hydnoh = 9999# is a user-specified value that is output if a value cannot be computed at a hydrograph location

    obs_data = []# list of lists   or numpy array (nhyd, 7) - Each row of obsdata includes data defining pckg (3 character string), arr (2 characater string), intyp (1 character string) klay (int), xl (float), yl (float), hydlbl (14 character string) for each observation.

    x_pos = data['pp']['x'].reshape(nhyd,)
    x_pos = x_pos - grid_ref.xul

    y_pos = data['pp']['y'].reshape(nhyd,)
    y_pos = y_pos + grid_ref.yul
    
    for obs in np.arange(0,nhyd):
        pckg = 'BAS' # is a 3-character flag to indicate which package is to be addressed by hydmod for the hydrograph of each observation point.
        arr = 'HD' # text code indicating which model data value is to be accessed for the hydrograph of each observation point.
        intyp = 'C'
        klay = 0
        xl = "{:.2E}".format(x_pos[obs])
        yl = "{:.2E}".format(y_pos[obs])

        #print(xl)
        hydlbl = 'obs'+str("{:02d}".format(obs))
        #print(len(hydlbl))
        obs_data.append([pckg,arr,intyp,klay,xl,yl,hydlbl])

    
    hymod = flopy.modflow.mfhyd.ModflowHyd(model = mf,
                                           nhyd = nhyd,
                                           ihydun = ihydun,
                                           hydnoh = hydnoh,
                                           obsdata = obs_data,
                                           extension = ['hyd','hyd.bin'])
    
    
    # Output control
    sp_data_OC = {}
    for kper in range(nper):
        for kstp in range(nstp[kper]):
            sp_data_OC[(kper, kstp)] = ['save head',
                                        'save drawdown',
                                        'save budget']
            
            
##    oc = flopy.modflow.ModflowOc(mf, stress_period_data=sp_data_OC,
##                                 compact=True)
    oc = flopy.modflow.ModflowOc(mf, stress_period_data=sp_data_OC,
                                 compact=True, chedfm ='('+str(nrow)+'G11.4)LABEL', extension = ['oc','hds','ddn','cbc','ibo','hyd'] )


    # Write the model input files
    mf.write_input()


    # Run the model
    success, mfoutput = mf.run_model(silent=False, pause=False, report=False)
    if not success:
        raise Exception('MODFLOW did not terminate normally.')


    # read hydmod output and convert to text file
    hydlbl_len=20# length of hydmod labels
    #print(hydlbl_len)
    obsout = flopy.utils.observationfile.HydmodObs(modelname+'.hyd.bin', verbose=True, hydlbl_len=hydlbl_len)
    obsnames = obsout.get_obsnames()
    heads_raw = []
    data = obsout.get_data()
    # create new file
    file = open(modelname+'.hdsraw', 'w')
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

    
        
        

    return mf, grid_ref, heads_raw



# for initial guess for hyraulic conductivity
nrow = 80 	    # n rows in model
ncol = 50           # n cols in model
hk_in = np.ones([nrow,ncol])

# load pilot point location data
fpath = 'C:\PEST_examples\pilot_points_tkreg_example\Model'
pp_data = np.load(fpath + os.sep + 'pilot_point_and_variogram_data.npy').flatten()[0]

data_in = {'modelname': 'example','hk':hk_in, 'pp':pp_data}
mf,grid_ref,h = example1_Modflow(data_in)


#### load estimated HK from pest results
##nparams = pp['nx']*pp['ny']
##fpath = 'C:\PEST_examples\pilot_points_example\pest'
##pest_pars = open(fpath +os.sep+'example'+'.par','r').readlines()
##hk_est = []# estimated hk's from PEST
##for item in np.arange(1,nparams+1):
##    #print(float(pest_pars[item][18:36]))
##    val = '{:4f}'.format(float(pest_pars[item][18:36]),7)
##    #print(val)
##    hk_est.append(val)
##hk_est = np.array(hk_est, dtype = float).reshape(nrow,ncol)
##hk_in = hk_est
##
##data_in = {'modelname': 'example','hk':hk_in}
##mf = example1_Modflow(data_in)


