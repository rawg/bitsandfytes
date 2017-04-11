
init.time = proc.time()

conf <- getOption("repos")
conf["CRAN"] <- "http://cran.rstudio.com/"
options(repos = conf)

if (!require("xlsx")) {
	#install.packages("rJava", type = "mac.binary", dependencies = TRUE)
	#install.packages("xlsx", dependencies = TRUE)
}
if (!require("vegan")) {
	install.packages("vegan", dependencies = TRUE)
}
if (!require("Hmisc")) {
	install.packages("Hmisc", dependencies = TRUE)
}
if (!require("dplyr")) {
	install.packages("dplyr", dependencies = TRUE)
}
if (!require("BioPhysConnectoR")) {
	install.packages("BioPhysConnectoR", dependencies = TRUE)
}

# Apparently, it's impossible to get rJava installed on OS X+Homebrew, but it doesn't appear to be needed.
#library(xlsx)
library(vegan)
library(Hmisc)
library(dplyr)
library(BioPhysConnectoR)

#install.packages('BioPhysConnectoR')

getwd()
#setwd("D://2017//contest")
#setwd("/resources/data/cat-art/")
getwd()

#data = read.csv("category-article.csv")
#data = read.csv("redundant-removals.csv")
#data = read.csv("multiple-merges.csv")
#data = read.csv("remix.csv")
#data = read.csv("1.10x10.csv")
data = read.csv("input.csv")

tab = as.matrix(data)

nonblanks = apply(tab,c(1,2),function(x) x[1] != "") == TRUE
main = tab[nonblanks[,1]==TRUE,]
rownames(main) = seq(1:length(main[,1]))

frame = data.frame(main,stringsAsFactors = FALSE)

frame1 = table(frame)

nrow(distinct(frame,category))
nrow(distinct(frame,article))
nrow(distinct(frame))

# time taken for below function
prc = proc.time()
dist = designdist(frame1,method="(A+B-2*J)/(A+B-J)",terms="binary")
proc.time() - prc

prc = proc.time()
str(dist)
proc.time() - prc

mat = as.matrix(dist)

length(which(dist <= 0.25 & dist >= 0))

length(which(mat < 0.25 & mat >= 0))

categories = rownames(mat)

# catlist contains 2 columns -> id of category, count of articles & category name
catlist = data.frame(id=seq(1:nrow(mat)),art_count=rep(0,nrow(mat)),name=rep('',nrow(mat)),
                     stringsAsFactors = FALSE)
for (ii in 1:nrow(main)) {
  inc(catlist[which(rownames(mat) == main[ii,1]),2]) = 1
  catlist[which(rownames(mat) == main[ii,1]),3] = main[ii,1]
}



rownames(mat) = seq(1:nrow(mat))
colnames(mat) = seq(1:ncol(mat))

#vect = data.frame(key=0,val=c(''),stringsAsFactors = FALSE)
vectkey = c()
vectval = c()

for (ii in 1:(nrow(mat))) {

#for (ii in 1:100) {

 temp = ''
 for (jj in 1:ncol(mat)) {
 #for (jj in 2:101) {

   #print (ii)
   if (ii == jj) {
     next
   }
   if (mat[ii,jj] < 0.25) {
     if (temp == '') {
       temp = jj
     }
     else {
       temp = paste(temp,jj,sep=',')
     }

     #vect['val'] = jj
     #print (temp)
   }

 }

   vectkey[ii] = ii
   vectval[ii] = temp

}


tup = length(vectkey)
# list contains 3 columns - id of category, main category or not, main category's id
list = data.frame(id=seq(1,tup), is_it_main_cat=rep(TRUE,tup),main_cat=rep(0,tup),
                  stringsAsFactors = FALSE)
#kk = 0


for (ii in 1:length(vectkey)) {
#for (ii in 1:1) {
  if (vectval[ii] == "" | list[ii,2] == FALSE) {
    next
  }
  else {
   temp = strsplit(vectval[ii],',')
   sphere = paste(vectval[ii],sep=',')
   #print (sphere)
   #print (vectval[ii])
   maxcnt = catlist[vectkey[ii],2]
   maxcat = catlist[vectkey[ii],1]

   for (jj in 1:length(temp[[1]])) {
     num = as.integer(temp[[1]][jj])
     #print (num)
     sphere = paste(sphere,vectval[num],sep=",")
     if (max(maxcnt , catlist[num,2]) > maxcnt) {
       list[maxcat,2] = FALSE
       maxcat = catlist[num,1]
       maxcnt = max(maxcnt , catlist[num,2])
     }
     else {
       list[num,2] = FALSE
     }
     #print (sphere)
   }

   list[vectkey[ii],3] = maxcat
   for (jj in 1:length(temp[[1]])) {
     num = as.integer(temp[[1]][jj])
     list[num,3] = maxcat
   }

   }
   ### below logic will form a group of categories ###
   #print (sphere)
   x = strsplit(sphere,',')
   y = table(x)

   cnt = y[[1]]
   z = table(y == cnt)

     # print (y)
     # print (z)


   #print (z[[1,1]])
   if (rownames(z)[1] == FALSE) {
     print (paste('WATCH out - ', vectkey[ii], sep=':'))
   }
  }



table(list[,2])

write = function(main,list,catlist) {
  final = main
  repl = 0
  for (ii in 1:nrow(final)) {
  #for (ii in 1:1) {
    catname = final[ii,1]
    catid = catlist[which(catlist[,3] == catname),1]
    catmainid = catid

    if (list[catid,3] != 0) {
      catmainid = list[catid,3]
      #print (paste(list[catid,3],list[catid,1],sep=','))
      if (list[catid,3] != list[catid,1]) {
        inc(repl) = 1
      }

    }
    #print (catmainid)
    maincatname = catlist[catmainid,3]
    final[ii,1] = maincatname
    #final[ii,2] = main[ii,2]
  }
  print (paste('replaced ',repl,sep=':'))
  return(final)
}




final = write(main,list,catlist)

sortfinal = mat.sort(final,c(1,2),decreasing = FALSE)

uniqfinal = distinct(data.frame(sortfinal))

#write.csv(uniqfinal,file="v0.2-output-catart.csv",row.names = FALSE)
#write.csv(uniqfinal,file="v0.2-output-redundant.csv",row.names = FALSE)
#write.csv(uniqfinal,file="v0.2-output-merges.csv",row.names = FALSE)
#write.csv(uniqfinal,file="v0.2-output-remix.csv",row.names = FALSE)
#write.csv(uniqfinal,file="v0.2-output-1.10x10.csv",row.names = FALSE)
write.csv(uniqfinal,file="output.csv",row.names = FALSE)

nrow(distinct(as.data.frame(final),category))
nrow(distinct(as.data.frame(final),article))

# Total elapsed time
proc.time() - init.time
