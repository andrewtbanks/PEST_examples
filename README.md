# PEST_examples
Code demonstrating Pilot Point technique for highly parameterized inversion with PEST  

Required python packages: Matplotlib, flopy, numpy, shutil, skimage

Required Software: PEST http://www.pesthomepage.org/About_Us.php - Make sure PEST is specified as a system PATH variable on your machine.
______________________________________________________________________________________________________________
There are four examples included in this repository, each in its own directory. 

Within each example there are four folders 

...\Model  :contains the MODFLOW model used by PEST and python scripts for initalizing pilot point data and kriging estimated values to the modflow model grid

...\Model_results :contains a clone fo the modflow model used by PEST, along with python scripts to perform MODPATH simulations 

...\pest  :contains the python script for generating PEST input files 

...\Truth :contains the MODFLOW model representing the truth. Experimental/Field measurments used by PEST originate from this model. Also contains python script to perform MODPATH simulations. 

and a python script for generating figures "results_figures.py"


_________________________________________________________________________________________________________________
TO RUN AN EXAMPLE

1) Open the directory correpsonding to the example. 

2) Navigate to ..xxx_example\Truth\modflow and run  example_Truth_MF.py - This generates the truth MODFLOW model

3) Navigate to ..xxx_example\Truth and run  true_pathline_sim.py - This generates a modpath simulation for the truth MODFLOW model

4) Navigate to ..xxx_example\Model\modflow and run example_MF.py -  This initalizes the MODFLOW model used by PEST. The variable **fmain** specifies the path to the current example directory and may need to be modified.  

5) Navigate to ..xxx_example\Model and run  gen_observation_data.py - This initalizes the pilot point data using output from truth MODFLOW model. The variable **fmain** may need to be modified.  

6) Navigate to ..xxx_example\pest and run  pest_input.py - This builds the PEST input files.The variable **fmain** may need to be modified.  

7) To execute PEST, open Command Prompt in adminstrator mode and set the current directory to ...xxx_example\pest and enter the command 
 > **pest.exe example.pst** - This will run PEST for the given example
 
 8) Once PEST has finished, navigate to ..xxx_example\Model_results\modflow and run "example_MF_pest_results.py" - This will generate a MODFLOW model based on the optimized pilot point parameter values delieved by PEST. The variable **fmain** may need to be modified.
 
 9) navigate to ..xxx_example\Model_results and run "model_pathline_sim.py" - this generates a MODPATH simulation to compare with the truth simulation 

10) Finally, navigate back to ...\xxx_example and run "results_figures.py" - this generates figures comparing the PEST results to the truth model. The variable **fmain** may need to be modified.


 
 


