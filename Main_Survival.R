suppressPackageStartupMessages({
  library(nsROC)
  library(caret)
  library(survival)
  library(pROC)
  library(cutpointr)
  library(coefplot)
  library(ggplot2)
  library(yaml)
})

# Source the helper function file
source("Survival_TrainAUC_StepwiseSelection.R")

parse_config_path <- function(args) {
  if (!length(args)) {
    return(file.path("config", "example_analysis.yaml"))
  }
  eq_idx <- grep("^--config=", args)
  if (length(eq_idx)) {
    return(sub("^--config=", "", args[eq_idx[1]]))
  }
  flag_idx <- which(args %in% c("--config", "-c"))
  if (length(flag_idx) > 0 && flag_idx[1] < length(args)) {
    return(args[flag_idx[1] + 1])
  }
  return(args[1])
}

args <- commandArgs(trailingOnly = TRUE)
config_path <- parse_config_path(args)

if (!file.exists(config_path)) {
  stop("Configuration file not found: ", config_path)
}

config <- yaml::read_yaml(config_path)
if (is.null(config$survival)) {
  stop("The configuration file must contain a 'survival' section.")
}

workdir <- if (!is.null(config$workdir)) config$workdir else getwd()
# Handle "." or NA from YAML parsing
if (is.na(workdir) || identical(workdir, ".")) {
  workdir <- getwd()
}
if (!is.character(workdir) || !dir.exists(workdir)) {
  stop("Configured working directory does not exist: ", workdir)
}
setwd(workdir)

surv_cfg <- config$survival

data_file <- if (!is.null(surv_cfg$data_file)) surv_cfg$data_file else config$data_file
if (is.null(data_file)) {
  stop("Specify 'data_file' either at the top level or inside the 'survival' section of the configuration.")
}
if (!file.exists(data_file)) {
  stop("Input data file not found: ", data_file)
}

dat <- read.csv(data_file, header = TRUE, stringsAsFactors = FALSE)

SampleID <- if (!is.null(surv_cfg$sample_id)) surv_cfg$sample_id else "sample"
Survtime <- surv_cfg$time_variable
if (is.null(Survtime)) {
  stop("The 'survival.time_variable' field is required in the configuration file.")
}
Event <- surv_cfg$event
if (is.null(Event)) {
  stop("The 'survival.event' field is required in the configuration file.")
}

non_feature_cols <- unique(c(SampleID, Survtime, Event))
non_feature_cols <- non_feature_cols[non_feature_cols %in% colnames(dat)]

totvar <- if (!is.null(surv_cfg$features)) {
  as.character(unlist(surv_cfg$features))
} else {
  setdiff(colnames(dat), non_feature_cols)
}

horizon <- if (!is.null(surv_cfg$horizon)) as.numeric(surv_cfg$horizon) else 5
numSeed <- if (!is.null(surv_cfg$num_seed)) as.integer(surv_cfg$num_seed) else 100L
SplitProp <- if (!is.null(surv_cfg$split_prop)) as.numeric(surv_cfg$split_prop) else 0.7
outdir <- if (!is.null(surv_cfg$output_dir)) surv_cfg$output_dir else "StepSurv"
excvar <- surv_cfg$exclude
if (is.null(excvar) || length(excvar) == 0) {
  excvar <- character(0)
} else {
  excvar <- as.character(unlist(excvar))
  # Remove NA and empty strings
  excvar <- excvar[!is.na(excvar) & nchar(excvar) > 0]
}

fixvar <- surv_cfg$include
if (is.null(fixvar) || length(fixvar) == 0) {
  fixvar <- character(0)
} else {
  fixvar <- as.character(unlist(fixvar))
  # Remove NA and empty strings
  fixvar <- fixvar[!is.na(fixvar) & nchar(fixvar) > 0]
}

# Output initial progress to stderr (unbuffered)
cat("PROGRESS_START:", numSeed, "\n", sep = "", file = stderr())
cat("STEPWISE_START\n", sep = "", file = stderr())

Result <- SurvTrainAUCStepwise(totvar, dat, fixvar, excvar, horizon, numSeed, SplitProp, outdir, Survtime, Event)

cat("STEPWISE_DONE\n", sep = "", file = stderr())

