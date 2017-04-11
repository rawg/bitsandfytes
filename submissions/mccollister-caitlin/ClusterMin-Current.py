# -*- coding: utf-8 -*-

import numpy as np
from collections import OrderedDict
from scipy.sparse import csr_matrix as sparse_matrix
from scipy.sparse import triu
from pandas import read_csv
from copy import deepcopy
from csv import QUOTE_MINIMAL
import pandas

Filename = "redundant-removals.csv"
#Filename = "multiple-merges.csv"
#Filename = "remix.csv"
#Filename = "category-article.csv"
#Filename = "1.10x10.csv"

def JSim(*args):
    if not all([type(s) == set for s in args]):
        return None
    elif len(args) == 0:
        return None
    elif len(args) == 1:
        return float(1)
    else:
        numerator = len(set.intersection(*args))
        denominator = len(set.union(*args))
        result = numerator / denominator
        print("{n} / {d} = {r:0.4}".format(n=numerator, d=denominator, r=result))
        
        if result > 0.75:
            print(" --> return union (size {s})\n".format(s=len(set.union(*args))))
            return set.union(*args)
        else:
            print(" --> return empty set\n")
            return set()

class PatternHolder(object):
    def __init__(self, Filename):
        self.OrigFilename = Filename
        self.ImportFromFile(self.OrigFilename)
        
        self.UpdateGroupNames()

        self.OrigGroupArticlePairsCount = len(self.OriginalPairs)
        self.OrigGroupCount = len(self.GroupNames)
        self.OrigArticleCount = len(self.ArticleNames)
        self.UpdateJSimMatrix()
        
    def ImportFromFile(self, Filename):
        self.OriginalPairs = []
        self.ArticlesInGroup = OrderedDict()
        self.GroupInArticles = OrderedDict()
        self.OutputArticlesInGroup = OrderedDict()
        
#        Data = np.array(open(FileName).read().replace('\n\n','\n').split('\n'))
#        DataArray = [x.split(",") for x in Data]
#        DataArray = np.array(DataArray[1:-1])

        DataArray = read_csv(Filename, header=0).to_records()
        for Entry in DataArray:
            Group   = str(Entry[1])
            Article = str(Entry[2])

            # Note: It's much faster to use an exception as opposed to a conditional in this case.
            try:
                self.ArticlesInGroup[Group]
            except KeyError:
                self.ArticlesInGroup[Group] = set([Article])
                
            try:
                self.GroupInArticles[Article]
            except KeyError:
                self.GroupInArticles[Article] = set([Group])
            
