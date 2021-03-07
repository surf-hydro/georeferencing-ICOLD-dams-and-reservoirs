# [Description] ------------------------------
# Module name "Geocoding_ICOLD.py"
# This module performs forward (regular) geocoding for each record in the ICOLD World Regster of Dams (WRD)
# and output all geocoded results and their quality scenarios. Forward geocoding converts a nominal address
# to a pair of geographic coordinates (lat/lon), and meanwhile, the name and administrative divisions
# associated with the geographic coordinates will also be returned. 

# In this module, forward geocoding was implemented using the cloud-based geocoding service through Google
# Maps geocoding API (http://developers.google.com/maps). See more about forward geocoding and Google Maps
# geocoding API at: https://developers.google.com/maps/documentation/geocoding/overview.

# One WRD record may have multiple geocoding outputs. These outputs will be ranked by "Geocoding_QA.py" and
# the best quality result will be selected and labeled with a QA level.
# See Wang et al. (2021) for method details.

# The ICOLD WRD records were accessed from https://www.icold-cigb.org.

# Reference: Wang, J., Walter, B.A., Yao, F., Song, C., Ding, M., Maroof, M.A.S., Zhu, J., Fan, C., Xin, A.,
# McAlister, J.M., Sikder, M.S., Sheng, Y., Allen, G.H., Crétaux, J.-F., and Wada, Y., 2021. GeoDAR:
# Georeferenced global dam and reservoir database for bridging attributes and geolocations. Earth System
# Science Data, in review.

# Script written by: Jida Wang and Blake A. Walter, Kansas State University.
# Last update: March 4, 2021
# Contact: jidawang@ksu.edu; gdbruins@ucla.edu
#---------------------------------------------



# [Setup] -----------------------------------
# Inputs
# 1. ICOLD_file: full path of ICOLD WRD.
# The recent WRD (not released in this repository) can be accessed from ICOLD (https://www.icold-cigb.org). 
ICOLD_file = r"...\export_registre13_3_2019_cleaned.xlsx"

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

# 6. initial_row_number: initial record index in the register that the geocoding will start with.
initial_row_number = 11 # for example, starting from the 11th record in the register

# 7. end_row_number: last record index in the register that the geocoding will end with.
end_row_number = 1000 # for example, ending at the 1000th record, meaning that 990 records will be geocoded.
# The settings of initial_row_number and end_row_number give control to the user so that the maximum request
# quota for this API will not be exceeded.

# 8. similarity_threshold: numeric value for the minimum similarity score between two sequences (such as
# dam names from ICOLD WRD and the regional register) that were considered to be equivalent.
similarity_threshold = 5.0/6.0 #close to 85%, which is slightly more lenient than that used for geo-matching
# considering that the spelling variation in WRD and Google Maps (in different regions) could be more evident
# and the outputs from the geocoding API have already gone through a similarity measure.

# Output
# geocoded_records: full path of the geocoded WRD records.
geo_matched_records = r"...\Geocoded_ICOLD.xlsx"
#---------------------------------------------



# [Script] -----------------------------------
# Import built-in functions and tools
import http, urllib, csv, json, unicodedata, sys, datetime, xlsxwriter, openpyxl
import urllib.request
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

# Define input spreadsheet (original WRD) and output spreadsheet (geocoded WRD).
infile_obj = openpyxl.load_workbook(infile) 
infile_sheet = infile_obj.active
outfile_obj = xlsxwriter.Workbook(outfile)
outfile_sheet = outfile_obj.add_worksheet("Geocoded-WRD")

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

