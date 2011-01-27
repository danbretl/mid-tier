import ml

originalDistribution = [("A",0.3),("B",0.1), ("C", 0.5), ("D", 0.1)]
a = ml.SampleDistribution(originalDistribution,100)
dict={}
for x in a:
    try:
        dict[x]+=1
    except:
        dict[x]=1
print dict