#            if (Group, Article) in self.OriginalPairs:
#                 print("Duplicate Found: {}".format((Group, Article)))

            self.OriginalPairs.append((Group, Article))
            
            self.ArticlesInGroup[Group].add(Article)
            self.GroupInArticles[Article].add(Group)

    def ArticlesInGroupNum(self, GroupNumber):
        return self.ArticlesInGroup[self.GroupNames[GroupNumber]]
    
    def BuildMatrix(self):
        self.SortArticlesInGroup()
        self.UpdateGroupNames()
        self.UpdateIndices()
        self.RelationshipMatrix = np.zeros((len(self.GroupNames), len(self.ArticleNames)), dtype=bool)
        for (Group, Articles) in self.ArticlesInGroup.items():
            for Article in Articles:
                self.RelationshipMatrix[self.GroupIndices[Group],self.ArticleIndices[Article]]=True

    def SortArticlesInGroup(self):
        self.ArticlesInGroup = OrderedDict(sorted(self.ArticlesInGroup.items(), key=lambda item: len(item[1])))

    def UpdateIndices(self):
        self.ArticleIndices = {}
        self.GroupIndices = {}
        for i, Article in enumerate(self.ArticleNames):
            self.ArticleIndices[Article] = i
        for i, Group in enumerate(self.GroupNames):
            self.GroupIndices[Group] = i

    
    def UpdateGroupNames(self):
        self.GroupNames = deepcopy(list(self.ArticlesInGroup.keys()))

    @property
    def ArticleNames(self):
        return deepcopy(list(self.GroupInArticles.keys()))

    @property
    def GroupSizes(self):
        return deepcopy([len(x) for x in self.ArticlesInGroup.values()])
    
    def UpdateJSimMatrix(self, IncludeUpdate = True):
        if IncludeUpdate:
            self.UpdateIntersectionMatrix(IncludeUpdate)
            
        IntersectionMatrix = np.array(self.IntersectionMatrix.toarray().astype(float))
        
        self.GroupSizeMatrix = np.array([self.GroupSizes]*len(self.GroupNames)) + np.array([self.GroupSizes]*len(self.GroupNames)).T
        self.JSimMatrix = sparse_matrix(IntersectionMatrix/(self.GroupSizeMatrix - IntersectionMatrix))
        self.JSimMatrix = triu(self.JSimMatrix,k=1)
        
    def UpdateIntersectionMatrix(self, IncludeUpdate = True):
        if IncludeUpdate:
            self.BuildMatrix()
        RMIntForm = sparse_matrix(self.RelationshipMatrix.astype(np.float))
        self.IntersectionMatrix = np.dot(RMIntForm,RMIntForm.T)

    def UnconnectedGroups(self, IncludeUpdate = True):
        if IncludeUpdate:
            self.UpdateIntersectionMatrix()
        GroupSizes = [len(x) for x in self.ArticlesInGroup.values()]
        OnlySelfIntersectingGroups = (sum(self.IntersectionMatrix.toarray()) == GroupSizes)
        return np.array(self.GroupNames)[OnlySelfIntersectingGroups]
    
    def TransferUnconnectedGroupsToOutput(self, CheckOutput=False, IncludeUpdate = True):
        ToTransfer = self.UnconnectedGroups(IncludeUpdate)
        print("Found {} Unconnected Groups to Transfer.".format(len(ToTransfer)))
        for Group in ToTransfer:
            self.TransferToOutput(Group, CheckOutput)
            
    def TransferToOutput(self, Group, CheckOutput=False):
        try:
            self.OutputArticlesInGroup[Group] = self.ArticlesInGroup.pop(Group)
            # Cleanup
            self.CleanupGroup(Group)
            
            if CheckOutput:
                K = [len(self.GroupInArticles[x]) for x in self.OutputArticlesInGroup[Group]]
                print("{} : {} : {}".format(K, Group,self.OutputArticlesInGroup[Group]))
            return True
        except KeyError as e:
            print("Group not found: {}".format(e))
            return False

    def RemoveEqual(self):
        ToRemove = self.FindEqualGroupsToRemove()
        print("Found {} Equal Type Groups to Remove.".format(len(ToRemove)))
        for Group in ToRemove:
            try:
                self.ArticlesInGroup.pop(Group)
                # Cleanup
                self.CleanupGroup(Group)
            except KeyError as e:
                print("Group : {} : Was not found!!!".format(e))

    def RemoveProperSubsets(self):
        ToRemove = self.FindProperSubsetsToRemove()
        print("Found {} Proper Subset Type Groups to Remove.".format(len(ToRemove)))
        for Group in ToRemove:
            try:
                self.ArticlesInGroup.pop(Group)
                # Cleanup
                self.CleanupGroup(Group)
            except KeyError as e:
                print("Group : {} : Was not found!!!".format(e))

    def CleanupGroup(self, Group, CheckOutput=False):
        pass
    
    def WriteOutput(self, Filename=False):
        if Filename:
            pass
        else:
            Filename = "output-{}".format(self.OrigFilename)
        
        OutputPairs = []
        for Group in self.OutputArticlesInGroup.keys():
            for Article in self.OutputArticlesInGroup[Group]:
                OutputPairs.append([Group, Article])
                
        PDFOutput = pandas.DataFrame(OutputPairs)
        PDFOutput.to_csv(Filename, index=False, encoding="utf8", quoting=QUOTE_MINIMAL,header=None)
