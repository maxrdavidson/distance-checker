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

df_destinations = pd.read_csv("addresses.csv")

origin = '8825 166th Ave NE, Redmond, WA 98052'

#### format the origin ####
org = origin.replace(' ','+')

#### initialize a bunch of variables ####
api_key = os.environ['GOOG_API']
base_url = 'https://maps.googleapis.com/maps/api/%s/json?'
org_part= 'origin='
mode = 'mode=transit'
dest_part = 'destination='
end_url = 'key='
alternatives = 'alternatives=true'
arrive = 'arrival_time=1587481200'
# departure time is either 4pm workday [0] or noon saturday [1] or arriving at 8am [2] or departing at 11pm saturday [3]
time_set = ['departure_time=1587510000','departure_time=1587236400','arrival_time=1587481200', 'departure_time=1587276000']
base_fin = base_url%('directions')+org_part+org
api_fin = end_url+api_key
df_columns = ['destination','travel_method','time_mins','num_busses','direction']
df_travel = pd.DataFrame(columns=df_columns)



df_destinations = df_destinations.append(pd.DataFrame(data={'name':['new_place'],'coords':[origin]})).reset_index()
df_destinations = df_destinations[['name','coords']]
### find nearest store

### first get lat+lon for origin
latlon_url = "https://maps.googleapis.com/maps/api/geocode/json?address="+org+"&key="
url_fin = latlon_url+api_key
result = json.loads(requests.get(url_fin).content)
 
if result['status'] != 'OK':
    print(result['status'])
else: 
    lat = result['results'][0]['geometry']['location']['lat']
    lon = result['results'][0]['geometry']['location']['lng']
    ### then look up grocery stores
    store_list = ['QFC','Safeway']
    for store in store_list:
        store_url  = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input="+str(store)+"&inputtype=textquery&fields=formatted_address,name,rating&locationbias=circle:2000@"+str(lat)+","+str(lon)+"&key="
        url_fin = store_url+api_key
        result = json.loads(requests.get(url_fin).content)
        if result['status'] != 'OK':
             print(result['status'])
        else:
            content = result['candidates']
            addy = content[0]['formatted_address']
            store_name = content[0]['name']
            # add address to df_destinations
            df_destinations = df_destinations.append(pd.DataFrame(data={'name':[store_name],'coords':[addy]})).reset_index()
            df_destinations = df_destinations[['name','coords']]
            
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
       data_temp = {'destination':df_destinations['name'].iloc[i],'travel_method':[travel_mode],'time_mins':[travel_mins],'num_busses':[num_busses]}
       df_agg = df_agg.append(pd.DataFrame(data_temp,columns=df_columns))
       df_temp = df_agg.groupby(['destination','travel_method','num_busses'])['time_mins'].min().to_frame().reset_index()
       df_temp['direction'] = direction
       return df_temp
    


#### begin looping through possible destinations ####
i = 0
while i < len(df_destinations):

    #### format the destination ####
    base_fin = base_url%('directions')+org_part+org
    dest = df_destinations['coords'].iloc[i].replace(' ','+')
    dest_fin = dest_part+dest
    #### change departure time based on if the destination is work ####
    if df_destinations['name'].iloc[i] == 'work':
        departure = time_set[2]
    else:
        departure = time_set[1]
    #### construct the rest of the URL ####
    url ='&'.join([base_fin,dest_fin,mode,alternatives,departure,api_fin])

    #### get the json from the API call ####
    result = json.loads(requests.get(url).content)

    #### only proceed if everything is green ####
    if result['status'] != 'OK':
        print(result['status'])
        #break
    
    #### begin going through the routes given ####
    df_temp = get_routes(result['routes'], 'leaving')
    df_travel = df_travel.append(df_temp)
     
    ####
    #### Now get the going back home leg ####
    ####
    
    dest_fin = dest_part+org
    base_fin = base_url%('directions')+org_part+dest
    
    #### change departure time based on if the destination is work ####
    if df_destinations['name'].iloc[i] == 'work':
        departure = time_set[0]
    else:
        departure = time_set[3]
    
    url ='&'.join([base_fin,dest_fin,mode,alternatives,departure,api_fin])
    
    #### get the json from the API call ####
    result = json.loads(requests.get(url).content)

    #### only proceed if everything is green ####
    if result['status'] != 'OK':
        print(result['status'])
        #break
        
    #### begin going through the routes given ####
    df_temp = get_routes(result['routes'], 'returning')
    df_travel = df_travel.append(df_temp)
    i += 1
    
    



