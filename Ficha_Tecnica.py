#!/usr/bin/env python
# coding: utf-8

import fiona
import geopandas as gpd
import pandas as pd
import numpy as np
import folium
import ipywidgets as widgets

from aws_helpers import s3
from dotenv import load_dotenv

# Imports Streamlit
import streamlit as st
from streamlit_folium import folium_static
import pandas as pd
import numpy as np
import time

import warnings
warnings.filterwarnings('ignore')

pd.set_option('display.max_columns', None)
pd.set_option('display.float_format', lambda x: '%.3f' % x)

st.title('FICHA TÉCNICA')
st.write("Prueba ficha técnica")

dotenv_path = 'C:/Users/ypalaciosp/OneDrive - Constructora Conconcreto/Documentos/Corner/Notebooks/FT_Arquitectura - Comment/.env'
load_dotenv(dotenv_path) 
usuario = 'YuraniPalaciosPalacios'

#Creando puntos para cruzar información
dicc = {'Nombre':['Lote1','Lote2'], 'Latitud':['4.6680315','4.668367'], 'Longitud':['-74.05813','-74.0579033']}
data = pd.DataFrame(dicc)

#Tabla a geografica
data = gpd.GeoDataFrame(data,geometry=gpd.points_from_xy(data.Longitud, data.Latitud),crs="EPSG:4326")

#Se obtiene la información de lotes y barrios 
lotes = gpd.read_file('C:/Users/ypalaciosp/OneDrive - Constructora Conconcreto/Documentos/Corner/Notebooks/FT_Arquitectura - Comment/Estructura urbana/Lote.shp')
barrios = gpd.read_file('s3://pactia-datalake-in/variables_externas/MapInfo/Servinformación/Proyecciones 2018/Capas/capas1/BOGOTA/WGS84/Barrios_Bogota.TAB', driver="MapInfo File")

#Join de la data(Muestra de dos lotes) y los barrios 
data = gpd.sjoin(data, barrios, how='left', op='intersects',rsuffix='barrio')
data.drop(columns='index_barrio', inplace=True)

m = folium.Map(location=[4.60971, -74.08175], zoom_start=12, tiles='OpenStreetMap')

for i in range(0,len(data)):
    folium.Marker(location = [data.iloc[i]['Latitud'], data.iloc[i]['Longitud']],
                  popup =folium.Popup(data.iloc[i]['NOM_BAR'], max_width=1000),
                  tooltip=data.iloc[i]['Nombre'],icon=folium.Icon(color='gray')).add_to(m)

#for geometry in barrios.geometry:
#    try:
#        folium.GeoJson(geometry).add_to(m)
#    except:
#        continue

#folium_static(m)


#data = gpd.sjoin(data, barrios, how='left', op='intersects',rsuffix='barrio')
#data.drop(columns='index_barrio', inplace=True)

### MANZANAS Y PARQUES
manzanas = gpd.read_file('C:/Users/ypalaciosp/Constructora Conconcreto/CORNER - PROPNIVERSE/01-FASE 1-FICHA NORMATIVA/01-INFORMACION FUENTE/02. Geopackage/Manzanas.gdb' , layer = 'Manzanas Bogotá')
manzanas.to_crs(crs="EPSG:4326", inplace = True)

parques = gpd.read_file('C:/Users/ypalaciosp/OneDrive - Constructora Conconcreto/Documentos/Corner/Notebooks/FT_Arquitectura - Comment/nuevo_pot/files.gdb/', layer = 'EP_Parques')
parques.to_crs(crs="EPSG:4326", inplace = True)

datos = gpd.overlay(manzanas, parques, how='symmetric_difference')
datos = datos.head(1)


## GRAFICO DE MAPA CON TODA LA INFORMACIÓN 

folium.GeoJson(data=datos, style_function= lambda feature:{'color':'black'}).add_to(m)
folium.GeoJson(data=manzanas, style_function= lambda feature:{'color':'gray'}).add_to(m)
folium.GeoJson(data=parques, style_function= lambda feature:{'color':'green'}).add_to(m)

folium_static(m)

# MERGE LOTES Y BARRIOS
lista_barrios = list(data.NOM_BAR.values)

cruce_lb = gpd.sjoin(lotes, barrios, how='left', op='intersects', lsuffix='lote')
cruce_lb = cruce_lb[cruce_lb['NOM_BAR'].isin(lista_barrios)]

geo_col = ['LOTCODIGO','geometry']
data_col = ['LOTCODIGO','area']


