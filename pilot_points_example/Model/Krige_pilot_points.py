import os
import numpy as np
import flopy 
import flopy.utils.reference  as srf
import pykrige.kriging_tools as kt
from pykrige.ok import OrdinaryKriging
import matplotlib.pyplot as plt

# load model being used with PEST
mf_path      = os.getcwd()+os.sep+'modflow'
mf_modelname = 'example'
mf           = flopy.modflow.Modflow.load(mf_path+os.sep+mf_modelname+ '.nam')# import modflow object
# create reference grid object corresponding to model
xul = -sum(mf.dis.delr)/2                   # modflow model spatial domain upper left x coordinate 
yul =  sum(mf.dis.delc)/2                   # modflow model spatial domain upper left y coordinate
grid_ref = srf.SpatialReference(delr   = mf.dis.delr,   
                                delc   = mf.dis.delc,
                                lenuni = mf.dis.lenuni,
                                xul    = xul,
                                yul    = yul)

# load current K array
hk           = np.zeros(np.shape(mf.lpf.hk.array[0,:,:]))
hk[:,:] = mf.lpf.hk.array[0,:,:]
# load K field
#hk[10:50,10:50] = 9

# load pilot point data
fpath = os.getcwd() +os.sep +'pilot_point_and_variogram_data.npy' # path to pilot point data
pp = np.load(fpath).flatten()[0]
n_pp = pp['nx']*pp['ny'] # number of pilot points

# get hk parameter value at each pilot point
hk_pp = hk[pp['r'],pp['c']]



# krige pilot point parameters using experimental variogram data
OK = OrdinaryKriging(pp['x'].reshape(n_pp,),
                     pp['y'].reshape(n_pp,),
                     hk_pp.reshape(n_pp,),
                     variogram_model=pp['variogram_model'],
                     variogram_parameters = pp['variogram_parameters'],
                     verbose=False,
                     enable_plotting=False)

# kriging predictions
xpred = grid_ref.get_xcenter_array()+xul# get list of x of centers for cells
ypred = grid_ref.get_ycenter_array()-yul# get list of y of centers for cells
Xpred,Ypred = np.meshgrid(xpred,ypred) # form grid
pred,ss = OK.execute('grid',xpred,ypred)  
hk_krig = abs(pred.data)




# update hk and rewrite .lpf file
hknew = mf.lpf.hk.array
hknew[0,:,:] = hk_krig
hkout = flopy.utils.util_array.Util3d(mf,shape = (mf.nlay,mf.nrow,mf.ncol), dtype = np.float32, value = hknew, name = 'hk')
mf.lpf.hk = hkout
mf.lpf.fn_path = mf_path+os.sep+mf.lpf.file_name[0]
mf.lpf.write_file()

# retrieve updated K array for testing purposes)
hk_new = mf.lpf.hk.array[0,:,:]


####
#### PLOTS 
##
### kriged K
##fig = plt.figure()
##ax = fig.gca()
##hk_kr = ax.imshow(hk_krig.data, cmap = 'jet', extent =[xul, -xul, -yul, yul])
##pred_pts = ax.scatter(Xpred,Ypred, s = 1, facecolor = 'white', edgecolor = 'black', linewidth = 0.1)
##plt.colorbar(mappable = hk_kr,ax = ax, label = 'Kriged K')
##
### true K
##fig = plt.figure()
##ax = fig.gca()
##hk_true = ax.imshow(hk, cmap = 'jet', extent =[xul, -xul, -yul, yul])
##pilot_pts = ax.scatter(pp['x'],pp['y'], s = 15, facecolor = 'white', edgecolor = 'black', linewidth = 1)
##plt.colorbar(mappable = hk_true,ax = ax, label = 'True K')
##
### updated K
##fig = plt.figure()
##ax = fig.gca()
##hk_n = ax.imshow(hk_new, cmap = 'jet', extent =[xul, -xul, -yul, yul])
##pilot_pts = ax.scatter(pp['x'],pp['y'], s = 15, facecolor = 'white', edgecolor = 'black', linewidth = 1)
##plt.colorbar(mappable = hk_n,ax = ax, label = 'updated K')
##plt.show()
