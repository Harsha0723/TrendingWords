from __future__ import print_function
# for setup
import os
os.environ['PYSPARK_PYTHON'] = '/opt/homebrew/bin/python3.10'

import sys

from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, col
from pyspark.sql.functions import udf
from pyspark.sql.types import ArrayType, StringType
from kafka import KafkaProducer
import spacy
import json


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("""
        Usage: structured_kafka_wordcount.py <bootstrap-servers> <subscribe-type> <topics>
        """, file=sys.stderr)
        sys.exit(-1)

    bootstrapServers = sys.argv[1]
    subscribeType = sys.argv[2]
    topics = sys.argv[3]

    spark = SparkSession\
        .builder\
        .appName("StructuredKafkaWordCount")\
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")

    nlp = spacy.load("en_core_web_sm")

    # def ner_spacy(text):
    #     doc = nlp(text)
    #     return [(ent.text, ent.label_) for ent in doc.ents]
 
    # ner_udf = udf(ner_spacy, ArrayType(StringType()))

    producer = KafkaProducer(bootstrap_servers=bootstrapServers)

    # DataSet representing the stream of input lines from kafka
    lines = spark\
        .readStream\
        .format("kafka")\
        .option("kafka.bootstrap.servers", bootstrapServers)\
        .option(subscribeType, topics)\
        .load()\
        .selectExpr("CAST(value AS STRING) as data")

    # Define UDF to perform NER using Spacy
    @udf(ArrayType(StringType()))
    def ner_spacy(text):
        doc = nlp(text)
        return [ent.text for ent in doc.ents]

    # Registering the UDF
    spark.udf.register("ner_spacy", ner_spacy)

    # Applying the function to the streaming DataFrame
    word_count_df = lines \
    .select("data", explode(ner_spacy("data")).alias("word")) \
    .groupBy("word") \
    .count() \
    .orderBy(col("count").desc())


   # Function to show the word count (taking top 10 occuring words)
    def word_count(df, epoch_id):
        word_count_dict = dict(df.take(10))
        producer.send('topic2', value=json.dumps(word_count_dict).encode())

    # Applying the function to the streaming DataFrame
    output = word_count_df.writeStream \
        .outputMode("complete") \
        .foreachBatch(word_count) \
        .start()

    output.awaitTermination()