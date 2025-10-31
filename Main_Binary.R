library(caret)
library(ROCR)

library(pROC)
library(cutpointr)
library(coefplot)

Path = "G:/Research/TNBC_Analysis_2024/R_code/Software"                 
setwd(Path)                                                             # Set working path
DataFile = "Example_data.csv"                                           # Input data (Including Header)
dat = read.csv(DataFile,header = T,stringsAsFactors = F)

#####################################################################
##### Run TrainAUC-based stepwise selction (Outcome: Binary)
#####################################################################
source('Binary_TrainAUC_StepwiseSelection.R')                         # Import and run external R script
SampleID = "sample"                                                     # Sample ID
Outcome = "OS"                                                          # Outcome (Binary)
totvar= colnames(dat)[-match(c(SampleID,Outcome,'OS.year'),colnames(dat))] # Total gene lists for variable selection
numSeed=100                                                                # Number of iterations
outdir="StepBin"                                                           # Output folder to be created
excvar=c("")                                                               # Gene lists to exclude from variable selection. (e.g. excvar=c("BVES","COL4A2"))
fixvar=""                                                               # A list of genes that must be included in the model (e.g. fixvar=c("CTNNA1","GRIP1"))
SplitProp=0.7                             # Ratio for data split (training:test = 7:3 → set to 0.7)

Result<-BinTrainAUCStepwise(totvar,dat,fixvar,excvar,numSeed,SplitProp,outdir)
#####################################################################

#####################################################################
##### Plot ROC curves from 100 repetitions 
#####################################################################
FinalRes <- NULL
trROCobjList <- tsROCobjList <- NULL
for (s in seq(numSeed)){
  set.seed(s)
  repeat {
    trIdx <- createDataPartition(dat[,Outcome], p = SplitProp, list = FALSE, times = 1)
    trdat <- dat[trIdx, ]
    tsdat <- dat[-trIdx, ]
    
    n_tr_0 <- sum(trdat[,Outcome] == 0)
    n_tr_1 <- sum(trdat[,Outcome] == 1)
    n_ts_0 <- sum(tsdat[,Outcome] == 0)
    n_ts_1 <- sum(tsdat[,Outcome] == 1)
    
    if (min(n_tr_0, n_tr_1, n_ts_0, n_ts_1) >= 2) break
  }
  
  f=as.formula(paste0(Outcome,' ~ ',as.character(Result[1,1])))
  trdat1 <- trdat[complete.cases(trdat[,c(Outcome,strsplit(Result[1,1],' \\+ ')[[1]])]),c(Outcome,strsplit(Result[1,1],' \\+ ')[[1]])]
  tsdat1 <- tsdat[complete.cases(tsdat[,c(Outcome,strsplit(Result[1,1],' \\+ ')[[1]])]),c(Outcome,strsplit(Result[1,1],' \\+ ')[[1]])]
  model<-glm(f, data = trdat1, family = "binomial")
  lptr <- predict(model,trdat1,type="response")
  trROCobjList[[s]] <- performance(prediction(lptr,trdat1[,match(Outcome,colnames(trdat1))]),"tpr", "fpr")
  trauc<-performance(prediction(lptr,trdat1[,match(Outcome,colnames(trdat1))]),"auc")@y.values[[1]][1]
  lpts <- predict(model,tsdat1,type="response")
  tsROCobjList[[s]]<-performance(prediction(lpts,tsdat1[,match(Outcome,colnames(tsdat1))]),"tpr", "fpr")
  tsauc <- performance(prediction(lpts,tsdat1[,match(Outcome,colnames(tsdat1))]),"auc")@y.values[[1]][1]
  FinalRes <- rbind(FinalRes,c(s,trauc,tsauc))
}
round(colMeans(FinalRes,na.rm = T),4)
round(sd(FinalRes[,3],na.rm = T),4)
MeantsTPR <- rowMeans(cbind(sapply(seq(100),function(v) tsROCobjList[[v]]@y.values[[1]])),na.rm = T)
MeantsFPR <- rowMeans(cbind(sapply(seq(100),function(v) tsROCobjList[[v]]@x.values[[1]])),na.rm = T)
MeantrTPR <- rowMeans(cbind(sapply(seq(100),function(v) trROCobjList[[v]]@y.values[[1]])),na.rm = T)
MeantrFPR <- rowMeans(cbind(sapply(seq(100),function(v) trROCobjList[[v]]@x.values[[1]])),na.rm = T)

