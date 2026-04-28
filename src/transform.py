import pandas as pd
import numpy as np


def formato_sales(df_sales_validation):
    #Castear columnas de id a category y dias a int16 para reducir memoria

    columnas_id   = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]
    columnas_dias = [col for col in df_sales_validation.columns if col.startswith("d_")]

    for col in columnas_id:
        df_sales_validation[col] = df_sales_validation[col].astype("category")

    df_sales_validation[columnas_dias] = df_sales_validation[columnas_dias].astype(np.int16)

    print("formato_sales listo")
    return df_sales_validation


def formato_calendar(df_calendar):
    # Cambiar date a datetime, rellenar nan eventos, convertir strings a category, eliminar columnas innecesarias

    df_calendar["date"] = pd.to_datetime(df_calendar["date"], format="%Y-%m-%d", errors="coerce")

    columnas_eventos = ["event_name_1", "event_type_1", "event_name_2", "event_type_2"]
    for col in columnas_eventos:
        df_calendar[col] = df_calendar[col].fillna("No event").astype("category")

    columnas_string = ["weekday", "d"]
    for col in columnas_string:
        df_calendar[col] = df_calendar[col].astype("category")

    df_calendar = df_calendar.drop(columns=["wday", "month", "year"])

    print("formato_calendar listo")
    return df_calendar


def formato_prices(df_sell):
    #Cambiar datatype a category
    columnas_string = ["store_id", "item_id"]
    for col in columnas_string:
        df_sell[col] = df_sell[col].astype("category")

    print("formato_prices listo")
    return df_sell
