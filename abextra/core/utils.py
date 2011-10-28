from itertools import ifilterfalse
from BeautifulSoup import BeautifulSoup, Comment

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

def dict_path_get(d, path, default=None):
    """Recursive dictionary getter.
    dict: D = {'a': {'b': {'c': value}}}
    path: "/a/b/c"
    >>> dict_path_get(D, path) --> value
    """
    # parameter checks
    if not isinstance(d, dict):
        raise ValueError('requires a dictionary')
    if not path:
        raise ValueError('requires a path')

    partials = path.strip('/').split('/', 1)
    # base case
    if len(partials) == 1:
        return d.get(path, default)
    # recursive case
    key, path_remainder = partials
    nested_dict = d.get(key)
    return dict_path_get(nested_dict, path_remainder, default) if isinstance(nested_dict, dict) else default

def dict_from_values(D):
    return dict((k, v) for k, v in D.iteritems() if v is not None)

def html_sanitize(value, valid_tags=[], valid_attrs=[]):
    soup = BeautifulSoup(value)
    for comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
        comment.extract()
    for tag in soup.findAll(True):
        if tag.name not in valid_tags:
            tag.hidden = True
            tag.attrs = [(attr, val) for attr, val in tag.attrs if attr in valid_attrs]
    return soup.renderContents().decode('utf8')


