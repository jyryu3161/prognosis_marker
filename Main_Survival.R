library(nsROC)
library(caret)
library(survival)
library(pROC)
library(cutpointr)
library(coefplot)

Path = "G:/Research/TNBC_Analysis_2024/R_code/Software"                 
setwd(Path)                                                             # Set working path
DataFile = "Example_data.csv"                                           # Input data (Including Header)
dat = read.csv(DataFile,header = T,stringsAsFactors = F)

#####################################################################
##### Run TrainAUC-based stepwise selction (Outcome: Survival time)
#####################################################################
source('Survival_TrainAUC_StepwiseSelection.R')                         # Import and run external R script
SampleID = "sample"                                                     # Sample ID
Survtime = "OS.year"                                                    # Outcome variable (e.g. Survival time)
Event = "OS"                                                            # Event status
totvar= colnames(dat)[-match(c(SampleID,Survtime,Event),colnames(dat))] # Total gene lists for variable selection
horizon=5                                                               # Specific time point of interest (e.g. 5-year OS)
numSeed=100                                                             # Number of iterations
outdir="StepSurv"                                                        # Output folder to be created
excvar=c("")                              # Gene lists to exclude from variable selection. (e.g. excvar=c("BVES","COL4A2"))
fixvar=""                                 # A list of genes that must be included in the model (e.g. fixvar=c("CTNNA1","GRIP1"))
SplitProp=0.7                             # Ratio for data split (training:test = 7:3 → set to 0.7)

Result<-SurvTrainAUCStepwise(totvar,dat,fixvar,excvar,horizon,numSeed,SplitProp,outdir)
#####################################################################

#####################################################################
##### Plot ROC curves from 100 repetitions 
#####################################################################
FinalRes <- NULL
trROCobjList <- tsROCobjList <- NULL
for (s in seq(numSeed)){
  set.seed(s)
  repeat {
    trIdx <- createDataPartition(dat[,Event], p = SplitProp, list = FALSE, times = 1)
    trdat <- dat[trIdx, ]
    tsdat <- dat[-trIdx, ]
    
    n_tr_0 <- sum(trdat[,Event] == 0)
    n_tr_1 <- sum(trdat[,Event] == 1)
    n_ts_0 <- sum(tsdat[,Event] == 0)
    n_ts_1 <- sum(tsdat[,Event] == 1)
    
    if (min(n_tr_0, n_tr_1, n_ts_0, n_ts_1) >= 2) break
  }
  
  f=as.formula(paste0('Surv(',Survtime,',',Event,') ~ ',as.character(Result[1,1])))
  trdat1 <- trdat[complete.cases(trdat[,c(Survtime,Event,strsplit(Result[1,1],' \\+ ')[[1]])]),c(Survtime,Event,strsplit(Result[1,1],' \\+ ')[[1]])]
  tsdat1 <- tsdat[complete.cases(tsdat[,c(Survtime,Event,strsplit(Result[1,1],' \\+ ')[[1]])]),c(Survtime,Event,strsplit(Result[1,1],' \\+ ')[[1]])]
  CoxPHres<-coxph(f,data = trdat1)
  lptr <- predict(CoxPHres,trdat1)
  trROCobjList[[s]] <- cdROC(stime=trdat1[,Survtime],status=trdat1[,Event],marker = lptr,predict.time = horizon)
  trauc<-trROCobjList[[s]]$auc
  lpts <- predict(CoxPHres,tsdat1)
  tsROCobjList[[s]]<-cdROC(stime=tsdat1[,Survtime],status=tsdat1[,Event],marker = lpts,predict.time = horizon)
  tsauc <- tsROCobjList[[s]]$auc
  FinalRes <- rbind(FinalRes,c(s,trauc,tsauc))
}
round(colMeans(FinalRes,na.rm = T),4)
round(sd(FinalRes[,3],na.rm = T),4)
MeantsTPR <- rowMeans(cbind(sapply(seq(100),function(v) tsROCobjList[[v]]$TPR)),na.rm = T)
MeantsTNR <- rowMeans(cbind(sapply(seq(100),function(v) tsROCobjList[[v]]$TNR)),na.rm = T)
MeantrTPR <- rowMeans(cbind(sapply(seq(100),function(v) trROCobjList[[v]]$TPR)),na.rm = T)
MeantrTNR <- rowMeans(cbind(sapply(seq(100),function(v) trROCobjList[[v]]$TNR)),na.rm = T)

png('ROCcurve.png',width = 800,height = 400)
par(mfrow=c(1,2))
plot(1-trROCobjList[[1]]$TNR,trROCobjList[[1]]$TPR,col=1,type='l',lwd=1,lty=2,cex.axis=1.5,xlab='1-Specificity',ylab='Sensitivity',main='[ROC curve] Training set',cex.main=1.8,cex.lab=1.5)
sapply(seq(2,100),function(v) lines(1-trROCobjList[[v]]$TNR,trROCobjList[[v]]$TPR,col=v,type='l',lwd=1,lty=2))
lines(1-MeantrTNR,MeantrTPR,col='midnightblue',type='l',lwd=5)
legend('bottomright',legend = paste0('Mean AUC:\n',round(mean(FinalRes[,2],na.rm = T),3),' ± ',round(sd(FinalRes[,2],na.rm = T),3)),lwd=5,cex=1.5,col = 'midnightblue')
plot(1-tsROCobjList[[1]]$TNR,tsROCobjList[[1]]$TPR,col=1,type='l',lwd=1,lty=2,cex.axis=1.5,xlab='1-Specificity',ylab='Sensitivity',main='[ROC curve] Test set',cex.main=1.8,cex.lab=1.5)
sapply(seq(2,100),function(v) lines(1-tsROCobjList[[v]]$TNR,tsROCobjList[[v]]$TPR,col=v,type='l',lwd=1,lty=2))
lines(1-MeantsTNR,MeantsTPR,col=1,type='l',lwd=5)
legend('bottomright',legend = paste0('Mean AUC:\n',round(mean(FinalRes[,3],na.rm = T),3),' ± ',round(sd(FinalRes[,3],na.rm = T),3)),lwd=5,cex=1.5)
dev.off()
#####################################################################

#####################################################################
##### Plot Variable Importance 
#####################################################################
Scaledat <- cbind(dat[,match(c(SampleID,Survtime,Event),colnames(dat))],apply(dat[,-match(c(SampleID,Survtime,Event),colnames(dat))],2,function(v) scale(v)))

mod<-coxph(as.formula(paste0('Surv(',Survtime,',',Event,') ~ ',as.character(Result[1,1]))),data = Scaledat)
ce=function(model.obj){
  extract=summary(get(model.obj))$coefficients[,c(1,3)]
  return(data.frame(extract,vars=row.names(extract),model=model.obj))
}
coefs = ce('mod')
names(coefs)[2]='se'

ggplot(coefs,aes(vars,coef))+geom_hline(yintercept = 0,lty=2,lwd=1,colour='grey50')+geom_errorbar(aes(ymin = coef -  se, ymax = coef  +  se,colour = vars),lwd=1,width=0)+geom_point(size=3,aes(colour=vars))+
  geom_text(aes(label = sprintf("%.2f", coef), colour = vars),hjust = 0.4,vjust=-1,size = 5,fontface = "bold") +
  coord_flip()+guides(colour=FALSE)+labs(x='Predictors',y='Standardized Coefficient')+theme_minimal()+theme(axis.text = element_text(size=15,face='bold'),axis.title = element_text(size=15,face='bold'),strip.text =element_text(size=15,face='bold'))
ggsave('Variable_Importance.png')
#####################################################################

