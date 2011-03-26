from importer.consumer import ScrapeFeedConsumer
from importer.parsers import PointParser

def importd(parser = PointParser()):
    consumer = ScrapeFeedConsumer()
    for location in consumer.locations:
        print parser.parse(location)
