from spambayes import classifier 
from events.models import Event
from django.conf import settings

# This is awfully hacky right now. The idea is to use a small set of
# words that are unlikely to be in a legitimate description (like 'insurance'
# or 'enlargement') to get an initial spam corpus, and then arbitrarily
# fetch an equal amount of legitimate events for a ham corpus.
# From
# there, test performance on mixed corpus. Then, try to use it to
# filter results from the imported Eventful events -- return events
# flagged as spam or unsure in a quarantined container, and process
# them last, requiring manual confirmation from the user (after
# inspecting the event details) that the event is legitimate in order
# to load them into the database.


class EventfulSpamFilter(object):

    def __init__(self):
        self.flag_words=('Homeowners','Insurance','Penis')
        self.spam_classifier = classifier.Classifier()
        self.seed_spam_corpus = set()
        self.seed_ham_corpus = set()

    def harvest_by_keywords(self):
        for e in Event.objects.all():
            if any(word in e.description or word in e.title for word in self.flag_words):
                self.seed_spam_corpus.add(e)
            elif len(self.seed_spam_corpus)-len(self.seed_ham_corpus) > 0:
                self.seed_ham_corpus.add(e)

    def train(self):
        for e in self.seed_spam_corpus:
            msg = e.title + '\n' + e.description
            self.spam_classifier.learn(msg,is_spam=True)
        for e in self.seed_ham_corpus:
            msg = e.title + '\n' + e.description
            self.spam_classifier.learn(msg,is_spam=False)
        pass

    def test(self):
        corpus_ids = set(e.id for e in self.seed_spam_corpus.union(self.seed_ham_corpus))
        testing_corpus = [e for e in Event.objects.all() if not e.id in corpus_ids]
        for e in testing_corpus:
            msg = e.title + '\n' + e.description
            print self.spam_classifier.spamprob(msg)
            print msg


