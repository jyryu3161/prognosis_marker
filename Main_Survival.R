library(nsROC)
library(caret)
library(survival)
library(pROC)
library(cutpointr)
library(coefplot)
library(yaml)

# Parse command line arguments
args <- commandArgs(trailingOnly = TRUE)
config_file <- "config/example_analysis.yaml"  # Default config file

# Find --config argument
if (length(args) > 0) {
  config_idx <- grep("^--config", args)
  if (length(config_idx) > 0) {
    if (args[config_idx] == "--config" && length(args) > config_idx) {
      config_file <- args[config_idx + 1]
    } else if (grepl("^--config=", args[config_idx])) {
      config_file <- sub("^--config=", "", args[config_idx])
    }
  }
}

# Load config
if (!file.exists(config_file)) {
  stop(paste("Config file not found:", config_file))
}

config <- yaml::read_yaml(config_file)

# Get working directory
if (!is.null(config$workdir)) {
  setwd(config$workdir)
} else {
  setwd(".")
}

cat(paste("STEPWISE_LOG:Starting Survival Analysis\n"), file = stderr())
source('Survival_TrainAUC_StepwiseSelection.R')

# Get survival config
if (is.null(config$survival)) {
  stop("Survival configuration not found in config file")
}

surv_config <- config$survival

# Load data
data_file <- ifelse(is.null(surv_config$data_file), 
                    ifelse(is.null(config$data_file), "Example_data.csv", config$data_file),
                    surv_config$data_file)

if (!file.exists(data_file)) {
  stop(paste("Data file not found:", data_file))
}

cat(paste("STEPWISE_LOG:Loading data from:", data_file, "\n"), file = stderr())
dat <- read.csv(data_file, header = TRUE, stringsAsFactors = FALSE)
cat(paste("STEPWISE_LOG:Data loaded -", nrow(dat), "samples,", ncol(dat), "columns\n"), file = stderr())

# Extract parameters from config
sample_id <- ifelse(is.null(surv_config$sample_id), "sample", surv_config$sample_id)
Survtime <- ifelse(is.null(surv_config$time_variable), "OS.year", surv_config$time_variable)
Event <- ifelse(is.null(surv_config$event), "OS", surv_config$event)
horizon <- ifelse(is.null(surv_config$horizon), 5, as.numeric(surv_config$horizon))
numSeed <- ifelse(is.null(surv_config$num_seed), 100, as.integer(surv_config$num_seed))
SplitProp <- ifelse(is.null(surv_config$split_prop), 0.7, as.numeric(surv_config$split_prop))
Freq <- ifelse(is.null(surv_config$freq), 80, as.integer(surv_config$freq))
output_dir <- ifelse(is.null(surv_config$output_dir), "results/survival", surv_config$output_dir)

# Handle exclude and include lists
excvar <- ifelse(is.null(surv_config$exclude) || length(surv_config$exclude) == 0, 
                 c(""), 
                 surv_config$exclude)
if (length(excvar) == 1 && excvar == "") {
  excvar <- c("")
}

fixvar <- ifelse(is.null(surv_config$include) || length(surv_config$include) == 0, 
                 "", 
                 surv_config$include)
if (length(fixvar) == 0 || (length(fixvar) == 1 && fixvar == "")) {
  fixvar <- ""
}

# Get feature columns (exclude sample_id, Survtime, and Event)
exclude_cols <- c(sample_id, Survtime, Event)

# If features are specified in config, use those; otherwise use all columns except excluded ones
if (!is.null(surv_config$features) && length(surv_config$features) > 0) {
  totvar <- surv_config$features
  cat(paste("STEPWISE_LOG:Using", length(totvar), "specified features from config\n"), file = stderr())
} else {
  totvar <- colnames(dat)[-match(exclude_cols, colnames(dat), nomatch = 0)]
  cat(paste("STEPWISE_LOG:Using", length(totvar), "features (auto-selected from", ncol(dat), "total columns)\n"), file = stderr())
}

# Create output directories
outcandir <- file.path(output_dir, "ExtCandidat")
outdir <- file.path(output_dir, "StepSurv")

dir.create(output_dir, showWarnings = FALSE, recursive = TRUE)
dir.create(outcandir, showWarnings = FALSE, recursive = TRUE)
dir.create(outdir, showWarnings = FALSE, recursive = TRUE)

############################################################################
##### Extract candidate gene lists with Freq threshold
############################################################################
# Rename columns for consistency
colnames(dat) <- gsub(paste0("^", Event, "$"), "Event", 
                      gsub(paste0("^", Survtime, "$"), "Survtime", colnames(dat)), 
                      ignore.case = TRUE)

cat("STEPWISE_START\n", file = stderr())
cat(paste("STEPWISE_LOG:Starting candidate gene extraction...\n"), file = stderr())
cat(paste("STEPWISE_LOG:Total iterations:", numSeed, ", Variables:", length(totvar), ", Frequency threshold:", Freq, "\n"), file = stderr())
cat(paste("PROGRESS_START:", numSeed, "\n"), file = stderr())

# Extract candidate genes
Candivar <- Extract_CandidGene(dat, numSeed, SplitProp, totvar, outcandir, Freq)

cat(paste("STEPWISE_LOG:Candidate gene extraction completed -", length(Candivar), "candidate genes selected\n"), file = stderr())
# Candivar: Candidate gene lists for variable selection
############################################################################

#####################################################################
##### Run TrainAUC-based stepwise selection (Outcome: Survival time)
#####################################################################
cat(paste("STEPWISE_LOG:Starting stepwise selection with", length(Candivar), "candidate genes\n"), file = stderr())
Result <- SurvTrainAUCStepwise(Candivar, dat, fixvar, excvar, horizon, numSeed, SplitProp, outdir)
cat(paste("STEPWISE_LOG:Stepwise selection completed\n"), file = stderr())

# Result: Final variable selection result eg. Variable / trainAUC / testAUC
#####################################################################

#####################################################################
##### Plot ROC curves and Variable Importance 
#####################################################################
cat(paste("STEPWISE_LOG:Generating plots...\n"), file = stderr())
# Change to output directory for saving plots
old_dir <- getwd()
setwd(output_dir)
PlotSurvROC(dat, numSeed, SplitProp, Result, horizon)    # Plot ROC curves from repetitions 
cat(paste("STEPWISE_LOG:ROC curve plot saved\n"), file = stderr())
PlotSurVarImp(dat, Result)                      # Plot Variable Importance 
cat(paste("STEPWISE_LOG:Variable importance plot saved\n"), file = stderr())
PlotSurvKM(dat, numSeed, SplitProp, Result, horizon)  # Kaplan-Meier survival curves
cat(paste("STEPWISE_LOG:Kaplan-Meier plot saved\n"), file = stderr())
PlotSurvTimeAUC(dat, numSeed, SplitProp, Result)  # Time-dependent AUC
cat(paste("STEPWISE_LOG:Time-dependent AUC plot saved\n"), file = stderr())
PlotSurvRiskDist(dat, Result)  # Risk score distribution
cat(paste("STEPWISE_LOG:Risk distribution plots saved\n"), file = stderr())
PlotSurvStepwiseProcess(outdir)  # Stepwise selection process
cat(paste("STEPWISE_LOG:Stepwise process plot saved\n"), file = stderr())
setwd(old_dir)  # Restore original directory
cat(paste("STEPWISE_LOG:Analysis complete!\n"), file = stderr())
#####################################################################