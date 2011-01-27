import helper
import ml


print "Children: ", helper.Get_Children(1)
print "Sub Tree: ", helper.Get_SubTree(1)

print "G,V,I,X: ", helper.Get_Node_Val(1,12)

print "Get Children at Root ", helper.Get_Children()

print ml.User_Category_Score(1,2)

print ml.SummaryScore(ml.TrivialAlgorithm(1))

print ml.User_Category_Score(1,12)
