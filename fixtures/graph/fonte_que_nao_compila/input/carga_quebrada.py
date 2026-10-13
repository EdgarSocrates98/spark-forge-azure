from graphframes import GraphFrame


def componentes(spark:
    return GraphFrame(spark, spark).connectedComponents()