# Loop through each WRD record and implement geocoding.
# To georeference as many records as possible, all possible geocoding outputs associated with a WRD record are written to the output.
# This step also assigns a quality scenario for each output based on how well the input and output address components agree with each other.
# After this module, "Geocoding_QA.py" will then loop through the outputs for each WRD record and determine the best quality result with a
# final QA level (see Wang et al (2021)). 
row_number = 0 # Initiate the record index number in the input
row_number_write = 0 # Initiate the record index number in the output
load_number = 0 # Initiate the number of request using this API key
success = "No"  # Initiate a logical variable indicating whether the geocoding is successful ("No" indicates not yet successful)
considered_IDs = [] # Initiate an array that will be gradually expanded by ICOLD IDs that have been geocoded.
for ii in range(0, len(infile_ICOLDIDs)):
    row = infile_rows[ii] # Read this ICOLD WRD record
    ICOLD_ID = infile_ICOLDIDs[ii] # Retrieve this ICOLD WRD ID
    row_number = row_number + 1
    if row_number == 1: # Header
        # Write header
        header_new = tuple(row + ['gc_lat', 'gc_lng', 'gc_scenario', 'gc_cntry_long', 'gc_cntry_short', 'gc_admin_1', 'gc_admin_2', 'gc_admin_3', \
                                  'gc_admin_4', 'gc_admin_5', 'gc_local', 'gc_local_1', 'gc_local_2', 'gc_text_encoded', 'gc_encoded', 'gc_name', 'gc_addr'])
        outfile_sheet.write_row(row_number_write, 0, header_new)
        row_number_write = row_number_write + 1
    else:
        if (row_number >= initial_row_number and row_number < end_row_number):
            print(row_number)
            if (ICOLD_ID not in considered_IDs): # If this WRD record has not been geocoded.
                considered_IDs.append(ICOLD_ID) 
                success = "No" # Ensure a new WRD record always starts with "NO" for geocoding success.

                # Retrieve WRD attributes. 
                dam_name = (row[23]).lower().strip()  
                dam_other_name = (row[26]).lower().strip()  
                reservoir_name = (row[31]).lower().strip()
                town = (row[24]).lower().strip()
                state_province = (row[38]).lower().strip()
                country = (row[10]).lower().strip()
                country_index = [i for i, x in enumerate(country_NAME_array) if x == country]
                this_country_ISO = country_ISO_array[country_index[0]]

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
                elif len(reservoir_name)>5: #> 5 and <= 10
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
                success = "No" # Initiate success variable ("Yes" or "No"), and iterate different address scenarios as long as "success" is "No".
                Sc_list = []
                if dam_name == '' and dam_other_name == '' and reservoir_name == '' : # Indicating no reservoir or dam name.
                    # Write flag values in the output
                    outfile_sheet.write_row(row_number_write, 0, \
                          tuple(row + ["-999", "-999", "bad: no-name", "-999", "-999", "-999", "-999", "-999", "-999", "-999", "-999", "-999", \
                                       "-999", "-999", "-999", "-999", "-999"]))
                    row_number_write = row_number_write + 1
                    success = "Yes"
                    print(str(row_number) + ': DAM HAS INVALID or NO NAMES')
                elif dam_name == '' and dam_other_name == '': # Only reservoir name exists
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

                if success == "No": # Iterate different address scenarios as long as "success" is "No"
                    # Extend the address scenario list (to later include and exclude the country component)
                    Sc_list_1 = []
                    for Sc_list_unit in Sc_list:
                        Sc_list_1.append(Sc_list_unit)
                    Sc_list_1_len = len(Sc_list_1)
                    for this_Sc_unit in Sc_list_1:
                        Sc_list.append(this_Sc_unit)
    
                    # Format addresses to get prepared for geocoding                
                    text_addr_array_all = [] # In regular text format
                    encoded_addr_array_all = [] # In encoded format for Google Maps geocoding API
                    for this_rank_index in range(len(Sc_list)):
                        text_encoded_addr = ''
                        this_scenario = Sc_list[this_rank_index]
                        for this_element in this_scenario:
                            if this_element != '': # if this element is not blank
                                text_encoded_addr = text_encoded_addr + this_element + ', '
                        text_encoded_addr = text_encoded_addr[0 : len(text_encoded_addr)-2]
                        if this_rank_index < Sc_list_1_len:
                            encoded_addr = urllib.parse.quote(text_encoded_addr) + '&components=' + administrative_components
                        else:
                            encoded_addr = urllib.parse.quote(text_encoded_addr)
                        text_addr_array_all.append(text_encoded_addr)
                        encoded_addr_array_all.append(encoded_addr)

                    # Initiate arrays for geocoding output components
                    lat_array = [] # Latitude returned by geocoding
                    lng_array = [] # Longitude returned by geocoding
                    match_scenario_array = [] # Matching/quality scenario of the geocoding result
                    encoded_addr_array = [] # Encoded address for geocoding
                    text_encoded_addr_array = [] # Regular text address (before geocoding)
                    country_longname_array = [] # Country long name returned by geocoding
                    country_shortname_array = [] # Country short name returned by geocoding
                    administration_area_level_1_longname_array = [] # Multiple administrative division names returned by geocoding
                    administration_area_level_2_longname_array = []
                    administration_area_level_3_longname_array = []
                    administration_area_level_4_longname_array = []
                    administration_area_level_5_longname_array = []
                    locality_longname_array = []
                    locality_1_longname_array = []
                    locality_2_longname_array = []
                    addr_full_array = [] # Full address returned by geocoding
                    addr_name_array = [] # Feature name returned by geocoding
                       
                    # Extract unique address formats in case there are duplicates in encoded_addr_array_all (due to the same dam and reservoir names). 
                    # encoded_addr_array_unique = list(set(encoded_addr_array_all)) #this doesn't work because "set()" will mess up the original scenario orders.
                    encoded_addr_array_unique = []
                    for this_encoded_addr_array_all in encoded_addr_array_all:
                        if this_encoded_addr_array_all not in encoded_addr_array_unique:
                            encoded_addr_array_unique.append(this_encoded_addr_array_all)                       

                    # Loop through each unique address format
                    for encoded_addr in encoded_addr_array_unique:
                        # Geocode this address usng Google Map API
                        this_URL = 'https://maps.googleapis.com/maps/api/geocode/json?address=' + encoded_addr + '&key=' + geocoding_key
                        geodata = json.load(urllib.request.urlopen(this_URL))
                        load_number = load_number + 1
                        if geodata == {'error_message': \
                                       'You have exceeded your daily request quota for this API. If you did not set a custom daily request quota, verify your project has an active billing account: http://g.co/dev/maps-no-account',\
                                       'results': [], 'status': 'OVER_QUERY_LIMIT'}:
                            print(geodata) # Print this error message
                            print(row) # Track the row index number when the quota is exceeded.
                            print(load_number) # Print the load number
                            outfile_obj.close() # Save output
                            sys.exit('exceeding requests')

                        if geodata["status"] == 'OK': # Indicating geocoding result exists. The result may contain multiple solutions (or components).
                            # Loop through each of the solutions and evaluate the quality.
                            for this_geodata in geodata["results"]:
                                this_all_index = [i for i, x in enumerate(encoded_addr_array_all) if x == encoded_addr]
                                text_encoded_addr_array.append(text_addr_array_all[this_all_index[0]])
                                encoded_addr_array.append(encoded_addr)
                                lat = this_geodata["geometry"]["location"]["lat"]
                                lng = this_geodata["geometry"]["location"]["lng"]
                                lat_array.append(lat)
                                lng_array.append(lng)
                                # Retrieve feature name in the geocoding address
                                if this_geodata["address_components"] == []:
                                    google_dam_name = ''
                                else:
                                    # I noticed this may not be the best way to retrieve the feature name as the first address component is not always
                                    # the feature name. This can be improved in future work. 
                                    google_dam_name = this_geodata["address_components"][0]['long_name'] # Estimated feature name in this solution  
                                addr_name_array.append(google_dam_name) # Appending the array of feature names returned by geocoding
                                google_full_address = this_geodata['formatted_address'] # Fully formatted address in this solution
                                addr_full_array.append(google_full_address) # Appending the array of full addresses returned by geocoding

                                # Compute the similarity between the input dam/reservoir name(s) and the geocoding output feature name.
                                particular_damname_similar = damname_similar_v2(similarity_threshold, dam_name, dam_other_name, reservoir_name, google_dam_name, this_country_ISO)
                            
                                # Retrieve administrative divisions in this solution. 
                                a = this_geodata["address_components"]
                                a_i_country = {'long_name': '-999', 'short_name': '-999'}
                                for a_i in a:
                                    aa = a_i
                                    aaa=aa["types"]
                                    if aaa == ['country', 'political']:
                                        a_i_country = a_i
                                        break
                                a_i_state = {'long_name': '-999', 'short_name': '-999'}
                                for a_i in a:
                                    aa = a_i
                                    aaa=aa["types"]
                                    if aaa == ['administrative_area_level_1', 'political']:
                                        a_i_state = a_i
                                        break
                                a_i_state_2 = {'long_name': '-999', 'short_name': '-999'}
                                for a_i in a:
                                    aa = a_i
                                    aaa=aa["types"]
                                    if aaa == ['administrative_area_level_2', 'political']:
                                        a_i_state_2 = a_i
                                        break
                                a_i_state_3 = {'long_name': '-999', 'short_name': '-999'} 
                                for a_i in a:
                                    aa = a_i
                                    aaa=aa["types"]
                                    if aaa == ['administrative_area_level_3', 'political']:
                                        a_i_state_3 = a_i
                                        break
                                a_i_state_4 = {'long_name': '-999', 'short_name': '-999'} 
                                for a_i in a:
                                    aa = a_i
                                    aaa=aa["types"]
                                    if aaa == ['administrative_area_level_4', 'political']:
                                        a_i_state_4 = a_i
                                        break
                                a_i_state_5 = {'long_name': '-999', 'short_name': '-999'} 
                                for a_i in a:
                                    aa = a_i
                                    aaa=aa["types"]
                                    if aaa == ['administrative_area_level_5', 'political']:
                                        a_i_state_5 = a_i
                                        break
                                a_i_locality = {'long_name': '-999', 'short_name': '-999'} 
                                for a_i in a:
                                    aa = a_i
                                    aaa=aa["types"]
                                    if aaa == ['locality', 'political']:
                                        a_i_locality = a_i
                                        break
                                a_i_locality_1 = {'long_name': '-999', 'short_name': '-999'} 
                                for a_i in a:
                                    aa = a_i
                                    aaa=aa["types"]
                                    if aaa == ['political', 'sublocality', 'sublocality_level_1']:
                                        a_i_locality_1 = a_i
                                        break
                                a_i_locality_2 = {'long_name': '-999', 'short_name': '-999'} 
                                for a_i in a:
                                    aa = a_i
                                    aaa=aa["types"]
                                    if aaa == ['political', 'sublocality', 'sublocality_level_2']:
                                        a_i_locality_2 = a_i
                                        break    
                                # Extract long and short names for each of the administrative divisions in the solution.
                                country_longname = (a_i_country["long_name"]).lower().strip()
                                country_shortname = (a_i_country["short_name"]).lower().strip() # This is the ISO 3166-2 code.
                                country_longname_array.append(country_longname)
                                country_shortname_array.append(country_shortname)
                                administration_area_level_1_longname = (a_i_state["long_name"]).lower().strip()
                                administration_area_level_1_shortname = (a_i_state["short_name"]).lower().strip()
                                administration_area_level_1_longname_array.append(administration_area_level_1_longname)
                                administration_area_level_2_longname = (a_i_state_2["long_name"]).lower().strip()
                                administration_area_level_2_shortname = (a_i_state_2["short_name"]).lower().strip()
                                administration_area_level_2_longname_array.append(administration_area_level_2_longname)
                                administration_area_level_3_longname = (a_i_state_3["long_name"]).lower().strip()
                                administration_area_level_3_shortname = (a_i_state_3["short_name"]).lower().strip()
                                administration_area_level_3_longname_array.append(administration_area_level_3_longname)
                                administration_area_level_4_longname = (a_i_state_4["long_name"]).lower().strip()
                                administration_area_level_4_shortname = (a_i_state_4["short_name"]).lower().strip()
                                administration_area_level_4_longname_array.append(administration_area_level_4_longname)
                                administration_area_level_5_longname = (a_i_state_5["long_name"]).lower().strip()
                                administration_area_level_5_shortname = (a_i_state_5["short_name"]).lower().strip()
                                administration_area_level_5_longname_array.append(administration_area_level_5_longname)
                                locality_longname = (a_i_locality["long_name"]).lower().strip()
                                locality_shortname = (a_i_locality["short_name"]).lower().strip()
                                locality_longname_array.append(locality_longname)
                                locality_1_longname = (a_i_locality_1["long_name"]).lower().strip()
                                locality_1_shortname = (a_i_locality_1["short_name"]).lower().strip()
                                locality_1_longname_array.append(locality_1_longname)
                                locality_2_longname = (a_i_locality_2["long_name"]).lower().strip()
                                locality_2_shortname = (a_i_locality_2["short_name"]).lower().strip()
                                locality_2_longname_array.append(locality_2_longname)

                                # Remove accents in all ICOLD WRD and Google address components. 
                                state_province_ascii = remove_accents(state_province)
                                town_ascii = remove_accents(town)
                                country_longname_ascii = remove_accents(country_longname)
                                administration_area_level_1_longname_ascii = remove_accents(administration_area_level_1_longname)
                                administration_area_level_1_shortname_ascii = remove_accents(administration_area_level_1_shortname) 
                                administration_area_level_2_longname_ascii = remove_accents(administration_area_level_2_longname)
                                administration_area_level_2_shortname_ascii = remove_accents(administration_area_level_2_shortname) 
                                administration_area_level_3_longname_ascii = remove_accents(administration_area_level_3_longname) 
                                administration_area_level_3_shortname_ascii = remove_accents(administration_area_level_3_shortname) 
                                administration_area_level_4_longname_ascii = remove_accents(administration_area_level_4_longname)
                                administration_area_level_4_shortname_ascii = remove_accents(administration_area_level_4_shortname)
                                administration_area_level_5_longname_ascii = remove_accents(administration_area_level_5_longname)
                                administration_area_level_5_shortname_ascii = remove_accents(administration_area_level_5_shortname)
                                locality_longname_ascii = remove_accents(locality_longname)
                                locality_shortname_ascii = remove_accents(locality_shortname)
                                locality_1_longname_ascii = remove_accents(locality_1_longname)
                                locality_1_shortname_ascii = remove_accents(locality_1_shortname)
                                locality_2_longname_ascii = remove_accents(locality_2_longname)
                                locality_2_shortname_ascii = remove_accents(locality_2_shortname)        

                                # Compute the similarity of the state/provincial-level divisions between the WRD input and this geocoding solution. 
                                similarity_metric_long_state0 = similar_v2(country_longname_ascii, state_province_ascii) # This happens to situations like Taiwan and Puerto Rico. 
                                #For most other regions 
                                similarity_metric_long_state1 = similar_v2(administration_area_level_1_longname_ascii, state_province_ascii)
                                similarity_metric_short_state1 = similar_v2(administration_area_level_1_shortname_ascii, state_province_ascii)
                                similarity_metric_long_state2 = similar_v2(administration_area_level_2_longname_ascii, state_province_ascii)
                                similarity_metric_short_state2 = similar_v2(administration_area_level_2_shortname_ascii, state_province_ascii)                           
                                similarity_metric_long_state3 = similar_v2(administration_area_level_3_longname_ascii, state_province_ascii)
                                similarity_metric_short_state3 = similar_v2(administration_area_level_3_shortname_ascii, state_province_ascii)                        
                                # Generate similarity array for the state level. 
                                if country_shortname == 'tw' or country_shortname == 'hk' or country_shortname == 'fo' or \
                                   country_shortname == 'gl' or country_shortname == 'pr' or country_shortname == 're' or \
                                   country_shortname == 'gp' or country_shortname == 'mq' or country_shortname == 'yt' or \
                                   country_shortname == 'im' or country_shortname == 'je' or country_shortname == 'gg' or \
                                   country_shortname == 'gu':
                                    similarity_metric_state_array = [similarity_metric_long_state0, \
                                                                     similarity_metric_long_state1, similarity_metric_short_state1, \
                                                                     similarity_metric_long_state2, similarity_metric_short_state2, \
                                                                     similarity_metric_long_state3, similarity_metric_short_state3]
                                else:
                                    similarity_metric_state_array = [similarity_metric_long_state1, similarity_metric_short_state1, \
                                                                     similarity_metric_long_state2, similarity_metric_short_state2, \
                                                                     similarity_metric_long_state3, similarity_metric_short_state3]

                                # Compute the similarity of the city/township-level divisions between the WRD input and this geocoding solution. 
                                similarity_metric_long_town1 = similar_v2(administration_area_level_3_longname_ascii, town_ascii) 
                                similarity_metric_short_town1 = similar_v2(administration_area_level_3_shortname_ascii, town_ascii)
                                similarity_metric_long_town2 = similar_v2(administration_area_level_4_longname_ascii, town_ascii) 
                                similarity_metric_short_town2 = similar_v2(administration_area_level_4_shortname_ascii, town_ascii)
                                similarity_metric_long_town3 = similar_v2(administration_area_level_5_longname_ascii, town_ascii) 
                                similarity_metric_short_town3 = similar_v2(administration_area_level_5_shortname_ascii, town_ascii)
                                similarity_metric_long_town4 = similar_v2(locality_longname_ascii, town_ascii) 
                                similarity_metric_short_town4 = similar_v2(locality_shortname_ascii, town_ascii)
                                similarity_metric_long_town5 = similar_v2(locality_1_longname_ascii, town_ascii) 
                                similarity_metric_short_town5 = similar_v2(locality_1_shortname_ascii, town_ascii)
                                similarity_metric_long_town6 = similar_v2(locality_2_longname_ascii, town_ascii) 
                                similarity_metric_short_town6 = similar_v2(locality_2_shortname_ascii, town_ascii)
                                similarity_metric_long_town7 = similar_v2(administration_area_level_2_longname_ascii, town_ascii) 
                                similarity_metric_short_town7 = similar_v2(administration_area_level_2_shortname_ascii, town_ascii)
                                similarity_metric_long_town8 = similar_v2(administration_area_level_1_longname_ascii, town_ascii) # situations like Tokyo, Beijing, Washington DC, etc.
                                similarity_metric_short_town8 = similar_v2(administration_area_level_1_shortname_ascii, town_ascii)
                                # Generate similarity array for the township level. 
                                if country_shortname == 'tw' or country_shortname == 'hk' or country_shortname == 'fo' or \
                                   country_shortname == 'gl' or country_shortname == 'pr' or country_shortname == 're' or \
                                   country_shortname == 'gp' or country_shortname == 'mq' or country_shortname == 'yt' or \
                                   country_shortname == 'im' or country_shortname == 'je' or country_shortname == 'gg' or \
                                   country_shortname == 'gu':
                                    similarity_metric_town_array = [similarity_metric_long_town1, similarity_metric_short_town1, \
                                                                similarity_metric_long_town2, similarity_metric_short_town2, \
                                                                similarity_metric_long_town3, similarity_metric_short_town3, \
                                                                similarity_metric_long_town4, similarity_metric_short_town4, \
                                                                similarity_metric_long_town5, similarity_metric_short_town5, \
                                                                similarity_metric_long_town6, similarity_metric_short_town6, \
                                                                similarity_metric_long_town7, similarity_metric_short_town7, \
                                                                similarity_metric_long_town8, similarity_metric_short_town8]
                                else:
                                    similarity_metric_town_array = [similarity_metric_long_town1, similarity_metric_short_town1, \
                                                                similarity_metric_long_town2, similarity_metric_short_town2, \
                                                                similarity_metric_long_town3, similarity_metric_short_town3, \
                                                                similarity_metric_long_town4, similarity_metric_short_town4, \
                                                                similarity_metric_long_town5, similarity_metric_short_town5, \
                                                                similarity_metric_long_town6, similarity_metric_short_town6, \
                                                                similarity_metric_long_town7, similarity_metric_short_town7]

                                # Remove township titles (such as xian, qu, sheng, shi) for China.
                                # In the ICOLD WRD input
                                China_town_ascii = town_ascii
                                if len(town_ascii) > 4 and this_country_ISO == 'cn':
                                    if town_ascii[-4:] == 'xian': # WRD usually does not have space in between the town's name and title.
                                        China_town_ascii = (town_ascii[0:(len(town_ascii)-4)]).lower().strip()
                                    elif town_ascii[-3:] == 'shi':
                                        China_town_ascii = (town_ascii[0:(len(town_ascii)-3)]).lower().strip()  
                                    elif town_ascii[-2:] == 'qu':
                                        China_town_ascii = (town_ascii[0:(len(town_ascii)-2)]).lower().strip()
                                # In the geocoding output
                                if country_shortname == 'tw' or country_shortname == 'hk' or country_shortname == 'fo' or \
                                   country_shortname == 'gl' or country_shortname == 'pr' or country_shortname == 're' or \
                                   country_shortname == 'gp' or country_shortname == 'mq' or country_shortname == 'yt' or \
                                   country_shortname == 'im' or country_shortname == 'je' or country_shortname == 'gg' or \
                                   country_shortname == 'gu':
                                    google_array = [administration_area_level_3_longname_ascii, administration_area_level_3_shortname_ascii, \
                                                      administration_area_level_4_longname_ascii, administration_area_level_4_shortname_ascii, \
                                                      administration_area_level_5_longname_ascii, administration_area_level_5_shortname_ascii, \
                                                      locality_longname_ascii, locality_shortname_ascii, locality_1_longname_ascii, locality_1_shortname_ascii,\
                                                      locality_2_longname_ascii, locality_2_shortname_ascii, \
                                                      administration_area_level_2_longname_ascii, administration_area_level_2_shortname_ascii, \
                                                      administration_area_level_1_longname_ascii, administration_area_level_1_shortname_ascii]
                                else:
                                    google_array = [administration_area_level_3_longname_ascii, administration_area_level_3_shortname_ascii, \
                                                      administration_area_level_4_longname_ascii, administration_area_level_4_shortname_ascii, \
                                                      administration_area_level_5_longname_ascii, administration_area_level_5_shortname_ascii, \
                                                      locality_longname_ascii, locality_shortname_ascii, locality_1_longname_ascii, locality_1_shortname_ascii,\
                                                      locality_2_longname_ascii, locality_2_shortname_ascii, \
                                                      administration_area_level_2_longname_ascii, administration_area_level_2_shortname_ascii]
                                China_similarity_metric_town_array = []
                                for google_i in google_array:
                                    China_google_i = google_i
                                    if len(google_i) > 5 and this_country_ISO == 'cn':
                                        if google_i[-6:] == ' sheng': #Google geocoding output may has a space in between the town's name and title. 
                                            China_google_i = (google_i[0:(len(google_i)-6)]).lower().strip()
                                        elif google_i[-5:] == ' xian':
                                            China_google_i = (google_i[0:(len(google_i)-5)]).lower().strip()
                                        elif google_i[-4:] == ' shi':
                                            China_google_i = (google_i[0:(len(google_i)-4)]).lower().strip()
                                        elif google_i[-3:] == ' qu':
                                            China_google_i = (google_i[0:(len(google_i)-3)]).lower().strip()
                                    China_similarity_metric_town_array.append(similar_v2(China_google_i, China_town_ascii))
                                # We did not do this sort of title removal for the state level as in ICOLD WRD, I did not see 'xxxsheng' or 'xx sheng'.
                                # If this happens in Google Maps, very likely there is a space between the name and title, and this will be handled by
                                # the following containment check. We assume there is a space between the name and title for other countries. 

                                # Perform another round of similar comparison that considers the containment relationship,
                                # e.g., "city of Manhattan" vs "Manhattan", and "Kansas/Colorado" vs "Kansas" (if the reservoir is on the border). 
                                if country_shortname == 'tw' or country_shortname == 'hk' or country_shortname == 'fo' or \
                                   country_shortname == 'gl' or country_shortname == 'pr' or country_shortname == 're' or \
                                   country_shortname == 'gp' or country_shortname == 'mq' or country_shortname == 'yt' or \
                                   country_shortname == 'im' or country_shortname == 'je' or country_shortname == 'gg' or \
                                   country_shortname == 'gu':
                                    google_state_arrays = [country_longname_ascii, \
                                                           administration_area_level_1_longname_ascii, administration_area_level_1_shortname_ascii, \
                                                           administration_area_level_2_longname_ascii, administration_area_level_2_shortname_ascii, \
                                                           administration_area_level_3_longname_ascii, administration_area_level_3_shortname_ascii]
                                    google_town_arrays = [administration_area_level_1_longname_ascii, administration_area_level_1_shortname_ascii, \
                                                      administration_area_level_2_longname_ascii, administration_area_level_2_shortname_ascii, \
                                                      administration_area_level_3_longname_ascii, administration_area_level_3_shortname_ascii, \
                                                      administration_area_level_4_longname_ascii, administration_area_level_4_shortname_ascii, \
                                                      administration_area_level_5_longname_ascii, administration_area_level_5_shortname_ascii, \
                                                      locality_longname_ascii, locality_shortname_ascii, locality_1_longname_ascii, locality_1_shortname_ascii, \
                                                      locality_2_longname_ascii, locality_2_shortname_ascii]
                                else:
                                    google_state_arrays = [administration_area_level_1_longname_ascii, administration_area_level_1_shortname_ascii, \
                                                           administration_area_level_2_longname_ascii, administration_area_level_2_shortname_ascii, \
                                                           administration_area_level_3_longname_ascii, administration_area_level_3_shortname_ascii]
                                    google_town_arrays = [administration_area_level_2_longname_ascii, administration_area_level_2_shortname_ascii, \
                                                      administration_area_level_3_longname_ascii, administration_area_level_3_shortname_ascii, \
                                                      administration_area_level_4_longname_ascii, administration_area_level_4_shortname_ascii, \
                                                      administration_area_level_5_longname_ascii, administration_area_level_5_shortname_ascii, \
                                                      locality_longname_ascii, locality_shortname_ascii, locality_1_longname_ascii, locality_1_shortname_ascii, \
                                                      locality_2_longname_ascii, locality_2_shortname_ascii]
                                containment_check_state = 0
                                # If containment_check_state = 1, it means that the string of state/province in ICOLD WRD contains that in the geocoding output (or vice versa).
                                for this_google_state in google_state_arrays:
                                    if (state_province_ascii in this_google_state) == True and (state_province_ascii != this_google_state) == True: #ICOLD contained by geocoding
                                        if this_google_state.find(state_province_ascii) == 0: #'manhattan city': 'manhattan'
                                            if this_google_state[this_google_state.find(state_province_ascii)+len(state_province_ascii)] == ' ' or \
                                               this_google_state[this_google_state.find(state_province_ascii)+len(state_province_ascii)] == '-':
                                                containment_check_state = 1
                                                break
                                        else:
                                            if (this_google_state.find(state_province_ascii)+len(state_province_ascii)) == len(this_google_state): #'city of manhattan': 'manhattan'
                                                if this_google_state[this_google_state.find(state_province_ascii)-1] == ' ' or \
                                                   this_google_state[this_google_state.find(state_province_ascii)-1] == '-':
                                                    containment_check_state = 1
                                                    break
                                    else:
                                        if (this_google_state in state_province_ascii) == True and (state_province_ascii != this_google_state) == True: #ICOLD containing geocoding
                                            if state_province_ascii.find(this_google_state) == 0: #'manhattan city': 'manhattan'
                                                if state_province_ascii[state_province_ascii.find(this_google_state)+len(this_google_state)] == ' ' or \
                                                   state_province_ascii[state_province_ascii.find(this_google_state)+len(this_google_state)] == '-':
                                                    containment_check_state = 1
                                                    break
                                            else:
                                                if (state_province_ascii.find(this_google_state)+len(this_google_state)) == len(state_province_ascii): #'city of manhattan': 'manhattan'
                                                    if state_province_ascii[state_province_ascii.find(this_google_state)-1] == ' ' or \
                                                       state_province_ascii[state_province_ascii.find(this_google_state)-1] == '-':
                                                        containment_check_state = 1
                                                        break 
                                containment_check_town = 0
                                # If containment_check_town = 1, it means that the string of town in ICOLD WRD contains that in the geocoding output (or vice versa).
                                for this_google_town in google_town_arrays:
                                    if (town_ascii in this_google_town) == True and (town_ascii != this_google_town) == True: #ICOLD contained by geocoding
                                        if this_google_town.find(town_ascii) == 0: #'manhattan city': 'manhattan'
                                            if this_google_town[this_google_town.find(town_ascii)+len(town_ascii)] == ' ' or \
                                               this_google_town[this_google_town.find(town_ascii)+len(town_ascii)] == '-':
                                                containment_check_town = 1
                                                break
                                        else:
                                            if (this_google_town.find(town_ascii)+len(town_ascii)) == len(this_google_town): #'city of manhattan': 'manhattan'
                                                if this_google_town[this_google_town.find(town_ascii)-1] == ' ' or \
                                                   this_google_town[this_google_town.find(town_ascii)-1] == '-':
                                                    containment_check_town = 1
                                                    break
                                    else:
                                        if (this_google_town in town_ascii) == True and (town_ascii != this_google_town) == True: #ICOLD containing geocoding
                                            if town_ascii.find(this_google_town) == 0: #'manhattan city': 'manhattan'
                                                if town_ascii[town_ascii.find(this_google_town)+len(this_google_town)] == ' ' or \
                                                   town_ascii[town_ascii.find(this_google_town)+len(this_google_town)] == '-':
                                                    containment_check_town = 1
                                                    break
                                            else:
                                                if (town_ascii.find(this_google_town)+len(this_google_town)) == len(town_ascii): #'city of manhattan': 'manhattan'
                                                    if town_ascii[town_ascii.find(this_google_town)-1] == ' ' or \
                                                       town_ascii[town_ascii.find(this_google_town)-1] == '-':
                                                        containment_check_town = 1
                                                        break 

                                # Tackle spelling variations between different Chinese province  
                                if this_country_ISO == 'cn':
                                    if (state_province_ascii ==  'shanxi' and administration_area_level_1_longname_ascii == 'shaanxi') or \
                                       (state_province_ascii ==  'shanxi' and administration_area_level_1_longname_ascii == 'shaanxi sheng') or \
                                       (state_province_ascii ==  'shanxi' and administration_area_level_1_longname_ascii == 'shaanxi province') or \
                                       (state_province_ascii ==  'shaanxi' and administration_area_level_1_longname_ascii == 'shanxi') or \
                                       (state_province_ascii ==  'shaanxi' and administration_area_level_1_longname_ascii == 'shanxi sheng') or \
                                       (state_province_ascii ==  'shaanxi' and administration_area_level_1_longname_ascii == 'shanxi province'):
                                        similarity_metric_state_array = [0]

                                # Check whether the feature type returned by this geocoding solution is reasonable.
                                wrong_type = 0 
                                if this_geodata["types"] != ['establishment', 'natural_feature'] and \
                                   this_geodata["types"] != ['establishment', 'park', 'point_of_interest'] and \
                                   this_geodata["types"] != ['premise'] and \
                                   this_geodata["types"] != ['establishment', 'point_of_interest', 'premise'] and \
                                   this_geodata["types"] != ['establishment', 'point_of_interest'] and \
                                   this_geodata["types"] != ['campground', 'establishment', 'lodging', 'park', 'point_of_interest'] and \
                                   this_geodata["types"] != ['establishment', 'general_contractor', 'point_of_interest']:
                                    wrong_type = 1 # Indicating the feature at the geocoded location has little chance to be dam or reservoir.

                                # Defining the quality scenario in this geocoding solution
                                if wrong_type ==0: # Indicating this feature may be a dam or reservoir.
                                    # All WRD records have valid country values but are sometimes missing state/province/town values.
                                    if country_longname_ascii == '-999': # Meaning country is unknown in the Google geocoding result. 
                                        if ('partial_match' in this_geodata)== False: # Meaning this is an explicit result
                                            match_scenario = 'complete-match unknown-country'
                                        else:
                                            if this_geodata["partial_match"] == True: # Meaning indeed partial match
                                                match_scenario = 'partial-match unknown-country'
                                            else:
                                                match_scenario = 'complete-match unknown-country'
                                    else: # Google country is known
                                        if country_shortname != this_country_ISO: # Country name is wrong
                                            if ('partial_match' in this_geodata)== False:
                                                match_scenario = 'complete-match out-country'
                                            else:
                                                if this_geodata["partial_match"] == True:
                                                    match_scenario = 'partial-match out-country'
                                                else:
                                                    match_scenario = 'complete-match out-country'
                                        else: # Google country is correct.
                                            if state_province_ascii == '': # No state in ICOLD
                                                # Then only check township in ICOLD
                                                if town_ascii == '': # ICOLD has no town either. 
                                                    if ('partial_match' in this_geodata)== False:
                                                        match_scenario = 'complete-match unknown-state-town' # State and town both unknown
                                                    else:
                                                        if this_geodata["partial_match"] == True:
                                                            match_scenario = 'partial-match unknown-state-town'
                                                        else:
                                                            match_scenario = 'complete-match unknown-state-town'
                                                    # Complete-match, unknown-state, unknown-town 
                                                    if match_scenario == 'complete-match unknown-state-town' and particular_damname_similar == 1:
                                                    # This is the best result possible under this situation. So write the result to the output file. 
                                                        outfile_sheet.write_row(row_number_write, 0, \
                                                                                tuple(row + [lat, lng, match_scenario, \
                                                                                country_longname, country_shortname, administration_area_level_1_longname, \
                                                                                administration_area_level_2_longname, administration_area_level_3_longname, \
                                                                                administration_area_level_4_longname, administration_area_level_5_longname, \
                                                                                locality_longname, locality_1_longname, locality_2_longname, \
                                                                                text_encoded_addr, encoded_addr, google_dam_name, google_full_address]))                                                        
                                                        row_number_write = row_number_write + 1
                                                        print(str(row_number) + ': Found for ... ' + text_encoded_addr + ' ' + str(lat) + ' ' + str(lng) + \
                                                                              '       M A T C H =======================')
                                                        success = "Yes"
                                                        break
                                                else: # Town known in ICOLD    
                                                    if administration_area_level_1_longname_ascii=='-999' and administration_area_level_2_longname_ascii=='-999' and \
                                                       administration_area_level_3_longname_ascii=='-999' and administration_area_level_4_longname_ascii=='-999' and \
                                                       administration_area_level_5_longname_ascii=='-999' and locality_longname_ascii=='-999' and \
                                                       locality_1_longname_ascii=='-999' and locality_2_longname_ascii=='-999': # Town unknown in Google
                                                        if ('partial_match' in this_geodata)== False:
                                                            match_scenario = 'complete-match unknown-state-town' # State and town both unknown
                                                        else:
                                                            if this_geodata["partial_match"] == True:
                                                                match_scenario = 'partial-match unknown-state-town'
                                                            else:
                                                                match_scenario = 'complete-match unknown-state-town' 
                                                    else: # Town known in Google
                                                        if max(similarity_metric_town_array) >= similarity_threshold or \
                                                           max(China_similarity_metric_town_array) >= similarity_threshold or \
                                                           containment_check_town == 1: # Town matched between WRD and the Google geocoding result
                                                            if ('partial_match' in this_geodata)== False:
                                                                match_scenario = 'complete-match in-town'
                                                            else:
                                                                if this_geodata["partial_match"] == True:
                                                                    match_scenario = 'partial-match in-town'
                                                                else:
                                                                    match_scenario = 'complete-match in-town'
                                                            # Complete-match, unknown-state, in-town
                                                            if match_scenario == 'complete-match in-town' and particular_damname_similar == 1:
                                                                # This is the best result possible under this situation. So write the result to the output file. 
                                                                outfile_sheet.write_row(row_number_write, 0, \
                                                                                        tuple(row + [lat, lng, match_scenario, \
                                                                                        country_longname, country_shortname, administration_area_level_1_longname, \
                                                                                        administration_area_level_2_longname, administration_area_level_3_longname, \
                                                                                        administration_area_level_4_longname, administration_area_level_5_longname, \
                                                                                        locality_longname, locality_1_longname, locality_2_longname, \
                                                                                        text_encoded_addr, encoded_addr, google_dam_name, google_full_address]))
                                                                row_number_write = row_number_write + 1
                                                                print(str(row_number) + ': Found for ... ' + text_encoded_addr + ' ' + str(lat) + ' ' + str(lng) + \
                                                                                      '       M A T C H =======================')
                                                                success = "Yes"
                                                                break
                                                        else:
                                                            if ('partial_match' in this_geodata)== False:
                                                                match_scenario = 'complete-match out-town' # State unknown, town likely wrong
                                                            else:
                                                                if this_geodata["partial_match"] == True:
                                                                    match_scenario = 'partial-match out-town'
                                                                else:
                                                                    match_scenario = 'complete-match out-town'
                                            else: # State known in ICOLD
                                                if (administration_area_level_1_longname_ascii=='-999' and administration_area_level_2_longname_ascii=='-999' and \
                                                    administration_area_level_3_longname_ascii=='-999') and \
                                                    country_shortname != 'tw' and country_shortname != 'hk' and country_shortname != 'fo' and \
                                                    country_shortname != 'gl' and country_shortname != 'pr' and \
                                                    country_shortname != 're' and country_shortname != 'gp' and \
                                                    country_shortname != 'mq' and country_shortname != 'yt' and \
                                                    country_shortname != 'im' and country_shortname != 'je' and \
                                                    country_shortname != 'gg' and country_shortname != 'gu': # No valid state in Google
                                                    # The ambiguous regions are excluded here because their 'state/province' in ICOLD will not match any of the results from Google.
                                                    # In other words, if they are included, it will be always "out-state".
                                                    if town_ascii == '': # Town unknown in ICOLD
                                                        if ('partial_match' in this_geodata)== False:
                                                            match_scenario = 'complete-match unknown-state-town' # State and town both unknown
                                                        else:
                                                            if this_geodata["partial_match"] == True:
                                                                match_scenario = 'partial-match unknown-state-town'
                                                            else:
                                                                match_scenario = 'complete-match unknown-state-town'
                                                    else: # Town known in ICOLD
                                                        if administration_area_level_1_longname_ascii=='-999' and administration_area_level_2_longname_ascii=='-999' and \
                                                           administration_area_level_3_longname_ascii=='-999' and administration_area_level_4_longname_ascii=='-999' and \
                                                           administration_area_level_5_longname_ascii=='-999' and locality_longname_ascii=='-999' and \
                                                           locality_1_longname_ascii=='-999' and locality_2_longname_ascii=='-999': # Town unknown in Google
                                                            if ('partial_match' in this_geodata)== False:
                                                                match_scenario = 'complete-match unknown-state-town' # State and town both unknown
                                                            else:
                                                                if this_geodata["partial_match"] == True:
                                                                    match_scenario = 'partial-match unknown-state-town'
                                                                else:
                                                                    match_scenario = 'complete-match unknown-state-town' 
                                                        else: # Town known in Google
                                                            if max(similarity_metric_town_array) >= similarity_threshold or \
                                                               max(China_similarity_metric_town_array) >= similarity_threshold or \
                                                               containment_check_town == 1:
                                                                if ('partial_match' in this_geodata)== False:
                                                                    match_scenario = 'complete-match in-town' # State unknown, but town known
                                                                else:
                                                                    if this_geodata["partial_match"] == True:
                                                                        match_scenario = 'partial-match in-town'
                                                                    else:
                                                                        match_scenario = 'complete-match in-town'
                                                            else:
                                                                if ('partial_match' in this_geodata)== False:
                                                                    match_scenario = 'complete-match out-town' # State unknown, town wrong
                                                                else:
                                                                    if this_geodata["partial_match"] == True:
                                                                        match_scenario = 'partial-match out-town'
                                                                    else:
                                                                        match_scenario = 'complete-match out-town'
                                                else: # State known in Google and state known in ICOLD. They have to match otherwise there is no need to check town.
                                                    if max(similarity_metric_state_array) >= similarity_threshold or containment_check_state == 1:
                                                        if ('partial_match' in this_geodata)== False:
                                                            if town_ascii == '': # Town unknown in ICOLD
                                                                match_scenario = 'complete-match in-state unknown-town'
                                                                #ICOLD: complete-match, in-state, unknown-town
                                                                if particular_damname_similar == 1:
                                                                    # This is the best result possible under this situation. So write the result to the output file.
                                                                    outfile_sheet.write_row(row_number_write, 0, \
                                                                                            tuple(row + [lat, lng, match_scenario, \
                                                                                            country_longname, country_shortname, administration_area_level_1_longname, \
                                                                                            administration_area_level_2_longname, administration_area_level_3_longname, \
                                                                                            administration_area_level_4_longname, administration_area_level_5_longname, \
                                                                                            locality_longname, locality_1_longname, locality_2_longname, \
                                                                                            text_encoded_addr, encoded_addr, google_dam_name, google_full_address]))
                                                                    row_number_write = row_number_write + 1
                                                                    print(str(row_number) + ': Found for ... ' + text_encoded_addr + ' ' + str(lat) + ' ' + str(lng) + \
                                                                                          '       M A T C H =======================')
                                                                    success = "Yes"
                                                                    break
                                                            else: # Town known in ICOLD
                                                                if administration_area_level_1_longname_ascii=='-999' and administration_area_level_2_longname_ascii=='-999' and \
                                                                   administration_area_level_3_longname_ascii=='-999' and administration_area_level_4_longname_ascii=='-999' and \
                                                                   administration_area_level_5_longname_ascii=='-999' and locality_longname_ascii=='-999' and \
                                                                   locality_1_longname_ascii=='-999' and locality_2_longname_ascii=='-999': # Town unknown in Google
                                                                    match_scenario = 'complete-match in-state unknown-town'
                                                                else: # Town known in Google
                                                                    if max(similarity_metric_town_array) >= similarity_threshold or \
                                                                       max(China_similarity_metric_town_array) >= similarity_threshold or \
                                                                       containment_check_town == 1:
                                                                        match_scenario = 'complete-match in-state in-town'
                                                                        #ICOLD: complete-match, in-state, in-town
                                                                        if particular_damname_similar == 1:
                                                                            # This is the best result possible under this situation. So write the result to the output file.
                                                                            outfile_sheet.write_row(row_number_write, 0, \
                                                                                                    tuple(row + [lat, lng, match_scenario, \
                                                                                                    country_longname, country_shortname, administration_area_level_1_longname, \
                                                                                                    administration_area_level_2_longname, administration_area_level_3_longname, \
                                                                                                    administration_area_level_4_longname, administration_area_level_5_longname, \
                                                                                                    locality_longname, locality_1_longname, locality_2_longname, \
                                                                                                    text_encoded_addr, encoded_addr, google_dam_name, google_full_address]))
                                                                            row_number_write = row_number_write + 1
                                                                            print(str(row_number) + ': Found for ... ' + text_encoded_addr + ' ' + str(lat) + ' ' + str(lng) + \
                                                                                                  '       M A T C H =======================')
                                                                            success = "Yes"
                                                                            break
                                                                    else:
                                                                        match_scenario = 'complete-match in-state out-town'            
                                                        else:
                                                            if this_geodata["partial_match"] == True: # Partially matched result from this geocoding solution
                                                                match_scenario = 'partial-match in-state'
                                                            else:
                                                                if town_ascii == '': # Town unknown in ICOLD
                                                                    match_scenario = 'complete-match in-state unknown-town'
                                                                    #ICOLD: complete-match, in-state, unknown-town
                                                                    if particular_damname_similar == 1:
                                                                        # This is the best result possible under this situation. So write the result to the output file.
                                                                        outfile_sheet.write_row(row_number_write, 0, \
                                                                                                tuple(row + [lat, lng, match_scenario, \
                                                                                                country_longname, country_shortname, administration_area_level_1_longname, \
                                                                                                administration_area_level_2_longname, administration_area_level_3_longname, \
                                                                                                administration_area_level_4_longname, administration_area_level_5_longname, \
                                                                                                locality_longname, locality_1_longname, locality_2_longname, \
                                                                                                text_encoded_addr, encoded_addr, google_dam_name, google_full_address]))
                                                                        row_number_write = row_number_write + 1
                                                                        print(str(row_number) + ': Found for ... ' + text_encoded_addr + ' ' + str(lat) + ' ' + str(lng) + \
                                                                                              '       M A T C H =======================')
                                                                        success = "Yes"
                                                                        break                                    
                                                                else: # Town known in ICOLD
                                                                    if administration_area_level_1_longname_ascii=='-999' and administration_area_level_2_longname_ascii=='-999' and \
                                                                       administration_area_level_3_longname_ascii=='-999' and administration_area_level_4_longname_ascii=='-999' and \
                                                                       administration_area_level_5_longname_ascii=='-999' and locality_longname_ascii=='-999' and \
                                                                       locality_1_longname_ascii=='-999' and locality_2_longname_ascii=='-999': # Town unknown in Google
                                                                        match_scenario = 'complete-match in-state unknown-town'
                                                                    else: # Town known in Google
                                                                        if max(similarity_metric_town_array) >= similarity_threshold or \
                                                                           max(China_similarity_metric_town_array) >= similarity_threshold or \
                                                                           containment_check_town == 1:
                                                                            match_scenario = 'complete-match in-state in-town'
                                                                            #ICOLD: complete-match, in-state, in-town
                                                                            if particular_damname_similar == 1:
                                                                                # This is the best result possible under this situation. So write the result to the output file.
                                                                                outfile_sheet.write_row(row_number_write, 0, \
                                                                                                        tuple(row + [lat, lng, match_scenario, \
                                                                                                        country_longname, country_shortname, administration_area_level_1_longname, \
                                                                                                        administration_area_level_2_longname, administration_area_level_3_longname, \
                                                                                                        administration_area_level_4_longname, administration_area_level_5_longname, \
                                                                                                        locality_longname, locality_1_longname, locality_2_longname, \
                                                                                                        text_encoded_addr, encoded_addr, google_dam_name, google_full_address]))
                                                                                row_number_write = row_number_write + 1
                                                                                print(str(row_number) + ': Found for ... ' + text_encoded_addr + ' ' + str(lat) + ' ' + str(lng) + \
                                                                                                      '       M A T C H =======================')
                                                                                success = "Yes"
                                                                                break
                                                                        else:
                                                                            match_scenario = 'complete-match in-state out-town'
                                                    else:
                                                        if ('partial_match' in this_geodata)== False: # An explicit match
                                                            match_scenario = 'complete-match out-state'
                                                        else:
                                                            if this_geodata["partial_match"] == True:
                                                                match_scenario = 'partial-match out-state'
                                                            else:
                                                                match_scenario = 'complete-match out-state' 
                                else:
                                    match_scenario = 'bad: non-feature'
                                match_scenario_array.append(match_scenario)
                        else: # Meaning that the geocoding output status is unsuccessful. If so, write the flag values into output arrays. 
                            this_all_index = [i for i, x in enumerate(encoded_addr_array_all) if x == encoded_addr]
                            text_encoded_addr_array.append(text_addr_array_all[this_all_index[0]])
                            encoded_addr_array.append(encoded_addr)
                            lat_array.append('-999')
                            lng_array.append('-999')
                            match_scenario_array.append('bad: no-result')
                            country_longname_array.append('-999')
                            country_shortname_array.append('-999')
                            administration_area_level_1_longname_array.append('-999')
                            administration_area_level_2_longname_array.append('-999')
                            administration_area_level_3_longname_array.append('-999')
                            administration_area_level_4_longname_array.append('-999')
                            administration_area_level_5_longname_array.append('-999')
                            locality_longname_array.append('-999')
                            locality_1_longname_array.append('-999')
                            locality_2_longname_array.append('-999')
                            addr_name_array.append('-999')
                            addr_full_array.append('-999')
                        if success == "Yes":
                            break
                    
                    # If no optimal geocoding solution is identified, write the best-quality solutions associated with each of the unique lat/lon pairs to the output.
                    # These outputs will be ranked by "Geocoding_QA.py" and the best quality result will be selected and labeled with a QA level.
                    if success == "No":
                        # This array lists all possible matching scenarios in a descrending order of preference (or quality). 
                        result_scenario_list = ['complete-match in-state in-town', 'complete-match in-state unknown-town', 'complete-match in-state out-town', \
                                                'partial-match in-state', 'complete-match in-town', 'partial-match in-town', 'complete-match unknown-state-town', \
                                                'partial-match unknown-state-town', 'complete-match out-town', 'partial-match out-town', 'complete-match out-state', \
                                                'partial-match out-state', 'complete-match unknown-country', 'partial-match unknown-country', \
                                                'complete-match out-country', 'partial-match out-country', 'bad: non-feature', 'bad: no-result']
                        # Retrieve unique lat/lon coordinates
                        row_records_array = []
                        lat_lng_list = []
                        for coord_i in range(len(lat_array)):
                            lat_lng_list.append([lat_array[coord_i], lng_array[coord_i]])
                        unique_lat_lng_list = []
                        for this_pair in lat_lng_list:
                            if this_pair not in unique_lat_lng_list:
                                unique_lat_lng_list.append(this_pair)
                        # Loop through each unique lat/lon pair and select the geocoding solution with the best-quality matching scenario. 
                        for this_unique_pair in unique_lat_lng_list:
                            this_pair_indices = [i for i, x in enumerate(lat_lng_list) if x == this_unique_pair]
                            # Retrieve the matching scenarios associated with this lat/lon pair
                            these_scenarios = [match_scenario_array[i] for i in this_pair_indices]
                            # Select the best-quality matching scenario
                            for this_result_scenario in result_scenario_list: 
                                this_result_scenario_indices = [i for i, x in enumerate(these_scenarios) if x == this_result_scenario]
                                if len(this_result_scenario_indices) >0:
                                    this_final_index = this_pair_indices[this_result_scenario_indices[0]] # Just use one record
                                    row_record = [lat_array[this_final_index], lng_array[this_final_index], \
                                                  match_scenario_array[this_final_index], \
                                                  country_longname_array[this_final_index], \
                                                  country_shortname_array[this_final_index], \
                                                  administration_area_level_1_longname_array[this_final_index], \
                                                  administration_area_level_2_longname_array[this_final_index], \
                                                  administration_area_level_3_longname_array[this_final_index], \
                                                  administration_area_level_4_longname_array[this_final_index], \
                                                  administration_area_level_5_longname_array[this_final_index], \
                                                  locality_longname_array[this_final_index], \
                                                  locality_1_longname_array[this_final_index], \
                                                  locality_2_longname_array[this_final_index], \
                                                  text_encoded_addr_array[this_final_index], \
                                                  encoded_addr_array[this_final_index], \
                                                  addr_name_array[this_final_index], \
                                                  addr_full_array[this_final_index]]
                                    row_records_array.append(row_record)
                                    break
                        # Compute the rank for the best-quality geocoding solution associated with each unique lat/lon pair. 
                        good_records_scenario_rank = []
                        for row_records_array_this in row_records_array:
                            this_final_record_scenario = row_records_array_this[2]
                            this_scenario_rank = [i for i, x in enumerate(result_scenario_list) if x == this_final_record_scenario] #len must be >=1
                            good_records_scenario_rank.append(this_scenario_rank[0])
                        indices_for_sorted = [i[0] for i in sorted(enumerate(good_records_scenario_rank), key=lambda x:x[1])]
                        # Write the best-quality solutions associated with each of the unique lat/lon pairs to the output.
                        for index_for_sorted in indices_for_sorted:
                            outfile_sheet.write_row(row_number_write, 0, tuple(row + row_records_array[index_for_sorted]))
                            row_number_write = row_number_write + 1
                            print(str(row_number) + ': ' + row_records_array[index_for_sorted][2] +'. Found for ... ' + row_records_array[index_for_sorted][13] \
                                  + ' ' + str(row_records_array[index_for_sorted][0]) + ' ' + str(row_records_array[index_for_sorted][1]))  
                print('load number: ' + str(load_number))         
print('total load number: ' + str(load_number))

# Close files
outfile_obj.close() # Save the output
infile_obj.close() # Release the input

print("----- Module Completed -----")
print(datetime.datetime.now())
