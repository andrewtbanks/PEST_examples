import matplotlib.pyplot as plt
import os
import numpy as np
import flopy 
import flopy.utils.reference  as srf
import flopy.utils.binaryfile as bf


path = np.load('modpath'+ os.sep+ 'path_ex' + os.sep+ 'path_ex_tserdata.npy')


# load base modflow model
mf_path      = os.getcwd()+os.sep+'modflow'
mf_modelname = 'example_Truth'
# import modflow object
mf           = flopy.modflow.Modflow.load(mf_path+os.sep+mf_modelname+ '.nam')
# load K field
hk= mf.lpf.hk.array[0,:,:]
# load heads
hdobj        = bf.HeadFile(mf_path+os.sep+mf_modelname+'.hds', precision = 'single')         # import heads file as flopy object ( output from modflow)
kstpkper =hdobj.get_kstpkper()
hds =  hdobj.get_data(kstpkper = kstpkper[0])

# create reference grid object corresponding to modflow model
xul = -sum(mf.dis.delr)/2                   # modflow model spatial domain upper left x coordinate 
yul =  sum(mf.dis.delc)/2                   # modflow model spatial domain upper left y coordinate
grid_ref = srf.SpatialReference(delr   = mf.dis.delr,   
                                delc   = mf.dis.delc,
                                lenuni = mf.dis.lenuni,
                                xul    = xul,
                                yul    = yul)

Xc = grid_ref.get_xcenter_array()
Yc = grid_ref.get_ycenter_array()
X,Y = np.meshgrid(Xc,Yc)


fig = plt.figure()
ax = fig.gca()

plt.imshow(hds[0,:,:], cmap = 'jet', extent =[xul, -xul, -yul, yul], vmin = 10, vmax =12 )
#plt.imshow(hk, cmap = 'jet', extent =[xul, -xul, -yul, yul])
plt.plot(path['x'][0],path['y'][0],lw = 2, c = 'black')
plt.colorbar()
plt.show()
