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

def unique_everseen(iterable, key=None):
    """List unique elements, preserving order. Remember all elements ever seen.
    >>> unique_everseen('AAAABBBCCDAABBB') --> A B C D
    >>> unique_everseen('ABBCcAD', str.lower) --> A B C D
    """
    seen = set()
    seen_add = seen.add
    if key is None:
        for element in ifilterfalse(seen.__contains__, iterable):
            seen_add(element)
            yield element
    else:
        for element in iterable:
            k = key(element)
            if k not in seen:
                seen_add(k)
                yield element

def dict_path_get(d, path):
    """recursive dictionary getter.
    dict: D = {'a': {'b': {'c': value}}}
    path: "/a/b/c"
    >>> dict_path_get(D, path) --> value
    """
    if not isinstance(d, dict):
        raise ValueError('requires a dictionary')
    if path:
        path = path.strip('/')
        partials = path.split('/', 1)
        if len(partials) > 1:
            key, path_remainder = partials
            return dict_path_get(d[key], path_remainder) if d.has_key(key) else None
        else:
            return d.get(path)
    else:
        raise ValueError('requires a path')
