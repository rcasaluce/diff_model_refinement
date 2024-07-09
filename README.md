# Artifact -  Enhancing Threat Model Validation: A White-Box Approach based on Statistical Model Checking and Process Mining

## Paper presented in the First International Workshop on Detection And Mitigation Of Cyber attacks that exploit human vuLnerabilitiES (DAMOCLES) Workshop at AVI ‘24, Arenzano (Genoa), Italy, 4 June 2024 
### Published in the workshop proceedings: https://ceur-ws.org/Vol-3713/

## Check the [Documentation_DAMOCLES](https://github.com/rcasaluce/diff_model_refinement/blob/main/Documentation_DAMOCLES.pdf) for the complete instructions on how to use the artifact.


Some packages require Python version >= 3.9. Tested with Python version 3.10.6 on Ubuntu 22.04.2 LTS

> install it from pip with `pip install -r requirements.txt`. Make sure to use a fresh virtual environment.


> To install pygraphviz on Windows - See https://pygraphviz.github.io/documentation/stable/install.html#advanced for additional information.
> For Macs ARM see https://github.com/pygraphviz/pygraphviz/issues/398 

Project Organization - DiffModel_Refined_Model Folder

------------

    
    ├── data               <- Data sets for modeling - simulated event logs CSV files and dot files
    │     │
    │     ├── csv          <- event logs csv files.
    │     ├── dot          <- dot files - graphical representation of the procedural part of the RisQFLan models.
    │     ├── bbt          <- BBT files - RisQFLan file.
    │     ├── refined_BBT  <- store preview new attacker behavior and new refined RISQFLan file      
    │     │   ├── preview_AB
    │     │   └── refined_model
    │     └── results_DIFF  <- PDF files and dot files representing the diff models. 
    ├── src          	   
    │    ├── __init__.py
    │    └── utilities.py  <- utilities
    │
    ├── diff_model.py      <- Diff script
    ├── diff_model_auto_refinement.py  <- Diff script and automatic refinement
    ├── README.md          <- The top-level README for developers using this project.
    ├── LICENSE.txt
    └── requirements.txt
   
--------

## Options diff_model.py script. 

Returns the Diff model:


	-h, --help: Show the help message and exit.
	
	-i INPUTCSV, --inputcsv INPUTCSV: Input CSV file - 
 	simulated event logs saved from RisQFLan.
	
	-idot INPUTDOT, --inputdot INPUTDOT: Input DOT file - 
 	the graphical representation of the procedural part of the RisQFLan model.
	
	-o OUTPUT, --output OUTPUT: Output NAME - 
 	diff model between the graphical representation 
  	of the procedural part of the RisQFLan model and the mined PM model.

    
### To run experiments diff_model.py

Make sure to be in `DiffModel_Refined_Model` folder and run: 

`python diff_model.py -i log_RobBank_original.csv - idot RobBankAttacker.dot -o diff_model_w_diff_script.pdf`


## Options diff_model_auto_refinement.py script. 

Returns the Diff model and the RiSQFLan file with the refined model:


	-h, --help: Show the help message and exit.`
	
	-i INPUTCSV, --inputcsv INPUTCSV: Input CSV file - simulated event
	logs saved from RisQFLan.
	
	-idot INPUTDOT, --inputdot INPUTDOT: Input DOT file - the graphical
	representation of the procedural part of the RisQFLan model.
	
	-ibbt INPUTBBT, --inputbbt INPUTBBT: Input BBT file - the textual
	representation of model written in RisQFLan.
	
	-o OUTPUT, --output OUTPUT: Output NAME - diff model between the
	graphical representation of the procedural part of the RisQFLan model
	and the mined PM model.

    
### To run experiments diff_model_auto_refinement.py

Make sure to be in `DiffModel_Refined_Model` folder and run: 

`python diff_model_auto_refinement.py -i  log_RobBank_original.csv -idot RobBankAttacker.dot -ibbt RobBank.bbt  o- diff_model_w_ref_script.pdf`


### Please cite this work using:

```
@inproceedings{CASALUCE2024process,
  author       = {Roberto Casaluce and
                  Andrea Burratin and
                  Francesca Chiaromonte and
                  Alberto Lluch{-}Lafuente and
                  Andrea Vandin},
  title        = {Enhancing Threat Model Validation: {A} White-Box Approach based on
                  Statistical Model Checking and Process Mining},
  booktitle    = {Proceedings of the First International Workshop on Detection And Mitigation
                  Of Cyber attacks that exploit human vuLnerabilitiES {(DAMOCLES} 2024)
                  co-located with 17th International Conference on Advanced Visual Interfaces
                  {(AVI} 2024), Arenzano (Genoa), Italy, Arenzano, Italy, June 4th,
                  2024},
  series       = {{CEUR} Workshop Proceedings},
  volume       = {3713},
  pages        = {9--20},
  publisher    = {CEUR-WS.org},
  year         = {2024},
  url          = {https://ceur-ws.org/Vol-3713/paper\_2.pdf},
  timestamp    = {Tue, 02 Jul 2024 16:41:11 +0200},
  biburl       = {https://dblp.org/rec/conf/damocles/CasaluceBCLV24.bib},
  bibsource    = {dblp computer science bibliography, https://dblp.org}
}
```


