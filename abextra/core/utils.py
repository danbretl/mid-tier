class Bunch(dict):
    """When prototyping (or even finalizing) data structures such as trees,
    it can be useful to have a flexible class that will allow you to specify 
    arbitrary attributes in the constructor.
    In these cases, the "Bunch" pattern (named by Alex Martelli in the Python Cookbook) 
    can come in handy.

    >>> x = Bunch(name="Jayne Cobb", position="Public Relations") >>> x.name 'Jayne Cobb'

    >>> T = Bunch
    >>> t = T(left=T(left="a", right="b"), right=T(left="c"))
    """
    def __init__(self, *args, **kwds):
        super(Bunch, self).__init__(*args, **kwds)
        self.__dict__ = self
