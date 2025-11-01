library(nsROC)
library(caret)
library(survival)

Survforward_step <- function(dat, candid, fixvar, horizon, numSeed,SplitProp){
  forward_ls <- NULL
  for (s in seq(numSeed)){
    set.seed(s)
    repeat {
      trIdx <- createDataPartition(dat$Event, p = SplitProp, list = FALSE, times = 1)
      trdat <- dat[trIdx, ]
      tsdat <- dat[-trIdx, ]
      
      n_tr_0 <- sum(trdat$Event == 0)
      n_tr_1 <- sum(trdat$Event == 1)
      n_ts_0 <- sum(tsdat$Event == 0)
      n_ts_1 <- sum(tsdat$Event == 1)
      
      if (min(n_tr_0, n_tr_1, n_ts_0, n_ts_1) >= 2) break
    }
    for (g in setdiff(candid,fixvar)){
      # Build formula based on whether fixvar is empty
      # Remove NA and empty strings from fixvar
      valid_fixvar <- fixvar[!is.na(fixvar) & nchar(fixvar) > 0]

      if (length(valid_fixvar) == 0) {
        formula_str <- paste('Surv(Survtime,Event) ~', g)
        vars_to_use <- g
      } else {
        formula_str <- paste('Surv(Survtime,Event) ~', paste(valid_fixvar, collapse = ' + '), '+', g)
        vars_to_use <- c(valid_fixvar, g)
      }
      f <- as.formula(formula_str)

      # Select complete cases with proper column names
      cols_needed <- c('Survtime', 'Event', vars_to_use)
      trdat1 <- trdat[complete.cases(trdat[, cols_needed]), cols_needed]
      tsdat1 <- tsdat[complete.cases(tsdat[, cols_needed]), cols_needed]
      CoxPHres<-coxph(f,data = trdat1)
      lptr <- predict(CoxPHres,trdat1)
      if (max(trdat1$Survtime)>=horizon){
        trauc<-cdROC(stime=trdat1$Survtime,status=trdat1$Event,marker = lptr,predict.time = horizon)$auc
      } else{
        trauc <- NA
      }
      lpts <- predict(CoxPHres,tsdat1)
      if (max(tsdat1$Survtime)>=horizon){
        tsauc<-cdROC(stime=tsdat1$Survtime,status=tsdat1$Event,marker = lpts,predict.time = horizon)$auc
      } else{
        tsauc <- NA
      }
      forward_ls <- rbind(forward_ls,c(s,paste(vars_to_use, collapse = ' + '),trauc,tsauc))
    }
  }
  forward_ls1 <- data.frame(forward_ls)
  forward_ls1$X3 <- as.numeric(forward_ls1$X3)
  forward_ls1$X4 <- as.numeric(forward_ls1$X4)
  AUCsumm <- NULL
  for (g in unique(forward_ls1$X2)){
    AUCsumm <- rbind(AUCsumm,c(g,colMeans(forward_ls1[which(forward_ls1$X2==g),-c(1,2)],na.rm = T)))
  }
  return(AUCsumm)
}

