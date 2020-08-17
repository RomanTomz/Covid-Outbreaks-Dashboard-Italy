import streamlit as st
import pandas as pd
import geojson
import plotly.express as px
import plotly.graph_objs as go

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
@st.cache(persist=True)
def load_data_r():
    data_r = pd.read_csv(url_r, parse_dates=True)
    return data_r

data_r = load_data_r()

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

# Plot Crescita Casi Settimanale
#st.markdown(f'## Nuovi Casi Negli Ultimi 7 Giorni al {date.today().strftime("%d/%m/%Y")}')
fig_nc7=px.bar(top5_nc7.sort_values(ascending=True, by='nuovi_casi_7gg'), x='nuovi_casi_7gg', y='denominazione_provincia', orientation='h',
           width=600, height=300, labels={'denominazione_provincia':'','nuovi_casi_7gg':'Nuovi Casi Positivi'})
fig_nc7.update_traces(marker_color='#FF5533')
fig_nc7.update_layout(margin={"r":0,"t":20,"l":0,"b":0})

#st.plotly_chart(fig_nc7)


# Mappa nuovi casi
#st.markdown('## Nuovi Casi 7 Giorni - Visualizzazione Geografica')
fig_geo_7 = go.Figure(go.Choroplethmapbox(geojson=province_geo, locations=data_p.denominazione_provincia, z=data_p.nuovi_casi_7gg,
                                    colorscale="Reds", zmin=0, zmax=170,
                                    marker_opacity=0.5, marker_line_width=0.6))
fig_geo_7.update_layout(mapbox_style="carto-positron",
                  mapbox_zoom=4, mapbox_center = {"lat": 41.8719, "lon": 12.5674})
fig_geo_7.update_layout(margin={"r":0,"t":20,"l":0,"b":0})

#st.plotly_chart(fig)

#Plot media mobile
#st.markdown(f'## Crescita Media Mobile Negli Ultimi 7 Giorni al {date.today().strftime("%d/%m/%Y")}')
fig_mm = px.bar(top5_mm.sort_values(by='media_mobile', ascending=True), x='media_mobile',y='denominazione_provincia', orientation='h',
                width=600, height=300, labels={'media_mobile':'% Crescita MM', 'denominazione_provincia':''})
fig_mm.update_traces(marker_color='#FF5533')
fig_mm.update_layout(margin={"r":0,"t":20,"l":0,"b":0})

#st.plotly_chart(fig_mm)

#Mappa media Mobile
#st.markdown('## Media Mobile 7 Giorni - Visualizzazione Geografica')

fig_geo_mm = go.Figure(go.Choroplethmapbox(geojson=province_geo, locations=data_p.denominazione_provincia, z=data_p.media_mobile,
                                    colorscale="Reds", zmin=0, zmax=1.5,
                                    marker_opacity=0.5, marker_line_width=0.6))
fig_geo_mm.update_layout(mapbox_style="carto-positron",
                  mapbox_zoom=4, mapbox_center = {"lat": 41.8719, "lon": 12.5674})
fig_geo_mm.update_layout(margin={"r":0,"t":20,"l":0,"b":0})

st.sidebar.markdown('viz')
#st.plotly_chart(fig_mm)
#st.sidebar.subheader('Seleziona Visualizzazione')
viz = st.sidebar.radio('Seleziona Visualizzazione',('Nuovi Casi 7 gg','Media Mobile 7 gg'))

if viz == 'Nuovi Casi 7 gg':
    st.markdown(f'#### 5 Province con maggiore crescita di casi negli ultimi 7 giorni al {date.today().strftime("%d/%m/%Y")}')
    st.plotly_chart(fig_nc7)
    st.markdown('#### Nuovi Casi Negli Ultimi 7 Giorni - Visualizzazione Geografica')
    st.plotly_chart(fig_geo_7)

if viz == 'Media Mobile 7 gg':
    st.markdown(f'#### 5 province con maggiore crescita media mobile negli ultimi 7 giorni al {date.today().strftime("%d/%m/%Y")}')
    st.plotly_chart(fig_mm)
    st.markdown('#### Crescita Media Mobile Negli Ultimi 7 Giorni - Visualizzazione Geografica')
    st.plotly_chart(fig_geo_mm)
