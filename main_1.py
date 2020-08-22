import streamlit as st
import pandas as pd
import geojson
import plotly.express as px
import plotly.graph_objs as go
import numpy as np

from datetime import date

import json
from urllib.request import urlopen


st.title('Analisi Nuovi Focolai Covid 19')


url_p = 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/dpc-covid19-ita-province.json'
url_r = 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-regioni/dpc-covid19-ita-regioni.csv'

@st.cache(persist=True)
def load_data_p():
    data_p = pd.read_json(url_p)
    data_p['data'] = pd.to_datetime(data_p['data'])
    return data_p

# Data cleaning and preparation (province)

data_p = load_data_p()
data_p = data_p[~(data_p.denominazione_provincia == 'In fase di definizione/aggiornamento') & ~(data_p.denominazione_provincia == 'Fuori Regione / Provincia Autonoma')]
data_p['pct_crescita'] = data_p.groupby('denominazione_provincia')['totale_casi'].transform(lambda x :(x.pct_change()*100).round(2))
data_p['media_mobile'] = data_p.groupby('denominazione_provincia')['pct_crescita'].apply(lambda x : x.rolling(window=7).mean().round(2))
data_p['nuovi_casi_7gg'] = data_p.groupby('denominazione_provincia')['totale_casi'].apply(lambda x:x.diff(periods=7))

prov_latest = data_p.set_index('data').sort_index().groupby('denominazione_provincia').tail(1)
top5_nc7 = prov_latest.sort_values('nuovi_casi_7gg', ascending=False).head(5)
top5_mm = prov_latest.sort_values('media_mobile', ascending=False).head(5)
# Data cleaning and preparation (regioni)
@st.cache(persist=True, allow_output_mutation=True)
def load_data_r():
    data_r = pd.read_csv(url_r, parse_dates=True)
    return data_r

data_r = load_data_r()
data_r['crescita_ospedalizzati_sett'] = data_r.groupby('denominazione_regione')['totale_ospedalizzati'].apply(lambda x : x.diff(periods=7))
data_r['casi_testati_7gg'] = data_r.groupby('denominazione_regione')['casi_testati'].apply(lambda x: x.diff(periods=7))
data_r['nuovi_pos_7gg'] = data_r.groupby('denominazione_regione')['nuovi_positivi'].apply(lambda x: x.diff(periods=7))
data_r['indice_pos'] = (data_r.nuovi_pos_7gg/data_r.casi_testati_7gg).mul(100).round(2)
reg_latest = data_r.set_index('data').sort_index().groupby('denominazione_regione').tail(1)





top5_osp = reg_latest.set_index('denominazione_regione').sort_values(by='crescita_ospedalizzati_sett', ascending=False).head()
indice = reg_latest.set_index('denominazione_regione').sort_values(by='indice_pos', ascending=False).head()

indice.index.rename('Regione', inplace=True)
indice.rename(columns={'indice_pos':'Indice di Positivitá'}, inplace=True)
top5_osp.index.rename('Regione', inplace=True)
top5_osp.rename(columns={'crescita_ospedalizzati_sett':'Incremento Ricoveri Negli Ultimi 7 gg'}, inplace=True)

top5_osp = top5_osp[['Incremento Ricoveri Negli Ultimi 7 gg']].style.background_gradient(cmap='Reds', ).format('{0:,.0f}')
indice = indice[['Indice di Positivitá']].style.background_gradient(cmap='Reds', ).format('{0:,.2f}')


# Geo Data import and preparation
    #Province
def load_geo_p():
    with urlopen('https://gist.githubusercontent.com/datajournalism-it/212e7134625fbee6f9f7/raw/dabd071fe607f5210921f138ad3c7276e3841166/province.geojson') as response:
        province = json.load(response)
    return province

province_geo = load_geo_p()

for feature in province_geo['features']:
  feature['id'] = feature['properties']['NOME_PRO']

    #Regioni
def load_geo_r():
    with urlopen('https://gist.githubusercontent.com/datajournalism-it/48e29e7c87dca7eb1d29/raw/2636aeef92ba0770a073424853f37690064eb0ea/regioni.geojson') as response:
        regjson = json.load(response)
    return regjson

regioni_geo = load_geo_r()

for feature in regioni_geo['features']:
  feature['id'] = feature['properties']['NOME_REG']


top5_mm.rename(columns={'denominazione_provincia':'Provincia', 'media_mobile':'Crescita % Media Mobile 7gg'}, inplace=True)
top5_nc7.rename(columns={'denominazione_provincia':'Provincia', 'nuovi_casi_7gg':'Nuovi Casi in 7gg'}, inplace=True)
top5_mm.set_index('Provincia', inplace=True)
top5_nc7.set_index('Provincia', inplace=True)


formatted_mm = top5_mm[['Crescita % Media Mobile 7gg']].style.background_gradient(cmap='Reds', ).format('{0:,.2f}')
formatter_nc7 = top5_nc7[['Nuovi Casi in 7gg']].style.background_gradient(cmap='Reds', ).format('{0:,.0f}')