FinalRes <- NULL
trROCobjList <- tsROCobjList <- vector("list", numSeed)

for (s in seq_len(numSeed)) {
  # Output progress to stderr (unbuffered)
  cat("PROGRESS:", s, "\n", sep = "", file = stderr())

  set.seed(s)
  repeat {
    trIdx <- createDataPartition(dat[, Event], p = SplitProp, list = FALSE, times = 1)
    trdat <- dat[trIdx, ]
    tsdat <- dat[-trIdx, ]

    n_tr_0 <- sum(trdat[, Event] == 0)
    n_tr_1 <- sum(trdat[, Event] == 1)
    n_ts_0 <- sum(tsdat[, Event] == 0)
    n_ts_1 <- sum(tsdat[, Event] == 1)

    if (min(n_tr_0, n_tr_1, n_ts_0, n_ts_1) >= 2) break
  }

  model_formula <- as.formula(paste0("Surv(", Survtime, ",", Event, ") ~ ", as.character(Result[1, 1])))
  predictors <- strsplit(Result[1, 1], " \\+ ")[[1]]
  predictors <- gsub(" ", "", predictors)
  trdat1 <- trdat[complete.cases(trdat[, c(Survtime, Event, predictors)]), c(Survtime, Event, predictors)]
  tsdat1 <- tsdat[complete.cases(tsdat[, c(Survtime, Event, predictors)]), c(Survtime, Event, predictors)]
  CoxPHres <- coxph(model_formula, data = trdat1)

  lptr <- predict(CoxPHres, trdat1)
  trROCobjList[[s]] <- cdROC(stime = trdat1[, Survtime], status = trdat1[, Event], marker = lptr, predict.time = horizon)
  trauc <- trROCobjList[[s]]$auc

  lpts <- predict(CoxPHres, tsdat1)
  tsROCobjList[[s]] <- cdROC(stime = tsdat1[, Survtime], status = tsdat1[, Event], marker = lpts, predict.time = horizon)
  tsauc <- tsROCobjList[[s]]$auc
  FinalRes <- rbind(FinalRes, c(s, trauc, tsauc))
}

FinalRes <- as.data.frame(FinalRes)
colnames(FinalRes) <- c("iteration", "train_auc", "test_auc")
FinalRes$iteration <- as.integer(FinalRes$iteration)
FinalRes$train_auc <- as.numeric(FinalRes$train_auc)
FinalRes$test_auc <- as.numeric(FinalRes$test_auc)

mean_train_auc <- round(mean(FinalRes$train_auc, na.rm = TRUE), 4)
mean_test_auc <- round(mean(FinalRes$test_auc, na.rm = TRUE), 4)
std_test_auc <- round(sd(FinalRes$test_auc, na.rm = TRUE), 4)

MeantsTPR <- rowMeans(cbind(sapply(seq_len(numSeed), function(v) tsROCobjList[[v]]$TPR)), na.rm = TRUE)
MeantsTNR <- rowMeans(cbind(sapply(seq_len(numSeed), function(v) tsROCobjList[[v]]$TNR)), na.rm = TRUE)
MeantrTPR <- rowMeans(cbind(sapply(seq_len(numSeed), function(v) trROCobjList[[v]]$TPR)), na.rm = TRUE)
MeantrTNR <- rowMeans(cbind(sapply(seq_len(numSeed), function(v) trROCobjList[[v]]$TNR)), na.rm = TRUE)

if (!dir.exists(outdir)) {
  dir.create(outdir, recursive = TRUE)
}

