# Manda a llamar las funciones para ejecutar el pipeline

from extract   import cargar_archivos
from transform import formato_sales, formato_calendar, formato_prices
from load      import guardar_datasets

def run():

    print("Extract (E)")
    df_sales_validation, df_calendar, df_sell = cargar_archivos()

    print("Transform (T)")
    df_sales_validation = formato_sales(df_sales_validation)
    df_calendar         = formato_calendar(df_calendar)
    df_sell             = formato_prices(df_sell)


    print("Load (L)")
    guardar_datasets(df_sales_validation, df_calendar, df_sell)
    print("Pipeline terminado")


if __name__ == "__main__":
    run()