Survbackward_step <- function(dat, backcandid, fixvar, horizon, numSeed, SplitProp){
  backward_ls <- NULL
  for (s in seq(numSeed)){
    set.seed(s)
    repeat {
      trIdx <- createDataPartition(dat$Event, p = SplitProp, list = FALSE, times = 1)
      trdat <- dat[trIdx, ]
      tsdat <- dat[-trIdx, ]
      
      n_tr_0 <- sum(trdat$Event == 0)
      n_tr_1 <- sum(trdat$Event == 1)
      n_ts_0 <- sum(tsdat$Event == 0)
      n_ts_1 <- sum(tsdat$Event == 1)
      
      if (min(n_tr_0, n_tr_1, n_ts_0, n_ts_1) >= 2) break
    }
    for (g in backcandid){
      # Remove g from fixvar
      vars_remaining <- setdiff(fixvar, g)

      # Remove NA and empty strings
      valid_vars_remaining <- vars_remaining[!is.na(vars_remaining) & nchar(vars_remaining) > 0]

      # Build formula based on remaining variables
      if (length(valid_vars_remaining) == 0) {
        formula_str <- 'Surv(Survtime,Event) ~ 1'  # Intercept only
        cols_needed <- c('Survtime', 'Event')
      } else {
        formula_str <- paste('Surv(Survtime,Event) ~', paste(valid_vars_remaining, collapse = ' + '))
        cols_needed <- c('Survtime', 'Event', valid_vars_remaining)
      }
      f <- as.formula(formula_str)

      trdat1 <- trdat[complete.cases(trdat[, cols_needed]), ]
      tsdat1 <- tsdat[complete.cases(tsdat[, cols_needed]), ]
      CoxPHres<-coxph(f,data = trdat1)
      lptr <- predict(CoxPHres,trdat1)
      if (max(trdat1$Survtime)>=horizon){
        trauc<-cdROC(stime=trdat1$Survtime,status=trdat1$Event,marker = lptr,predict.time = horizon)$auc
      } else{
        trauc <- NA
      }
      lpts <- predict(CoxPHres,tsdat1)
      if (max(tsdat1$Survtime)>=horizon){
        tsauc<-cdROC(stime=tsdat1$Survtime,status=tsdat1$Event,marker = lpts,predict.time = horizon)$auc
      } else{
        tsauc <- NA
      }

      # Use appropriate variable list for backward_ls
      if (length(valid_vars_remaining) == 0) {
        var_str <- "1"  # Intercept only
      } else {
        var_str <- paste(valid_vars_remaining, collapse = ' + ')
      }
      backward_ls <- rbind(backward_ls,c(s, var_str, trauc, tsauc))
    }
  }
  backward_ls1 <- data.frame(backward_ls)
  backward_ls1$X3 <- as.numeric(backward_ls1$X3)
  backward_ls1$X4 <- as.numeric(backward_ls1$X4)
  AUCsumm <- NULL
  for (g in unique(backward_ls1$X2)){
    AUCsumm <- rbind(AUCsumm,c(g,colMeans(backward_ls1[which(backward_ls1$X2==g),-c(1,2)],na.rm = T)))
  }
  return(AUCsumm)
}