#        with open(Filename,"w") as OutputFileHandle:
#            for Group in self.OutputArticlesInGroup.keys():
#                for Article in self.OutputArticlesInGroup[Group]:
#                    print("\"{}\",\"{}\"".format(Group,Article), file=OutputFileHandle)

    def FindEqualGroupsToRemove(self):
        self.UpdateJSimMatrix()
        AllGroupSets = {}
        for Group in self.GroupNames:
            CurrentArticleSet = frozenset(self.ArticlesInGroup[Group])
            try:
                AllGroupSets[CurrentArticleSet].update([Group])
            except KeyError:
                AllGroupSets[CurrentArticleSet]=set([Group])
        GroupsToRemove = set()
        [GroupsToRemove.update(list(Groups)[1:]) for Groups in AllGroupSets.values() if len(Groups) > 1]
        return GroupsToRemove


    def FindProperSubsetsToRemove(self):
        self.UpdateJSimMatrix()
        ProperSubsets = set()
        GroupSizes = self.GroupSizes
        for i in np.arange(self.IntersectionMatrix.shape[0]):
            Candidates = [x for x in self.IntersectionMatrix.getrow(i).nonzero()[1] if GroupSizes[x] > GroupSizes[i]]
            for Candidate in Candidates:
                if self.ArticlesInGroup[self.GroupNames[i]] < self.ArticlesInGroup[self.GroupNames[Candidate]]:
                    ProperSubsets.update([self.GroupNames[i]])
        return ProperSubsets

    def MergeIsolated(self, Cutoff = 0.75, ShowOutput = False):
        self.UpdateJSimMatrix()
        SimilarGroups = self.CurrentSimilarGroupPairs(Cutoff)
        AllGroups = np.hstack(SimilarGroups)
        # Check is SimilarGroups are seperated
        
        IsolatedGroups = []
        AllSets = [self.ArticlesInGroup[self.GroupNames[i]] for i in AllGroups]
        for i,j in zip(*(SimilarGroups)):
            
            GroupNameI = self.GroupNames[i]
            GroupNameJ = self.GroupNames[j]
            CSetI = self.ArticlesInGroup[GroupNameI]
            CSetJ = self.ArticlesInGroup[GroupNameJ]
            SetI = sum([len(CSetI.intersection(k)) for k in AllSets if (CSetI.intersection(k) != CSetI) and (CSetJ.intersection(k) != CSetJ)])
            SetJ = sum([len(CSetJ.intersection(k)) for k in AllSets if (CSetI.intersection(k) != CSetI) and (CSetJ.intersection(k) != CSetJ)])
            if SetI + SetJ == 0:
                IsolatedGroups.append((GroupNameI,GroupNameJ))
                if ShowOutput:
                    print("--------------------------------------------------------------------------------------")
                    print("{} : {}".format(self.GroupNames[i],self.GroupNames[j]))
                    print("{}".format(self.ArticlesInGroup[self.GroupNames[i]]))
                    print("{}".format(self.ArticlesInGroup[self.GroupNames[j]]))
        for GroupPair in IsolatedGroups:
            self.MergeGroups(self.GroupNames[GroupPair[0]],self.GroupNames[GroupPair[1]], ShowOutput)
        print("Merged Isolated {} Groups.".format(len(IsolatedGroups)))
        return len(IsolatedGroups)
            
    def MergeGroups(self, Group1, Group2, ShowOutput = False):
        try:
            SizeGroup1 = len(self.ArticlesInGroup[Group1])
            SizeGroup2 = len(self.ArticlesInGroup[Group2])
            if SizeGroup1 > SizeGroup2:
                LGroup = Group1
                SGroup = Group2
            else:
                LGroup = Group2
                SGroup = Group1
            if ShowOutput:
                print("--------------------------------------------------------------------------------------")
                print("Large Group: {} : {}".format(LGroup,self.ArticlesInGroup[LGroup]))
                print("Small Group: {} : {}".format(SGroup,self.ArticlesInGroup[SGroup]))
            
            self.ArticlesInGroup[LGroup] = self.ArticlesInGroup[LGroup].union(self.ArticlesInGroup[SGroup])
            self.ArticlesInGroup.pop(SGroup)
            if ShowOutput:
                print("Result Group {} : {}".format(LGroup,self.ArticlesInGroup[LGroup]))
            # Cleanup
            self.CleanupGroup(SGroup)
        except KeyError as e:
            print("Group : {} : Was not found!!!".format(e))

    def MergeSimilarGroups(self, Cutoff = 0.75, ShowOutput = False):
        self.UpdateJSimMatrix()
        SimilarGroups = self.CurrentSimilarGroupPairs(Cutoff)
        MergedGroups = []
        for i,j in zip(*(SimilarGroups)):
            GroupNameI = self.GroupNames[i]
            GroupNameJ = self.GroupNames[j]
            CSetI = self.ArticlesInGroup[GroupNameI]
            CSetJ = self.ArticlesInGroup[GroupNameJ]
            MergedGroups.append((i,j))
            if ShowOutput:
                print("--------------------------------------------------------------------------------------")
                print("{} : {}".format(GroupNameI,GroupNameJ))
                print("{}".format(CSetI))
                print("{}".format(CSetJ))
        for GroupPair in MergedGroups:
            self.MergeGroups(self.GroupNames[GroupPair[0]],self.GroupNames[GroupPair[1]], ShowOutput)
        print("Merged {} Groups.".format(len(MergedGroups)))
        return len(MergedGroups)
    
    def MergeAllSimilarGroups(self, Cutoff = 0.75, ShowOutput = False):
        self.UpdateJSimMatrix()
        SimilarGroups = self.CurrentSimilarGroupPairs(Cutoff)
        if len(SimilarGroups[0]) == 0:
            return 0
        MergedGroups = {}
        for i,j in zip(*(SimilarGroups)):
            try:
                MergedGroups[i].add(j)
            except KeyError:
                MergedGroups[i] = set([j])
        MergeSets = set()
        for key in MergedGroups.keys():
            MergeList = [key,]
            MergeList.extend(MergedGroups[key])
            if len(MergeList) > 2:
                MergeSets.add(frozenset(MergeList))
        MergeSets = list(MergeSets)
        print("{} : N-way merges Remaining.".format(len(MergeSets)))
        CompletedMerges = set()
        RemovedGroups = set()
        for MergeSet in MergeSets:
            if not (MergeSet in CompletedMerges):
                if len(MergeSet.intersection(RemovedGroups)) == 0:
                    self.NaryMerge(list(MergeSet))
                    print("{}-way merge.".format(len(MergeSets[0])))
                    CompletedMerges.add(MergeSet)
                    RemovedGroups = RemovedGroups.union(MergeSet)
