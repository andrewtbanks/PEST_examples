import numpy as np
import sys
import os
import flopy
import flopy.utils.binaryfile as bf
import flopy.utils.reference  as srf
from datetime import datetime
import shutil
#######################################
#### GENERATE MODPATH MODEL OBJECTS ###
#######################################


###################################################################
#### GEN CIRCLE OF npt POINTS ABOUT [xcent,ycent] WITH RADIUS R ###
###################################################################
def genCirclePts(xcent,ycent,r,npt):
    x = np.zeros([npt,],dtype = float)
    y = np.zeros([npt,],dtype = float)

    for item in np.arange(0,npt):
        x[item] = xcent+(np.cos(2*np.pi/npt*item)*r)
        y[item] = ycent+(np.sin(2*np.pi/npt*item)*r)
                         
    return x,y 


####################################################
#### CONVERT GLOBAL X-Y-Z TO R-C-L AND LOCAL XYZ ###
####################################################
def XYZtoCell(X,Y,Z,mf,grid_ref):
    cells = grid_ref.get_rc(x = X,y= Y)
    npt = len(X)
    row = np.zeros((npt,),dtype=int)
    col = np.zeros((npt,),dtype=int)
    lay = np.zeros((npt,),dtype=int)
    xloc = np.zeros((npt,),dtype=float)
    yloc = np.zeros((npt,),dtype=float)
    zloc = np.zeros((npt,),dtype=float)
    for particle in np.arange(0,npt):
        row[particle,] = cells[0][particle]
        col[particle,] = cells[1][particle]
        lay[particle,] = 1
        
        verts = grid_ref.get_vertices(row[particle,],col[particle,])        
        xverts = [verts[0][0],verts[1][0],verts[2][0],verts[3][0]]
        yverts = [verts[0][1],verts[1][1],verts[2][1],verts[3][1]]
        zverts = [mf.dis.top[0,0] , mf.dis.botm[0][0,0]]
            
        #dx = abs(max(xverts)-min(xverts))
        #dy = abs(max(yverts)-min(yverts))
        #dz = abs(max(zverts)-min(zverts))


        dx = max(xverts)-min(xverts)
        dy = max(yverts)-min(yverts)
        dz = max(zverts)-min(zverts)
        
        xcol = max(xverts)
        ycol = max(yverts)
        zcol = max(zverts)
        
        xloc[particle,] = 1-(xcol-X[particle] )/dx
        yloc[particle,] = 1-(ycol-Y[particle] )/dy

        zloc[particle,] = 1-(zcol - Z[particle])/dz

        
    #row = row+1
    #col = col+1    

    #row = row+1
    #col = col-1
    
    return row, col, lay, xloc, yloc, zloc


