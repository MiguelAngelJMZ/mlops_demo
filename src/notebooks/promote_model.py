# Databricks notebook source
# MAGIC %md
# MAGIC # Promover modelo de dev a prod (sin reentrenar)
# MAGIC Copia la versión "Champion" (o la última) del modelo desde el catálogo origen al catálogo destino.
# MAGIC **Demo 2:** train once in dev, deploy only the model to prod.

# COMMAND ----------

# Parámetros inyectados por el job (source = dev, target = prod cuando se corre con -t prod)
dbutils.widgets.text("source_catalog", "")
dbutils.widgets.text("target_catalog", "")
dbutils.widgets.text("schema", "")
dbutils.widgets.text("model_alias", "Champion")
source_catalog = dbutils.widgets.get("source_catalog")
target_catalog = dbutils.widgets.get("target_catalog")
schema_name = dbutils.widgets.get("schema")
model_alias = dbutils.widgets.get("model_alias")

assert source_catalog and target_catalog and schema_name, "Faltan source_catalog, target_catalog o schema"

# COMMAND ----------

from mlflow import MlflowClient

client = MlflowClient()
source_model_name = f"{source_catalog}.{schema_name}.demo_model"
target_model_name = f"{target_catalog}.{schema_name}.demo_model"

# COMMAND ----------

# Obtener la versión a promover: por alias (Champion) o la última
try:
    source_version = client.get_model_version_by_alias(source_model_name, model_alias)
except Exception:
    source_version = None
if source_version is None:
    versions = client.search_model_versions(f"name='{source_model_name}'")
    versions = sorted(versions, key=lambda v: int(v.version), reverse=True)
    if not versions:
        raise ValueError(f"No hay versiones del modelo {source_model_name}. Entrena primero en dev.")
    source_version = versions[0]

run_id = source_version.run_id
version = source_version.version
print(f"Promoviendo versión {version} (run_id={run_id}) de {source_model_name} -> {target_model_name}")

# COMMAND ----------

# Registrar en el catálogo destino (mismo artifact, sin reentrenar)
model_uri = f"runs:/{run_id}/model"
try:
    client.create_registered_model(target_model_name, description="Modelo promovido desde dev")
except Exception:
    pass  # ya existe
result = client.create_model_version(
    name=target_model_name,
    source=model_uri,
    run_id=run_id,
)
print(f"Modelo promovido: {target_model_name} versión {result.version}")

# Opcional: marcar como Champion en prod
client.set_registered_model_alias(target_model_name, model_alias, result.version)
print(f"Alias '{model_alias}' apunta a la versión {result.version} en prod.")
