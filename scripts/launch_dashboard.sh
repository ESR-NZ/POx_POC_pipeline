#!/bin/bash

# Metagenomics Pipeline interactive results dashboard launcher
# M Benton - ESR
# 30/07/2021

# this script should identify a systems default browser, enter a previously installed conda r_env, and 
# require all options and packages to launch an interactive dashboard in a local browser
# this need to be system specific C
source ~/miniconda3/etc/profile.d/conda.sh 

RESULTSDIR=$1

echo -e "your chosen Results directory is: $RESULTSDIR"

# grab the default browser (for auto launch)
DEFAULTBROWS=$(xdg-settings get default-web-browser | sed 's/\.desktop//g')

# actually load the thing
conda activate r_env; R -e "options(shiny.port = 8100);                     # activate r_env, set the port to 8100 ("static")
  options(browser=\"$DEFAULTBROWS\");                                       # set default browser
  setwd(\"dashboard\");                                                     # mv to correct dur
  require(flexdashboard);                                                   # package required to open/run
  require(rmarkdown);                                                       # package required to open/run
  run(file=\"dashboard.Rmd\", shiny_args = list(launch.browser = TRUE))" \
  --args "$RESULTSDIR"    # launch the server directly in browser

# dashboard.Rmd contains a call to shiny server that will stop the server on the closing of the browser tab