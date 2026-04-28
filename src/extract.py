import pandas as pd

ruta = r"C:\Users\david\Documents\M5 challenge\data\raw" # usar la ruta donde tengas los archivos originales

def cargar_archivos():

    df_sales_validation = pd.read_csv(ruta+"/sales_train_validation.csv")
    df_calendar= pd.read_csv(ruta+"/calendar.csv")
    df_sell= pd.read_csv(ruta+"/sell_prices.csv")

    print("Se han cargado los archivos ")

    return df_sales_validation, df_calendar, df_sell
