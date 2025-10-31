library(caret)
library(ROCR)

Binforward_step <- function(dat, candid, fixvar, numSeed,SplitProp){
  forward_ls <- NULL
  for (s in seq(numSeed)){
    set.seed(s)
    repeat {
      trIdx <- createDataPartition(dat$Outcome, p = SplitProp, list = FALSE, times = 1)
      trdat <- dat[trIdx, ]
      tsdat <- dat[-trIdx, ]
      
      n_tr_0 <- sum(trdat$Outcome == 0)
      n_tr_1 <- sum(trdat$Outcome == 1)
      n_ts_0 <- sum(tsdat$Outcome == 0)
      n_ts_1 <- sum(tsdat$Outcome == 1)
      
      if (min(n_tr_0, n_tr_1, n_ts_0, n_ts_1) >= 2) break
    }
    for (g in setdiff(candid,fixvar)){
      f=as.formula(paste('Outcome ~ ',paste(fixvar,collapse = ' + '),' + ',g,collapse = ''))
      trdat1 <- trdat[complete.cases(trdat[,c('Outcome',setdiff(c(fixvar,g),''))]),c('Outcome',setdiff(c(fixvar,g),''))]
      tsdat1 <- tsdat[complete.cases(tsdat[,c('Outcome',setdiff(c(fixvar,g),''))]),c('Outcome',setdiff(c(fixvar,g),''))]
      Logitres<-glm(f, data = trdat1, family = "binomial")
      
      lptr <- predict(Logitres,trdat1, type="response")
      trauc <- performance(prediction(lptr,trdat1[,'Outcome']),"auc")@y.values[[1]][1]
      lpts <- predict(Logitres,tsdat1)
      tsauc <- performance(prediction(lpts,tsdat1[,'Outcome']),"auc")@y.values[[1]][1]
      forward_ls <- rbind(forward_ls,c(s,paste(c(fixvar,g),collapse = ' + '),trauc,tsauc))
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

Binbackward_step <- function(dat, backcandid, fixvar, numSeed, SplitProp){
  backward_ls <- NULL
  for (s in seq(numSeed)){
    set.seed(s)
    repeat {
      trIdx <- createDataPartition(dat$Outcome, p = SplitProp, list = FALSE, times = 1)
      trdat <- dat[trIdx, ]
      tsdat <- dat[-trIdx, ]
      
      n_tr_0 <- sum(trdat$Outcome == 0)
      n_tr_1 <- sum(trdat$Outcome == 1)
      n_ts_0 <- sum(tsdat$Outcome == 0)
      n_ts_1 <- sum(tsdat$Outcome == 1)
      
      if (min(n_tr_0, n_tr_1, n_ts_0, n_ts_1) >= 2) break
    }
    for (g in backcandid){
      f=as.formula(paste('Outcome ~ ',paste(setdiff(fixvar,g),collapse = ' + '),collapse = ''))
      trdat1 <- trdat[complete.cases(trdat[,c('Outcome',setdiff(fixvar,g))]),]
      tsdat1 <- tsdat[complete.cases(tsdat[,c('Outcome',setdiff(fixvar,g))]),]
      Logitres<-glm(f, data = trdat1, family = "binomial")
      lptr <- predict(Logitres,trdat1, type="response")
      trauc <- performance(prediction(lptr,trdat1[,'Outcome']),"auc")@y.values[[1]][1]
      lpts <- predict(Logitres,tsdat1)
      tsauc <- performance(prediction(lpts,tsdat1[,'Outcome']),"auc")@y.values[[1]][1]
      backward_ls <- rbind(backward_ls,c(s,paste(setdiff(fixvar,g),collapse = ' + '),trauc,tsauc))
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

BinTrainAUCStepwise <- function(totvar,dat,fixvar,excvar,numSeed,SplitProp,outdir){
  colnames(dat) <- gsub(Outcome,"Outcome",colnames(dat))
  imtres <- NULL
  while (length(setdiff(fixvar,excvar))<length(totvar)){
    candid <- setdiff(totvar,c(fixvar,excvar))
    
    ##### Forward step
    forward_ls <- Binforward_step(dat, candid, fixvar, numSeed,SplitProp)
    forward.trauc1<-max(as.numeric(forward_ls[,2]))
    forward.var1 <- forward_ls[which.max(as.numeric(forward_ls[,2])),1];forward.tsauc1 <-forward_ls[which.max(as.numeric(forward_ls[,2])),3]
    forward.newstep <-matrix(c(forward.var1,forward.trauc1,forward.tsauc1),nrow=1)
    if (length(setdiff(gsub(" ","",strsplit(forward.var1,"\\+")[[1]]),""))==1){
      if (!dir.exists(outdir)) {
        dir.create(outdir, recursive = TRUE)
      }
      imtres <- rbind(imtres, forward.newstep)
      colnames(forward.newstep)<-c('Variable','trainAUC','testAUC')
      eval(parse(text = paste("write.csv(forward.newstep,'./",outdir,"/Intermediate_Forward",nrow(imtres),".csv',row.names = F)",sep = "")))
      fixvar <- gsub(" ","",strsplit(forward.var1,'\\+')[[1]][2])
      forward.old <- forward.newstep
    } else{
      forward.old <- imtres[nrow(imtres),]
      if (as.numeric(forward.newstep[2]) > (as.numeric(forward.old[2]) + 0.005)){
        colnames(forward.newstep) <- colnames(imtres)
        imtres <- rbind(imtres, forward.newstep)
        colnames(forward.newstep)<-c('Variable','trainAUC','testAUC')
        eval(parse(text = paste("write.csv(forward.newstep,'./",outdir,"/Intermediate_Forward",nrow(imtres),".csv',row.names = F)",sep = "")))
        fixvar <- append(fixvar,gsub(' ','',strsplit(forward.var1,'\\+')[[1]])[length(gsub(' ','',strsplit(forward.var1,'\\+')[[1]]))])
        forward.old <- forward.newstep
        
        if (nrow(imtres)>2){
          
          ##### Backward step
          backcandid<-fixvar[c(1:(length(fixvar)-2))]
          backward_ls<-Binbackward_step(dat, backcandid, fixvar, numSeed, SplitProp)
          backward.trauc1<-max(as.numeric(backward_ls[,2]))
          backward.var1 <- backward_ls[which.max(as.numeric(backward_ls[,2])),1];backward.tsauc1 <-backward_ls[which.max(as.numeric(backward_ls[,2])),3]
          backward.newstep <-matrix(c(backward.var1,backward.trauc1,backward.tsauc1),nrow=1)
          if (backward.trauc1 > (as.numeric(forward.old[2]) + 0.005)){
            imtres <- rbind(imtres, backward.newstep)
            colnames(backward.newstep)<-c('Variable','trainAUC','testAUC')
            eval(parse(text = paste("write.csv(backward.newstep,'./",outdir,"/Intermediate_Backward",nrow(imtres),".csv',row.names = F)",sep = "")))
            fixvar <- gsub(' ','',strsplit(backward_ls[which.max(as.numeric(backward_ls[,2])),1],'\\+')[[1]])
            forward.old <- backward.trauc1
          }
        }
      } else{
        
        mat<-matrix(imtres[nrow(imtres),],nrow=1)
        colnames(mat)<-c('Variable','trainAUC','testAUC')
        colnames(imtres)<-c('Variable','trainAUC','testAUC')
        eval(parse(text = paste("write.csv(imtres,'./",outdir,"/Intermediate_Stepwise_Total.csv',row.names = F)",sep = "")))
        eval(parse(text = paste("write.csv(mat,'./",outdir,"/Final_Stepwise_Total.csv',row.names = F)",sep = "")))
        break
      }
    }
  }
  mat<-matrix(imtres[nrow(imtres),],nrow=1)
  colnames(mat)<-c('Variable','trainAUC','testAUC')
  colnames(imtres)<-c('Variable','trainAUC','testAUC')
  eval(parse(text = paste("write.csv(imtres,'./",outdir,"/Intermediate_Stepwise_Total.csv',row.names = F)",sep = "")))
  eval(parse(text = paste("write.csv(mat,'./",outdir,"/Final_Stepwise_Total.csv',row.names = F)",sep = "")))
  return (mat)
}
