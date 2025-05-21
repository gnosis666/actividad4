# archivo: app_muertes_mensual.py

import pandas as pd
import numpy as np
import plotly.express as px
from dash import Dash, dcc, html, dash_table

#CARGA TODOS LOS ARCHIVOS EXCEL Y LOS ACOMODA EN DIFERENTES DF QUE SERAN USADOS POSTERIORMENTE 
df = pd.read_excel("datos_mortalidad_colombia_2019.xlsx",dtype={"COD_DEPARTAMENTO": str})
df_main = pd.read_excel("datos_mortalidad_colombia_2019.xlsx",dtype={"COD_DEPARTAMENTO": str, "COD_MUNICIPIO": str})
df_cities = pd.read_excel("codigo_ciudades.xlsx",usecols=["COD_DEPARTAMENTO", "DEPARTAMENTO", "COD_MUNICIPIO", "MUNICIPIO"], dtype={"COD_DEPARTAMENTO": str, "COD_MUNICIPIO": str  })
df_codigomuertes = pd.read_excel("codigo_muertes.xlsx")

df_merged = df_main.merge(df_cities, on="COD_DEPARTAMENTO", how="left")
df_merged["COD_DEPARTAMENTO"] = df_merged["DEPARTAMENTO"]
df_merged = df_merged.drop(columns=["DEPARTAMENTO"])


df_merged_municipio = df_main.merge(df_cities, on="COD_MUNICIPIO", how="left")
df_merged_municipio["COD_MUNICIPIO"] = df_merged_municipio["MUNICIPIO"]
df_merged_municipio = df_merged_municipio.drop(columns=["MUNICIPIO"])

df_merged_muertes = df_main.merge(df_codigomuertes, on="COD_MUERTE", how="left")

#### PRIMERA GRAFICA 
df['MES'] = df['MES'].astype(int)

# 1) Agrupar por mes y contar muertes (cada fila = una persona fallecida)
df_mes = (
    df.groupby('MES')
      .size()                   # o .count() sobre cualquier otra columna
      .reset_index(name='Muertes')
      .sort_values('MES')
)

# 2) Crear la figura de línea con Plotly Express
fig = px.line(
    df_mes,
    x='MES',
    y='Muertes',
    markers=True,
    title='Total de muertes por mes en Colombia (2019)',
    labels={'MES': 'Mes', 'Muertes': 'Número de muertes'}
)
fig.update_layout(xaxis=dict(tickmode='linear'))

#### SEGUNDA GRAFICA
# 1) Filtrar solo los registros de tipo "Homicidio"
df_homicidios = df_merged_municipio[
    df_merged_municipio['MANERA_MUERTE'] == 'Homicidio'
]

# 2) Contar homicidios por municipio y quedarnos con los 5 más altos
df_top5 = (
    df_homicidios
      .groupby('COD_MUNICIPIO')
      .size()
      .reset_index(name='Homicidios')
      .nlargest(5, 'Homicidios')
)

# 3) Crear gráfico de barras
fig_bar = px.bar(
    df_top5,
    x='COD_MUNICIPIO',
    y='Homicidios',
    title='Top 5 municipios más violentos (Homicidios)',
    labels={'COD_MUNICIPIO': 'Código de municipio', 'Homicidios': 'Número de homicidios'}
)

##### TERCERA GRAFICA 

# 1) Contar muertes por municipio
df_mortalidad = (
    df_merged_municipio
      .groupby('COD_MUNICIPIO')
      .size()
      .reset_index(name='Muertes')
)

# 2) Seleccionar los 10 con menos muertes
df_bottom10 = df_mortalidad.nsmallest(10, 'Muertes')

# 3) Crear el gráfico circular
fig_pie = px.pie(
    df_bottom10,
    names='COD_MUNICIPIO',
    values='Muertes',
    title='10 municipios con menor índice de mortalidad',
    hole=0.0  # si quieres un donut, usa hole=0.3
)


##### CUARTA GRAFICA 

# 1) Agrupar por código y nombre, contar casos
df_causas = (
    df_merged_muertes
      .groupby(['COD_MUERTE', 'NOMBRE'])
      .size()
      .reset_index(name='Total')
)

