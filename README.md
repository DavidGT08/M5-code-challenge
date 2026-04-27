# M5 Supply Chain Analytics — Walmart Sales Dataset

> Análisis de supply chain sobre el dataset M5 Forecasting de Walmart, con pipeline ETL en Python, modelo dimensional en Star Schema y dashboard ejecutivo en Power BI orientado a detección de desbalance de inventario.

---

## 📊 Sobre el dataset

Datos hierárquicos de ventas diarias de **3,049 productos** vendidos en **10 tiendas Walmart** distribuidas en **3 estados de Estados Unidos** (California, Texas, Wisconsin). El periodo cubre del **29-ene-2011 al 19-jun-2016** (1,941 días, ~5.4 años).

**Fuente:** [M5 Forecasting Accuracy — Kaggle](https://www.kaggle.com/competitions/m5-forecasting-accuracy), organizado por la Makridakis Open Forecasting Centre (MOFC) de la Universidad de Nicosia.

| Archivo | Filas | Descripción |
|---|---|---|
| `sales_train_validation.csv` | 30,490 | Series de tiempo: 1 fila por SKU × tienda, 1 columna por día |
| `calendar.csv` | 1,969 | Calendario con eventos y flags SNAP por estado |
| `sell_prices.csv` | 6,841,121 | Precios semanales por SKU × tienda |

> **Importante:** este proyecto **no busca resolver el reto de forecasting**. Se enfoca en explotar el dataset desde una perspectiva de supply chain y logística — patrones de demanda, impacto de eventos externos, comportamiento de precios y segmentación de productos.

---

## 🛠 Stack tecnológico

- **Python 3.x** — Pandas, NumPy, Matplotlib, Seaborn (ETL + EDA)
- **Jupyter / Google Colab** — Notebooks de análisis
- **Power BI Desktop** — Modelo dimensional y dashboard
- **DAX** — Medidas analíticas
- **Parquet** — Formato de intercambio entre etapas

---

## 📂 Estructura del repositorio

```
M5_supply_chain_analytics/
│
├── data/
│   ├── raw/                    # CSVs originales (intactos)
│   ├── processed/              # Parquets tipados post-ETL
│   └── mart/                   # Outputs analíticos para Power BI
│
├── src/
│   ├── extract.py              # Carga de CSVs sin modificación
│   ├── transform.py            # Tipado, NaN handling, optimización
│   ├── load.py                 # Persistencia en Parquet
│   └── pipeline.py             # Orquestador del ETL
│
├── notebooks/
│   ├── 01_eda_quality.ipynb
│   ├── 02_eda_temporal.ipynb
│   ├── 03_segmentacion_abc_xyz.ipynb
│   └── 04_pricing_analysis.ipynb
│
├── powerbi/
│   └── AnalyticsChallenge_Ventagium_dashboard.pbix
│
├── docs/
│   ├── data_dictionary.md
│   └── methodology.md
│
└── README.md
```

---

## 🚀 Reproducibilidad

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd M5_supply_chain_analytics

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Descargar dataset desde Kaggle a data/raw/
#    https://www.kaggle.com/competitions/m5-forecasting-accuracy/data

# 4. Ejecutar pipeline ETL completo
python src/pipeline.py

# 5. Abrir el dashboard
#    powerbi/AnalyticsChallenge_Ventagium_dashboard.pbix
```

---

## 🗺 Estructura del proyecto en 9 etapas

El proyecto se organiza en **3 fases** con **9 etapas** que avanzan progresivamente desde los datos crudos hasta insights accionables.

### 🔵 Fase 1 — Datos: construir la base sólida

#### 01. Planeación

Antes de tocar código, se define el alcance: **supply chain analytics, no forecasting**. Se elige Python para ETL (volumen incompatible con Power BI directo) y Power BI como capa de visualización. Se establece la separación de carpetas `raw/`, `processed/`, `mart/` y los entregables de cada etapa.

#### 02. ETL — Pipeline modular

El pipeline se divide en 3 módulos independientes orquestados por `pipeline.py`:

- **`extract.py`** — carga los 3 CSVs sin transformaciones. La carpeta `raw/` se considera inmutable.
- **`transform.py`** — aplica tres optimizaciones:
  - Columnas de identidad → tipo `category` (-60% memoria)
  - Columnas de unidades → `int16` (-75% memoria vs `int64`)
  - `NaN` en eventos → `"No Event"` explícito (evita errores silenciosos en `groupby`)
- **`load.py`** — persiste en formato Parquet, preservando tipos y reduciendo tiempos de lectura ~10x vs CSV.

#### 03. EDA — Quality checks y hallazgos

| Validación | Resultado |
|---|---|
| Duplicados | 0 en los 3 datasets |
| Nulos en ventas y precios | 0 |
| Integridad referencial | Verificada entre los 3 datasets |
| Cobertura | FOODS: 69% del volumen total |

**Hallazgo crítico:** el **78.4% de los SKUs tienen más del 50% de sus días en cero**. Solo el 1.2% tienen menos del 10% de días sin venta. **No es problema de calidad — es la naturaleza del retail de alta diversidad**, con implicaciones directas en la estrategia de inventario.

### 🟡 Fase 2 — Análisis: encontrar la historia

#### 04. Análisis de serie temporal

Caracterización de las 30,490 series de tiempo simultáneas:

- **Estacionalidad múltiple:** diaria, semanal y anual
- **SNAP:** lift de hasta **+29.9% en FOODS Wisconsin** los días con beneficio activo
- **Días nacionales (4 de julio, Thanksgiving):** lift **negativo** de -12% a -24% — la demanda se desplaza al día previo
- **No estacionariedad:** la mayoría de las series son intermitentes; ARIMA no aplica directamente

#### 05. Modelado de datos — Star Schema

Modelo dimensional estándar de Data Warehousing, optimizado para el motor VertiPaq de Power BI (compresión ~10-20% del tamaño original).

```
                 ┌─────────────┐
                 │ Dim_calendar│  fechas, eventos, SNAP
                 └──────┬──────┘
                        │
┌─────────────┐  ┌──────┴──────┐  ┌─────────────┐
│ Dim_product │──│ Fact_sales  │──│ Dim_store   │
│ cat → dept  │  │   58M rows  │  │ tienda → estado
└─────────────┘  └──────┬──────┘  └─────────────┘
                        │
                 ┌──────┴──────┐
                 │ Fact_prices │
                 └─────────────┘
```

#### 06. Insights de supply chain

| Insight | Implicación |
|---|---|
| **9,471 SKUs A-Z** (alto valor + alta variabilidad) | Mayor problema operacional: lo que más importa es lo más impredecible |
| **Solo 77 SKUs A-X** (alto valor + demanda estable) | Candidatos ideales para forecasting preciso |
| **Pareto 80-20** se cumple estrictamente | El 20% de SKUs genera el 80% del revenue → priorizar esfuerzo analítico |
| **SNAP +29.9% en WI** | Sincronizar reabastecimiento con calendario federal |
| **73% de SKUs cambian de precio** | Apertura a análisis de elasticidad — FOODS inelástica, HOBBIES elástica |

### 🔴 Fase 3 — Comunicación: hacer accionable el insight

#### 07. Dashboard — Propósito y medidas DAX

**Propósito:** Inventory Intelligence — herramienta de **detección de desbalance**, no reporte de ventas.

**Medidas DAX clave** (con su decisión metodológica):

```
Ingresos = SUMX(Fact_sales, Fact_sales[units_sold] * Fact_sales[sell_price])
```
> `sell_price` materializado como columna calculada para evitar `LOOKUPVALUE` en runtime que causaba `rsQueryMemoryLimitExceeded` (1,142 MB).

```
Baseline 28d = AVERAGEX(
    DATESINPERIOD(Dim_calendar[date], LASTDATE(Dim_calendar[date]), -28, DAY),
    [Unidades Vendidas]
)
```
> Ventana de 4 semanas exactas → elimina sesgo del día de la semana sin modelos externos.

```
Desviación vs Baseline % = DIVIDE(
    [Unidades Vendidas] - [Unidades Esperadas],
    [Unidades Esperadas]
)
```
> Formato `+0.0%;-0.0%` con signo siempre explícito.

```
Índice Desbalance = AVERAGEX(
    VALUES(Dim_store[store_id]),
    ABS([Desviación vs Baseline %])
) * 100
```
> **Mean Absolute Deviation (MAD)** — calcula dispersión por tienda primero y luego promedia, evitando que opuestos (CA -8%, WI +12%) se cancelen.

```
Desviación Promedio por Día = AVERAGEX(
    VALUES(Dim_calendar[date]),
    [Desviación vs Baseline %]
)
```
> Itera por fecha (donde el baseline tiene contexto) y luego agrupa por `weekday`.

#### 08. Dashboard — Diseño y storytelling

**Lienzo:** 1,366 × 768 px, fondo `#1A1A1A`, paleta semántica de 3 colores:

- 🔴 `#E05252` — desviación negativa / riesgo
- 🟡 `#F5C518` — desviación positiva / alerta
- ⚫ `#888888` — referencia / baseline

> Sistema de semáforo **sin verde** — en inventario ni el exceso es positivo.

**Layout: lectura en F**

```
┌─ Header con slicers ────────────────────────────────────┐
├─ Banner de alerta (titular en amber) ───────────────────┤
├─ 5 KPI cards: Unidades → Ingresos → vs Baseline ────────┤
│                  → Desbalance → En Riesgo               │
├─ Mapa por estado ────┬─ Serie temporal con baseline ────┤
├─ Top tiendas (h.bar) ┴─ Días de la semana (v.bar) ──────┤
└──────────────────────────────────────────────────────────┘
```

**Decisiones de diseño:**

- Cards ordenadas por progresión narrativa: magnitud → diagnóstico → severidad → acción
- Línea sólida (real) vs punteada (baseline) → leyenda no necesaria
- Shape Map sobre burbujas → la geografía codifica magnitud naturalmente
- Sparklines simulados con gráficos de líneas mini (sin ejes, transparentes, agrupados con la card)
- `Orden_dia = WEEKDAY(Dim_calendar[date], 2)` para ordenar L→D sin dependencia circular

#### 09. Roadmap de forecasting

> No todos los SKUs merecen el mismo modelo.

| Segmento | SKUs | Estrategia | Justificación |
|---|---|---|---|
| **A-X** | 77 | LightGBM con lag features (d-7, d-14, d-28), rolling means, calendar/price features | Ganador histórico del M5; captura no-linealidades |
| **B-Y** | ~10,000 | Prophet (Meta) | Estacionalidad múltiple + eventos como features explícitas |
| **C-Z** | ~20,000 | Croston's Method o stock mínimo fijo | CV > 2 con 90% ceros: forecastear es ruido disfrazado |

**Métrica de evaluación:** WRMSSE (Weighted Root Mean Squared Scaled Error) — métrica oficial del M5 que pondera el error por revenue del SKU. RMSE simple sería un error metodológico.

---

## 📋 Resumen de entregables por etapa

| # | Etapa | Entregable principal |
|---|---|---|
| 01 | Planeación | Estructura de carpetas, stack y enfoque analítico |
| 02 | ETL | `pipeline.py` modular + 3 Parquet files |
| 03 | EDA | Quality checks, estadística descriptiva, distribuciones |
| 04 | Serie Temporal | Caracterización de estacionalidad, eventos y patrón de ceros |
| 05 | Modelado de Datos | Star Schema con FACT_SALES + 4 dimensiones |
| 06 | Insights Supply Chain | ABC-XYZ, impacto SNAP, elasticidad de precios |
| 07 | Dashboard — Métricas | 18 medidas DAX con justificación técnica |
| 08 | Dashboard — Diseño | `.pbix` con dashboard ejecutivo |
| 09 | Roadmap | Estrategia diferenciada de forecasting por segmento |

---

## 📚 Referencias

- Makridakis, S., Spiliotis, E., & Assimakopoulos, V. (2022). *The M5 accuracy competition: Results, findings, and conclusions.* International Journal of Forecasting.
- [M5 Forecasting - Accuracy (Kaggle)](https://www.kaggle.com/competitions/m5-forecasting-accuracy)
- [Vertipaq Engine - SQLBI](https://www.sqlbi.com/articles/the-vertipaq-engine-in-dax/)
- Croston, J. D. (1972). *Forecasting and stock control for intermittent demands.* Operational Research Quarterly.

---

## 📝 Licencia

Este proyecto se distribuye con fines educativos y de portafolio. El dataset original es propiedad de Walmart y fue compartido bajo los términos de la competencia M5 en Kaggle.

---

*Proyecto desarrollado como parte del Analytics Challenge — Ventagium.*
