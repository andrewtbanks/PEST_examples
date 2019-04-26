import matplotlib.pyplot as plt
import os
import numpy as np
import flopy
import flopy.utils.binaryfile as bf
import flopy.utils.formattedfile as ff
import flopy.utils.reference  as srf
import shutil

fmain = r'C:\PEST_examples\fault_example' # directory folder for all data used in this PEST run (MODEL, TRUTH, PEST results etc.. )

# Load TRUTH model  
mfdir = fmain+os.sep+'Truth\modflow'
mdlname  = 'example_Truth' # name of TRUTH modflow model
mf_truth           = flopy.modflow.Modflow.load(mfdir+os.sep+mdlname+ '.nam')               # import modflow object
hdobj_truth        = bf.HeadFile(mfdir+os.sep+mdlname+'.hds', precision = 'single')         # import heads file as flopy object ( output from modflow)
hd_truth = hdobj_truth.get_data((2,0))[0,:,:]
#hdobj_truth = ff.FormattedHeadFile(mfdir+os.sep+mdlname+'.hds', precision = 'single')
hk_truth = mf_truth.lpf.hk.array[0,:,:] # get hydraulic conductivity array (used for initial guess for parameters)
Lx =sum(mf_truth.dis.delr.array)
Ly =sum(mf_truth.dis.delc.array)
xul = -Lx/2
yul = Ly/2
grid_ref_truth = flopy.utils.reference.SpatialReference(delr=mf_truth.dis.delr, delc=mf_truth.dis.delc, lenuni=mf_truth.dis.lenuni ,xul = xul,yul = yul)
Xt,Yt = np.meshgrid(grid_ref_truth.get_xcenter_array()+xul,grid_ref_truth.get_ycenter_array()-yul)



# specify modflow model Results directory and load relevant model data 
mfdir = fmain+os.sep+'Model_results\modflow'
mdlname  = 'example_pest_results' # name of modflow model
# load flopy modflow model   
mf  = flopy.modflow.Modflow.load(mfdir+os.sep+mdlname+ '.nam')               # import modflow object
hdobj_est        = bf.HeadFile(mfdir+os.sep+mdlname+'.hds', precision = 'single')
hd_est = hdobj_est.get_data((2,0))[0,:,:]
#hdobj = ff.FormattedHeadFile(mfdir+os.sep+mdlname+'.hds', precision = 'single') # import heads file as flopy object ( output from modflow)
hk_est = mf.lpf.hk.array[0,:,:] # get hydraulic conductivity array (used for initial guess for parameters) 
grid_ref = flopy.utils.reference.SpatialReference(delr=mf.dis.delr, delc=mf.dis.delc, lenuni=mf.dis.lenuni ,xul = xul,yul = yul)
Xm,Ym = np.meshgrid(grid_ref.get_xcenter_array()+xul,grid_ref.get_ycenter_array()-yul)

nx = mf.nrow
ny = mf.ncol

# load paths for truth model
fpath = fmain+os.sep+'Truth'
rname  ='path_ex' # name of modpath model run
path_true = np.load(fpath + os.sep + 'modpath'+ os.sep+ rname + os.sep + rname +'_tserdata.npy')

# load paths for modflow model with PEST estimated hk parameters
fpath = fmain+os.sep+'Model_results'
rname = 'model_path_ex' # name of modpath model run
path_sim = np.load(fpath + os.sep + 'modpath'+ os.sep+ rname + os.sep+rname +'_tserdata.npy')

# load pilot point location data
fpath = fmain + os.sep + 'Model'
pp_data = np.load(fpath + os.sep + 'pilot_point_and_variogram_data.npy').flatten()[0]



## PLOTS
# Estimated K
fig = plt.figure()
ax = fig.gca()
hk_est = ax.imshow(hk_est, cmap = 'jet', extent =[xul, -xul, -yul, yul])
pilot_pts = ax.scatter(pp_data['x'],pp_data['y'], s = 15, facecolor = 'white', edgecolor = 'black', linewidth = 1)
path_est = ax.plot(path_sim['x'][0],path_sim['y'][0],lw = 2, c = 'black')
plt.colorbar(mappable = hk_est,ax = ax, label = 'Estimated K')
#plt.show()

# True K
fig = plt.figure()
ax = fig.gca()
hk_tr = ax.imshow(hk_truth, cmap = 'jet', extent =[xul, -xul, -yul, yul])
pilot_pts = ax.scatter(pp_data['x'],pp_data['y'], s = 15, facecolor = 'white', edgecolor = 'black', linewidth = 1)
path_tr = ax.plot(path_true['x'][0],path_true['y'][0],lw = 2, c = 'black')
plt.colorbar(mappable = hk_tr,ax = ax, label = 'True K')
#plt.show()


# log True K
fig = plt.figure()
ax = fig.gca()
hk_tr = ax.imshow(np.log10(hk_truth+0.0001), cmap = 'jet', extent =[xul, -xul, -yul, yul])
pilot_pts = ax.scatter(pp_data['x'],pp_data['y'], s = 15, facecolor = 'white', edgecolor = 'black', linewidth = 1)
path_tr = ax.plot(path_true['x'][0],path_true['y'][0],lw = 2, c = 'black')
plt.colorbar(mappable = hk_tr,ax = ax, label = 'log10(True K)')
#plt.show()

#fitted heads
fig = plt.figure()
ax = fig.gca()
vmax = 12
vmin = 10
cmap = 'cividis'
levels = np.linspace(vmin,vmax,10).tolist()
hed_est = ax.imshow(hd_est, cmap = cmap, extent =[xul, -xul, -yul, yul], vmax = vmax)
cont_est = ax.contour(Xm,Ym,hd_est,levels = levels, colors = 'gray')
ax.clabel(cont_est, inline=2, fontsize=6,fontweight = 'bold', colors = 'black')
pilot_pts = ax.scatter(pp_data['x'],pp_data['y'], s = 15, facecolor = 'white', edgecolor = 'black', linewidth = 1)
path_est = ax.plot(path_sim['x'][0],path_sim['y'][0],lw = 2, c = 'black')
plt.colorbar(mappable = hed_est,ax = ax, label = 'Fitted Heads')

#true heads
fig = plt.figure()
ax = fig.gca()
vmax = 12
vmin = 10
cmap = 'cividis'
levels = np.linspace(vmin,vmax,10).tolist()
hed_tr = ax.imshow(hd_truth, cmap = cmap, extent =[xul, -xul, -yul, yul], vmax = vmax)
cont_tr = ax.contour(Xt,Yt,hd_truth,levels = levels, colors = 'gray')
ax.clabel(cont_tr, inline=2, fontsize=6,fontweight = 'bold', colors = 'black')
pilot_pts = ax.scatter(pp_data['x'],pp_data['y'], s = 15, facecolor = 'white', edgecolor = 'black', linewidth = 1)
path_true = ax.plot(path_true['x'][0],path_true['y'][0],lw = 2, c = 'black')
plt.colorbar(mappable = hed_tr,ax = ax, label = 'True Heads')

plt.show()
'''
fig = plt.figure()
ax = fig.gca()
ax.imshow(hk_est,extent =[xul, -xul, -yul, yul])
ax.plot(path_sim['x'][0],path_sim['y'][0],lw = 2, c = 'black')

fig = plt.figure()
ax = fig.gca()
ax.imshow(hk_truth[0,:,:],extent =[xul, -xul, -yul, yul])
ax.plot(path_true['x'][0],path_true['y'][0],lw = 2, c = 'black')
plt.show()
'''

                    

