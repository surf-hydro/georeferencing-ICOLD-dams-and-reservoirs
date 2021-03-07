# [Description] ------------------------------
# Module name "Geocoding_ICOLD_QA.py"
# This module loops through all geocoding solutions for each ICOLD WRD record (output of Geocoding_ICOLD.py)
# and rank them based on their corresponding QA levels (see Table 5 in Wang et al. (2021). For each unique
# ICOLD WRD record, the geocoding solution with the best possible rank is then written to the output with
# the associated QA label.

# Please note that if the best possible solution does not meet the baseline QA scenario as defined in
# Table 5 of Wang et al. (2021), this ICOLD WRD record will be filtered out and will not be written to the
# output.

# Reference: Wang, J., Walter, B.A., Yao, F., Song, C., Ding, M., Maroof, M.A.S., Zhu, J., Fan, C., Xin, A.,
# McAlister, J.M., Sikder, M.S., Sheng, Y., Allen, G.H., Crétaux, J.-F., and Wada, Y., 2021. GeoDAR:
# Georeferenced global dam and reservoir database for bridging attributes and geolocations. Earth System
# Science Data, in review.

# Script written by: Jida Wang, Kansas State University.
# Last update: March 4, 2021
# Contact: jidawang@ksu.edu; gdbruins@ucla.edu
#---------------------------------------------



# [Setup] -----------------------------------
# Inputs
# 1. geocoded_ICOLD: full path of the geocoded ICOLD WRD.
# This file is the output from Geocoding_ICOLD.py, which is then further expanded with additional address
# components from another round of reverse geocoding before being used here. See Wang et al. (2021) for methods. 
geocoded_ICOLD = r"...\Geocoded_ICOLD_revgeo.xlsx"

# 2. country_lookup_table: full path of the lookup table for country ISO 3166-2 codes (file provided).
country_lookup_table = r'...\Countries_lookup.csv'

# 3. US_state_lookup_table: full path of the lookup table for the ISO 3166-2 codes for US states (file provided). 
US_state_lookup_table = r'...\Countries_lookup.csv'

# 4. Korea_state_lookup_table: full path of the lookup table for South Korean provinces. Some of them are
# spelled differently in between ICOLD WRD and Google Maps. 
Korea_state_lookup_table = r'...\Countries_lookup.csv'

# 5. geocoding_key: user-specific Google Maps API key.
# The API key can be created by following the instruction below:
# https://developers.google.com/maps/documentation/geocoding/get-api-key
geocoding_key = 'Google-Maps-API-Key'

# 6. similarity_threshold: numeric value for the minimum similarity score between two sequences (such as
# dam names from ICOLD WRD and the regional register) that were considered to be equivalent.
similarity_threshold = 5.0/6.0 #close to 85%, which is slightly more lenient than that used for geo-matching
# considering that the spelling variation in WRD and Google Maps (in different regions) could be more evident
# and the outputs from the geocoding API have already gone through a similarity measure.

# Output
# geocoded_ICOLD_QA: full path of the geocoded WRD records after QA filtering. If there are multiple geocoding
# solutions for the same original WRD record in geocoded_ICOLD, the solution with the best possible QA ranking
# will be selected. If the best possible QA ranking does not satisfy the minimum baseline QA scenario (see
# Table 5 in Wang et al. (2021)), this WRD record will not be written to the output.
geocoded_ICOLD_QA = r"...\Geocoded_ICOLD_QA.xlsx"
#---------------------------------------------



# [Script] -----------------------------------
# Import built-in functions and tools
import http, urllib, csv, json, unicodedata, sys, datetime, xlsxwriter, openpyxl
import statistics
from statistics import stdev
from difflib import SequenceMatcher
# Import customized functions (see Preparation and descriptions within "Georeferencing_functions.py"). 
from Georeferencing_functions import remove_accents, similar_v2, damname_similar_v2

print("----- Module Started -----")
print(datetime.datetime.now())
                       
# Read country names and ISO codes
country_ISO_array = []
country_NAME_array = []
country_NAME_array_no_accent = []
with open(country_lookup_CSV, "r") as csvinput:
    for row in csv.reader(csvinput, delimiter=','):
        country_ISO_array.append((row[1]).lower().strip())
        country_NAME_array.append((row[6]).lower().strip())
        country_NAME_array_no_accent.append(remove_accents((row[6]).lower().strip())) #ICOLD NAMES

# Read US state names and ISO codes
state_ISO_array = []
state_NAME_array = []
with open(US_state_lookup_table, "r") as csvinput:
    for row in csv.reader(csvinput, delimiter=','):
        state_ISO_array.append((row[0]).lower().strip())
        state_NAME_array.append((row[2]).lower().strip())

# Read names of South Korean provices used in ICOLD WRD and Google Maps
Korea_states_ICOLD = []
Korea_states_Google = []
with open(Korea_state_lookup_table, "r") as csvinput:
    for row in csv.reader(csvinput, delimiter=','):
        Korea_states_ICOLD.append((row[0]).lower().strip())
        Korea_states_Google.append((row[1]).lower().strip())
      
# Define input spreadsheet (geocoded WRD) and output spreadsheets. ------------------------------------------
infile_obj = openpyxl.load_workbook(geocoded_ICOLD)
infile_sheet = infile_obj.active
outfile_obj = xlsxwriter.Workbook(geocoded_ICOLD_QA)
outfile_sheet = outfile_obj.add_worksheet("Geocoded-WRD-QA")
                      
# Read original WRD records and their IDs (ICOLDIDs)
infile_rows = []
infile_ICOLDIDs = []
for each_row in infile_sheet:
    row = []
    for cell in each_row:
        if cell.value == None:
            row.append('')
        else:
            row.append(str(cell.value))  
    infile_rows.append(row)
    infile_ICOLDIDs.append((row[0]).lower().strip())

