"""
Implements a person for testing.
"""



class Person():
    """
    """
    def __init__(self, user=None):
        self.last_actions = None
        self.last_recommendation = None
        if user:
            self.user = user
            self.delete_user = False
        else:
            # Create and assign a new user.
            # if necessary later delete the user as well. But this might not be 
            # necessary since in Django we will be working with a fresh database 
            # that will in any case be destructed at the end of testing.
            self.delete_user = True
            success = False
            count = 0
            while not success:
                count += 1
                try:
                    self.user = User(username="test"+str(count), 
                                     password='test'+str(count))
                    self.user.save()
                    success = True
                except:
                    success = False
                    
        for c in Category.objects.all():
            try:
                #See if event action aggregate exists.If it does, reset it to default.
                eaa = EventActionAggregate.objects.get(user=self.user,category=c)
            except:
                #Else create one.
                eaa = EventActionAggregate(user=self.user, category=c)
            
            eaa.g, eaa.v, eaa.i, eaa.x = 0, 0, 0, 0
            eaa.save()
        

    def __del__(self):
        if self.delete_user:
            self.user.delete()
        self.reset_user_behavior()


    def push_recommendations(self, categories=None, events = None):
        self.last_recommendations = categories[:]
        self.last_actions = map(self.get_action,
                                self.last_recommendations)
        
        self.update_user_category_behavior(
            (self.last_actions.count(a)
             for a in [GO, VIEW, IGNORE, XOUT]))
        return(self.last_actions)

    def update_user_category_behavior(self,category_id,(g,v,i,x)=(0,0,0,0)):
        """change the user's aggregate action by given (g,v,i,x) tuple"""
        eaa = EventActionAggregate.objects.get(user=self.user, 
                                               category__id=category_id)
        eaa.g += g
        eaa.v += v
        eaa.i += i
        eaa.x += x
        eaa.save()

    
    