SurvTrainAUCStepwise <- function(totvar,dat,fixvar,excvar,horizon,numSeed,SplitProp,outdir,Survtime,Event){
  colnames(dat) <- gsub(Event,"Event",gsub(Survtime,"Survtime",colnames(dat)))

  cat("STEPWISE_LOG:Starting stepwise selection with", length(totvar), "variables\n", sep = "", file = stderr())

  imtres <- NULL
  step_count <- 0
  while (length(setdiff(fixvar,excvar))<length(totvar)){
    step_count <- step_count + 1
    candid <- setdiff(totvar,c(fixvar,excvar))

    cat("STEPWISE_LOG:Step", step_count, "- Evaluating", length(candid), "candidate variables\n", sep = " ", file = stderr())

    ##### Forward step
    cat("STEPWISE_LOG:Running forward step with", length(candid), "candidates x", numSeed, "iterations =", length(candid) * numSeed, "models\n", sep = " ", file = stderr())
    forward_ls <- Survforward_step(dat, candid, fixvar, horizon, numSeed,SplitProp)
    cat("STEPWISE_LOG:Forward step completed\n", sep = "", file = stderr())
    forward.trauc1<-max(as.numeric(forward_ls[,2]))
    forward.var1 <- forward_ls[which.max(as.numeric(forward_ls[,2])),1];forward.tsauc1 <-forward_ls[which.max(as.numeric(forward_ls[,2])),3]
    forward.newstep <-matrix(c(forward.var1,forward.trauc1,forward.tsauc1),nrow=1)

    cat("STEPWISE_LOG:Best variable combination:", forward.var1, "(trainAUC:", forward.trauc1, ")\n", sep = " ", file = stderr())

    if (length(setdiff(gsub(" ","",strsplit(forward.var1,"\\+")[[1]]),""))==1){
      if (!dir.exists(outdir)) {
        dir.create(outdir, recursive = TRUE)
      }
      imtres <- rbind(imtres, forward.newstep)
      colnames(forward.newstep)<-c('Variable','trainAUC','testAUC')
      eval(parse(text = paste("write.csv(forward.newstep,'./",outdir,"/Intermediate_Forward",nrow(imtres),".csv',row.names = F)",sep = "")))
      fixvar <- gsub(" ","",strsplit(forward.var1,'\\+')[[1]][2])
      forward.old <- forward.newstep
      cat("STEPWISE_LOG:First variable selected:", fixvar, "\n", sep = " ", file = stderr())
    } else{
      forward.old <- imtres[nrow(imtres),]
      if (as.numeric(forward.newstep[2]) > (as.numeric(forward.old[2]) + 0.005)){
        colnames(forward.newstep) <- colnames(imtres)
        imtres <- rbind(imtres, forward.newstep)
        colnames(forward.newstep)<-c('Variable','trainAUC','testAUC')
        eval(parse(text = paste("write.csv(forward.newstep,'./",outdir,"/Intermediate_Forward",nrow(imtres),".csv',row.names = F)",sep = "")))
        new_var <- gsub(' ','',strsplit(forward.var1,'\\+')[[1]])[length(gsub(' ','',strsplit(forward.var1,'\\+')[[1]]))]
        fixvar <- append(fixvar, new_var)
        forward.old <- forward.newstep
        cat("STEPWISE_LOG:Added variable:", new_var, "- Total selected:", length(fixvar), "\n", sep = " ", file = stderr())

        if (nrow(imtres)>2){

          ##### Backward step
          cat("STEPWISE_LOG:Running backward step to check if any variable should be removed\n", sep = "", file = stderr())
          backcandid<-fixvar[c(1:(length(fixvar)-2))]
          backward_ls<-Survbackward_step(dat, backcandid, fixvar, horizon, numSeed, SplitProp)
          cat("STEPWISE_LOG:Backward step completed\n", sep = "", file = stderr())
          backward.trauc1<-max(as.numeric(backward_ls[,2]))
          backward.var1 <- backward_ls[which.max(as.numeric(backward_ls[,2])),1];backward.tsauc1 <-backward_ls[which.max(as.numeric(backward_ls[,2])),3]
          backward.newstep <-matrix(c(backward.var1,backward.trauc1,backward.tsauc1),nrow=1)
          if (backward.trauc1 > (as.numeric(forward.old[2]) + 0.005)){
            imtres <- rbind(imtres, backward.newstep)
            colnames(backward.newstep)<-c('Variable','trainAUC','testAUC')
            eval(parse(text = paste("write.csv(backward.newstep,'./",outdir,"/Intermediate_Backward",nrow(imtres),".csv',row.names = F)",sep = "")))
            fixvar <- gsub(' ','',strsplit(backward_ls[which.max(as.numeric(backward_ls[,2])),1],'\\+')[[1]])
            forward.old <- backward.trauc1
            cat("STEPWISE_LOG:Backward step improved model - updated variables\n", sep = "", file = stderr())
          } else {
            cat("STEPWISE_LOG:Backward step did not improve model - keeping current variables\n", sep = "", file = stderr())
          }
        }
      } else{
        cat("STEPWISE_LOG:No improvement from adding more variables - stopping stepwise selection\n", sep = "", file = stderr())
        mat<-matrix(imtres[nrow(imtres),],nrow=1)
        colnames(mat)<-c('Variable','trainAUC','testAUC')
        colnames(imtres)<-c('Variable','trainAUC','testAUC')
        eval(parse(text = paste("write.csv(imtres,'./",outdir,"/Intermediate_Stepwise_Total.csv',row.names = F)",sep = "")))
        eval(parse(text = paste("write.csv(mat,'./",outdir,"/Final_Stepwise_Total.csv',row.names = F)",sep = "")))
        break
      }
    }
  }
  cat("STEPWISE_LOG:Stepwise selection completed - Final variables:", nrow(imtres), "\n", sep = " ", file = stderr())
  mat<-matrix(imtres[nrow(imtres),],nrow=1)
  colnames(mat)<-c('Variable','trainAUC','testAUC')
  colnames(imtres)<-c('Variable','trainAUC','testAUC')
  eval(parse(text = paste("write.csv(imtres,'./",outdir,"/Intermediate_Stepwise_Total.csv',row.names = F)",sep = "")))
  eval(parse(text = paste("write.csv(mat,'./",outdir,"/Final_Stepwise_Total.csv',row.names = F)",sep = "")))
  return (mat)
}