# 2) Ordenar de mayor a menor y tomar las 10 primeras
df_top10 = df_causas.sort_values('Total', ascending=False).head(10)


#### QUINTA GRAFICA 
# 1) Obtener la edad máxima registrada en la columna 'GRUPO_EDAD1'
max_edad = df['GRUPO_EDAD1'].max()
# 2) Definir los “bins” (intervalos) para agrupar edades de 5 en 5 años
bins = list(range(0, 30, 5)) + [30, np.inf]
# 3) Crear las etiquetas correspondientes a cada intervalo:

labels = [f"{i}-{i+4}" for i in range(0, 30, 5)] + ["30+"]
#4) Categorizar cada registro de df en su grupo de edad
df['GrupoEdad5a'] = pd.cut(
    df['GRUPO_EDAD1'],
    bins=bins,
    labels=labels,
    right=False,
    include_lowest=True
)
# 5) Agrupar el DataFrame por la nueva columna 'GrupoEdad5a'
df_hist = (
    df
    .groupby('GrupoEdad5a')
    .size()
    .reset_index(name='Muertes')
)
# 6) Crear el gráfico de barras
fig_hist = px.bar(
    df_hist,
    x='GrupoEdad5a',
    y='Muertes',
    title='Distribución de muertes por grupos quinquenales de edad',
    labels={'GrupoEdad5a':'Grupo de edad','Muertes':'Número de muertes'}
)


#### SEXTA GRAFICA 
df_tmp = df_merged.copy()
# Mapear 1→Hombre, 2→Mujer para que la leyenda sea legible
df_tmp['Sexo'] = df_tmp['SEXO'].map({1: 'Hombre', 2: 'Mujer'})

# 2) Agrupar por departamento y sexo, contando muertes
df_group = (
    df_tmp
      .groupby(['COD_DEPARTAMENTO', 'Sexo'])
      .size()
      .reset_index(name='Muertes')
)

# 3) Crear la figura de barras apiladas
fig_stack = px.bar(
    df_group,
    x='COD_DEPARTAMENTO',
    y='Muertes',
    color='Sexo',
    barmode='stack',
    title='Muertes por sexo en cada departamento (2019)',
    labels={'COD_DEPARTAMENTO': 'Departamento', 'Muertes': 'Número de muertes'}
)
# Opcional: ordenar eje x alfabéticamente
fig_stack.update_layout(
    xaxis={'categoryorder': 'category ascending'},
    legend_title_text='Sexo'
)
# Se crea el objeto APP
app = Dash(__name__)

# Se crea el layout con cada una de las graficas solicitadas 
app.layout = html.Div([
    html.H2("Muertes mensuales en Colombia (2019)", style={'textAlign': 'center'}),
    dcc.Graph(figure=fig),
    html.H2("Top 5 municipios más violentos (Homicidios)", style={'textAlign': 'center'}),
    dcc.Graph(figure=fig_bar),
    html.H2("Top 10 municipios con menor mortalidad", style={'textAlign': 'center'}),
    dcc.Graph(figure=fig_pie),
    html.H2("10 principales causas de muerte en Colombia", style={'textAlign': 'center'}),
    dash_table.DataTable(
        id='tabla-causas',
        columns=[
            {'name': 'Código', 'id': 'COD_MUERTE'},
            {'name': 'Causa',  'id': 'NOMBRE'},
            {'name': 'Total de casos', 'id': 'Total'}
        ],
        data=df_top10.to_dict('records'),
        sort_action='native',
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '5px'},
        style_header={
            'backgroundColor': 'lightgrey',
            'fontWeight': 'bold'
        }
    ),
    html.H2("Histograma de muertes por edad (grupos quinquenales)",
            style={'textAlign':'center'}),
    dcc.Graph(figure=fig_hist),
    html.H2("Muertes por sexo y departamento", style={'textAlign': 'center'}),
    dcc.Graph(figure=fig_stack)
])

# Se ejecuta la app 
if __name__ == '__main__':  
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=True)









