# Databricks notebook source
# MAGIC %md
# MAGIC # Entrenar modelo y registrar en Unity Catalog
# MAGIC Lee `training_data` del catalog/schema del target y registra el modelo en UC.

# COMMAND ----------

# Parámetros inyectados por el job del bundle
dbutils.widgets.text("catalog", "")
dbutils.widgets.text("schema", "")
catalog = dbutils.widgets.get("catalog")
schema_name = dbutils.widgets.get("schema")

assert catalog and schema_name, "Faltan parámetros catalog y schema"

# COMMAND ----------

import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# COMMAND ----------

# Leer datos generados por la tarea anterior
table_name = f"{catalog}.{schema_name}.training_data"
df = spark.table(table_name)
pandas_df = df.toPandas()

feature_cols = ["feature_1", "feature_2", "feature_3"]
X = pandas_df[feature_cols]
y = pandas_df["target"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# COMMAND ----------

# Experimento por ambiente para no mezclar runs
experiment_name = f"/Shared/demo_mlops_{catalog}"
mlflow.set_experiment(experiment_name)

with mlflow.start_run(run_name="rf_demo"):
    model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    accuracy = accuracy_score(y_test, preds)

    mlflow.log_param("n_estimators", 50)
    mlflow.log_param("max_depth", 5)
    mlflow.log_metric("accuracy", accuracy)
    # UC exige firma (inputs + outputs) para registrar el modelo
    signature = mlflow.models.infer_signature(X_train, model.predict(X_train))
    mlflow.sklearn.log_model(model, "model", signature=signature)

    # Registrar en Unity Catalog: catalog.schema.model_name
    model_uri = f"runs:/{mlflow.active_run().info.run_id}/model"
    full_model_name = f"{catalog}.{schema_name}.demo_model"
    reg = mlflow.register_model(model_uri, full_model_name)
    mlflow.MlflowClient().set_registered_model_alias(full_model_name, "Champion", reg.version)
    print(f"Modelo registrado: {full_model_name} v{reg.version} (alias Champion, accuracy={accuracy:.4f})")