#        for MergeSet in MergeSets:
#            MergeSet = list(MergeSet)
#            if len(MergeSet) > 2:
#                print("{} way merge.".format(len(MergeList)))
#                self.NaryMerge(MergeList)
#            else:
#                self.MergeGroups(self.GroupNames[MergeList[0]],self.GroupNames[MergeList[1]], ShowOutput)
        return len(MergeSets)

    def CurrentSimilarGroupPairs(self, Cutoff = 0.75):
        self.UpdateJSimMatrix()
        return (self.JSimMatrix > Cutoff).nonzero()
    
    def DeclareDone(self):
        self.UpdateJSimMatrix()
        for Group in self.GroupNames:
            self.TransferToOutput(Group)
            
    def MergeBad(self, Cutoff = 0.75, ShowOutput = False):
        self.UpdateJSimMatrix()
        SimilarGroups = self.CurrentSimilarGroupPairs(Cutoff)
        AllGroups = np.hstack(SimilarGroups)
        print(AllGroups)
        if len(AllGroups) > 0:
            self.NaryMerge(AllGroups)
        return len(AllGroups)

    def NaryMerge(self, GroupList, ShowOutput = False):
        try:
            SizeGroups = []
            Groups = []
            for Group in GroupList:
                GroupName = self.GroupNames[Group]
                Groups.append(GroupName)
                SizeGroups.append(len(self.ArticlesInGroup[GroupName]))
            LargestGroup = Groups[np.argmax(SizeGroups)]
            for Group in Groups:
                self.ArticlesInGroup[LargestGroup].update(self.ArticlesInGroup[Group])
                if Group != LargestGroup:
                    self.ArticlesInGroup.pop(Group)
                    self.CleanupGroup(Group)
        except KeyError as e:
            print("N-way Merge tried to use group \"{}\" even though it's already been removed.".format(e))

    def CheckOutputArticles(self):
        OutputArtcilesSet = set()
        [OutputArtcilesSet.update(x) for x in self.OutputArticlesInGroup.values()]
        return len(OutputArtcilesSet)
        
