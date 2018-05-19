occ_prob = read.csv('Results/1YearProba.csv')
nb_sources = dim(occ_prob)[1]
rand = runif(n=nb_sources, min=0, max=1)
act_sources=c()
for(i in c(1:nb_sources)){
  if(rand[i]<=occ_prob$Proba[i]){
    print(as.character(occ_prob$Code[i]))
    act_sources = c(act_sources, as.character(occ_prob$Code[i]))
  }
}
pref_losses=data.frame()
for(code in act_sources){
  source_losses =read.csv(paste0('Results/Instrumental/', code, '/prefectures.csv'))
  pref_losses = data.frame(pref_losses, source_losses)
}
