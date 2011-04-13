from pundit.arbiter import Arbiter
from pundit.classification_rules import *

default_arbiter = Arbiter([
    SourceCategoryRule(),
    SourceRule()
])
