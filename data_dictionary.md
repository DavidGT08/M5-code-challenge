# Data Dictionary — M5 Supply Chain Analytics

> Documentación de todos los campos, tablas y medidas del proyecto, organizados en tres capas:
> **Capa 1** — Archivos fuente (CSV raw) · **Capa 2** — Modelo dimensional Power BI (Star Schema) · **Capa 3** — Medidas DAX

---

## Índice

- [Capa 1 — Archivos fuente](#capa-1--archivos-fuente)
  - [sales_train_validation.csv](#sales_train_validationcsv)
  - [calendar.csv](#calendarcsv)
  - [sell_prices.csv](#sell_pricescsv)
- [Capa 2 — Modelo dimensional](#capa-2--modelo-dimensional-star-schema)
  - [Fact_sales](#fact_sales)
  - [Fact_prices](#fact_prices)
  - [Dim_calendar](#dim_calendar)
  - [Dim_product](#dim_product)
  - [Dim_store](#dim_store)
  - [Dim_week](#dim_week)
  - [Columnas calculadas](#columnas-calculadas)
- [Capa 3 — Medidas DAX](#capa-3--medidas-dax)
  - [Carpeta Base](#carpeta-base)
  - [Carpeta Baseline & Desviación](#carpeta-baseline--desviación)
  - [Carpeta Alertas](#carpeta-alertas)
  - [Carpeta Elasticidad](#carpeta-elasticidad)
  - [Carpeta Factores Externos](#carpeta-factores-externos)
- [Glosario de términos de negocio](#glosario-de-términos-de-negocio)
- [Relaciones del modelo](#relaciones-del-modelo)

---

## Capa 1 — Archivos fuente

> Archivos CSV originales almacenados en `data/raw/`. **Nunca se modifican directamente.**
> El ETL los consume y produce los Parquet equivalentes en `data/processed/`.

---

### `sales_train_validation.csv`

**Descripción:** Serie de tiempo de ventas diarias por SKU y tienda. Cada fila es un producto en una tienda específica; cada columna `d_N` representa las unidades vendidas en el día N del período.

**Dimensiones:** 30,490 filas × 1,919 columnas (5 de identidad + 1,914 días)

**Período:** d_1 = 2011-01-29 → d_1,913 = 2016-05-22

| Campo | Tipo raw | Tipo post-ETL | Valores únicos | Descripción |
|---|---|---|---|---|
| `id` | string | category | 30,490 | Identificador único compuesto: `{item_id}_{store_id}_validation` |
| `item_id` | string | category | 3,049 | Código del producto. Formato: `{CAT}_{DEPT}_{N}` ej. `FOODS_3_001` |
| `dept_id` | string | category | 7 | Departamento del producto. Subconjunto de `cat_id` |
| `cat_id` | string | category | 3 | Categoría: `FOODS`, `HOBBIES`, `HOUSEHOLD` |
| `store_id` | string | category | 10 | Tienda. Formato: `{STATE}_{N}` ej. `CA_1`, `TX_2` |
| `state_id` | string | category | 3 | Estado: `CA`, `TX`, `WI` |
| `d_1` … `d_1913` | int64 | int16 | 0–∞ | Unidades vendidas ese día. **0 es un valor válido** (no nulo). ~78.4% de los valores son 0 |

**Notas:**
- La granularidad es SKU × tienda × día
- Los primeros días de cada SKU pueden tener todos ceros si el producto aún no había sido introducido en la tienda
- El formato wide (días como columnas) se transforma a long (una fila por día) durante el ETL para facilitar el análisis temporal

---

### `calendar.csv`

**Descripción:** Calendario con información contextual de cada día: eventos especiales, semana Walmart, y elegibilidad SNAP por estado.

**Dimensiones:** 1,969 filas × 14 columnas

**Período:** 2011-01-29 → 2016-06-19

| Campo | Tipo raw | Tipo post-ETL | Valores únicos | Descripción |
|---|---|---|---|---|
| `date` | string | datetime64 | 1,969 | Fecha en formato YYYY-MM-DD |
| `wm_yr_wk` | int64 | int32 | 282 | Código de semana Walmart. Formato: `{YY}{WW}` — sirve como llave de unión con `sell_prices.csv` |
| `weekday` | string | category | 7 | Nombre del día en inglés: `Monday`…`Sunday` |
| `wday` | int64 | int8 | 7 | Número del día de la semana. **Sábado=1, Domingo=2, Lunes=3…Viernes=7** (convención Walmart, no ISO) |
| `month` | int64 | int8 | 12 | Mes (1–12) |
| `year` | int64 | int16 | 6 | Año (2011–2016) |
| `d` | string | category | 1,969 | Identificador de día. Formato: `d_{N}` — sirve como llave de unión con `sales_train_validation.csv` |
| `event_name_1` | string | category | 30 + NaN | Nombre del evento principal del día. NaN si no hay evento → transformado a `"No Event"` en ETL |
| `event_type_1` | string | category | 5 + NaN | Tipo del evento principal: `Sporting`, `Cultural`, `National`, `Religious`, `No Event` |
| `event_name_2` | string | category | 5 + NaN | Nombre del evento secundario (días con dos eventos simultáneos) |
| `event_type_2` | string | category | 5 + NaN | Tipo del evento secundario |
| `snap_CA` | int64 | int8 | 2 | Flag SNAP para California: `1` = día elegible para compras SNAP, `0` = no elegible |
| `snap_TX` | int64 | int8 | 2 | Flag SNAP para Texas: `1` = día elegible, `0` = no elegible |
| `snap_WI` | int64 | int8 | 2 | Flag SNAP para Wisconsin: `1` = día elegible, `0` = no elegible |

**Notas sobre SNAP:** El Supplemental Nutrition Assistance Program (SNAP) es el programa federal de asistencia alimentaria de EE.UU. Los días SNAP no son uniformes entre estados — cada estado tiene su propio calendario de elegibilidad basado en el número de la tarjeta del beneficiario. Esto genera picos de demanda en FOODS no correlacionados entre estados.

**Eventos registrados (muestra):** `SuperBowl`, `ValentinesDay`, `PresidentsDay`, `LentStart`, `Easter`, `Cinco De Mayo`, `IndependenceDay`, `LaborDay`, `Thanksgiving`, `Christmas`, `NewYear`

---

### `sell_prices.csv`

**Descripción:** Precio de venta semanal por combinación de producto y tienda. La granularidad es semanal (no diaria): un precio es válido para todos los días de la semana Walmart correspondiente.

**Dimensiones:** 6,841,121 filas × 4 columnas

| Campo | Tipo raw | Tipo post-ETL | Valores únicos | Descripción |
|---|---|---|---|---|
| `store_id` | string | category | 10 | Identificador de tienda. Llave foránea a `sales_train_validation.store_id` |
| `item_id` | string | category | 3,049 | Identificador de producto. Llave foránea a `sales_train_validation.item_id` |
| `wm_yr_wk` | int64 | int32 | 282 | Semana Walmart. Llave de unión con `calendar.wm_yr_wk` |
| `sell_price` | float64 | float32 | — | Precio en USD. Rango: $0.01 – $107.32. Percentil 75 = $8.99, IQR cutoff = $11.29 |

**Notas:**
- Si un combo `item_id × store_id` no aparece en una semana, significa que el producto **no estaba disponible** en esa tienda esa semana
- El 73% de los combos `item_id × store_id` tuvieron al menos un cambio de precio en el período de 5 años
- Los precios son constantes dentro de la semana; los cambios siempre ocurren en límites de semana Walmart

---

## Capa 2 — Modelo dimensional (Star Schema)

> Tablas del modelo en Power BI, derivadas de los archivos fuente después del ETL.
> El motor VertiPaq comprime las columnas categóricas a **10–20% del tamaño original**.

### Diagrama del modelo

```
                     ┌─────────────────┐
                     │   Dim_calendar  │
                     │  PK: date       │
                     └────────┬────────┘
                              │ *:1
              ┌───────────────┼───────────────┐
              │               │               │
    ┌─────────┴──────┐ ┌──────┴───────┐ ┌───┴───────────┐
    │  Dim_product   │ │  Fact_sales  │ │   Dim_store   │
    │  PK: item_id   │ │  FK: item_id │ │  PK: store_id │
    └────────────────┘ │  FK: store_id│ └───────────────┘
                       │  FK: date    │
                       │  FK: wm_yr_wk│
                       └──────┬───────┘
                              │ *:1
                     ┌────────┴────────┐
                     │   Fact_prices   │
                     │  FK: item_id    │
                     │  FK: store_id   │
                     │  FK: wm_yr_wk   │
                     └─────────────────┘
                              │ *:1
                     ┌────────┴────────┐
                     │    Dim_week     │
                     │  PK: wm_yr_wk   │
                     └─────────────────┘
```

---

### `Fact_sales`

**Descripción:** Tabla de hechos central. Una fila por combinación de SKU × tienda × día. Es el resultado de transformar `sales_train_validation.csv` de formato wide a long durante el ETL.

**Cardinalidad:** ~58 millones de filas (30,490 SKUs × 1,913 días, con gaps por productos no disponibles)

| Campo | Tipo | Rol | Descripción |
|---|---|---|---|
| `item_id` | category | FK → Dim_product | Identificador del producto |
| `store_id` | category | FK → Dim_store | Identificador de la tienda |
| `date` | datetime | FK → Dim_calendar | Fecha de la venta |
| `wm_yr_wk` | int32 | FK → Fact_prices / Dim_week | Semana Walmart del día. Calculado a partir de `date` o mapeado desde calendar |
| `units_sold` | int16 | Medida | Unidades vendidas. 0 es un valor válido. Nunca nulo |
| `sell_price` | float32 | Columna calculada | **Ver sección Columnas Calculadas.** Precio materializado desde `Fact_prices` |

---

### `Fact_prices`

**Descripción:** Tabla de precios semanales por SKU × tienda. Técnicamente es una tabla de hechos (tiene medidas numéricas) pero actúa como dimensión de precio al unirse con `Fact_sales`.

**Cardinalidad:** 6,841,121 filas

| Campo | Tipo | Rol | Descripción |
|---|---|---|---|
| `store_id` | category | FK → Dim_store | Identificador de la tienda |
| `item_id` | category | FK → Dim_product | Identificador del producto |
| `wm_yr_wk` | int32 | FK → Dim_week | Semana Walmart |
| `sell_price` | float32 | Medida | Precio de venta en USD para esa semana. Es el precio original sin transformar |

---

### `Dim_calendar`

**Descripción:** Dimensión temporal. Contiene un registro por cada día del período más el contexto de eventos y SNAP. Es la tabla de fechas marcada en Power BI para habilitar inteligencia de tiempo en DAX.

**Cardinalidad:** 1,969 filas

| Campo | Tipo | Rol | Descripción |
|---|---|---|---|
| `date` | datetime | PK | Fecha. Marcada como tabla de fechas en Power BI |
| `wm_yr_wk` | int32 | FK → Dim_week | Semana Walmart — permite unir con precios |
| `weekday` | category | Atributo | Nombre del día en inglés. Ordenado por `Orden_dia` (columna calculada) |
| `wday` | int8 | Atributo | Número del día según convención Walmart (Sábado=1). **No usar para ordenar días** — usar `Orden_dia` |
| `month` | int8 | Atributo | Número de mes (1–12) |
| `year` | int16 | Atributo | Año (2011–2016) |
| `d` | category | Atributo | Código de día tipo `d_1`…`d_1969`. Uso interno para trazabilidad |
| `event_name_1` | category | Atributo / Filtro | Nombre del evento principal. `"No Event"` si no hay evento |
| `event_type_1` | category | Atributo / Filtro | Tipo del evento principal: `Sporting`, `Cultural`, `National`, `Religious`, `No Event` |
| `event_name_2` | category | Atributo | Nombre del evento secundario (días con dos eventos) |
| `event_type_2` | category | Atributo | Tipo del evento secundario |
| `snap_CA` | int8 | Atributo / Filtro | `1` = día SNAP activo en California |
| `snap_TX` | int8 | Atributo / Filtro | `1` = día SNAP activo en Texas |
| `snap_WI` | int8 | Atributo / Filtro | `1` = día SNAP activo en Wisconsin |
| `Orden_dia` | int8 | **Columna calculada** | Ver sección Columnas Calculadas |

---

### `Dim_product`

**Descripción:** Dimensión de producto. Captura la jerarquía completa: categoría → departamento → item.

**Cardinalidad:** 3,049 filas

| Campo | Tipo | Rol | Descripción |
|---|---|---|---|
| `item_id` | category | PK | Identificador único del producto. Formato: `{CAT}_{DEPT}_{N}` |
| `dept_id` | category | Atributo | Departamento. 7 valores: `FOODS_1`, `FOODS_2`, `FOODS_3`, `HOBBIES_1`, `HOBBIES_2`, `HOUSEHOLD_1`, `HOUSEHOLD_2` |
| `cat_id` | category | Atributo | Categoría. 3 valores: `FOODS` (69% del volumen), `HOBBIES`, `HOUSEHOLD` |

**Jerarquía de análisis:**
```
cat_id (3) → dept_id (7) → item_id (3,049)
```
Cada nivel corresponde a un tomador de decisión diferente en supply chain: el **category manager** ve `cat_id`, el **planner** de reposición ve `item_id`.

---

### `Dim_store`

**Descripción:** Dimensión de tienda y geografía.

**Cardinalidad:** 10 filas

| Campo | Tipo | Rol | Descripción |
|---|---|---|---|
| `store_id` | category | PK | Identificador de tienda. Formato: `{STATE}_{N}` — 10 valores: `CA_1`–`CA_4`, `TX_1`–`TX_3`, `WI_1`–`WI_3` |
| `state_id` | category | Atributo | Estado. 3 valores: `CA`, `TX`, `WI` — usado para el Shape Map del dashboard |

**Notas:** CA_3 es la tienda de mayor volumen (2.7× más que CA_4, la de menor volumen en el mismo estado).

---

### `Dim_week`

**Descripción:** Dimensión de semana Walmart. Permite unir `Fact_sales` con `Fact_prices` a través de la semana, y provee atributos semanales para análisis de precios.

**Cardinalidad:** 282 filas

| Campo | Tipo | Rol | Descripción |
|---|---|---|---|
| `wm_yr_wk` | int32 | PK | Código de semana Walmart. Formato: los primeros 2 dígitos son el año, los últimos 2 la semana del año |

---

### Columnas calculadas

> Columnas que no existen en los archivos fuente sino que se calculan en el modelo Power BI.
> Se evalúan **una vez al refrescar** el modelo, no en cada query.

#### `Fact_sales[sell_price]`

| Atributo | Detalle |
|---|---|
| **Tabla** | `Fact_sales` |
| **Tipo** | float32 |
| **Propósito** | Materializar el precio de venta en la tabla de hechos para evitar `LOOKUPVALUE` en runtime |
| **DAX** | `LOOKUPVALUE(Fact_prices[sell_price], Fact_prices[item_id], Fact_sales[item_id], Fact_prices[store_id], Fact_sales[store_id], Fact_prices[wm_yr_wk], RELATED(Dim_calendar[wm_yr_wk]))` |
| **Decisión técnica** | La medida `Ingresos` originalmente usaba `SUMX` con `LOOKUPVALUE` anidado. Con 58M filas, ejecutar el lookup en cada query consumía 1,142 MB (límite: 1,024 MB), generando `rsQueryMemoryLimitExceeded`. Al materializar el precio en refresh, el motor comprime la columna una vez y todas las queries posteriores la leen de memoria comprimida. |
| **Impacto** | Reduce el consumo de memoria de la medida `Ingresos` de ~1,142 MB a <50 MB por query |

#### `Dim_calendar[Orden_dia]`

| Atributo | Detalle |
|---|---|
| **Tabla** | `Dim_calendar` |
| **Tipo** | int8 (oculto) |
| **Propósito** | Proveer el orden correcto (Lunes=1…Domingo=7) para la columna `weekday` sin dependencia circular |
| **DAX** | `WEEKDAY(Dim_calendar[date], 2)` |
| **Parámetro 2** | El segundo argumento de `WEEKDAY` define el inicio de semana: `2` = Lunes como día 1, conforme a la convención ISO 8601 |
| **Decisión técnica** | La versión inicial usaba `SWITCH(Dim_calendar[weekday], "Monday", 1, ...)`, lo que creó una dependencia circular: `weekday` ordenado por `Orden_dia`, pero `Orden_dia` calculado desde `weekday`. Al calcular el orden directamente desde `date` (que no depende de `weekday`), el ciclo se rompe. |
| **Uso** | Asignado como "Ordenar por columna" de `Dim_calendar[weekday]` en Power BI Desktop → Herramientas de columna |

---

## Capa 3 — Medidas DAX

> Todas las medidas están en la tabla `Fact_sales` y organizadas en carpetas de display.
> Las medidas se evalúan en **cada query**, respondiendo al contexto de filtros activo.

---

### Carpeta Base

Medidas fundamentales de agregación directa. Sin lógica de baseline ni condicional.

---

#### `Unidades Vendidas`

| Atributo | Detalle |
|---|---|
| **Fórmula** | `SUM(Fact_sales[units_sold])` |
| **Formato** | `#,##0` |
| **Descripción** | Total de unidades vendidas en el contexto actual. Es la medida más básica del modelo: suma directa de `units_sold`. Cualquier filtro de fecha, tienda, categoría o evento la afecta directamente. |
| **Uso en dashboard** | KPI Card 1 — headline del estado del período |

---

#### `Ingresos`

| Atributo | Detalle |
|---|---|
| **Fórmula** | `SUMX(Fact_sales, Fact_sales[units_sold] * Fact_sales[sell_price])` |
| **Formato** | `$#,##0` |
| **Descripción** | Revenue total calculado como suma de (unidades × precio) fila por fila. Usa la columna calculada `sell_price` materializada — no `LOOKUPVALUE` en runtime. |
| **Uso en dashboard** | KPI Card 2 |

---

#### `Precio Promedio`

| Atributo | Detalle |
|---|---|
| **Fórmula** | `AVERAGE(Fact_prices[sell_price])` |
| **Formato** | `$#,##0.00` |
| **Descripción** | Precio promedio en el contexto de filtros. Opera sobre `Fact_prices` directamente, no sobre la columna calculada. Útil para análisis de elasticidad. |

---

### Carpeta Baseline & Desviación

Medidas que implementan la lógica de ventana móvil y cuantifican el desbalance.

---

#### `Baseline 28d`

| Atributo | Detalle |
|---|---|
| **Fórmula** | `AVERAGEX(DATESINPERIOD(Dim_calendar[date], LASTDATE(Dim_calendar[date]), -28, DAY), [Unidades Vendidas])` |
| **Formato** | `#,##0.0` |
| **Descripción** | Promedio de unidades vendidas en los 28 días anteriores a la última fecha del contexto actual. Representa la demanda "esperada" basada en comportamiento reciente. |
| **Por qué 28 días** | 28 días = exactamente 4 semanas completas. Cualquier ventana de N×7 días incluye el mismo número de cada día de la semana (4 lunes, 4 martes, etc.), eliminando el sesgo de estacionalidad semanal del propio baseline. Una ventana de 30 días podría incluir 4 lunes y 5 martes según el día actual, sesgando el promedio. |
| **Dependencia** | Requiere que `Dim_calendar` esté marcada como tabla de fechas en Power BI. Sin esto, `DATESINPERIOD` no funciona correctamente. |

---

#### `Unidades Esperadas`

| Atributo | Detalle |
|---|---|
| **Fórmula** | `VAR _n_dias = COUNTROWS(VALUES(Dim_calendar[date])) RETURN [Baseline 28d] * _n_dias` |
| **Formato** | `#,##0` |
| **Descripción** | Proyección de unidades esperadas para el período actual, escalando el baseline diario por el número de días en contexto. Permite comparar cualquier período (una semana, un mes, un trimestre) con su expectativa correspondiente. |
| **Por qué COUNTROWS(VALUES(...))** | `COUNTROWS(VALUES(Dim_calendar[date]))` cuenta los días únicos visibles en el contexto actual del filtro, haciéndola agnóstica al nivel de agregación temporal. Si el filtro es un mes (31 días), multiplica por 31. Si es una semana, por 7. Sin este escalado, la desviación sería incorrecta al cambiar granularidad. |

---

#### `Desviación vs Baseline %`

| Atributo | Detalle |
|---|---|
| **Fórmula** | `DIVIDE([Unidades Vendidas] - [Unidades Esperadas], [Unidades Esperadas])` |
| **Formato** | `+0.0%;-0.0%;0.0%` |
| **Descripción** | Diferencia relativa entre ventas reales y esperadas. Positivo = por encima del baseline (sobreinventario potencial). Negativo = por debajo (quiebre potencial). |
| **Por qué DIVIDE y no `/`** | `DIVIDE` maneja de forma segura la división por cero (retorna 0 o BLANK en lugar de error), que puede ocurrir si no hay baseline disponible para el período. |
| **Por qué el formato con `+`** | El signo explícito en el formato (`+0.0%`) es una decisión de comunicación: en un dashboard ejecutivo, la dirección de la desviación es la primera información que debe saltar a la vista. Sin el `+`, un valor positivo parecería neutral. |
| **Color condicional** | `< 0` → `#E05252` (rojo) · `>= 0` → `#F5C518` (dorado). No hay verde porque en inventario el exceso también es un problema. |

---

#### `Índice Desbalance`

| Atributo | Detalle |
|---|---|
| **Fórmula** | `AVERAGEX(VALUES(Dim_store[store_id]), ABS([Desviación vs Baseline %])) * 100` |
| **Formato** | `0.0` |
| **Descripción** | **Mean Absolute Deviation (MAD)** de la desviación vs baseline, calculada primero por tienda y luego promediada. Cuantifica la magnitud del desbalance de inventario entre tiendas independientemente de la dirección. |
| **Por qué MAD y no ABS del total** | Si CA=-8% y WI=+12% y TX=-1%, el promedio total es +1%, y `ABS(1%) × 100 = 1`. Pero el MAD es `promedio(8, 12, 1) = 7`. La versión `ABS(total)` permite que desviaciones opuestas se cancelen, ocultando un desbalance real. La MAD mide la **dispersión de las magnitudes**, no la magnitud del promedio. Estos son conceptos distintos: el primero describe el sistema, el segundo oculta su heterogeneidad. |
| **Error original** | La primera versión era `ABS([Desviación vs Baseline %]) * 100` — producía el mismo valor que `Desviación vs Baseline %` formateado en escala 100. El error fue aplicar `ABS` al total ya agregado en lugar de por tienda. |
| **Interpretación** | Valores >15 activan alerta en el dashboard. Umbral definido por análisis del percentil 85 del histórico del período. |

---

#### `Desviación Promedio por Día`

| Atributo | Detalle |
|---|---|
| **Fórmula** | `AVERAGEX(VALUES(Dim_calendar[date]), [Desviación vs Baseline %])` |
| **Formato** | `+0.0%;-0.0%;0.0%` |
| **Descripción** | Desviación promedio agrupada por día de semana. Diseñada específicamente para el gráfico de barras de días de semana (eje X = `weekday`). |
| **Por qué existe esta medida y no se usa la original** | `Desviación vs Baseline %` requiere un rango de fechas continuo para que `DATESINPERIOD` pueda construir la ventana de 28 días. Cuando el eje X es solo `weekday` (sin fechas en contexto), el baseline no tiene fechas para calcular y retorna BLANK → gráfico vacío. `AVERAGEX(VALUES(date), ...)` itera fecha por fecha (donde el baseline sí funciona), y Power BI agrupa el resultado por `weekday` automáticamente al estar en el eje X. |

---

### Carpeta Alertas

Medidas que clasifican estados críticos y cuentan tiendas en riesgo.

---

#### `# Tiendas en Riesgo`

| Atributo | Detalle |
|---|---|
| **Fórmula** | `COUNTROWS(FILTER(VALUES(Dim_store[store_id]), [Desviación vs Baseline %] < -0.05))` |
| **Formato** | `0` |
| **Descripción** | Número de tiendas con desviación vs baseline menor a -5% en el contexto actual. Umbral de -5% definido como señal de quiebre potencial basado en análisis de distribución histórica de desviaciones. |
| **Uso en dashboard** | KPI Card 5 — mostrado como `N/10` para dar referencia del total de tiendas |

---

### Carpeta Elasticidad

Medidas para análisis de sensibilidad de la demanda al precio.

---

#### `Variación de Precio %`

| Atributo | Detalle |
|---|---|
| **Fórmula** | `DIVIDE([Precio Promedio] - CALCULATE([Precio Promedio], DATEADD(Dim_calendar[date], -28, DAY)), CALCULATE([Precio Promedio], DATEADD(Dim_calendar[date], -28, DAY)))` |
| **Formato** | `+0.0%;-0.0%` |
| **Descripción** | Variación porcentual del precio promedio respecto a los 28 días anteriores. Complementa `Desviación vs Baseline %` para análisis de causalidad: si precio baja y ventas suben, es respuesta elástica. |

---

### Carpeta Factores Externos

Medidas que cuantifican el impacto de variables externas (SNAP, eventos).

---

#### `Lift SNAP`

| Atributo | Detalle |
|---|---|
| **Fórmula** | `DIVIDE(CALCULATE([Unidades Vendidas], FILTER(Dim_calendar, Dim_calendar[snap_CA]=1 \|\| Dim_calendar[snap_TX]=1 \|\| Dim_calendar[snap_WI]=1)) - CALCULATE([Unidades Vendidas], FILTER(Dim_calendar, Dim_calendar[snap_CA]=0 && Dim_calendar[snap_TX]=0 && Dim_calendar[snap_WI]=0)), CALCULATE([Unidades Vendidas], FILTER(Dim_calendar, Dim_calendar[snap_CA]=0 && Dim_calendar[snap_TX]=0 && Dim_calendar[snap_WI]=0)))` |
| **Formato** | `+0.0%;-0.0%` |
| **Descripción** | Diferencia relativa entre ventas en días SNAP vs días no-SNAP. Cuantifica el impacto del programa federal sobre la demanda. El lift máximo observado es +29.9% en FOODS Wisconsin. |

---

## Glosario de términos de negocio

| Término | Definición en el contexto del proyecto |
|---|---|
| **SKU** | Stock Keeping Unit. La unidad más granular de producto — en este dataset es `item_id`. Un mismo artículo en dos tiendas distintas son dos SKUs distintos a efectos de inventario |
| **Demanda intermitente** | Serie de tiempo donde la mayoría de los períodos tienen valor cero, con ventas esporádicas. El 78.4% de los SKUs del dataset tienen este comportamiento |
| **SNAP** | Supplemental Nutrition Assistance Program. Programa federal de EE.UU. de asistencia alimentaria. Los "días SNAP" son los días en que los beneficiarios pueden usar sus tarjetas en tiendas autorizadas. Genera picos de demanda en la categoría FOODS |
| **Semana Walmart (`wm_yr_wk`)** | Sistema de semanas fiscal de Walmart. No coincide con semanas calendario ISO. Sirve como clave de unión entre `calendar.csv` y `sell_prices.csv` |
| **Baseline** | Referencia de demanda esperada calculada como promedio móvil de 28 días. Cualquier desviación significativa de esta referencia indica un comportamiento anómalo (evento, quiebre, sobreinventario) |
| **Lift** | Incremento porcentual en ventas atribuible a un factor externo (evento, SNAP, promoción) respecto a un período de referencia sin ese factor |
| **Desbalance de inventario** | Situación donde algunas tiendas tienen exceso y otras tienen déficit del mismo producto simultáneamente. El `Índice Desbalance` (MAD) lo cuantifica |
| **Quiebre de stock (stockout)** | Situación donde la demanda supera el inventario disponible, resultando en ventas perdidas. Se detecta por desviación vs baseline fuertemente negativa sin evento explicativo |
| **Sobreinventario** | Exceso de stock respecto a la demanda real. Capital inmovilizado, riesgo de obsolescencia o vencimiento. Se detecta por desviación vs baseline positiva persistente |
| **MAD** | Mean Absolute Deviation. Promedio de los valores absolutos de las desviaciones individuales. Mide dispersión sin permitir que valores opuestos se cancelen |
| **CV** | Coefficient of Variation. Desviación estándar dividida entre la media. Mide variabilidad relativa. CV > 2 indica demanda altamente errática, ineficientemente modelable |
| **ABC** | Segmentación de items por contribución acumulada a revenue: A = top 80%, B = siguiente 15%, C = último 5% |
| **XYZ** | Segmentación de items por variabilidad de demanda: X = CV bajo (estable), Y = CV medio, Z = CV alto (errático) |
| **WRMSSE** | Weighted Root Mean Squared Scaled Error. Métrica oficial del M5. Pondera el error por el revenue histórico del SKU, reflejando el costo real de errar en items de alto valor |

---

## Relaciones del modelo

| Desde | Campo | Hacia | Campo | Cardinalidad | Dirección de filtro |
|---|---|---|---|---|---|
| `Fact_sales` | `item_id` | `Dim_product` | `item_id` | N:1 | → (Dim filtra Fact) |
| `Fact_sales` | `store_id` | `Dim_store` | `store_id` | N:1 | → (Dim filtra Fact) |
| `Fact_sales` | `date` | `Dim_calendar` | `date` | N:1 | → (Dim filtra Fact) |
| `Fact_sales` | `wm_yr_wk` | `Dim_week` | `wm_yr_wk` | N:1 | → (Dim filtra Fact) |
| `Fact_prices` | `wm_yr_wk` | `Dim_week` | `wm_yr_wk` | N:1 | → (Dim filtra Fact) |
| `Fact_prices` | `item_id` | `Dim_product` | `item_id` | N:1 | → (Dim filtra Fact) |
| `Fact_prices` | `store_id` | `Dim_store` | `store_id` | N:1 | → (Dim filtra Fact) |

**Nota sobre la dirección de filtro:** todas las relaciones filtran de dimensión a hecho (nunca bidireccional). Esto es el estándar de Star Schema y es crítico para el comportamiento correcto de las medidas DAX: si una dimensión filtrara hacia otra dimensión, podrían generarse filtros implícitos inesperados.

---

*Última actualización: Abril 2026 — Proyecto Analytics Challenge Ventagium*
