import pandas as pd

ruta = r"C:\Users\david\Documents\M5 challenge\data\processed" # ajustar la ruta


def guardar_datasets(df_sales_validation, df_calendar, df_sell):

    df_sales_validation.to_parquet(ruta +"/sales_validation.parquet",index=False)
    df_calendar.to_parquet( ruta + "/calendar.parquet",index=False)
    df_sell.to_parquet(ruta + "/sell_prices.parquet",index=False)

    print(f"Datasets guardados en: {ruta}")

def cargar_datasets():
    #Cargamos los datasets para usarse en el EDA


    df_sales_validation= pd.read_parquet(ruta+ "/sales_validation.parquet")
    df_calendar= pd.read_parquet(ruta+ "/calendar.parquet")
    df_sell= pd.read_parquet(ruta+ "/sell_prices.parquet")

    print("Los Datasets han sido cargados")


    return df_sales_validation, df_calendar, df_sell
