import matplotlib.pyplot as plt
import os
import numpy as np
import flopy 
import flopy.utils.reference  as srf
import flopy.utils.binaryfile as bf
import pykrige.kriging_tools as kt
from pykrige.ok import OrdinaryKriging

# sample TRUTH MODEL to get observtions (i.e. field measurements) for use in PEST
# also fit variograms based on sample data for kriging step in pilot point approach

# load TRUTH modflow model
mf_path      = 'C:\PEST_examples\pilot_points_example\Truth'+os.sep+'modflow' # path to true model
mf_modelname = 'example_Truth'
mf           = flopy.modflow.Modflow.load(mf_path+os.sep+mf_modelname+ '.nam')# import modflow object
hk= mf.lpf.hk.array[0,:,:]# load K field
hdobj        = bf.HeadFile(mf_path+os.sep+mf_modelname+'.hds', precision = 'single')# load heads
kstpkper =hdobj.get_kstpkper() #list of valid kstep kper from TRUTH model
hds =  hdobj.get_data(kstpkper = kstpkper[0]) # array of heads from final timestep of SS stress period


# create reference grid object corresponding to TRUTH modflow model
xul = -sum(mf.dis.delr)/2                   # modflow model spatial domain upper left x coordinate 
yul =  sum(mf.dis.delc)/2                   # modflow model spatial domain upper left y coordinate
grid_ref = srf.SpatialReference(delr   = mf.dis.delr,   
                                delc   = mf.dis.delc,
                                lenuni = mf.dis.lenuni,
                                xul    = xul,
                                yul    = yul)
# get grid of x, y position of center of each cell
Xc = grid_ref.get_xcenter_array() #
Yc = grid_ref.get_ycenter_array()
X,Y = np.meshgrid(Xc,Yc)

# determine sampling (pilot) points - uniformly spaced on a grid throuout domain
nx_samp = 5
ny_samp = 10
nsamp = nx_samp*ny_samp
sclx = nx_samp/mf.dis.delc[0]#4.5
scly = ny_samp/mf.dis.delr[0]#1E6#7.5
xsamp = np.linspace(xul-xul/sclx,-xul+xul/sclx,nx_samp)
ysamp = np.linspace(yul-yul/scly,-yul+yul/scly,ny_samp)
Xsamp,Ysamp = np.meshgrid(xsamp,ysamp)
r,c = grid_ref.get_rc(Xsamp.reshape(nsamp,),Ysamp.reshape(nsamp,))
r = r.reshape((ny_samp,nx_samp))
c = c.reshape((ny_samp,nx_samp))

## SAMPLE HEADS - (experimental/field data for PEST input)
## and SAMPLE K - (for fitting experimental variogram and kriging intermediate K values from pilot point estimates)
hds_samp = np.zeros((ny_samp,nx_samp)) #experimental head measurements from corresponding cells in TRUTH model 
hk_samp = np.zeros((ny_samp,nx_samp)) #experimental K measurements from corresponding cells in TRUTH model 
for row in np.arange(0,ny_samp):
    for col in np.arange(0,nx_samp):
        hds_samp[row,col] = hds[0,r[row,col],c[row,col]]# Sample head 
        hk_samp[row,col] = hk[r[row,col],c[row,col]]# Sample K  


# Krige experimental K data
variogram_model = 'spherical'
OK_init = OrdinaryKriging(Xsamp.reshape(nsamp,),
                     Ysamp.reshape(nsamp,),
                     hk_samp.reshape(nsamp,),
                     variogram_model=variogram_model,
                     verbose=False,
                     enable_plotting=False)

# get variogram parameters
sill,rng,nug = OK_init.variogram_model_parameters
variogram_parameters = {'sill': sill, 'range': rng, 'nugget':nug}


#hk_pred = ax.imshow(z.data, cmap = 'jet', extent =[xul, -xul, -yul, yul])

# convert pilot point locations from TRUTH to row, col indicies in model used by PEST

