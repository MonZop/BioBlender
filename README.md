Hai everyone!
I am pleased to inform all interested users that we have a new version of BioBlender that can be found on a new Github page, here: https://github.com/PabloEnmanuelRamos/BioBlender2.1

It has been a major rewriting, to bring it to Python 3, and adapt to new Blender versions.
The new BB works ok with Blender 2.79, but we are already working to update it and make it available for Bender 2.8 .

I thank all the people who have worked on it, and especially Pablo, and also those among you who are willing to test, help, and contribute again to make this tool available.

Go to https://github.com/PabloEnmanuelRamos/BioBlender2.1 and let us know! 
(by MonZop 9 April 2020)


BioBlender is an addon for Blender, aimed at providing tools for the import and elaboration of biological molecules.
It consists of several functions, some executed by Blender and/or its Game Engine, and some others performed by external programs, such as PyMOL, APBS etc.

It was developed by the Scientific Visualization Unit of the Institute of Cliniclal Physiology of the CNR of Italy in Pisa, with the contribution of several colleagues.

We have now made it an Open Project, with the intent of keeping it updated, as long as Blender keeps moving on, and of possibly introducing new, better and useful features.

More info can be found on the SciVis website (www.scivis.it) and on BioBlender.eu

BioBlender was developed to work on Windows, Mac and Linux. Therefore each fix will need to be tested on each of these platforms.
Also, as BioBlender is supposed to handle different types of molecules, we will test:

  - Single protein, multiple conformations File: "01_CaM_protein3conformations.pdb";
  - Double strand DNA fragment  File  "02_4IHV_dsDNA.pdb";
  - Glycoprotein (protein with sugar-like molcule attached) file "05_glycoprotein_4AY9_FSH.pdb";
  - Small protein for testing GE. File "06_1L2Y_4GE.pdb";
  - Composite protein (dimer), file: "04_Dimer_1A4U.pdb";
  - Interacting protein/DNA, file "03_3IV5_ProteinComplex.pdb".

The SciVis Team is grateful to all that will contribute to this project.

#Getting Started#
**BioBlender is still under development**

## Prerequisites ##
- [Blender](http://www.blender.org/)
- [Python 2.7](https://www.python.org/downloads/)
- [PyMol](http://sourceforge.net/projects/pymol/?source=directory)

##Using the command line##
This set up will allow you to update dynamically to the latest snapshot of BioBlender. You need to be able to use the command line and have git properly set up.
### Unix/Mac ###
1. Get the latest version
   ```bash
   mkdir ~/BioBlender
   git clone https://github.com/MonZop/BioBlender.git ~/BioBlender
   ln -s ~/BioBlender ~/.config/blender/%BLENDER_VERSION_NUM%/scripts/addons/BioBlender
   ```

2. Checkout whichever branch you need. If you're not sure, skip this step.
   ```bash
   cd ~/BioBlender
   git checkout remotes/origin/BRANCH_NAME
   ```

3. Launch Blender and do File-->User Preferences-->Addons

4. Search the list for BioBlender2.0 and make sure it is ticked

5. Save user settings and restart blender

6. To update
   ```bash
   cd ~/BioBlender
   git pull --all
   ```

### Windows Vista and above ###
1. Get the latest version of BioBlender.
    Assuming you only have one partition C:. If not, just replace with your drive's letter (D, E, etc).

    ```dos
    mkdir C:\some\directory\BioBlender
    git clone https://github.com/MonZop/BioBlender.git C:\some\directory\BioBlender
    mklnk /d "C:\Users\%username%\AppData\Roaming\Blender Foundation\Blender\%BLENDER_VERSION_NUM%\scripts\addons\BioBlender" C:\some\directory\BioBlender
    ```
    The ```mklink``` step will work with ```/d``` or ```/j```, both ```/d``` and ```/j``` are good options, of the two /j requires no elevated user privileges so if ```/d``` fails, then use ```/j```

2. Checkout whichever branch you need. If you're not sure, skip this step.

   ```dos
   cd C:\some\directory\BioBlender
   git checkout remotes/origin/BRANCH_NAME
   ```
3. Launch Blender and do File-->User Preferences-->Addons

4. Search the list for BioBlender2.0 and make sure it is ticked

5. Save user settings and restart blender

6. To update
   ```dos
   cd C:\some\directory\BioBlender
   git pull --all
   ```
