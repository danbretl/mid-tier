from importer.consumer import ScrapeFeedConsumer
from importer.parsers import PlaceParser

def importd():
    consumer = ScrapeFeedConsumer()
    parser = PlaceParser()
    for location in consumer.locations:
        yield parser.parse(location)