# load modflow model used by PEST
mfmdl_path      = os.getcwd()+os.sep+'modflow' # path to true model
mfmdl_modelname = 'example'
mfmdl           = flopy.modflow.Modflow.load(mfmdl_path+os.sep+mfmdl_modelname+ '.nam')# import modflow object
grid_ref_mdl = srf.SpatialReference(delr   = mfmdl.dis.delr,   
                                delc   = mfmdl.dis.delc,
                                lenuni = mfmdl.dis.lenuni,
                                xul    = xul,
                                yul    = yul)

rmdl,cmdl = grid_ref_mdl.get_rc(Xsamp.reshape(nsamp,),Ysamp.reshape(nsamp,))
rmdl = rmdl.reshape((ny_samp,nx_samp))
cmdl = cmdl.reshape((ny_samp,nx_samp))



## save pilot point data and variogram parameters

pp = {'nx':nx_samp,
      'ny':ny_samp,
      'x':Xsamp,
      'y':Ysamp,
      'r':rmdl,
      'c':cmdl,
      'head':hds_samp,
      'variogram_model':variogram_model,
      'variogram_parameters' : variogram_parameters}

np.save('pilot_point_and_variogram_data', pp)




#####################################################      
##### test variogram input parameters feature 
OK = OrdinaryKriging(Xsamp.reshape(nsamp,),
                     Ysamp.reshape(nsamp,),
                     hk_samp.reshape(nsamp,),
                     variogram_model=variogram_model,
                     variogram_parameters = variogram_parameters,
                     verbose=False,
                     enable_plotting=False)

# kriging predictions (for testing)
nx_pred = 80
ny_pred = 50
npred = nx_pred*ny_pred
xpred = np.linspace(xul,-xul,nx_pred)
ypred = np.linspace(yul,-yul,ny_pred)
Xpred,Ypred = np.meshgrid(xpred,ypred)
hk_krig,ss = OK.execute('grid',xpred,ypred)     
      
        



## PLOTS ##

# true K
fig = plt.figure()
ax = fig.gca()
hk_true = ax.imshow(hk, cmap = 'jet', extent =[xul, -xul, -yul, yul])
plt.colorbar(mappable = hk_true,ax = ax, label = 'True K')
ax.set_title('Pilot Point Locations')
#sample_pts = ax.scatter(Xsamp,Ysamp, s = 15, facecolor = 'white', edgecolor = 'black', linewidth = 1)
ax.set_xlabel('x (m)', fontweight = 'bold', fontsize = 8)
ax.set_ylabel('y (m)', fontweight = 'bold', fontsize = 8)

# kriged K
fig = plt.figure()
ax = fig.gca()
hk_krig = ax.imshow(hk_krig.data, cmap = 'jet', extent =[xul, -xul, -yul, yul])
plt.colorbar(mappable = hk_krig,ax = ax, label = 'Kriged K')
ax.set_title('Pilot Point Locations')
#sample_pts = ax.scatter(Xsamp,Ysamp, s = 15, facecolor = 'white', edgecolor = 'black', linewidth = 1)
ax.set_xlabel('x (m)', fontweight = 'bold', fontsize = 8)
ax.set_ylabel('y (m)', fontweight = 'bold', fontsize = 8)

# true heads 
fig = plt.figure()
ax = fig.gca()
heads_true = ax.imshow(hds[0,:,:], cmap = 'jet', extent =[xul, -xul, -yul, yul], vmin = 10, vmax =12)
plt.colorbar(mappable = heads_true,ax = ax, label = 'True Head')
sample_pts = ax.scatter(Xsamp,Ysamp, s = 15, facecolor = 'white', edgecolor = 'black', linewidth = 1)
ax.set_title('Pilot Point Locations')
ax.set_xlabel('x (m)', fontweight = 'bold', fontsize = 8)
ax.set_ylabel('y (m)', fontweight = 'bold', fontsize = 8)   

#plt.imshow(hds_samp, cmap = 'jet', extent =[xul, -xul, -yul, yul], vmin = 10, vmax =12)


###plt.imshow(hk, cmap = 'jet', extent =[xul, -xul, -yul, yul])
##
##plt.colorbar()
##plt.show()
plt.show()