for geometry in cruce_lb.geometry:
    try:
        folium.GeoJson(geometry).add_to(m)
    except:continue


choropleth = folium.Choropleth(
    geo_data=cruce_lb[geo_col],
    name="choropleth",
    data=cruce_lb[data_col],
    columns=["LOTCODIGO", "area"],
    key_on="properties.LOTCODIGO",
    fill_color="YlOrRd",
    fill_opacity=0.5,
    line_opacity=0.4,
    highlight=True,
    legend_name="Lotes disponibles por barrio",).add_to(m)

style_function = "font-size: 11px; font-weight: bold"
choropleth.geojson.add_child(
    folium.features.GeoJsonTooltip(['LOTCODIGO'], style=style_function, labels=False))

lista_lotes = ['008313005012','008314020001']
data = cruce_lb[cruce_lb['LOTCODIGO'].isin(lista_lotes)]

data = data[['LOTCODIGO','area','geometry','NOM_BAR','NIVSOCIO']]
data.reset_index(drop=True, inplace=True)

# PLAN PARCIAL 
plan_parcial = gpd.read_file('C:/Users/ypalaciosp/OneDrive - Constructora Conconcreto/Documentos/Corner/Notebooks/FT_Arquitectura - Comment/nuevo_pot/files.gdb/', layer = 'Plan_parcial')
plan_parcial.to_crs(crs="EPSG:4326", inplace = True)

data = gpd.sjoin(data, plan_parcial, how='left', op='intersects', rsuffix='pp')
data.drop(columns='index_pp', inplace=True)

data = data[['LOTCODIGO','area','geometry','NOM_BAR','NIVSOCIO','NOMBRE','ESTADO','ACTO_ADMINISTRATIVO']]
#st.dataframe(data[['LOTCODIGO','area','NOM_BAR','NIVSOCIO']], 1200)

# TRATAMIENTO URBANISTICO
tratamiento_urbanistico = gpd.read_file('C:/Users/ypalaciosp/OneDrive - Constructora Conconcreto/Documentos/Corner/Notebooks/FT_Arquitectura - Comment/nuevo_pot/files.gdb/', layer = 'Tratamiento_urbanistico')
tratamiento_urbanistico.to_crs(crs="EPSG:4326", inplace = True)
tratamiento_urbanistico['TIPOLOGIA'].replace(' ', 'Colindante', inplace=True)
tratamiento_urbanistico['TIPOLOGIA'].replace('TA', 'Aislada', inplace=True)
tratamiento_urbanistico['TIPOLOGIA'].replace('', 'Colindante', inplace=True)

data = gpd.sjoin(data, tratamiento_urbanistico, how='left', op='intersects', rsuffix='tu')
data.drop(columns='index_tu', inplace=True)

data = data[['LOTCODIGO','area','geometry','NOM_BAR','NIVSOCIO','NOMBRE','ESTADO','ACTO_ADMINISTRATIVO_left','CODIGO_TRATAMIENTO',
             'TRATAMIENTO','ALTURA_MAXIMA','TIPOLOGIA']]
st.dataframe(data[['LOTCODIGO','area','NOM_BAR','NIVSOCIO','CODIGO_TRATAMIENTO','TRATAMIENTO','TIPOLOGIA']], 1200)

# AREAS ACTIVIDADES
areas_actividad = gpd.read_file('C:/Users/ypalaciosp/OneDrive - Constructora Conconcreto/Documentos/Corner/Notebooks/FT_Arquitectura - Comment/nuevo_pot/files.gdb/', layer = 'Area_Actividad')
areas_actividad.to_crs(crs="EPSG:4326", inplace = True)
areas_actividad.groupby(['CODIGO_AREA_ACTIVIDAD','NOMBRE_AREA_ACTIVIDAD']).sum()

data = gpd.sjoin(data, areas_actividad, how='left', op='intersects', rsuffix='aa')
data.drop(columns='index_aa', inplace=True)

data = data[['LOTCODIGO','area','geometry','NOM_BAR','NIVSOCIO','NOMBRE','ESTADO','ACTO_ADMINISTRATIVO_left','CODIGO_TRATAMIENTO',
             'TRATAMIENTO','ALTURA_MAXIMA','CODIGO_AREA_ACTIVIDAD','NOMBRE_AREA_ACTIVIDAD']]

data.rename(columns={'NOMBRE':'Nombre_PP'}, inplace = True)

