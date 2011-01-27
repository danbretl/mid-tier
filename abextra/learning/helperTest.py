import helper
import ml


print "Children: ", [x.id for x in helper.get_children(1)]
print "Sub Tree: ", helper.Get_SubTree()

print "G,V,I,X: ", helper.Get_Node_Val(1,12)

print "Get Children at Root: ", helper.get_children()

print "User 1 category 2: ", ml.User_Category_Score(1,2)
print "User 1, category 12: ", ml.User_Category_Score(1,12)


print "Scoring summary for user 1's root nodes", ml.SummaryScore(ml.TrivialAlgorithm(1))