# Loop through each geocoded ICOLD WRD record and determine their QA rank. 
considered_IDs = [] # Initiate an array that will be gradually expanded by ICOLD IDs that have been evaluated.
outfile_sheet_row = 0
for ii in range(0, len(infile_ICOLDIDs)):
    row = infile_rows[ii] # Read this ICOLD WRD record
    this_ICOLDID = infile_ICOLDIDs[ii] # Retrieve this ICOLD WRD ID
    
    if ii == 0: #header
        # Write header to the output
        outfile_sheet.write_row(outfile_sheet_row, 0, tuple(row + ['QA_rank']))
        outfile_sheet_row = outfile_sheet_row + 1
    else:
        # Retrieve WRD attributes. 
        dam_name = row[23].lower().strip()
        dam_other_name = row[26].lower().strip()
        reservoir_name = row[31].lower().strip()
        state_province = row[38].lower().strip()
        town_original = row[24].lower().strip()
        country = row[10].lower().strip()
        country_index = [i for i, x in enumerate(country_NAME_array) if x == country]
        this_country_ISO = country_ISO_array[country_index[0]]       
        
        if (this_ICOLDID not in considered_IDs): # If this WRD record has not been evaluated.
            considered_IDs.append(this_ICOLDID)               

           # Modify country names for certain districts/territories which are considered as a country in Google Maps but part of another country in ICOLD WRD. 
            if state_province == 'taiwan': # In this example, Google considers Taiwan as a country, but ICOLD considers it as a province of China. 
                this_country_ISO = 'tw' # Unify the country name based on Google standard just for consistency. 
                country = 'taiwan'
            # Similarly, unify the following to Google standard.
            if state_province == 'hongkong': 
                this_country_ISO = 'hk'
                country = 'hongkong'
            if state_province == 'faroe islands': 
                this_country_ISO = 'fo'
                country = 'faroe islands'
            if state_province == 'greenland':
                this_country_ISO = 'gl'
                country = 'greenland'
            if state_province == 'puerto rico':
                this_country_ISO = 'pr'
                country = 'puerto rico'
            if state_province == 'reunion':  
                this_country_ISO = 're'
                country = 'réunion'
            if state_province == 'guadeloupe':  
                this_country_ISO = 'gp' 
                country = 'guadeloupe'
            if state_province == 'martinique':  
                this_country_ISO = 'mq' 
                country = 'martinique'
            if state_province == 'mayotte':  
                this_country_ISO = 'yt' 
                country = 'mayotte'
            if state_province == 'isle of man':  
                this_country_ISO = 'im' 
                country = 'isle of man'
            if state_province == 'jersey':  
                this_country_ISO = 'je' 
                country = 'jersey'
            if state_province == 'guernsey':  
                this_country_ISO = 'gg' 
                country = 'guernsey'
            if state_province == 'guam':  
                this_country_ISO = 'gu' 
                country = 'guam'
            administrative_components = 'country:' + urllib.parse.quote(this_country_ISO) # Format the country component

            # Modify state/province names in the following regions so that their spellings are more consistent with those in Google Maps.  
            if len(state_province)>=4:
                if state_province[-4:] == '.ssr': # Indicating a state in the former Soviet Union
                    state_province = '' # Now an independent country 
            if state_province == 'former yugoslav rep. of macedonia' or state_province == 'mold.' or state_province == 'tadjik.' or \
                            state_province == 'ukr.' or state_province == 'ukraine' or state_province == 'uzbek.' or \
                            state_province == 'argentina / uruguay' or state_province == 'argentina/paraguay' or state_province == 'zambia / zimbabwe':
                state_province = '' # Other similiar sitautions and probably mistakes in state/province assignments. 
            if state_province == 'daghest.': # Use full spelling
                state_province = 'daghestan'
            if '/' in state_province: # If containing two states, use the first state
                state_province = (state_province.split('/')[0]).strip()
            if country == 'ireland': # delete 'co.'
                state_province = state_province[3:len(state_province)]
            if country == 'finland':
            # Provinces in WRD: ['e', 'm', 'n', 's', 'se', 'sw', 'w']. Not sure what they mean (Google does not use such provinces).
                state_province = ''
            if country == 'chile':
            # Provinces in WRD: ['atamaca', 'i región', 'ii región', 'iii región', 'iv región', 'región metropolitana', 'v región', 'vi región', 'vii región', 'viii región']
                if state_province == 'i región':
                    state_province = 'tarapacá region'
                if state_province == 'ii región':
                    state_province = 'antofagasta region'
                if state_province == 'iii región' or state_province == 'atacama':
                    state_province = 'atacama region'
                if state_province == 'iv región':
                    state_province = 'coquimbo region'
                # 'región metropolitana' is consistent. 
                if state_province == 'v región':
                    state_province = 'valparaiso region'
                if state_province == 'vi región':
                    state_province = "o'higgins region"
                if state_province == 'vii región':
                    state_province = "maule region"
                if state_province == 'viii región':
                    state_province = "bío bío region"
            if country == 'canada':
            # Provinces in WRD: ['alta', 'bc', 'man', 'nb', 'nb,maine,usa', 'nfld', 'ns', 'nwt', 'ont', 'ont/que', 'qc', 'qc/ont', 'sask', 'yukon']
                if state_province == 'alta':
                    state_province = 'ab'
                if state_province == 'man':
                    state_province = 'mb'
                if state_province == 'nfld':
                    state_province = 'nl'
                if state_province == 'nwt':
                    state_province = 'nt'
                if state_province == 'ont':
                    state_province = 'on'
                #if state_province == 'ont/que':
                #    state_province = 'on'
                #if state_province == 'qc/ont':
                #    state_province = 'qc'
                if state_province == 'sask':
                    state_province = 'sk'
                if state_province == 'yukon':
                    state_province = 'yt' 
                if state_province == 'nb,maine,usa':
                    state_province = 'nb'
            if country == 'sri lanka':
            # Provinces in WRD: ['', 'cp', 'ep', 'ncp', 'np', 'nwp', 'sab.p', 'sp', 'up', 'uva', 'wp']
                if state_province == 'cp':
                    state_province = 'central province'
                if state_province == 'ep':
                    state_province = 'eastern province'
                if state_province == 'ncp':
                    state_province = 'north central province'
                if state_province == 'np':
                    state_province = 'north province'
                if state_province == 'nwp':
                    state_province = 'north western  province'
                if state_province == 'sab.p':
                    state_province = 'sabaragamuwa province'
                if state_province == 'sp':
                    state_province = 'southern province'
                if state_province == 'up':
                    state_province = 'uva province'
                if state_province == 'uva':
                    state_province = 'uva province'
                if state_province == 'wp':
                    state_province = 'western province'
            if country == 'botswana':
            # Provinces in WRD: ['central', 'kgatleng', 'ne', 'se'], in Google ['central district', 'kgatleng district', 'north-east district', 'south-east district']
                if state_province == 'central':
                    state_province = 'central district'
                if state_province == 'kgatleng':
                    state_province = 'kgatleng district'
                if state_province == 'ne':
                    state_province = 'north-east district'
                if state_province == 'se':
                    state_province = 'south-east district'
            if country == 'australia':
            # Provinces in WRD: ['australian capital territory', 'new south wales', 'new south west australiales', 'northern territory', \
            #'nothern territory', 'queensland', 'south australia', 'tasmania', 'victoria', 'west australia'] #corrected below.
                if state_province == 'new south west australiales':
                    state_province = 'new south wales'
                if state_province == 'nothern territory':
                    state_province = 'northern territory'
                if state_province == 'west australia':
                    state_province = 'western australia'
            # Invalidate state/province names in WRD if the names appear to be country names (except the situations in the IF statement)
            if state_province != '':
                if state_province != 'taiwan' and state_province != 'hongkong' and state_province != 'faroe islands' \
                   and state_province != 'greenland' and state_province != 'puerto rico' \
                   and state_province != 'reunion' and state_province != 'guadeloupe' and state_province != 'martinique' and state_province != 'mayotte' \
                   and state_province != 'isle of man' and state_province != 'jersey' and state_province != 'guernsey' and state_province != 'guam' \
                   and ((state_province == 'niger' and this_country_ISO == 'ng') == False) and ((state_province == 'luxembourg' and this_country_ISO == 'be') == False) \
                   and ((state_province == 'georgia' and this_country_ISO == 'us') == False): # For the last case, "Georgia" can also be a country.
                    check_if_state_is_a_country_name = [i for i, x in enumerate(country_NAME_array_no_accent) if x == remove_accents(state_province)]
                    if len(check_if_state_is_a_country_name) > 0:
                        state_province = ''
            # Modify province names in South Korea
            if state_province != '' and (this_country_ISO == 'kr' or this_country_ISO == 'kp'):
                state_index = [i for i, x in enumerate(Korea_states_ICOLD) if x == state_province]
                state_province = Korea_states_Google[state_index[0]]
            # Use ISO codes for US states in order to increase geocoding accuracy. 
            state_province_addr = state_province
            if this_country_ISO == 'us':
                state_index = [i for i, x in enumerate(state_NAME_array) if x == state_province]
                if len(state_index)>0:
                    state_province_addr = state_ISO_array[state_index[0]]              

            # Formulate address inputs for geocoding (see Table 4 in Wang et al. (2021))
            reservoir_norm = 1
            if len(reservoir_name)>10:
                if reservoir_name[-10:] == ' reservoir' or reservoir_name[:10] == 'reservoir ' or (' reservoir ' in reservoir_name):
                    reservoir_norm = 0
                elif reservoir_name[-5:] == ' lake' or reservoir_name[:5] == 'lake ' or (' lake ' in reservoir_name):
                    reservoir_norm = 0
            elif len(reservoir_name)>5:
                if reservoir_name[-5:] == ' lake' or reservoir_name[:5] == 'lake ' or (' lake ' in reservoir_name):
                    reservoir_norm = 0
            dam_norm = 1
            if len(dam_name)>4:
                if dam_name[-4:] == ' dam' or dam_name[:4] == 'dam ' or (' dam ' in dam_name):
                    dam_norm = 0
            otherdam_norm = 1
            if len(dam_other_name)>4:
                if dam_other_name[-4:] == ' dam' or dam_other_name[:4] == 'dam ' or (' dam ' in dam_other_name):
                    otherdam_norm = 0
            # Generate the address list (which contains different scenarios of formatted addresses)
            Sc_list = []
            if dam_name == '' and dam_other_name == '': # Only reservoir name exists
                if reservoir_norm == 0:
                    if state_province != '':
                        Sc_list.append([reservoir_name, state_province_addr])
                    Sc_list.append([reservoir_name])
                else: # Meaning there is no 'reservoir' in the name (reservoir_norm == 1)         
                    if state_province != '':
                        Sc_list.append([reservoir_name+' reservoir', state_province_addr])
                    Sc_list.append([reservoir_name+' reservoir'])
                    if state_province != '':
                        Sc_list.append([reservoir_name+' dam', state_province_addr])
                    Sc_list.append([reservoir_name+' dam'])
                    if state_province != '':
                        Sc_list.append([reservoir_name+' lake', state_province_addr])
                    Sc_list.append([reservoir_name+' lake'])
                    Sc_list.append([reservoir_name])
            elif dam_name == '' and reservoir_name == '': # Only dam_other_name exists
                if otherdam_norm == 0:
                    if state_province != '':
                        Sc_list.append([dam_other_name, state_province_addr])
                    Sc_list.append([dam_other_name])
                else:
                    if state_province != '':
                        Sc_list.append([dam_other_name+' dam', state_province_addr])
                    Sc_list.append([dam_other_name+' dam'])
                    if state_province != '':
                        Sc_list.append([dam_other_name+' reservoir', state_province_addr])
                    Sc_list.append([dam_other_name+' reservoir'])
                    if state_province != '':
                        Sc_list.append([dam_other_name+' lake', state_province_addr])
                    Sc_list.append([dam_other_name+' lake'])
                    Sc_list.append([dam_other_name])
            elif dam_other_name == '' and reservoir_name == '': # Only dam_name exists
                if dam_norm == 0:
                    if state_province != '':
                        Sc_list.append([dam_name, state_province_addr])
                    Sc_list.append([dam_name])
                else:
                    if state_province != '':
                        Sc_list.append([dam_name+' dam', state_province_addr])
                    Sc_list.append([dam_name+' dam'])
                    if state_province != '':
                        Sc_list.append([dam_name+' reservoir', state_province_addr])
                    Sc_list.append([dam_name+' reservoir'])
                    if state_province != '':
                        Sc_list.append([dam_name+' lake', state_province_addr])
                    Sc_list.append([dam_name+' lake'])
                    Sc_list.append([dam_name])
            elif dam_name != '' and dam_other_name != '' and reservoir_name == '':
                if dam_norm == 0:
                    if state_province != '':
                        Sc_list.append([dam_name, state_province_addr])
                    Sc_list.append([dam_name])
                else:
                    if state_province != '':
                        Sc_list.append([dam_name+' dam', state_province_addr])
                    Sc_list.append([dam_name+' dam'])
                if otherdam_norm == 0:
                    if state_province != '':
                        Sc_list.append([dam_other_name, state_province_addr])
                    Sc_list.append([dam_other_name])
                else:
                    if state_province != '':
                        Sc_list.append([dam_other_name+' dam', state_province_addr])
                    Sc_list.append([dam_other_name+' dam'])
                if dam_norm == 1:
                    if state_province != '':
                        Sc_list.append([dam_name+' reservoir', state_province_addr])
                    Sc_list.append([dam_name+' reservoir'])
                if otherdam_norm == 1: 
                    if state_province != '':
                        Sc_list.append([dam_other_name+' reservoir', state_province_addr])
                    Sc_list.append([dam_other_name+' reservoir'])
                if dam_norm == 1:
                    if state_province != '':
                        Sc_list.append([dam_name+' lake', state_province_addr])
                    Sc_list.append([dam_name+' lake'])
                if otherdam_norm == 1:   
                    if state_province != '':
                        Sc_list.append([dam_other_name+' lake', state_province_addr])
                    Sc_list.append([dam_other_name+' lake'])
                if dam_norm == 1:
                    Sc_list.append([dam_name])
                if otherdam_norm == 1:
                    Sc_list.append([dam_other_name])
            elif dam_name != '' and dam_other_name == '' and reservoir_name != '':
                if dam_norm == 0:
                    if state_province != '':
                        Sc_list.append([dam_name, state_province_addr])
                    Sc_list.append([dam_name])
                else:
                    if state_province != '':
                        Sc_list.append([dam_name+' dam', state_province_addr])
                    Sc_list.append([dam_name+' dam'])
                if reservoir_norm == 0:
                    if state_province != '':
                        Sc_list.append([reservoir_name, state_province_addr])
                    Sc_list.append([reservoir_name])
                else:
                    if state_province != '':
                        Sc_list.append([reservoir_name+' reservoir', state_province_addr])
                    Sc_list.append([reservoir_name+' reservoir'])
                if dam_norm == 1:
                    if state_province != '':
                        Sc_list.append([dam_name+' reservoir', state_province_addr])
                    Sc_list.append([dam_name+' reservoir'])
                if reservoir_norm == 1:
                    if state_province != '':
                        Sc_list.append([reservoir_name+' dam', state_province_addr])
                    Sc_list.append([reservoir_name+' dam'])                   
                    if state_province != '':
                        Sc_list.append([reservoir_name+' lake', state_province_addr])
                    Sc_list.append([reservoir_name+' lake'])
                if dam_norm == 1:
                    if state_province != '':
                        Sc_list.append([dam_name+' lake', state_province_addr])
                    Sc_list.append([dam_name+' lake'])
                    Sc_list.append([dam_name])
                if reservoir_norm == 1:
                    Sc_list.append([reservoir_name])
            elif dam_name == '' and dam_other_name != '' and reservoir_name != '':
                if otherdam_norm == 0:
                    if state_province != '':
                        Sc_list.append([dam_other_name, state_province_addr])
                    Sc_list.append([dam_other_name])
                else:
                    if state_province != '':
                        Sc_list.append([dam_other_name+' dam', state_province_addr])
                    Sc_list.append([dam_other_name+' dam'])
                if reservoir_norm == 0:
                    if state_province != '':
                        Sc_list.append([reservoir_name, state_province_addr])
                    Sc_list.append([reservoir_name])
                else:
                    if state_province != '':
                        Sc_list.append([reservoir_name+' reservoir', state_province_addr])
                    Sc_list.append([reservoir_name+' reservoir'])
                if otherdam_norm == 1:
                    if state_province != '':
                        Sc_list.append([dam_other_name+' reservoir', state_province_addr])
                    Sc_list.append([dam_other_name+' reservoir'])
                if reservoir_norm == 1:    
                    if state_province != '':
                        Sc_list.append([reservoir_name+' dam', state_province_addr])
                    Sc_list.append([reservoir_name+' dam'])
                    if state_province != '':
                        Sc_list.append([reservoir_name+' lake', state_province_addr])
                    Sc_list.append([reservoir_name+' lake'])
                if otherdam_norm == 1:
                    if state_province != '':
                        Sc_list.append([dam_other_name+' lake', state_province_addr])
                    Sc_list.append([dam_other_name+' lake'])
                    Sc_list.append([dam_other_name])
                if reservoir_norm == 1:
                    Sc_list.append([reservoir_name])
            elif dam_name != '' and dam_other_name != '' and reservoir_name != '':
                if dam_norm == 0:
                    if state_province != '':
                        Sc_list.append([dam_name, state_province_addr])
                    Sc_list.append([dam_name])
                else:
                    if state_province != '':
                        Sc_list.append([dam_name+' dam', state_province_addr])
                    Sc_list.append([dam_name+' dam'])
                if otherdam_norm == 0:
                    if state_province != '':
                        Sc_list.append([dam_other_name, state_province_addr])
                    Sc_list.append([dam_other_name])
                else:
                    if state_province != '':
                        Sc_list.append([dam_other_name+' dam', state_province_addr])
                    Sc_list.append([dam_other_name+' dam'])
                if reservoir_norm == 0:
                    if state_province != '':
                        Sc_list.append([reservoir_name, state_province_addr])
                    Sc_list.append([reservoir_name]) 
                else:
                    if state_province != '':
                        Sc_list.append([reservoir_name+' reservoir', state_province_addr])
                    Sc_list.append([reservoir_name+' reservoir'])
                if dam_norm == 1:
                    if state_province != '':
                        Sc_list.append([dam_name+' reservoir', state_province_addr])
                    Sc_list.append([dam_name+' reservoir'])
                if otherdam_norm == 1:
                    if state_province != '':
                        Sc_list.append([dam_other_name+' reservoir', state_province_addr])
                    Sc_list.append([dam_other_name+' reservoir'])
                if reservoir_norm == 1:
                    if state_province != '':
                        Sc_list.append([reservoir_name+' dam', state_province_addr])
                    Sc_list.append([reservoir_name+' dam'])
                    if state_province != '':
                        Sc_list.append([reservoir_name+' lake', state_province_addr])
                    Sc_list.append([reservoir_name+' lake'])
                if dam_norm == 1:
                    if state_province != '':
                        Sc_list.append([dam_name+' lake', state_province_addr])
                    Sc_list.append([dam_name+' lake'])
                if otherdam_norm == 1:
                    if state_province != '':
                        Sc_list.append([dam_other_name+' lake', state_province_addr])
                    Sc_list.append([dam_other_name+' lake'])
                if dam_norm == 1:
                    Sc_list.append([dam_name])
                if otherdam_norm == 1:
                    Sc_list.append([dam_other_name])
                if reservoir_norm == 1:
                    Sc_list.append([reservoir_name])

            # Filter geocoding solutions for this ICOLD ID (WRD record)
            # C1 (as in Table 5, Wang et al. (2021)): 1, 1.1, 1.2, 1.5 (here below)
            # C2: 2, 2.5
            # C3: 3, 3.5, 4, 4.5
            # C4: 5, 5.5, 6, 6.5
            # C5: 7, 7.5, 8, 8.5
            if this_country_ISO != 'cn':
                # If the country is not China, use a slightly adjusted order of the address scenario in QA ranking.
                # Here we increase the iteration level of country name from level 3 (as used in geocoding) now to
                # level 1. In other words, for each comibination of dam/reservoir name and state/province, we first
                # include and then exclude the country name. This seems to lead to a more accurate geocoding result
                # in a faster way. This decision was based on experimentations, and may not always reflect the cases
                # all the time. Such details can be adjusted based on user discretion, and may not affect too much
                # the overall result and conclusion. 
                Sc_list_cleaned = []
                for this_scenario in Sc_list:
                    text_encoded_addr = ''
                    # Add ", " between each element to generate encoded_addr (searching SQL)
                    for this_element in this_scenario:
                        if this_element != '': # If this element is not blank
                            text_encoded_addr = text_encoded_addr + this_element + ', '
                    text_encoded_addr = text_encoded_addr[0 : len(text_encoded_addr)-2] # Delete the ending ', '
                    Sc_list_cleaned.append(text_encoded_addr)
                            
                # Retrieve all geocoded WRD records that share the same ICOLDID (this_ICOLDID)
                same_ICOLDID_indices = [i for i, x in enumerate(infile_ICOLDIDs) if x == this_ICOLDID]
                # Retrieve geocoding information for these records
                local_addresses = []
                local_encoded_addresses = []
                local_match = []
                local_scenarios = []
                local_geocoded_dam_name = []
                for ID_index in same_ICOLDID_indices:
                    local_addresses.append(infile_rows[ID_index][61])
                    local_encoded_addresses.append(infile_rows[ID_index][62])
                    local_match.append((infile_rows[ID_index][82]).lower().strip())
                    local_scenarios.append((infile_rows[ID_index][83]).lower().strip())
                    local_geocoded_dam_name.append((infile_rows[ID_index][90]).lower().strip())

                # Rank QA levels of each of the geocoded results associated with the same ICOLD ID, and write the best one to the output. 
                good_passed = 0 # "0" meaning the best possible rank has not been reached. 
                GOOD_ICOLDID_indices = [] # Array containing indices for this QA rank. 
                GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'complete-match'] 
                if state_province != '' and town_original != '':              
                    QA_rank = [1]
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if x == 'in-country in-state in-town' or x == 'in-country in-state in-town-2' \
                                              or x == 'in-country in-state-2 in-town' or x == 'in-country in-state-2 in-town-2']
                elif state_province != '' and town_original == '':
                    QA_rank = [1.1]
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if x == 'in-country in-state unknown-town' or x == 'in-country in-state-2 unknown-town']
                elif state_province == '' and town_original != '':
                    QA_rank = [1.1]
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if x == 'in-country unknown-state in-town' or x == 'in-country unknown-state in-town-2']
                elif state_province == '' and town_original == '':
                    QA_rank = [1.2]
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if x == 'in-country unknown-state unknown-town']
                else:
                    GOOD_ICOLDID_indices_2 = []
                GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                # Check if records for this QA_rank exists or not. 
                if len(GOOD_ICOLDID_indices) > 0: # Meaning this QA_rank exists. 
                    GOOD_local_addresses_rank = []
                    GOOD_local_dam_name_pass = []
                    for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                        rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                        if '&components=country:' in local_encoded_addresses[GOOD_ICOLDID_index]:
                            GOOD_local_addresses_rank.append(rank_index[0])
                        else:
                            GOOD_local_addresses_rank.append(rank_index[0]+0.1) # To lower the rank a little. 
                        GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                    # Rank the indices based on GOOD_local_addresses_rank
                    ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                    if max(GOOD_local_dam_name_pass) == 1: # Name matches
                        good_passed = 1
                        for this_rank_index in ranked_indices:
                            if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                # Write the result with the best address ranking to the output
                                outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                outfile_sheet_row = outfile_sheet_row + 1
                                break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [1.5]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'partial-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if \
                                              x == 'in-country in-state in-town' or \
                                              x == 'in-country in-state in-town-2' or \
                                              x == 'in-country in-state-2 in-town' or \
                                              x == 'in-country in-state-2 in-town-2']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2)) 
                    if len(GOOD_ICOLDID_indices) > 0: 
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            if '&components=country:' in local_encoded_addresses[GOOD_ICOLDID_index]:
                                GOOD_local_addresses_rank.append(rank_index[0])
                            else:
                                GOOD_local_addresses_rank.append(rank_index[0]+0.1)
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1: #name match exists
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [2]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'complete-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if \
                                              x == 'in-country in-state out-town' or \
                                              x == 'in-country in-state unknown-town' or \
                                              x == 'in-country in-state-2 out-town' or \
                                              x == 'in-country in-state-2 unknown-town']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            if '&components=country:' in local_encoded_addresses[GOOD_ICOLDID_index]:
                                GOOD_local_addresses_rank.append(rank_index[0])
                            else:
                                GOOD_local_addresses_rank.append(rank_index[0]+0.1)
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [2.5]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'partial-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if \
                                              x == 'in-country in-state out-town' or \
                                              x == 'in-country in-state unknown-town' or \
                                              x == 'in-country in-state-2 out-town' or \
                                              x == 'in-country in-state-2 unknown-town']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            if '&components=country:' in local_encoded_addresses[GOOD_ICOLDID_index]:
                                GOOD_local_addresses_rank.append(rank_index[0])
                            else:
                                GOOD_local_addresses_rank.append(rank_index[0]+0.1)
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [3]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'complete-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if \
                                              x == 'in-country unknown-state in-town' or \
                                              x == 'in-country unknown-state in-town-2']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            if '&components=country:' in local_encoded_addresses[GOOD_ICOLDID_index]:
                                GOOD_local_addresses_rank.append(rank_index[0])
                            else:
                                GOOD_local_addresses_rank.append(rank_index[0]+0.1)
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [3.5]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'partial-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if \
                                              x == 'in-country unknown-state in-town' or \
                                              x == 'in-country unknown-state in-town-2']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            if '&components=country:' in local_encoded_addresses[GOOD_ICOLDID_index]:
                                GOOD_local_addresses_rank.append(rank_index[0])
                            else:
                                GOOD_local_addresses_rank.append(rank_index[0]+0.1)
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [4]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'complete-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if \
                                              x == 'in-country out-state in-town' or \
                                              x == 'in-country out-state in-town-2']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            if '&components=country:' in local_encoded_addresses[GOOD_ICOLDID_index]:
                                GOOD_local_addresses_rank.append(rank_index[0])
                            else:
                                GOOD_local_addresses_rank.append(rank_index[0]+0.1)
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [4.5]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'partial-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if \
                                              x == 'in-country out-state in-town' or \
                                              x == 'in-country out-state in-town-2']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            if '&components=country:' in local_encoded_addresses[GOOD_ICOLDID_index]:
                                GOOD_local_addresses_rank.append(rank_index[0])
                            else:
                                GOOD_local_addresses_rank.append(rank_index[0]+0.1)
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. --------------------------------
                    QA_rank = [5]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'complete-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if \
                                              x == 'in-country unknown-state out-town' or \
                                              x == 'in-country unknown-state unknown-town']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            if '&components=country:' in local_encoded_addresses[GOOD_ICOLDID_index]:
                                GOOD_local_addresses_rank.append(rank_index[0])
                            else:
                                GOOD_local_addresses_rank.append(rank_index[0]+0.1)
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [5.5]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'partial-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if \
                                              x == 'in-country unknown-state out-town' or \
                                              x == 'in-country unknown-state unknown-town']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            if '&components=country:' in local_encoded_addresses[GOOD_ICOLDID_index]:
                                GOOD_local_addresses_rank.append(rank_index[0])
                            else:
                                GOOD_local_addresses_rank.append(rank_index[0]+0.1)
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [6]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'complete-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if \
                                              x == 'in-country out-state out-town' or \
                                              x == 'in-country out-state unknown-town']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            if '&components=country:' in local_encoded_addresses[GOOD_ICOLDID_index]:
                                GOOD_local_addresses_rank.append(rank_index[0])
                            else:
                                GOOD_local_addresses_rank.append(rank_index[0]+0.1)
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [6.5]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'partial-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if \
                                              x == 'in-country out-state out-town' or \
                                              x == 'in-country out-state unknown-town']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            if '&components=country:' in local_encoded_addresses[GOOD_ICOLDID_index]:
                                GOOD_local_addresses_rank.append(rank_index[0])
                            else:
                                GOOD_local_addresses_rank.append(rank_index[0]+0.1)
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [7]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'complete-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if x[0:16] == 'unknown-country ']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            if '&components=country:' in local_encoded_addresses[GOOD_ICOLDID_index]:
                                GOOD_local_addresses_rank.append(rank_index[0])
                            else:
                                GOOD_local_addresses_rank.append(rank_index[0]+0.1)
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [7.5]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'partial-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if x[0:16] == 'unknown-country ']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            if '&components=country:' in local_encoded_addresses[GOOD_ICOLDID_index]:
                                GOOD_local_addresses_rank.append(rank_index[0])
                            else:
                                GOOD_local_addresses_rank.append(rank_index[0]+0.1)
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [8]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'complete-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if x[0:12] == 'out-country ']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            if '&components=country:' in local_encoded_addresses[GOOD_ICOLDID_index]:
                                GOOD_local_addresses_rank.append(rank_index[0])
                            else:
                                GOOD_local_addresses_rank.append(rank_index[0]+0.1)
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [8.5]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'partial-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if x[0:12] == 'out-country ']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            if '&components=country:' in local_encoded_addresses[GOOD_ICOLDID_index]:
                                GOOD_local_addresses_rank.append(rank_index[0])
                            else:
                                GOOD_local_addresses_rank.append(rank_index[0]+0.1)
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached.
                    # The remaining geocoded records (QA_rank = 9) are considered to be unsuccessful and errorneous.
                    # They will not participate into manual quality control (QC). 
                    QA_rank = [9]  
            else:
                # If the country is China, use the original address order (as below) in QA ranking.
                Sc_list_1 = []
                for Sc_list_unit in Sc_list:
                    Sc_list_1.append(Sc_list_unit)
                Sc_list_1_len = len(Sc_list_1)
                for this_Sc_unit in Sc_list_1:
                    Sc_list.append(this_Sc_unit)
                Sc_list_cleaned = []
                for here_i in range(len(Sc_list)):
                    text_encoded_addr = ''
                    this_scenario = Sc_list[here_i]
                    for this_element in this_scenario:
                        if this_element != '': # If this element is not blank
                            text_encoded_addr = text_encoded_addr + this_element + ', '
                    # Delete the ending ', '
                    text_encoded_addr = text_encoded_addr[0 : len(text_encoded_addr)-2]
                    if here_i < Sc_list_1_len:
                        encoded_addr = urllib.parse.quote(text_encoded_addr) + '&components=' + administrative_components
                    else:
                        encoded_addr = urllib.parse.quote(text_encoded_addr)
                    Sc_list_cleaned.append(encoded_addr)
                            
                same_ICOLDID_indices = [i for i, x in enumerate(infile_ICOLDIDs) if x == this_ICOLDID]
                local_addresses = []
                local_match = []
                local_scenarios = []
                local_geocoded_dam_name = []
                for ID_index in same_ICOLDID_indices:
                    local_addresses.append(infile_rows[ID_index][62]) 
                    local_match.append((infile_rows[ID_index][82]).lower().strip())
                    local_scenarios.append((infile_rows[ID_index][83]).lower().strip())
                    local_geocoded_dam_name.append((infile_rows[ID_index][90]).lower().strip())

                # Rank QA levels of each of the geocoded results associated with the same ICOLD ID, and write the best one to the output. 
                good_passed = 0 # "0" meaning the best possible rank has not been reached. 
                GOOD_ICOLDID_indices = [] # Array containing indices for this QA rank. 
                GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'complete-match'] 
                if state_province != '' and town_original != '':              
                    QA_rank = [1]
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if x == 'in-country in-state in-town' or x == 'in-country in-state in-town-2' \
                                              or x == 'in-country in-state-2 in-town' or x == 'in-country in-state-2 in-town-2']
                elif state_province != '' and town_original == '':
                    QA_rank = [1.1]
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if x == 'in-country in-state unknown-town' or x == 'in-country in-state-2 unknown-town']
                elif state_province == '' and town_original != '':
                    QA_rank = [1.1]
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if x == 'in-country unknown-state in-town' or x == 'in-country unknown-state in-town-2']
                elif state_province == '' and town_original == '':
                    QA_rank = [1.2]
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if x == 'in-country unknown-state unknown-town']
                else:
                    GOOD_ICOLDID_indices_2 = []
                GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                # Check if records for this QA_rank exists or not. 
                if len(GOOD_ICOLDID_indices) > 0: # Meaning this QA_rank exists. 
                    GOOD_local_addresses_rank = []
                    GOOD_local_dam_name_pass = []
                    for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                        rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                        GOOD_local_addresses_rank.append(rank_index[0])
                        GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                    # Rank the indices based on GOOD_local_addresses_rank
                    ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                    if max(GOOD_local_dam_name_pass) == 1: # Name matches
                        good_passed = 1
                        for this_rank_index in ranked_indices:
                            if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                # Write the result with the best address ranking to the output
                                outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                outfile_sheet_row = outfile_sheet_row + 1
                                break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [1.5]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'partial-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if \
                                              x == 'in-country in-state in-town' or \
                                              x == 'in-country in-state in-town-2' or \
                                              x == 'in-country in-state-2 in-town' or \
                                              x == 'in-country in-state-2 in-town-2']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2)) 
                    if len(GOOD_ICOLDID_indices) > 0: 
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            GOOD_local_addresses_rank.append(rank_index[0])
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1: #name match exists
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [2]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'complete-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if \
                                              x == 'in-country in-state out-town' or \
                                              x == 'in-country in-state unknown-town' or \
                                              x == 'in-country in-state-2 out-town' or \
                                              x == 'in-country in-state-2 unknown-town']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            GOOD_local_addresses_rank.append(rank_index[0])
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [2.5]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'partial-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if \
                                              x == 'in-country in-state out-town' or \
                                              x == 'in-country in-state unknown-town' or \
                                              x == 'in-country in-state-2 out-town' or \
                                              x == 'in-country in-state-2 unknown-town']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            GOOD_local_addresses_rank.append(rank_index[0])
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [3]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'complete-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if \
                                              x == 'in-country unknown-state in-town' or \
                                              x == 'in-country unknown-state in-town-2']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            GOOD_local_addresses_rank.append(rank_index[0])
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [3.5]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'partial-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if \
                                              x == 'in-country unknown-state in-town' or \
                                              x == 'in-country unknown-state in-town-2']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            GOOD_local_addresses_rank.append(rank_index[0])
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [4]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'complete-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if \
                                              x == 'in-country out-state in-town' or \
                                              x == 'in-country out-state in-town-2']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            GOOD_local_addresses_rank.append(rank_index[0])
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [4.5]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'partial-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if \
                                              x == 'in-country out-state in-town' or \
                                              x == 'in-country out-state in-town-2']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            GOOD_local_addresses_rank.append(rank_index[0])
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. --------------------------------
                    QA_rank = [5]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'complete-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if \
                                              x == 'in-country unknown-state out-town' or \
                                              x == 'in-country unknown-state unknown-town']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            GOOD_local_addresses_rank.append(rank_index[0])
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [5.5]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'partial-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if \
                                              x == 'in-country unknown-state out-town' or \
                                              x == 'in-country unknown-state unknown-town']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            GOOD_local_addresses_rank.append(rank_index[0])
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [6]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'complete-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if \
                                              x == 'in-country out-state out-town' or \
                                              x == 'in-country out-state unknown-town']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            GOOD_local_addresses_rank.append(rank_index[0])
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [6.5]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'partial-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if \
                                              x == 'in-country out-state out-town' or \
                                              x == 'in-country out-state unknown-town']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            GOOD_local_addresses_rank.append(rank_index[0])
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [7]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'complete-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if x[0:16] == 'unknown-country ']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            GOOD_local_addresses_rank.append(rank_index[0])
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [7.5]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'partial-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if x[0:16] == 'unknown-country ']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            GOOD_local_addresses_rank.append(rank_index[0])
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [8]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'complete-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if x[0:12] == 'out-country ']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            GOOD_local_addresses_rank.append(rank_index[0])
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached. 
                    QA_rank = [8.5]
                    GOOD_ICOLDID_indices_1 = [i for i, x in enumerate(local_match) if x == 'partial-match']    
                    GOOD_ICOLDID_indices_2 = [i for i, x in enumerate(local_scenarios) if x[0:12] == 'out-country ']
                    GOOD_ICOLDID_indices = list(set(GOOD_ICOLDID_indices_1) & set(GOOD_ICOLDID_indices_2))
                    if len(GOOD_ICOLDID_indices) > 0:
                        GOOD_local_addresses_rank = []
                        GOOD_local_dam_name_pass = []
                        for GOOD_ICOLDID_index in GOOD_ICOLDID_indices:
                            rank_index = [i for i, x in enumerate(Sc_list_cleaned) if x == local_addresses[GOOD_ICOLDID_index]] 
                            GOOD_local_addresses_rank.append(rank_index[0])
                            GOOD_local_dam_name_pass.append(damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, local_geocoded_dam_name[GOOD_ICOLDID_index], this_country_ISO))        
                        # Rank the indices based on GOOD_local_addresses_rank
                        ranked_indices = [i[0] for i in sorted(enumerate(GOOD_local_addresses_rank), key=lambda x:x[1])]
                        if max(GOOD_local_dam_name_pass) == 1:
                            good_passed = 1
                            for this_rank_index in ranked_indices:
                                if GOOD_local_dam_name_pass[this_rank_index] == 1:
                                    final_index = same_ICOLDID_indices[GOOD_ICOLDID_indices[this_rank_index]]
                                    # Write the result with this best address ranking to the output
                                    outfile_sheet.write_row(outfile_sheet_row, 0, tuple(infile_rows[final_index] + QA_rank))  
                                    outfile_sheet_row = outfile_sheet_row + 1
                                    break
                if good_passed == 0: # Best possible rank not yet reached.
                    # The remaining geocoded records (QA_rank = 9) are considered to be unsuccessful and errorneous.
                    # They will not participate into manual quality control (QC). 
                    QA_rank = [9]

# Close files
outfile_obj.close() # Save the output
infile_obj.close() # Release the input

print("----- Module Completed -----")
print(datetime.datetime.now())
