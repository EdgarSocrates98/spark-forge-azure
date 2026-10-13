df.groupBy("user_id").count()
df.join(big_df, "user_id")
df.repartition(1)