""" Setup Section """ 
Data = PatternHolder(Filename)

""" Investigation Section """ 

Data.RemoveEqual()
Data.UpdateIntersectionMatrix()
Data.TransferUnconnectedGroupsToOutput(IncludeUpdate = True)

while \
    (Data.MergeAllSimilarGroups(ShowOutput=False) > 0) or \
    (Data.MergeSimilarGroups(ShowOutput=False) > 0) or \
    (Data.MergeIsolated(ShowOutput=False) > 0):
        pass

Data.UpdateGroupNames()
Data.RemoveProperSubsets()
Data.UpdateGroupNames()
Data.RemoveEqual()


"""
OPTIONAL GRAPH VISUALIZATION SECTION

import matplotlib.pyplot as mpl
import networkx as nx

def DrawGraph(Matrix):
    mpl.figure()
    G = nx.from_scipy_sparse_matrix(Matrix)
    pos=nx.spring_layout(G)
    nx.draw_networkx_nodes(G,pos)
    nx.draw_networkx_labels(G,pos)
    # specifiy edge labels explicitly
    edge_labels=dict([((u,v,),"{:.2f}".format(d['weight'])) for u,v,d in G.edges(data=True)])
    eSim=[(u,v) for (u,v,d) in G.edges(data=True) if d['weight'] > 0.75]
    eDis=[(u,v) for (u,v,d) in G.edges(data=True) if d['weight'] <= 0.75]
    nx.draw_networkx_edges(G,pos,edgelist=eSim,width=3,edge_labels=edge_labels)
    nx.draw_networkx_edges(G,pos,edgelist=eDis,width=3,alpha=0.5,edge_color='b',style='dashed',edge_labels=edge_labels)
    nx.draw_networkx_edge_labels(G,pos,edge_labels=edge_labels)

#Data.UpdateJSimMatrix()
#DrawGraph(Data.JSimMatrix)

#Data.MergeSimilarGroups(ShowOutput=True)
#Data.RemoveProperSubsets()

#Data.UpdateJSimMatrix()
#DrawGraph(Data.JSimMatrix)

#mpl.matshow(Data.RelationshipMatrix,interpolation=None,norm=None)
#mpl.matshow(Data.IntersectionMatrix.todense(),interpolation=None,norm=None)
#mpl.matshow(Data.JSimMatrix.todense(),interpolation=None,norm=None)
"""

""" Output/Display Section """

Data.DeclareDone()
Data.WriteOutput()

print("Original Pairs: {}".format(len(Data.OriginalPairs)))
print("Final Pairs: {}".format(sum([len(x) for x in Data.OutputArticlesInGroup.values()])))
print("Pairs Removed: {}".format(len(Data.OriginalPairs)-sum([len(x) for x in Data.OutputArticlesInGroup.values()])))

print("Original Groups: {}".format(Data.OrigGroupCount))
print("Final Groups: {}".format(len(Data.OutputArticlesInGroup.keys())))
print("Groups Removed: {}".format(Data.OrigGroupCount-len(Data.OutputArticlesInGroup.keys())))

print("Original Articles: {}".format(Data.OrigArticleCount))

print("Final Articles: {}".format(Data.CheckOutputArticles()))

print("Original Filename: {}".format(Data.OrigFilename))