# EL DORADO
inf_dorado = gpd.read_file('C:/Users/ypalaciosp/OneDrive - Constructora Conconcreto/Documentos/Corner/Notebooks/FT_Arquitectura - Comment/nuevo_pot/files.gdb/', layer =  'Influen_indir_El_Dorado')
inf_dorado.to_crs(crs="EPSG:4326", inplace = True)

data = gpd.sjoin(data, inf_dorado, how='left', op='intersects', rsuffix='inf_d')
data.drop(columns='index_inf_d', inplace=True)

data = data[['LOTCODIGO','area','geometry','NOM_BAR','NIVSOCIO','Nombre_PP','ESTADO','ACTO_ADMINISTRATIVO_left','CODIGO_TRATAMIENTO',
             'TRATAMIENTO','ALTURA_MAXIMA','CODIGO_AREA_ACTIVIDAD','NOMBRE_AREA_ACTIVIDAD','SECTOR']]

# UPL
upl = gpd.read_file('C:/Users/ypalaciosp/OneDrive - Constructora Conconcreto/Documentos/Corner/Notebooks/FT_Arquitectura - Comment/nuevo_pot/files.gdb/', layer =  'UPL')
upl.to_crs(crs="EPSG:4326", inplace = True)

data = gpd.sjoin(data, upl, how='left', op='intersects', rsuffix='upl')
data.drop(columns='index_upl', inplace=True)

data = data[['LOTCODIGO','area','geometry','NOM_BAR','NIVSOCIO','Nombre_PP','ESTADO','ACTO_ADMINISTRATIVO_left','CODIGO_TRATAMIENTO',
             'TRATAMIENTO','ALTURA_MAXIMA','CODIGO_AREA_ACTIVIDAD','NOMBRE_AREA_ACTIVIDAD','SECTOR','CODIGO_ID','NIOMBRE']]
st.dataframe(data[['CODIGO_AREA_ACTIVIDAD','NOMBRE_AREA_ACTIVIDAD','CODIGO_ID','NIOMBRE']], 1200)

# LOCALIDAD
localidad = gpd.read_file('C:/Users/ypalaciosp/OneDrive - Constructora Conconcreto/Documentos/Corner/Notebooks/FT_Arquitectura - Comment/nuevo_pot/files.gdb/', layer =  'Localidad')
localidad.to_crs(crs="EPSG:4326", inplace = True)

data = gpd.sjoin(data, localidad, how='left', op='intersects', rsuffix='localidad')
data.drop(columns=['index_localidad'], inplace=True)

# ESTACIONAMIENTOS
estacionamientos = {
                    'CODIGO_AREA_ACTIVIDAD':['AAERVIS','AAERAE','AAPGSU','AAPRSU-DCS','AAPRSU-NOVIS','AAPRSU-VIS','AAGSM'],
                    'AREA_ACTIVIDAD':['Estructurante - Receptora de vivienda de interés social', 'Estructurante - Receptora de actividades económicas',
                                      'Proximidad - Generadora de soportes urbanos' , 'Proximidad - Receptora de soportes urbanos','Proximidad - Receptora de soportes urbanos', 
                                      'Proximidad - Receptora de soportes urbanos','Grandes servicios metropolitanos'],
                    'Actividad':['Estructurante', 'Estructurante', 'Proximidad' , 'Proximidad','Proximidad', 
                                      'Proximidad','Grandes servicios metropolitanos'],
                   'Exigido':['0%', '0%', '5%', '5%', '8%', '6%', '0%'],
                   'Opcional 1':['10%', '15%', '15%', '20%', '20%', '20%', '20%'],
                   'Opcional 2':['15%', '15%', '10%', '15%', '15%', '15%', '15%']}
estacionamientos = pd.DataFrame(estacionamientos)
st.dataframe(estacionamientos, 1200)

data = data.merge(estacionamientos, how='left', left_on='NOMBRE_AREA_ACTIVIDAD',right_on='CODIGO_AREA_ACTIVIDAD')
data.rename(columns={'Exigido':'est_Exigido','Opcional 1':'est_opcional_1','Opcional 2':'est_opcional_2'}, inplace=True)
#data.drop(columns=['CODIGO_AREA_ACTIVIDAD','AREA_ACTIVIDAD'], inplace=True)
#st.dataframe(data[['Localidad','Actividad','est_Exigido','est_Opcional_1','est_Opcional_2']])

