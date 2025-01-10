#!/usr/bin/env python # [1]
"""\
This script generates a streamlit dashboard, hosted publicly at the following location:


This dashboard takes data regarding forecasts for Grid demand vs Wind & Solar generation from the elexon API and puts it in a convenient
graphical format for direct evaluation

Created and Maintained by: Tim Beresford
Contact: timwjberesford@outlook.com
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
import plotly.graph_objs as go
from datetime import datetime, timedelta

#Class to generate date/time strings required for API requests

class Dtnow:
  def __init__(self):
    now = datetime.now()
    self.year = str(now.strftime("%Y"))
    self.month = str(now.strftime("%m"))
    self.day = str(now.strftime("%d"))
    self.minutes = str(now.strftime("%d"))
    self.hours = str(now.strftime("%H"))
    self.hours_end = "23"
    self.minutes_end = "59"
    self.start = self.year+"-"+self.month+"-"+self.day+"T"+self.hours+"%3A"+self.minutes
    self.end = self.year+"-"+self.month+"-"+self.day+"T"+self.hours_end+"%3A"+self.minutes_end
    datetimeplus24 = datetime.now() + timedelta(hours=24)
    self.year_tmrw = datetimeplus24.strftime("%Y")
    self.month_tmrw = datetimeplus24.strftime("%m")
    self.day_tmrw = datetimeplus24.strftime("%d")
    self.start_time_tmrw = "00"
    self.start_tmrw = self.year_tmrw+"-"+self.month_tmrw+"-"+self.day_tmrw+"T"+self.start_time_tmrw+"%3A"+self.start_time_tmrw
    self.end_tmrw = self.year_tmrw+"-"+self.month_tmrw+"-"+self.day_tmrw+"T"+self.hours_end+"%3A"+self.minutes_end
    
# Function to fetch Day-ahead Demand Forecast for today & tomorrow
def fetch_demand_forecast():
    
    #Empty list to store today & tomorrow databases
    df = []
    
    for x in range(2):

        # datetime containing current date and time
        dt = Dtnow()

        # Static parts of URL to call elexon API. Dynamic parts regarding time and date generated in Dtnow
        base_url_1 = "https://data.elexon.co.uk/bmrs/api/v1/forecast/demand/total/day-ahead?from="
        base_url_2 = "&to="
        base_url_3 = "&format=json"
        
        # get url for today
        if x==0:
            url = base_url_1+dt.start+base_url_2+dt.end+base_url_3
        
        #get url for tomorrow
        elif x==1:
            url = base_url_1+dt.start_tmrw+base_url_2+dt.end_tmrw+base_url_3
        
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            # Parse JSON into a DataFrame
            forecast_data = data['data']
            df.append(pd.DataFrame(forecast_data))
        else:
            st.error("Failed to fetch data from Elexon API.")
            return pd.DataFrame()
    return df

# Fetch databases & separate out today/tomorrow
demand_forecast_list = fetch_demand_forecast()

demand_forecast_today_df = demand_forecast_list[0]
demand_forecast_tmrw_df = demand_forecast_list[1]

# Function to fetch Day-ahead Generation Forecast (Wind & Solar) for today & tomorrow
def fetch_generation_forecast():

    #Empty list to store today & tomorrow databases
    df = []

    for x in range(2):

        # datetime containing current date and time
        dt=Dtnow()

        # Static parts of URL to call elexon API. Dynamic parts regarding time and date generated in Dtnow
        base_url_1 = "https://data.elexon.co.uk/bmrs/api/v1/forecast/generation/wind-and-solar/day-ahead?from="
        base_url_2 = "&to="
        base_url_3 = "&processType=day%20ahead&format=json"

        # get url for today
        if x==0:
            url = base_url_1+dt.start+base_url_2+dt.end+base_url_3
            print("URL TODAY: ",url)
        
        #get url for tomorrow
        elif x==1:
            url = base_url_1+dt.start_tmrw+base_url_2+dt.end_tmrw+base_url_3
            print("URL TOMORROW: ",url)
        
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            # Parse JSON into a DataFrame
            forecast_data = data['data']
            
            df.append(pd.DataFrame(forecast_data))
            
        else:
            st.error("Failed to fetch data from Elexon API.")
            return pd.DataFrame()
    return df

# Fetch databases & separate out today/tomorrow
generation_forecast_list = fetch_generation_forecast()

generation_forecast_today_df = generation_forecast_list[0]
generation_forecast_tmrw_df = generation_forecast_list[1]

################ TODAY SECTION OF DASHBOARD ####################

# TODAY - Separate Solar, Offshore & Onshore Wind generation data
solar_forecast_today = generation_forecast_today_df[generation_forecast_today_df['businessType'] == 'Solar generation']
wind_offshore_forecast_today = generation_forecast_today_df[generation_forecast_today_df['psrType'] == 'Wind Offshore']
wind_onshore_forecast_today = generation_forecast_today_df[generation_forecast_today_df['psrType'] == 'Wind Onshore']

# Dashboard Layout

st.title("Short Term Forecasting: Demand vs Wind & Solar Generation")

# TODAY - Create a line chart
st.subheader("Today: Generation vs Demand")

if not demand_forecast_today_df.empty:
    # Create indvidual lines to plot, specifying line colours
    fig = go.Figure([
            go.Scatter(x=demand_forecast_today_df['startTime'], y=demand_forecast_today_df['quantity'],mode='lines+markers', name='Transmission System Demand',line=dict(color="red")),
            go.Scatter(x=solar_forecast_today['startTime'], y=solar_forecast_today['quantity'],mode='lines+markers',name='Solar Generation',line=dict(color="yellow")),
            go.Scatter(x=wind_offshore_forecast_today['startTime'], y=wind_offshore_forecast_today['quantity'],mode='lines+markers',name='Wind Offshore Generation',line=dict(color="white")),
            go.Scatter(x=wind_onshore_forecast_today['startTime'], y=wind_onshore_forecast_today['quantity'],mode='lines+markers',name='Wind Onshore Generation',line=dict(color="green"))   
    ])
    # Format chart, titles, legend, etc.
    fig.update_layout(title="Today's Forecast of Wind & Solar Generation vs Demand")
    fig.update_layout(legend_title_text = "Legend")
    fig.update_xaxes(title_text="Start Time")
    fig.update_yaxes(title_text="Forecast (MW)")

    # plot
    st.plotly_chart(fig)
else:
    st.warning("No data available to display.")

#Post time of last update
now = datetime.now()
st.write('Data accurate as of: ', now.strftime("%d/%m/%Y, %H:%M:%S") + ". Hit Refresh to update.")

st.button("Refresh", type="primary",key=1)


################ TOMORROW SECTION OF DASHBOARD ####################

# TOMORROW - Separate Solar, Offshore & Onshore Wind generation data & plot chart if data exists
st.subheader("Tomorrow: Generation vs Demand")

# If data does not exist, dataframe will be present but missing certain columns. Simple check to see if required columns exist
if 'businessType' in generation_forecast_tmrw_df.columns:

    solar_forecast_tmrw = generation_forecast_tmrw_df[generation_forecast_tmrw_df['businessType'] == 'Solar generation']
    wind_offshore_forecast_tmrw = generation_forecast_tmrw_df[generation_forecast_tmrw_df['psrType'] == 'Wind Offshore']
    wind_onshore_forecast_tmrw = generation_forecast_tmrw_df[generation_forecast_tmrw_df['psrType'] == 'Wind Onshore']
    # TOMORROW - Create a line chart
    
    if not demand_forecast_tmrw_df.empty:
        fig = go.Figure([
                # Create indvidual lines to plot, specifying line colours
                go.Scatter(x=demand_forecast_tmrw_df['startTime'], y=demand_forecast_tmrw_df['quantity'],mode='lines+markers', name='Transmission System Demand',line=dict(color="red")),
                go.Scatter(x=solar_forecast_tmrw['startTime'], y=solar_forecast_tmrw['quantity'],mode='lines+markers',name='Solar Generation',line=dict(color="yellow")),
                go.Scatter(x=wind_offshore_forecast_tmrw['startTime'], y=wind_offshore_forecast_tmrw['quantity'],mode='lines+markers',name='Wind Offshore Generation',line=dict(color="white")),
                go.Scatter(x=wind_onshore_forecast_tmrw['startTime'], y=wind_onshore_forecast_tmrw['quantity'],mode='lines+markers',name='Wind Onshore Generation',line=dict(color="green"))
                
        ])
        # Format chart, titles, legend, etc.
        fig.update_layout(title="Today's Forecast of Wind & Solar Generation vs Demand")
        fig.update_layout(legend_title_text = "Legend")
        fig.update_xaxes(title_text="Start Time")
        fig.update_yaxes(title_text="Forecast (MW)")
        st.plotly_chart(fig)
    else:
        st.warning("No data available to display.")

    #Post time of last update
    now = datetime.now()
    st.write('Data accurate as of: ', now.strftime("%d/%m/%Y, %H:%M:%S") + ". Hit Refresh to update.")

    st.button("Refresh", type="primary",key=2)

# Message to appear in place of chart if tomorrow data not published yet
else:
    st.write('Data for tomorrow has not yet been published. Please try again later.')

#Useful information provided by Elexon regarding data updates
st.write('From Elexon: The information shall be published no later than 18:00 Brussels time, one day before actual delivery takes place. The information shall be regularly updated and published during intra-day trading with at least one update to be published at 8:00 Brussels time on the day of actual delivery.')


# Link to Demand API source
url = "https://bmrs.elexon.co.uk/demand-forecast"
st.write("Demand forecast Data Source [here](%s)" % url)

# Link to Generation API source
url = "https://bmrs.elexon.co.uk/generation-forecast-for-wind-and-solar"
st.write("Generation forecast Data Source [here](%s)" % url)