plot_survival_roc <- function() {
  par(mfrow = c(1, 2))
  plot(1 - trROCobjList[[1]]$TNR, trROCobjList[[1]]$TPR, col = 1, type = "l", lwd = 1, lty = 2,
       cex.axis = 1.5, xlab = "1-Specificity", ylab = "Sensitivity", main = "[ROC curve] Training set",
       cex.main = 1.8, cex.lab = 1.5)
  invisible(sapply(seq(2, numSeed), function(v) lines(1 - trROCobjList[[v]]$TNR, trROCobjList[[v]]$TPR,
                                                     col = v, type = "l", lwd = 1, lty = 2)))
  lines(1 - MeantrTNR, MeantrTPR, col = "midnightblue", type = "l", lwd = 5)
  legend("bottomright", legend = paste0("Mean AUC:\n", mean_train_auc, ' ± ',
                                        round(sd(FinalRes$train_auc, na.rm = TRUE), 4)), lwd = 5, cex = 1.5,
         col = "midnightblue")

  plot(1 - tsROCobjList[[1]]$TNR, tsROCobjList[[1]]$TPR, col = 1, type = "l", lwd = 1, lty = 2,
       cex.axis = 1.5, xlab = "1-Specificity", ylab = "Sensitivity", main = "[ROC curve] Test set",
       cex.main = 1.8, cex.lab = 1.5)
  invisible(sapply(seq(2, numSeed), function(v) lines(1 - tsROCobjList[[v]]$TNR, tsROCobjList[[v]]$TPR,
                                                     col = v, type = "l", lwd = 1, lty = 2)))
  lines(1 - MeantsTNR, MeantsTPR, col = 1, type = "l", lwd = 5)
  legend("bottomright", legend = paste0("Mean AUC:\n", mean_test_auc, ' ± ', std_test_auc), lwd = 5, cex = 1.5)
}

save_survival_roc <- function(path, device) {
  if (device == "png") {
    png(path, width = 800, height = 400)
  } else if (device == "tiff") {
    tiff(path, width = 8, height = 4, units = "in", res = 300, compression = "lzw")
  } else {
    svg(path, width = 11, height = 5)
  }
  on.exit(dev.off(), add = TRUE)
  plot_survival_roc()
}

save_survival_roc(file.path(outdir, "ROCcurve.png"), "png")
save_survival_roc(file.path(outdir, "ROCcurve.tiff"), "tiff")
save_survival_roc(file.path(outdir, "ROCcurve.svg"), "svg")

feature_cols <- setdiff(colnames(dat), unique(c(SampleID, Survtime, Event)))
scaled_features <- scale(dat[, feature_cols, drop = FALSE])
Scaledat <- cbind(dat[, c(SampleID, Survtime, Event)], as.data.frame(scaled_features))

mod <- coxph(as.formula(paste0("Surv(", Survtime, ",", Event, ") ~ ", as.character(Result[1, 1]))), data = Scaledat)
ce <- function(model.obj) {
  extract <- summary(get(model.obj))$coefficients[, c(1, 3)]
  data.frame(extract, vars = row.names(extract), model = model.obj)
}
coefs <- ce("mod")
names(coefs)[2] <- "se"

importance_plot <- ggplot(coefs, aes(vars, coef)) +
  geom_hline(yintercept = 0, lty = 2, lwd = 1, colour = "grey50") +
  geom_errorbar(aes(ymin = coef - se, ymax = coef + se, colour = vars), lwd = 1, width = 0) +
  geom_point(size = 3, aes(colour = vars)) +
  geom_text(aes(label = sprintf("%.2f", coef), colour = vars), hjust = 0.4, vjust = -1, size = 5, fontface = "bold") +
  coord_flip() +
  guides(colour = "none") +
  labs(x = "Predictors", y = "Standardized Coefficient") +
  theme_minimal() +
  theme(axis.text = element_text(size = 15, face = "bold"),
        axis.title = element_text(size = 15, face = "bold"),
        strip.text = element_text(size = 15, face = "bold"))

ggsave(filename = file.path(outdir, "Variable_Importance.png"), plot = importance_plot,
       width = 8, height = 5, dpi = 300)
ggsave(filename = file.path(outdir, "Variable_Importance.tiff"), plot = importance_plot,
       width = 8, height = 5, dpi = 300, device = "tiff", compression = "lzw")
ggsave(filename = file.path(outdir, "Variable_Importance.svg"), plot = importance_plot,
       width = 8, height = 5, dpi = 300, device = "svg")

write.csv(FinalRes, file.path(outdir, "auc_iterations.csv"), row.names = FALSE)

cat("Survival analysis complete.\n")
cat("Mean training time-dependent AUC: ", mean_train_auc, "\n", sep = "")
cat("Mean test time-dependent AUC: ", mean_test_auc, " (SD = ", std_test_auc, ")\n", sep = "")
cat("Results saved to: ", normalizePath(outdir), "\n", sep = "")
