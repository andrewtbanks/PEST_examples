import numpy as np
import flopy
import sys
import os
import shutil
import flopy.utils.reference  as srf
import pykrige.kriging_tools as kt
from pykrige.ok import OrdinaryKriging
import matplotlib.pyplot as plt


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
   
    
    # Output control
    sp_data_OC = {}
    for kper in range(nper):
        for kstp in range(nstp[kper]):
            sp_data_OC[(kper, kstp)] = ['save head',
                                        'save drawdown',
                                        'save budget']
            
            
    oc = flopy.modflow.ModflowOc(mf, stress_period_data=sp_data_OC,
                                 compact=True)
#    oc = flopy.modflow.ModflowOc(mf, stress_period_data=sp_data_OC,
#                                 compact=True, chedfm ='('+str(nrow)+'G11.4)LABEL', extension = ['oc','hds','ddn','cbc','ibo','hyd'] )


    # Write the model input files
    mf.write_input()


    # Run the model
    success, mfoutput = mf.run_model(silent=False, pause=False, report=False)
    if not success:
        raise Exception('MODFLOW did not terminate normally.')

    return mf


# load modflow model object used by PEST
fmain = 'C:\PEST_examples\pilot_points_example' # directory folder for all data used in this PEST run (MODEL, TRUTH, PEST results etc.. )

mf_path      = fmain + os.sep +'Model'+os.sep+'modflow'
mf_modelname = 'example'
mf_pst       = flopy.modflow.Modflow.load(mf_path+os.sep+mf_modelname+ '.nam')# import modflow object
# create reference grid object corresponding to model
xul = -sum(mf_pst.dis.delr)/2                   # modflow model spatial domain upper left x coordinate 
yul =  sum(mf_pst.dis.delc)/2                   # modflow model spatial domain upper left y coordinate
grid_ref = srf.SpatialReference(delr   = mf_pst.dis.delr,   
                                delc   = mf_pst.dis.delc,
                                lenuni = mf_pst.dis.lenuni,
                                xul    = xul,
                                yul    = yul)
nrow = mf_pst.nrow	    # n rows in model
ncol = mf_pst.ncol          # n cols in model
hk_in = np.zeros([nrow,ncol])
hk = mf_pst.lpf.hk.array[0,:,:]


### for initial guess for hyraulic conductivity
##nrow = 80 	    # n rows in model
##ncol = 50           # n cols in model
##hk_in = np.ones([nrow,ncol])

# load pilot point location data
fpath = fmain + os.sep + 'Model'
pp_data = np.load(fpath + os.sep + 'pilot_point_and_variogram_data.npy').flatten()[0]
nx = pp_data['nx'] # number of pilot points in x dir
ny = pp_data['ny'] # number of pilot points in y dir
nparams = nx*ny


## load estimated HK from pest results
fpath = fmain + os.sep + 'pest'
pest_pars = open(fpath +os.sep+'example'+'.par','r').readlines()
hk_est = []# estimated hk's at pilot points from PEST

for item in np.arange(1,nparams+1):
    #print(float(pest_pars[item][18:45]))
    val = '{:4f}'.format(float(pest_pars[item][18:45]),7)
    #print(val)
    hk_est.append(val)    
hk_est = np.array(hk_est, dtype = float).reshape(nparams)

# krige pilot point values to modflow model grid
OK = OrdinaryKriging(pp_data['x'].reshape(nparams,),
                     pp_data['y'].reshape(nparams,),
                     hk_est,
                     variogram_model=pp_data['variogram_model'],
                     variogram_parameters = pp_data['variogram_parameters'],
                     verbose=False,
                     enable_plotting=False)

xpred = grid_ref.get_xcenter_array()+xul# get list of x of centers for cells
ypred = grid_ref.get_ycenter_array()-yul# get list of y of centers for cells
Xpred,Ypred = np.meshgrid(xpred,ypred) # form grid
pred,ss = OK.execute('grid',xpred,ypred) 
hk_krig = abs(pred.data)

#run model with optimized pilot point K parameters kriged to MF grid

data_in = {'modelname': 'example_pest_results','hk':hk_krig}
mf = example1_Modflow(data_in)



## PLOTS
# kriged K
fig = plt.figure()
ax = fig.gca()
hk_kr = ax.imshow(hk_krig, cmap = 'jet', extent =[xul, -xul, -yul, yul])
pred_pts = ax.scatter(Xpred,Ypred, s = 1, facecolor = 'white', edgecolor = 'black', linewidth = 0.1)
plt.colorbar(mappable = hk_kr,ax = ax, label = 'Kriged K')
#plt.show()


# last pest K
fig = plt.figure()
ax = fig.gca()
hk_p = ax.imshow(hk, cmap = 'jet', extent =[xul, -xul, -yul, yul])
pred_pts = ax.scatter(Xpred,Ypred, s = 1, facecolor = 'white', edgecolor = 'black', linewidth = 0.1)
plt.colorbar(mappable = hk_p,ax = ax, label = 'last pest K')
plt.show()


