import os
import sys
sys.path.append('/opt/local/lib/graphviz/python/')
import gv

from django.core.management.base import NoArgsCommand
from abextra.events.models import Category

from pygraph.classes.graph import graph
from pygraph.readwrite.dot import write
from pygraph.algorithms.searching import breadth_first_search
from pygraph.classes.digraph import digraph
from pygraph.classes.exceptions import AdditionError

from itertools import count

output_dir = 'category_graphs'

class Command(NoArgsCommand):
    help = 'Loads scraped events from the scraped view'

    def handle(self, **options):
        gr = graph()

        cats_by_id = dict((c.id, c) for c in Category.objects.all())

        # Add nodes
        dups = count()
        for c in cats_by_id.itervalues():
            try:
                gr.add_node(c)
            except AdditionError:
                dups.next()
                parent = cats_by_id.get(c.parent_id)
                print 'WARNING: duplicate node :: <Category %i | %s>' % (c.id, c)
                print '\twith parent ' + '<Category %i | %s>' % (parent.id, parent) if parent else 'None'

        if dups.next() > 0: return

        # Add edges
        # gr.add_edge((CONCRETE_NODE, ROOT_NODE))
        for c in cats_by_id.itervalues():
            parent = cats_by_id.get(c.parent_id)
            if parent:
                gr.add_edge((c, parent))

        # import ipdb; ipdb.set_trace()
        # The whole tree from the root
        st, order = breadth_first_search(gr, root=Category.objects.get(title="Abstract"))
        gst = digraph()
        gst.add_spanning_tree(st)

        dot = write(gst)
        gvv = gv.readstring(dot)

        gv.layout(gvv, 'dot')
        gv.render(gvv, 'pdf', os.path.join(output_dir, 'abstract.pdf'))

        st, order = breadth_first_search(gr, root=Category.objects.get(title="Concrete"))
        gst = digraph()
        gst.add_spanning_tree(st)

        dot = write(gst)
        gvv = gv.readstring(dot)

        gv.layout(gvv, 'dot')
        gv.render(gvv, 'pdf', os.path.join(output_dir, 'concrete.pdf'))


        # # Individual trees from
        # for c in Category.objects.filter(parent__exact=None):
        #     gr.del_edge((c, ROOT_NODE))
        #     st, order = breadth_first_search(gr, root=c)
        #     gst = digraph()
        #     gst.add_spanning_tree(st)
        # 
        #     dot = write(gst)
        #     gvv = gv.readstring(dot)
        # 
        #     gv.layout(gvv, 'dot')
        #     file_suffix = '_'.join(c.title.lower().split())
        #     file_path = os.path.join(output_dir, '%s.png' % file_suffix)
        #     gv.render(gvv, 'png', str(file_path))
