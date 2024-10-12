Using these three folders as a separate execution, because the location of the files is relevant to proper execution. Do the project download and use the 3 folders as the main folders for each execution

COMPILATION and DISASSEMBLATION PIPELINES

REQUIREMENTS -> only zlib, openssl, boost and curl libraries are allowed. ARM folder must be inside the main directory folder, if there is ARM folder inside src2 before the exection, then remove it to avoid problems

1) Download libraries, remember to rename the folder <name_of_library>-<version>.<version>.<version>

2) Library must have make file and configure file

3) Put the library you want to analyze into /src/libraries

4) Run Manager.py (see Thesis for more ditails)

5) After all executions, retrieve the dockerfinale container, it would have the database disassembly_info.db

TO DO -> fix the automatization regarding the retrieves of the db inside dockerfinale

MERGERDB

REQUIREMENTS -> databases must have the same structures as the database created by COMPILATION and DISASSEMBLATION PIPELINES. Modifies the code (DatabaseFileSelecter.py) regarding optimization levels you want to use (default is 0, 1, 2, 3). Modifies the code regarding distribution about files in specific libraries

1) Put all databases you want to merge inside MergingMachine folder

2) Run MergerDB.py, the result will be one single database merged from MergingMachine databases, multiple databases contain 1 single file for distribution set and multiple databases contain 1 single file for optimization level


SIMILARITY ALGORITHM

REQUIREMENTS -> databases must have the same structures as the database created by COMPILATION and DISASSEMBLATION PIPELINES. Modifies the code (CallerSim.py) regarding the names of databases to compare, and maybe metrics score

1) Put all database you want to compare inside src3 folder

2) Run Final.py

3) After execution retrieves the json files inside the contianer, named comparisonresults.json and metricsresult4files.json and put them in the main directory folder

4) Run PrintMultipleMetrics.py if you want to print average metrics about every file inside the metricsresult4files.json (if the analysis was performed on only 1 file database, don't worry, you can use this script to print the single file stats, because the mean of 1 single file is equal to its own value)

5) Run PrintCompareMultipleMetrics.py if you have 2 different metricsresult4files.json file (named metricsresult4files1.json and metricsresult4files2.json) and you want to compare their average score about metrics