# Mappa nuovi casi
fig_geo_7 = go.Figure(go.Choroplethmapbox(geojson=province_geo, locations=data_p.denominazione_provincia, z=data_p.nuovi_casi_7gg,
                                    colorscale="Reds", zmin=0, zmax=200,
                                    marker_opacity=0.5, marker_line_width=0.6))
fig_geo_7.update_layout(mapbox_style="carto-positron",
                  mapbox_zoom=4, mapbox_center = {"lat": 41.8719, "lon": 12.5674})
fig_geo_7.update_layout(margin={"r":0,"t":20,"l":0,"b":0})



#Mappa media Mobile

fig_geo_mm = go.Figure(go.Choroplethmapbox(geojson=province_geo, locations=data_p.denominazione_provincia, z=data_p.media_mobile,
                                    colorscale="Reds", zmin=0, zmax=1.5,
                                    marker_opacity=0.5, marker_line_width=0.6))
fig_geo_mm.update_layout(mapbox_style="carto-positron",
                  mapbox_zoom=4, mapbox_center = {"lat": 41.8719, "lon": 12.5674})
fig_geo_mm.update_layout(margin={"r":0,"t":20,"l":0,"b":0})

#Mappa Ospedalizzati
extremum_2 = max(np.max(reg_latest.crescita_ospedalizzati_sett), np.abs(np.min(reg_latest.crescita_ospedalizzati_sett)))
fig_osp = go.Figure(go.Choroplethmapbox(geojson=regioni_geo, locations=reg_latest.denominazione_regione, z=reg_latest.crescita_ospedalizzati_sett,
                                    colorscale="temps", zmin=-extremum_2,zmid=0, zmax=extremum_2,
                                    marker_opacity=0.5, marker_line_width=0.6))
fig_osp.update_layout(mapbox_style="carto-positron",
                  mapbox_zoom=4, mapbox_center = {"lat": 41.8719, "lon": 12.5674})
fig_osp.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

#Indice Positivi
extremum_3 = max(np.max(reg_latest.indice_pos), np.abs(np.min(reg_latest.indice_pos)))
fig_ind = go.Figure(go.Choroplethmapbox(geojson=regioni_geo, locations=reg_latest.denominazione_regione, z=reg_latest.indice_pos,
                                    colorscale="Temps", zmin=-extremum_3,zmid=0, zmax=extremum_3,
                                    marker_opacity=0.5, marker_line_width=0.6))
fig_ind.update_layout(mapbox_style="carto-positron",
                  mapbox_zoom=4, mapbox_center = {"lat": 41.8719, "lon": 12.5674})
fig_ind.update_layout(margin={"r":0,"t":20,"l":0,"b":0})


st.sidebar.header('Tipo Visualizzazione')

viz = st.sidebar.radio('Seleziona Visualizzazione',('Nuovi Casi 7 gg','Media Mobile 7 gg','Incremento Ospedalizzati 7 gg (Regionale)','Indice Positivitá 7gg (Regionale)'))


if viz == 'Nuovi Casi 7 gg':
        st.markdown('#### Prime 5 Province per Nuovi Contagi Negli Ultimi 7 Giorni')
        st.write(formatter_nc7)
        st.markdown('#### Nuovi Casi Negli Ultimi 7 Giorni - Visualizzazione Geografica')
        st.plotly_chart(fig_geo_7)

if viz == 'Media Mobile 7 gg':
        st.markdown('Prime 5 Province per Maggiore Incremento Media Mobile a 7 Giorni')
        st.write(formatted_mm)
        st.markdown('#### Crescita Media Mobile Negli Ultimi 7 Giorni - Visualizzazione Geografica')
        st.plotly_chart(fig_geo_mm)

if viz == 'Incremento Ospedalizzati 7 gg (Regionale)':
        st.markdown('#### Crescita Ospedalizzati Negli Ultimi 7 Giorni')
        st.write(top5_osp)
        st.markdown('#### Crescita Ospedalizzati Negli Ultimi 7 Giorni - Visualizzazione Geografica')
        st.plotly_chart(fig_osp)

if viz == 'Indice Positivitá 7gg (Regionale)':
        st.markdown('#### Indice di Positivitá Negli Ultimi 7 Giorni')
        st.write(indice)
        st.markdown('#### Indice di Positivitá a 7 Giorni - Visualizzazione Geografica')
        st.plotly_chart(fig_ind)


st.sidebar.markdown(
    ("#### La Dashboard utilizza la media mobile e l'incremento a 7 giorni per dare maggiore chiarezza al trend eliminando le oscillazioni quotidiane")

)

st.sidebar.markdown("#### L'indice di positivitá é ottenuto con: (nuovi_positivi_7gg/casi_testati_7gg)x100")

st.sidebar.markdown("###### Dati da https://github.com/pcm-dpc/COVID-19 ")
st.sidebar.button('Aggiorna Dati')
