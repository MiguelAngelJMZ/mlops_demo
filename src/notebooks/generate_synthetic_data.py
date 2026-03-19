# Databricks notebook source
# MAGIC %md
# MAGIC # Generar datos sintéticos para la demo MLOps
# MAGIC Escribe una tabla `training_data` en el catalog/schema del target (dev o prod).

# COMMAND ----------

# Parámetros inyectados por el job del bundle (base_parameters)
dbutils.widgets.text("catalog", "")
dbutils.widgets.text("schema", "")
catalog = dbutils.widgets.get("catalog")
schema_name = dbutils.widgets.get("schema")

assert catalog and schema_name, "Faltan parámetros catalog y schema"

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# COMMAND ----------

# Crear schema si no existe (evitar catalog.schema en una sola sentencia por compatibilidad con UC)
spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")

# COMMAND ----------

# Datos sintéticos: features numéricas + target binario (clasificación)
# Sin dependencias externas; solo Spark. Para más realismo se puede usar Faker en el cluster.
n_rows = 5000
seed = 42

df = (
    spark.range(0, n_rows)
    .withColumn("feature_1", F.rand(seed) * 10)
    .withColumn("feature_2", F.rand(seed + 1) * 5)
    .withColumn("feature_3", F.rand(seed + 2) * 20)
    .withColumn(
        "target",
        (
            (F.col("feature_1") * 0.3 + F.col("feature_2") * 0.2 + F.col("feature_3") * 0.02 + F.rand(seed + 3) * 2)
            > 3
        ).cast("int"),
    )
)

# COMMAND ----------

table_name = f"{catalog}.{schema_name}.training_data"
df.write.mode("overwrite").saveAsTable(table_name)
print(f"Tabla escrita: {table_name} ({df.count()} filas)")
