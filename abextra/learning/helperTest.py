import helper
import ml


#print "Children: ", [x.id for x in helper.get_children()]
#print "Sub Tree: ", helper.get_subTree()

#print "G,V,I,X: ", helper.get_node_val(1,12)

#print "Get Children at Root: ", helper.get_children()

print "Scoring summary for user 1's root nodes", ml.tree_walk_algorithm(1098)