png('ROCcurve.png',width = 800,height = 400)
par(mfrow=c(1,2))
plot(trROCobjList[[1]]@x.values[[1]],trROCobjList[[1]]@y.values[[1]],col=1,type='l',lwd=1,lty=2,cex.axis=1.5,xlab='1-Specificity',ylab='Sensitivity',main='[ROC curve] Training set',cex.main=1.8,cex.lab=1.5)
sapply(seq(2,100),function(v) lines(trROCobjList[[v]]@x.values[[1]],trROCobjList[[v]]@y.values[[1]],col=v,type='l',lwd=1,lty=2))
lines(MeantrFPR,MeantrTPR,col='midnightblue',type='l',lwd=5)
legend('bottomright',legend = paste0('Mean AUC:\n',round(mean(FinalRes[,2],na.rm = T),3),' ± ',round(sd(FinalRes[,2],na.rm = T),3)),lwd=5,cex=1.5,col = 'midnightblue')
plot(tsROCobjList[[1]]@x.values[[1]],tsROCobjList[[1]]@y.values[[1]],col=1,type='l',lwd=1,lty=2,cex.axis=1.5,xlab='1-Specificity',ylab='Sensitivity',main='[ROC curve] Test set',cex.main=1.8,cex.lab=1.5)
sapply(seq(2,100),function(v) lines(tsROCobjList[[v]]@x.values[[1]],tsROCobjList[[v]]@y.values[[1]],col=v,type='l',lwd=1,lty=2))
lines(MeantsFPR,MeantsTPR,col=1,type='l',lwd=5)
legend('bottomright',legend = paste0('Mean AUC:\n',round(mean(FinalRes[,3],na.rm = T),3),' ± ',round(sd(FinalRes[,3],na.rm = T),3)),lwd=5,cex=1.5)
dev.off()
#####################################################################

#####################################################################
##### Plot Variable Importance 
#####################################################################
Scaledat <- cbind(dat[,match(c(SampleID,Outcome),colnames(dat))],apply(dat[,-match(c(SampleID,Outcome,'OS.year'),colnames(dat))],2,function(v) scale(v)))

mod<-glm(as.formula(paste0(Outcome,' ~ ',as.character(Result[1,1]))),data = Scaledat, family = "binomial")
ce=function(model.obj){
  extract=summary(get(model.obj))$coefficients[-1,c(1,2)]
  return(data.frame(extract,vars=row.names(extract),model=model.obj))
}
coefs = ce('mod')
names(coefs)[1:2]=c('coef','se')

ggplot(coefs,aes(vars,coef))+geom_hline(yintercept = 0,lty=2,lwd=1,colour='grey50')+geom_errorbar(aes(ymin = coef -  se, ymax = coef  +  se,colour = vars),lwd=1,width=0)+geom_point(size=3,aes(colour=vars))+
  geom_text(aes(label = sprintf("%.2f", coef), colour = vars),hjust = 0.4,vjust=-1,size = 5,fontface = "bold") +
  coord_flip()+guides(colour=FALSE)+labs(x='Predictors',y='Standardized Coefficient')+theme_minimal()+theme(axis.text = element_text(size=15,face='bold'),axis.title = element_text(size=15,face='bold'),strip.text =element_text(size=15,face='bold'))
ggsave('Variable_Importance.png')
#####################################################################

