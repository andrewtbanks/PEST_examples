import numpy as np
import flopy
import sys
import os
import matplotlib.pyplot as plt

def example1_Modflow(data):
    modelname = data['modelname']# 'example1'
    

    # Space discretization parameters
    ztop = 0 		# top elevation of aquifer
    zbot = -10 		# bottom elevation of aquifer
    nlay = 1 	        # number of layers 
    nrow = 800 		# n rows 
    ncol = 500          # n cols

    delr = np.ones([ncol,]) # row spacing
    delc = np.ones([nrow,]) # col spacing
    delv = (ztop - zbot) / nlay # layer spacing
    botm = np.linspace(ztop, zbot, nlay + 1) #top elevation of aquifer and bottom elevation of each layer 

    Lx = np.sum(delr); #length of domain in X dir
    Ly = np.sum(delc); #length of domain in Y dir
    xul = -Lx/2 # x coordinate for upper left corner of grid
    yul =  Ly/2 # y coordinate for upper left corner of grid

    # Boundary Conditions
    ibound = np.ones((nlay, nrow, ncol), dtype=np.int32)
    ibound[:,0,:]  =   -1  # constant heads on N  border (val<0)
    ibound[:,-1,:] =   -1  # constant heads on S  border (val<0)
    #ibound[:,:,0]  =  -1  # constant heads on E  border (val<0)
    #ibound[:,:,-1] =  -1  # constant heads on W  border (val<0)
    hnoflo = 9999 # head at no flow boundaries (val=0)

    # specify initial heads
    strt = abs(ztop-zbot) * np.ones((nlay, nrow, ncol), dtype=np.float)
    strt[:,0,:] = 12  #  heads on N  border 
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

    # Output control
    sp_data_OC = {}
    for kper in range(nper):
        for kstp in range(nstp[kper]):
            sp_data_OC[(kper, kstp)] = ['save head',
                                        'save drawdown',
                                        'save budget']
            
    oc = flopy.modflow.ModflowOc(mf, stress_period_data=sp_data_OC,
                                 compact=True)
##    oc = flopy.modflow.ModflowOc(mf, stress_period_data=sp_data_OC,
##                                 compact=True, chedfm ='('+str(nrow)+'G11.4)LABEL' )
    # Write the model input files
    mf.write_input()


    # Run the model
    success, mfoutput = mf.run_model(silent=False, pause=False, report=True)
    if not success:
        raise Exception('MODFLOW did not terminate normally.')

    return mf



# load hyraulic conductivity data
rawK = np.load('K_field' + os.sep +'K1_n1000.npy')

hk_in = rawK[200:,200:700] # crok hydraulic conductivity field to fit model domain
hk_in = hk_in - np.min(hk_in)
hk_in = hk_in/np.amax(hk_in)
hk_in = (((hk_in+1)**4)-1)# 25*(hk_in + 0.01)

val = 500
hk_in[225:250,100:400] = val
hk_in[300:325,100:400] = val
hk_in[375:400,100:400] = val
hk_in[450:475,100:400] = val
hk_in[525:550,100:400] = val
hk_in[600:625,100:400] = val

#plt.imshow(rawK,cmap = 'jet')
plt.imshow(hk_in,cmap = 'jet')
plt.colorbar()
plt.show()

data_in = {'modelname': 'example_Truth','hk':hk_in}
mf = example1_Modflow(data_in)
