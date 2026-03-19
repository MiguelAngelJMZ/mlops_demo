# Demo MLOps con Databricks Asset Bundles

Demo para mostrar **promoción entre ambientes** (dev → prod) con **datos sintéticos** y **modelo en Unity Catalog**. Incluye **dos enfoques** para mostrar al cliente:

| Enfoque | Job | Qué hace |
|--------|-----|----------|
| **Demo 1: Reentrenar en ambos** | `demo_mlops_job` | En dev y en prod: genera datos sintéticos + entrena y registra el modelo en el catálogo del target. |
| **Demo 2: Solo promover modelo** | `promote_model_job` | Entrenas en dev; en prod solo copias la versión "Champion" del modelo de dev → prod (sin reentrenar). |

## Catálogos por ambiente

| Target | Catálogo UC      | Schema     |
|--------|------------------|------------|
| dev    | `demo_mlops_aval_dev`  | `mlops_demo` |
| prod   | `demo_mlops_aval_prod` | `mlops_demo` |

Los catálogos y el schema se crean al hacer `bundle deploy` (requiere CLI 0.287+ y motor de despliegue directo).

## Requisitos

- **Databricks CLI** >= 0.212.2 (recomendado 0.287+ para recursos `catalogs`).
- Autenticación configurada: `databricks auth login --host <workspace-url>`.
- Para dev y prod: dos perfiles en `~/.databrickscfg` (o el mismo `DEFAULT` si usas un solo workspace para la demo).

## Estructura del proyecto

```
.
├── databricks.yml          # Bundle, variables, targets dev/prod
├── resources/
│   ├── catalogs.yml        # Catálogo por target (demo_mlops_aval_dev / _prod)
│   ├── schemas.yml        # Schema mlops_demo en ese catálogo
│   └── jobs.yml           # Jobs: demo_mlops_job (reentrenar) + promote_model_job (promover)
├── src/notebooks/
│   ├── generate_synthetic_data.py   # Escribe training_data
│   ├── train_model.py               # Entrena, registra modelo en UC (alias Champion)
│   └── promote_model.py             # Copia modelo dev → target (Demo 2)
└── README.md
```

## Comandos para la demo

Usar motor directo para catálogos: `DATABRICKS_BUNDLE_ENGINE=direct` en deploy.

### 1. Validar configuración

```bash
cd /Users/miguel.jimenez/Documents/MLOps_Databricks
databricks bundle validate
databricks bundle validate -t prod
```

### 2. Desplegar

```bash
DATABRICKS_BUNDLE_ENGINE=direct databricks bundle deploy -t dev
DATABRICKS_BUNDLE_ENGINE=direct databricks bundle deploy -t prod
```

### 3. Demo 1 — Reentrenar en ambos ambientes

- **Dev:** genera datos + entrena → modelo en `demo_mlops_aval_dev.mlops_demo.demo_model`
- **Prod:** mismo job en prod → datos y modelo en `demo_mlops_aval_prod...`

```bash
databricks bundle run demo_mlops_job -t dev
databricks bundle run demo_mlops_job -t prod
```

### 4. Demo 2 — Solo promover el modelo (train once, deploy model)

- Entrenar **solo en dev:** `databricks bundle run demo_mlops_job -t dev`
- Promover el modelo **Champion** de dev a prod (sin reentrenar en prod):

```bash
databricks bundle run promote_model_job -t prod
```

El modelo en prod será una copia de la versión Champion de dev; en prod no se generan datos ni se entrena.

## Guion sugerido para el cliente

1. Explicar qué es un Asset Bundle y por qué usar un target por ambiente.
2. Mostrar `databricks.yml`: variables `catalog`/`schema` y targets dev/prod.
3. **Demo 1:** Desplegar, ejecutar `demo_mlops_job` en dev y en prod; mostrar que en cada ambiente se reentrena y se tiene modelo propio.
4. **Demo 2:** Ejecutar `demo_mlops_job` solo en dev; luego ejecutar `promote_model_job` con `-t prod`; mostrar que en prod aparece el mismo modelo (Champion) sin haber entrenado en prod.
5. Opcional: cambiar un hiperparámetro, reentrenar en dev, volver a ejecutar `promote_model_job -t prod` para actualizar prod.

## Notas

- Si tu CLI no soporta el recurso `catalogs` o el motor directo, crea los catálogos a mano en la UI (o con SQL) con los nombres `demo_mlops_aval_dev` y `demo_mlops_aval_prod` y comenta/elimina el archivo `resources/catalogs.yml` y la referencia al schema desde el recurso de catálogo; sigue usando las variables `catalog` y `schema` en el job.
- Perfil de workspace: en `databricks.yml` ambos targets usan `profile: DEFAULT`. Para dev y prod en workspaces distintos, define dos perfiles y pon `profile: dev-profile` y `profile: prod-profile` en cada target.
