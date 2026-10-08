spark.read.load("abfss://lake@stg.dfs.core.windows.net/finance/orders")
spark.sql("MERGE INTO prod.finance.orders t USING s ON t.id = s.id")
