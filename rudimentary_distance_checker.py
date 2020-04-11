# -*- coding: utf-8 -*-
"""
Created on Fri Apr  3 17:51:46 2020

@author: muuph
"""

import json
import requests
import math
import pandas as pd
import os
import datetime
import pytz

df_destinations = pd.read_csv("addresses.csv")
#data.fillna('',inplace=True)

#### set up the origin
origin = '8825 166th Ave NE, Redmond, WA 98052'

#### set up the grocery stores (or other stores) to find nearest of
store_list = ['QFC','Safeway']
default_departure = "Weekdays 20:00"
default_arrival = "Weekdays 16:00"

#### format the origin ####
origin_point = origin.replace(' ','+')

#### initialize a bunch of variables ####
# set up API calls and url parts
api_key = os.environ['GOOG_API']
base_url = 'https://maps.googleapis.com/maps/api/%s/json?'
org_part= 'origin='
mode = 'mode=transit'
dest_part = 'destination='
end_url = 'key='
alternatives = 'alternatives=true'
api_fin = end_url+api_key
# set up final dataframe parts
df_columns = ['destination','travel_method','time_mins','num_busses','direction','time']
df_travel = pd.DataFrame(columns=df_columns)
# time based variables
current_time = datetime.datetime.now()
day = current_time
tz = pytz.timezone('US/Pacific')

#df_destinations = data.append(pd.DataFrame(data={'name':['new_place'],'coords':[origin]})).reset_index().drop(columns=['index'])
#df_destinations = df_destinations[['name','coords']]


#### convert origin to coordinates and find the nearest stores
latlon_url = "https://maps.googleapis.com/maps/api/geocode/json?address="+origin_point+"&key="
url_fin = latlon_url+api_key
result = json.loads(requests.get(url_fin).content)
 
if result['status'] != 'OK':
    print(result['status'])
else: 
    lat = result['results'][0]['geometry']['location']['lat']
    lon = result['results'][0]['geometry']['location']['lng']
    origin_point = str(lat)+","+str(lon)
    ### find nearest grocery stores
    for store in store_list:
        store_url  = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input="+str(store)+"&inputtype=textquery&fields=formatted_address,name,rating&locationbias=circle:2000@"+origin_point+"&key="
        url_fin = store_url+api_key
        result = json.loads(requests.get(url_fin).content)
        if result['status'] != 'OK':
             print(result['status'])
        else:
            content = result['candidates']
            addy = content[0]['formatted_address']
            store_name = content[0]['name']
            # add address to df_destinations
            df_destinations = df_destinations.append(pd.DataFrame(data={'name':[store_name],'coords':[addy],'departure':default_departure,'arrival':default_arrival})).reset_index(drop=True)
            #df_destinations = df_destinations[['name','coords']]


#### melt the dataframe into a one row per time entry
df_m_dest = df_destinations.melt(['name','coords'])
df_m_dest['value'] = df_m_dest['value'].str.split(",")
df_m_dest = df_m_dest.explode('value')
df_m_dest['value'] = df_m_dest['value'].str.strip().str.split(' ')
df_m_dest = df_m_dest[df_m_dest.value.notnull()].reset_index(drop=True)



           
def get_routes(result_routes, direction):
   df_agg = pd.DataFrame(columns=df_columns)
   for routes in result_routes:
       legs = routes['legs'][0]
       steps= legs['steps']
       travel_mins = math.floor(legs['duration']['value']/60)
       num_busses = 0
       travel_list = []
       for step in steps:
           travel_list.append(step['travel_mode'])
           if step['travel_mode'] == 'TRANSIT':
               num_busses += 1        
       travel_mode = min(travel_list)
       data_temp = {'destination':df_m_dest['name'].iloc[i],'travel_method':[travel_mode],'time_mins':[travel_mins],'num_busses':[num_busses]}
       df_agg = df_agg.append(pd.DataFrame(data_temp,columns=df_columns))
       df_temp = df_agg.groupby(['destination','travel_method','num_busses'])['time_mins'].min().to_frame().reset_index(drop=True)
       df_temp['direction'] = direction
       df_temp['time'] = str(df_m_dest['value'].iloc[i][0])+" "+str(df_m_dest['value'].iloc[i][1])
       return df_temp
    


#### begin looping through possible destinations ####
i = 0
while i < len(df_m_dest):
    #### get the travel time ####
    time_of_week = df_m_dest['value'].iloc[i][0]
    hour_min = df_m_dest['value'].iloc[i][1].split(':')
    hour = int(hour_min[0])
    minute = int(hour_min[1])
    
    if time_of_week.lower() == 'weekdays':
        if current_time.isoweekday() in set((6, 7)):
            day += datetime.timedelta(days=8 - day.isoweekday())
    else:
        if current_time.isoweekday() != 6:
            day += datetime.timedelta(days=6 - day.isoweekday())
    
    time = datetime.datetime(year=current_time.year,month=current_time.month,day=current_time.day,hour=hour,minute=minute)
    time = tz.localize(time).timestamp()

    #### get what direction we are going in ####
    #### departure == leaving destination at to return home 
    #### arrival == leaving home to get to destination by
    direction = df_m_dest['variable'].iloc[i]
    
    dest_point = df_m_dest['coords'].iloc[i].replace(' ','+')
    
    if direction == 'departure':
        from_location = dest_point
        to_location = origin_point
    else:
        from_location = origin_point
        to_location = dest_point

    
    #### format the URL ####
    base_fin = base_url%('directions')+org_part+from_location
    dest_fin = dest_part+to_location
    time_value = direction+"_time="+str(int(time))
    
    #### construct the rest of the URL ####
    url ='&'.join([base_fin,dest_fin,mode,alternatives,time_value,api_fin])

    #### get the json from the API call ####
    result = json.loads(requests.get(url).content)

    #### only proceed if everything is green ####
    if result['status'] != 'OK':
        print(result['status'])
        #break
    
    #### begin going through the routes given ####
    df_temp = get_routes(result['routes'], direction)
    df_travel = df_travel.append(df_temp) 
    i += 1
    
df_travel.to_csv("distance_measures.csv",index=False)    