# TABLA DE USOS 
tabla_uso = pd.read_excel('C:/Users/ypalaciosp/Constructora Conconcreto/CORNER - PROPNIVERSE/01-FASE 1-FICHA NORMATIVA/01-INFORMACION FUENTE/03. Informacion procesada/Usos del suelo/Usos del suelo.xlsx', sheet_name='Matriz_pivote')
mascara = tabla_uso['Actividad'].str.upper().isin(list(set(data['Actividad'].str.upper())))
tabla_uso = pd.DataFrame(tabla_uso)
tabla_uso[['Condiciones', 'Mitigación urbana', 'Mitigación ambiental']]= tabla_uso[['Condiciones', 'Mitigación urbana', 'Mitigación ambiental']].astype(bytes)
#for i in range(0,len(data)):
#tabla_uso_filtro = tabla_uso[tabla_uso['Actividad'] == data['Actividad'][0]]
#tabla_uso_filtro = tabla_uso[tabla_uso['Actividad'] == 'Estructurante']
#st.write(tabla_uso) 

st.dataframe(tabla_uso)
#opciones_list = list(tabla_uso['Actividad'].unique())
#opciones = st.selectbox('Elija una actividad', opciones_list)

#query = f"Actividad=='{opciones}'"
#tabla_uso_filtro = tabla_uso.query(query)
#tabla_uso_filtro = tabla_uso[tabla_uso['Actividad'] == opciones]
#tabla_uso_filtro = tabla_uso[(mascara)&(tabla_uso['Actividad']==opciones)]
#def filtro_tabla(opciones):
#    tabla=tabla_uso[(mascara)&(tabla_uso['Actividad']==opciones)]
#    return tabla
#opcion_act = st.write(opciones)
#st.dataframe(tabla_uso[tabla_uso['Actividad'] == opcion_act])

#options = list(set(tabla_uso['Actividad']))
#values = tabla_uso[['Actividad','Categoría', 'Subcategoría','Nivel','Condiciones','Mitigación urbana','Mitigación ambiental']]
#dic= dict(zip(options, values))
#a = st.selectbox('Elija una Actividad', options)
#tabla = tabla_uso[(mascara)&(tabla_uso['Actividad']==)]
#st.write(a)
#st.dataframe(tabla)


### MANZANAS Y PARQUES
#manzanas = gpd.read_file('C:/Users/ypalaciosp/Constructora Conconcreto/CORNER - PROPNIVERSE/01-FASE 1-FICHA NORMATIVA/01-INFORMACION FUENTE/02. Geopackage/Manzanas.gdb' , layer = 'Manzanas Bogotá')
#manzanas.to_crs(crs="EPSG:4326", inplace = True)

#parques = gpd.read_file('C:/Users/ypalaciosp/OneDrive - Constructora Conconcreto/Documentos/Corner/Notebooks/FT_Arquitectura - Comment/nuevo_pot/files.gdb/', layer = 'EP_Parques')
#parques.to_crs(crs="EPSG:4326", inplace = True)

#datos = gpd.overlay(manzanas, parques, how='symmetric_difference')
#datos = datos.head(1)


## GRAFICO DE MAPA CON TODA LA INFORMACIÓN 

#folium.GeoJson(data=datos, style_function= lambda feature:{'color':'black'}).add_to(m)
#folium.GeoJson(data=manzanas, style_function= lambda feature:{'color':'gray'}).add_to(m)
#folium.GeoJson(data=parques, style_function= lambda feature:{'color':'green'}).add_to(m)

#folium_static(m)

#Tabla con la informacipon de barrio y manzanas
#data = data[['Nombre','COD_BAR','NOM_BAR','N_MANZANAS','NIVSOCIO']]
#data = data[['Codigo_lote','area','Barrio','Estrato','Plan_parcial','Tratamiento', 'Altura_maxima']]
#st.dataframe(data)

#data = data[['Area_Actividad','Nombre_Area_Actividad','Inf_Dorado','Nombre_UPL','Localidad','Actividad']]
#st.dataframe(data)

#data = data[['est_Exigido','est_opcional_1','est_opcional_2']]
#st.dataframe(data)

#Tarjetas
#col1, col2, col3 = st.columns(3)
#col1.metric("Codigo", data['COD_BAR'][0], None)
#col2.metric("Barrio", data['NOM_BAR'][0], None)
#col3.metric("Nivel Socieconomico",data['NIVSOCIO'][0], None)
#col4.metric("Tratamientooo",data['Tratamiento'][0], None)

# Streamlit widgets automatically run the script from top to bottom. Since
# this button is not connected to any other logic, it just causes a plain
# rerun.

st.button("Re-run")