# [Description] ------------------------------
# Module name "Geomatching_ICOLD.py"
# This module geo-matches (table-associates) records in a georeferenced regional register or inventory
# (with latitude/longitude) with records in the ICOLD World Register of Dams (WRD) for the same region.
# In the output, the geo-matched WRD records will be given the lat/lon coordinates as documented in the
# georeferenced regional register. Meanwhile the QA level of each geo-matched WRD record will also be
# labeled in the output. See Wang et al. (2021) for method details.

# Example in this module is given for Brazil.
# The original regional register for Brazil (before reverse geocoding) is Relatório de Segurança de Barragens
# (Dams Safety Report) (SNISB, 2017), accessed freely from
# http://www.snisb.gov.br/portal/snisb/relatorio-anual-de-seguranca-de-barragem/2017.
# The full reference of this register is: 
# Sistema Nacional de Informações sobre Segurança de Barragens (SNISB, Brazilian National Dam Safety
# Information System): Relatório de Segurança de Barragens 2017 (Dams Safety Report 2017) [data set],
# http://www.snisb.gov.br/portal/snisb/relatorio-anual-de-seguranca-de-barragem/2017, 2017.
# The ICOLD WRD records were accessed from https://www.icold-cigb.org.

# Reference: Wang, J., Walter, B.A., Yao, F., Song, C., Ding, M., Maroof, M.A.S., Zhu, J., Fan, C., Xin, A.,
# McAlister, J.M., Sikder, M.S., Sheng, Y., Allen, G.H., Crétaux, J.-F., and Wada, Y., 2021. GeoDAR:
# Georeferenced global dam and reservoir database for bridging attributes and geolocations. Earth System
# Science Data, in review.

# Script written by: Jida Wang
# Last update: March 4, 2021
# Contact: jidawang@ksu.edu; gdbruins@ucla.edu
#---------------------------------------------



# [Preparation] ------------------------------
# 1. The module "Reverse_geocoding_register.py" needs to be run first before running the current module.
# See Descriptions of "Reverse_geocoding_register.py" for more details.
# 2. Make sure that "Georeferencing_functions.py" (including customized common functions) has been placed
# in the same directory as that of this module. 
#---------------------------------------------



# [Setup] -----------------------------------
# Inputs
# 1. register_file: full path of the reverse-geocoded regional register. 
# This file is the output of module "Reverse_geocoding_register.py".
# The file for reverse-geocoded RSB (Brazil) was provided as "CadastroRSB2017_Portal_SNISB(v4)_revgeo.xlsx"
registry_file = r"...\CadastroRSB2017_Portal_SNISB(v4)_revgeo.xlsx"

# 2. ICOLD_file: full path of ICOLD WRD.
# The recent WRD (not released in this repository) can be accessed from ICOLD (https://www.icold-cigb.org). 
ICOLD_file = r"...\export_registre13_3_2019_cleaned.xlsx"

# 3. country_lookup_table: full path of the lookup table for country ISO 3166-2 codes (file provided).
country_lookup_table = r'...\Countries_lookup.csv'

# 4. similarity_threshold: numeric value for the minimum similarity score between two sequences (such as
# dam names from ICOLD WRD and the regional register) that were considered to be equivalent.
similarity_threshold = 6.0/7.0 #around 85%

# Output
# geo_matched_records: full path of the geo-matched WRD records.
geo_matched_records = r"...\Geo_matched_ICOLD_Brazil.xlsx"
#---------------------------------------------



# [Script] -----------------------------------
# Import built-in functions and tools
import http, urllib, csv, json, unicodedata, sys, datetime, xlsxwriter, openpyxl, re, statistics
from statistics import stdev
from difflib import SequenceMatcher
# Import customized functions (see Preparation and descriptions within "Georeferencing_functions.py"). 
from Georeferencing_functions import remove_accents, year_similar, similar, damname_similar, river_similar

print("----- Module Started -----")
print(datetime.datetime.now())

# Read country names and ISO codes
country_ISO_array = []
country_NAME_array = []
country_NAME_array_no_accent = []
with open(country_lookup_table, "r") as csvinput:
    for row in csv.reader(csvinput, delimiter=','):
        country_ISO_array.append((row[1]).lower().strip()) #country ISO codes
        country_NAME_array.append((row[6]).lower().strip()) #ICOLD country names
        country_NAME_array_no_accent.append(remove_accents((row[6]).lower().strip())) #ICOLD country names without accents 

# Read attributes from registry_file
registry_obj = openpyxl.load_workbook(registry_file)
registry_sheet = registry_obj.active
registry_countries = []
registry_countries_ISO = []
registry_dam_names = []
registry_lats = []
registry_lons = []
registry_addrs = []
registry_rivers = []
registry_years = []
registry_IDs = []
ii = 0
for each_row in registry_sheet:
    if ii > 0:
        row = []
        for cell in each_row:
            if cell.value == None:
                row.append('')
            else:
                row.append((str(cell.value)).lower().strip())
        # Replace province names as spelled in registry_file by those as spelled in ICOLD WRD (for Brazil only).
        # Caution: This clean-up is necessary as province names in both inventories are not consistent.  
        original_province = row[2]
        if original_province=='AC'.lower().strip():
            replace_province ='acre'.lower().strip()
        if original_province=='AL'.lower().strip():
            replace_province ='Alagoas'.lower().strip()
        if original_province=='AM'.lower().strip():
            replace_province ='Amazonas'.lower().strip()
        if original_province=='AP'.lower().strip():
            replace_province ='Amapá'.lower().strip()
        if original_province=='BA'.lower().strip():
            replace_province ='Bahia'.lower().strip()
        if original_province=='CE'.lower().strip():
            replace_province ='Ceará'.lower().strip()
        if original_province=='DF'.lower().strip():
            replace_province ='Distrito Federal'.lower().strip()
        if original_province=='ES'.lower().strip():
            replace_province ='Espírito Santo'.lower().strip()
        if original_province=='GO'.lower().strip():
            replace_province ='Goiás'.lower().strip()
        if original_province=='MA'.lower().strip():
            replace_province ='Maranhão'.lower().strip()
        if original_province=='MG'.lower().strip():
            replace_province ='Minas Gerais'.lower().strip()
        if original_province=='MS'.lower().strip():
            replace_province ='Mato Grosso do Sul'.lower().strip()
        if original_province=='MT'.lower().strip():
            replace_province ='Mato Grosso'.lower().strip()
        if original_province=='PA'.lower().strip():
            replace_province ='Pará'.lower().strip()
        if original_province=='PB'.lower().strip():
            replace_province ='Paraíba'.lower().strip()
        if original_province=='PE'.lower().strip():
            replace_province ='Pernambuco'.lower().strip()
        if original_province=='PI'.lower().strip():
            replace_province ='Piauí'.lower().strip()
        if original_province=='PR'.lower().strip():
            replace_province ='Paraná'.lower().strip()
        if original_province=='RJ'.lower().strip():
            replace_province ='Rio de Janeiro'.lower().strip()
        if original_province=='RN'.lower().strip():
            replace_province ='Rio Grande do Norte'.lower().strip()
        if original_province=='RO'.lower().strip():
            replace_province ='Rondônia'.lower().strip()
        if original_province=='RR'.lower().strip():
            replace_province ='Roraima'.lower().strip()
        if original_province=='RS'.lower().strip():
            replace_province ='Rio Grande do Sul'.lower().strip()
        if original_province=='SC'.lower().strip():
            replace_province ='Santa Catarina'.lower().strip()
        if original_province=='SE'.lower().strip():
            replace_province ='Sergipe'.lower().strip()
        if original_province=='SP'.lower().strip():
            replace_province ='São Paulo'.lower().strip()
        if original_province=='TO'.lower().strip():
            replace_province ='Tocantins'.lower().strip()
        # Generate parsed address
        # Component sequence: nearest town and province in the registry, and country, administrative levels 1-5, and local levels 1-2 from reverse geocoding
        registry_addrs.append([row[1], replace_province, row[54:72]]) 
        registry_dam_names.append(row[0]) 
        registry_lats.append(row[15])
        registry_lons.append(row[16])
        registry_rivers.append(row[29])
        original_year = row[26] 
        # Ensure the format of construction year is correct (after manual inspection). 
        if len(original_year) >= 4:
            replace_year = original_year[0:4]
        else:
            replace_year = ''
        registry_years.append(replace_year)
        registry_IDs.append(row[52])
        registry_countries.append('brazil')
        r_country_index = [i for i, x in enumerate(country_NAME_array) if x == 'brazil']
        registry_countries_ISO.append(country_ISO_array[r_country_index[0]])
    ii = ii + 1

# Define input spreadsheet (original WRD) and output spreadsheet (geo-matched WRD).
ICOLD_obj = openpyxl.load_workbook(ICOLD_file) 
ICOLD_sheet = ICOLD_obj.active #input spreadsheet (original WRD)
OUT_obj = xlsxwriter.Workbook(geo_matched_records) 
OUT_sheet = OUT_obj.add_worksheet("Geo-matched-WRD") #output spreadsheet (geo-matched WRD)

# Read original WRD records
infile_rows = [] 
for each_row in ICOLD_sheet:
    row = []
    for cell in each_row:
        if cell.value == None:
            row.append('')
        else:
            row.append(str(cell.value))  
    infile_rows.append(row)

# Loop through each WRD record and geo-match it with the most similar register record.
outfile_sheet_row = 0 # Initiate the output record index
ii = 0
for ii in range(0, len(infile_rows)):
    row = infile_rows[ii]    
    if ii == 0: # Header
        # Write header
        OUT_sheet.write_row(outfile_sheet_row, 0, \
                            tuple(row + ['reg_QA','reg_lat','reg_lon','reg_ID','reg_dam','reg_river','reg_year','reg_cntry','reg_state','reg_town', \
                                         'rgreg_cntry','rgreg_adm1','rgreg_adm2','rgreg_adm3','rgreg_adm4','rgreg_adm5','rgreg_loc','rgreg_loc1','rgreg_loc2']))
        # "rgreg" means: reverse-geocoded register
        outfile_sheet_row = outfile_sheet_row + 1
        print('hearder')
    else:
        # Retrieve ICOLD attribute values for this WRD record
        dam_name = row[23].lower().strip()
        dam_other_name = row[26].lower().strip()
        reservoir_name = row[31].lower().strip()
        river_name = row[33].lower().strip() 
        year_name = row[41].lower().strip()
        state_province = row[38].lower().strip()
        town_original = row[24].lower().strip()
        country = row[10].lower().strip()
        country_index = [i for i, x in enumerate(country_NAME_array) if x == country]
        this_country_ISO = country_ISO_array[country_index[0]] ##
        this_keep_FIN = (row[48]).lower().strip()
        # If "this_keep_FIN = 1", it indicates this ICOLD WRD record is unique. This is a result of WRD duplicate removal (see Methods in Wang et al. (2021). 

        if (this_country_ISO in registry_countries_ISO) and this_keep_FIN == '1':
            state_province_ascii = remove_accents(state_province) # Remove accents in the WRD state/province names (if any)
            town_ascii = remove_accents(town_original) # Remove accents in the WRD town names (if any)

            QA_mark = 0 # Initiate a QA indicator (0 means the QA is not yet optimized, and 1 means the QA has been optimized, i.e., QA level = 1).
            # Decreasing precedence of QA levels: M1 (1, 1.2, 1.3, 1.4), M2 (2, 2.2., 2.3, 2.4), M3 (3, 3.2, 3.3, 3.4). Also see Wang et al. (2021)
            #reg_i_QA1_array = [] # M1:1 No need to generate this array as once this optinmal scenario is reached, the following FOR loop will be broken.
            reg_i_QA1p2_array = [] # M1:1.2
            reg_i_QA1p3_array = [] # M1:1.3
            reg_i_QA1p4_array = [] # M1:1.4 
            reg_i_QA2_array=[] # M2:2
            reg_i_QA2p2_array=[] # M2:2.2 
            reg_i_QA2p3_array=[] # M2:2.3
            reg_i_QA2p4_array=[] # M2:2.4
            reg_i_QA3_array=[] # M3:3
            reg_i_QA3p2_array=[] # M3:3.2
            reg_i_QA3p3_array=[] # M3:3.3
            reg_i_QA3p4_array=[] # M3:3.4

            # Loop through each register record and calculate QA levels of the geo-matched candidates. Also see Wang et al. (2021). 
            for reg_i in range(0, len(registry_dam_names)):
                # Retrieve register attribute values
                this_registry_ID = registry_IDs[reg_i]
                this_registry_river = registry_rivers[reg_i]
                this_registry_year= registry_years[reg_i] 
                this_registry_dam_name = registry_dam_names[reg_i]
                this_registry_lat = registry_lats[reg_i]
                this_registry_lon = registry_lons[reg_i]
                this_registry_countries_ISO = registry_countries_ISO[reg_i]
                this_registry_country = registry_countries[reg_i]
                this_registry_town_ascii = remove_accents(registry_addrs[reg_i][0]) # Accents in address components removed (in any). 
                this_registry_province_ascii = remove_accents(registry_addrs[reg_i][1]) # Same below. 
                country_longname_ascii = remove_accents(registry_addrs[reg_i][2][0])
                country_shortname = remove_accents(registry_addrs[reg_i][2][1])
                administration_area_level_1_longname_ascii = remove_accents(registry_addrs[reg_i][2][2])
                administration_area_level_1_shortname_ascii = remove_accents(registry_addrs[reg_i][2][3]) 
                administration_area_level_2_longname_ascii = remove_accents(registry_addrs[reg_i][2][4])
                administration_area_level_2_shortname_ascii = remove_accents(registry_addrs[reg_i][2][5]) 
                administration_area_level_3_longname_ascii = remove_accents(registry_addrs[reg_i][2][6]) 
                administration_area_level_3_shortname_ascii = remove_accents(registry_addrs[reg_i][2][7]) 
                administration_area_level_4_longname_ascii = remove_accents(registry_addrs[reg_i][2][8])
                administration_area_level_4_shortname_ascii = remove_accents(registry_addrs[reg_i][2][9])
                administration_area_level_5_longname_ascii = remove_accents(registry_addrs[reg_i][2][10])
                administration_area_level_5_shortname_ascii = remove_accents(registry_addrs[reg_i][2][11])
                locality_longname_ascii = remove_accents(registry_addrs[reg_i][2][12])
                locality_shortname_ascii = remove_accents(registry_addrs[reg_i][2][13])
                locality_1_longname_ascii = remove_accents(registry_addrs[reg_i][2][14])
                locality_1_shortname_ascii = remove_accents(registry_addrs[reg_i][2][15])
                locality_2_longname_ascii = remove_accents(registry_addrs[reg_i][2][16])
                locality_2_shortname_ascii = remove_accents(registry_addrs[reg_i][2][17])        

                # Reorganize register address components on different administrative levels
                # Components on the country level
                country_google_array = [this_registry_countries_ISO, country_shortname]
                # All possible components on the state/provincial level
                state_google_array = [this_registry_province_ascii, \
                                      administration_area_level_1_longname_ascii, administration_area_level_1_shortname_ascii, \
                                      administration_area_level_2_longname_ascii, administration_area_level_2_shortname_ascii, \
                                      administration_area_level_3_longname_ascii, administration_area_level_3_shortname_ascii]
                # All possible components on the city/township level
                town_google_array = [this_registry_town_ascii, \
                                     administration_area_level_2_longname_ascii, administration_area_level_2_shortname_ascii, \
                                     administration_area_level_3_longname_ascii, administration_area_level_3_shortname_ascii, \
                                     administration_area_level_4_longname_ascii, administration_area_level_4_shortname_ascii, \
                                     administration_area_level_5_longname_ascii, administration_area_level_5_shortname_ascii, \
                                     locality_longname_ascii, locality_shortname_ascii, \
                                     locality_1_longname_ascii, locality_1_shortname_ascii, \
                                     locality_2_longname_ascii, locality_2_shortname_ascii]

                # Compute similarity for different administrative levels
                similarity_metric_country_array = [] # County level
                for this_country_google in country_google_array:
                    similarity_metric_country_array.append(similar(this_country_ISO, this_country_google))              
                similarity_metric_state_array = [] # State/provincial level
                for this_state_google in state_google_array:
                    similarity_metric_state_array.append(similar(state_province_ascii, this_state_google))                  
                similarity_metric_town_array = [] # City/township level
                for this_town_google in town_google_array:
                    similarity_metric_town_array.append(similar(town_ascii, this_town_google))

                # Perform another round of similar comparison that considers the containment relationship,
                # e.g., "city of Manhattan" vs "Manhattan", and "Kansas/Colorado" vs "Kansas" (if the reservoir is on the border). 
                google_state_arrays = state_google_array # "Google" indicates the regsiter after reverse geocoding using the Google API. 
                google_town_arrays = town_google_array
                # Decompose administrative components by possible delimiter.  
                google_state_arrays_c = [] # register state/province names
                for a_i in google_state_arrays:
                    if ('\\' in a_i) or ('/' in a_i):
                        for this_slash1 in a_i.split('/'):
                            for this_slash2 in this_slash1.split('\\'):
                                if this_slash2 != '':
                                    google_state_arrays_c.append(this_slash2.strip())
                    else:
                        google_state_arrays_c.append(a_i.strip())
                google_town_arrays_c = [] # register town names
                for a_i in google_town_arrays:
                    if ('\\' in a_i) or ('/' in a_i):
                        for this_slash1 in a_i.split('/'):
                            for this_slash2 in this_slash1.split('\\'):
                                if this_slash2 != '':
                                    google_town_arrays_c.append(this_slash2.strip())
                    else:
                        google_town_arrays_c.append(a_i.strip())          
                state_province_ascii_c = [] # WRD state/province names
                for a_i in [state_province_ascii]:
                    if ('\\' in a_i) or ('/' in a_i):
                        for this_slash1 in a_i.split('/'):
                            for this_slash2 in this_slash1.split('\\'):
                                if this_slash2 != '':
                                    state_province_ascii_c.append(this_slash2.strip())
                    else:
                        state_province_ascii_c.append(a_i.strip())                           
                town_ascii_c = [] # WRD town names
                for a_i in [town_ascii]:
                    if ('\\' in a_i) or ('/' in a_i):
                        for this_slash1 in a_i.split('/'):
                            for this_slash2 in this_slash1.split('\\'):
                                if this_slash2 != '':
                                    town_ascii_c.append(this_slash2.strip())
                    else:
                        town_ascii_c.append(a_i.strip())  
                containment_check_state = 0
                # If containment_check_state = 1, it means that the string of state/province in ICOLD WRD contains that in the register (or vice versa).
                for this_google_state in google_state_arrays_c:
                    for this_state_province_ascii in state_province_ascii_c:
                        if (this_state_province_ascii in this_google_state) == True and (this_state_province_ascii != this_google_state) == True and \
                           (this_state_province_ascii != '' and this_google_state != '' and this_state_province_ascii != '-999' and this_google_state != '-999'): #ICOLD contained by register
                            if this_google_state.find(this_state_province_ascii) == 0: #'manhattan city': 'manhattan'
                                if this_google_state[this_google_state.find(this_state_province_ascii)+len(this_state_province_ascii)] == ' ' or \
                                   this_google_state[this_google_state.find(this_state_province_ascii)+len(this_state_province_ascii)] == '-':
                                    containment_check_state = 1
                                    break
                            else:
                                if (this_google_state.find(this_state_province_ascii)+len(this_state_province_ascii)) == len(this_google_state): #'city of manhattan': 'manhattan'
                                    if this_google_state[this_google_state.find(this_state_province_ascii)-1] == ' ' or \
                                       this_google_state[this_google_state.find(this_state_province_ascii)-1] == '-':
                                        containment_check_state = 1
                                        break
                        else:
                            if (this_google_state in this_state_province_ascii) == True and (this_state_province_ascii != this_google_state) == True and \
                               (this_state_province_ascii != '' and this_google_state != '' and this_state_province_ascii != '-999' and this_google_state != '-999'): #ICOLD containing register
                                if this_state_province_ascii.find(this_google_state) == 0: #'manhattan city': 'manhattan'
                                    if this_state_province_ascii[this_state_province_ascii.find(this_google_state)+len(this_google_state)] == ' ' or \
                                       this_state_province_ascii[this_state_province_ascii.find(this_google_state)+len(this_google_state)] == '-':
                                        containment_check_state = 1
                                        break
                                else:
                                    if (this_state_province_ascii.find(this_google_state)+len(this_google_state)) == len(this_state_province_ascii): #'city of manhattan': 'manhattan'
                                        if this_state_province_ascii[this_state_province_ascii.find(this_google_state)-1] == ' ' or \
                                           this_state_province_ascii[this_state_province_ascii.find(this_google_state)-1] == '-':
                                            containment_check_state = 1
                                            break
                    if containment_check_state == 1:
                        break
                containment_check_town = 0
                # If containment_check_town = 1, it means that the string of town in ICOLD WRD contains that in the register (or vice versa).
                for this_google_town in google_town_arrays_c:
                    for this_town_ascii in town_ascii_c:
                        if (this_town_ascii in this_google_town) == True and (this_town_ascii != this_google_town) == True and \
                           (this_town_ascii != '' and this_google_town != '' and this_town_ascii != '-999' and this_google_town != '-999'): #ICOLD contained by register
                            if this_google_town.find(this_town_ascii) == 0: #'manhattan city': 'manhattan'
                                if this_google_town[this_google_town.find(this_town_ascii)+len(this_town_ascii)] == ' ' or \
                                   this_google_town[this_google_town.find(this_town_ascii)+len(this_town_ascii)] == '-':
                                    containment_check_town = 1
                                    break
                            else:
                                if (this_google_town.find(this_town_ascii)+len(this_town_ascii)) == len(this_google_town): #'city of manhattan': 'manhattan'
                                    if this_google_town[this_google_town.find(this_town_ascii)-1] == ' ' or \
                                       this_google_town[this_google_town.find(this_town_ascii)-1] == '-':
                                        containment_check_town = 1
                                        break
                        else:
                            if (this_google_town in this_town_ascii) == True and (this_town_ascii != this_google_town) == True and \
                               (this_town_ascii != '' and this_google_town != '' and this_town_ascii != '-999' and this_google_town != '-999'): #ICOLD containing register
                                if this_town_ascii.find(this_google_town) == 0: #'manhattan city': 'manhattan'
                                    if this_town_ascii[this_town_ascii.find(this_google_town)+len(this_google_town)] == ' ' or \
                                       this_town_ascii[this_town_ascii.find(this_google_town)+len(this_google_town)] == '-':
                                        containment_check_town = 1
                                        break
                                else:
                                    if (this_town_ascii.find(this_google_town)+len(this_google_town)) == len(this_town_ascii): #'city of manhattan': 'manhattan'
                                        if this_town_ascii[this_town_ascii.find(this_google_town)-1] == ' ' or \
                                           this_town_ascii[this_town_ascii.find(this_google_town)-1] == '-':
                                            containment_check_town = 1
                                            break
                    if containment_check_town == 1:
                        break

                # Determine whether names of each of the administrative levels (country, state/province, and city/township) are equivalent between ICOLD WRD and the register. 
                if this_country_ISO == this_registry_countries_ISO or this_country_ISO == country_shortname:
                    country_pass = 1 # indicating country names are equivalent. 
                else:
                    country_pass = 0
                if max(similarity_metric_state_array) >= similarity_threshold or containment_check_state == 1:
                    state_pass = 1 # indicating state/province names are equivalent. 
                else:
                    state_pass = 0
                if max(similarity_metric_town_array) >= similarity_threshold or containment_check_town == 1:
                    town_pass = 1 # indicating town/city names are equivalent. 
                else:
                    town_pass = 0

                # Compute similarity for other key attributes: dam/reservoir name, river name, and completion year. 
                name_pass = damname_similar(similarity_threshold, dam_name, dam_other_name, reservoir_name, this_registry_dam_name, this_country_ISO)               
                river_pass = river_similar(similarity_threshold, river_name, this_registry_river)
                year_pass = year_similar(year_name, this_registry_year)

                # Discuss QA levels and write the optimal geo-matched record to the output. Also see Wang et al. (2021) for QA scenarios. 
                if (name_pass==1 or name_pass==0.5) and country_pass==1 and ( (state_pass==1 and state_province_ascii !='') or state_province_ascii==''):
                    if town_pass==1:
                        if (river_pass==1 or year_pass==1) and name_pass==1: # M1:1 (optimal scenario). Once this scenario is reached, the FOR loop will be terminated.  
                            QA_mark = 1
                            print(dam_name + '...' + dam_other_name + '...' + reservoir_name + ':::::::' + this_registry_dam_name)
                            OUT_sheet.write_row(outfile_sheet_row, 0, tuple(row + ['1', this_registry_lat, this_registry_lon, this_registry_ID, \
                                                                                   this_registry_dam_name, this_registry_river, this_registry_year, \
                                                                                   this_registry_country, \
                                                                                   registry_addrs[reg_i][1], registry_addrs[reg_i][0], \
                                                                                   registry_addrs[reg_i][2][0], registry_addrs[reg_i][2][2], \
                                                                                   registry_addrs[reg_i][2][4], registry_addrs[reg_i][2][6], \
                                                                                   registry_addrs[reg_i][2][8], registry_addrs[reg_i][2][10], \
                                                                                   registry_addrs[reg_i][2][12], registry_addrs[reg_i][2][14], \
                                                                                   registry_addrs[reg_i][2][16]]))                                              
                            outfile_sheet_row = outfile_sheet_row + 1
                            break
                        elif (river_pass==0.5 or year_pass==1) and name_pass==1:
                            reg_i_QA1p2_array.append(reg_i)
                        elif (river_pass==1 or year_pass==1) and name_pass==0.5:
                            reg_i_QA1p3_array.append(reg_i)
                        elif (river_pass==0.5 or year_pass==1) and name_pass==0.5:
                            reg_i_QA1p4_array.append(reg_i)
                        elif (river_name=='' or this_registry_river=='') and (year_name=='' or this_registry_year=='') and state_province_ascii !='':
                            if name_pass==1:
                                reg_i_QA2_array.append(reg_i)
                            else:
                                reg_i_QA2p3_array.append(reg_i)
                        elif (river_name=='' or this_registry_river=='') and (year_name=='' or this_registry_year=='') and state_province_ascii =='':
                            if name_pass==1:
                                reg_i_QA3_array.append(reg_i)
                            else:
                                reg_i_QA3p3_array.append(reg_i)
                    elif town_pass==0 and river_pass>0 and year_pass==1 and state_province_ascii !='':   
                        if name_pass==1 and river_pass==1:
                            reg_i_QA2_array.append(reg_i)
                        elif name_pass==1 and river_pass==0.5:
                            reg_i_QA2p2_array.append(reg_i)
                        elif name_pass==0.5 and river_pass==1:
                            reg_i_QA2p3_array.append(reg_i)
                        else:
                            reg_i_QA2p4_array.append(reg_i)
                    elif town_pass==0 and river_pass>0 and year_pass==1 and state_province_ascii =='':
                        if name_pass==1 and river_pass==1:
                            reg_i_QA3_array.append(reg_i)
                        elif name_pass==1 and river_pass==0.5:
                            reg_i_QA3p2_array.append(reg_i)
                        elif name_pass==0.5 and river_pass==1:
                            reg_i_QA3p3_array.append(reg_i)
                        else:
                            reg_i_QA3p4_array.append(reg_i)
                    elif town_pass==0 and (river_pass>0 or year_pass==1):
                        if name_pass==1 and (river_pass==1 or year_pass==1):
                            reg_i_QA3_array.append(reg_i)
                        elif name_pass==1 and river_pass==0.5:
                            reg_i_QA3p2_array.append(reg_i)
                        elif name_pass==0.5 and (river_pass==1 or year_pass==1):
                            reg_i_QA3p3_array.append(reg_i)
                        else:
                            reg_i_QA3p4_array.append(reg_i)
            # If the optimal scenario (M1:1) was not reached, write the first register record with the next best QA level to the output.
            if QA_mark != 1:
                if len(reg_i_QA1p2_array)>0:
                    print('here QA1.2 === ' + dam_name + '...' + dam_other_name + '...' + reservoir_name + ':::::::' + registry_dam_names[reg_i_QA1p2_array[0]])
                    OUT_sheet.write_row(outfile_sheet_row, 0, tuple(row + ['1.2', registry_lats[reg_i_QA1p2_array[0]], registry_lons[reg_i_QA1p2_array[0]], registry_IDs[reg_i_QA1p2_array[0]], \
                                                                           registry_dam_names[reg_i_QA1p2_array[0]], registry_rivers[reg_i_QA1p2_array[0]], registry_years[reg_i_QA1p2_array[0]], \
                                                                           registry_countries[reg_i_QA1p2_array[0]], \
                                                                           registry_addrs[reg_i_QA1p2_array[0]][1], registry_addrs[reg_i_QA1p2_array[0]][0], \
                                                                           registry_addrs[reg_i_QA1p2_array[0]][2][0], registry_addrs[reg_i_QA1p2_array[0]][2][2], \
                                                                           registry_addrs[reg_i_QA1p2_array[0]][2][4], registry_addrs[reg_i_QA1p2_array[0]][2][6], \
                                                                           registry_addrs[reg_i_QA1p2_array[0]][2][8], registry_addrs[reg_i_QA1p2_array[0]][2][10], \
                                                                           registry_addrs[reg_i_QA1p2_array[0]][2][12], registry_addrs[reg_i_QA1p2_array[0]][2][14], \
                                                                           registry_addrs[reg_i_QA1p2_array[0]][2][16] ]))               
                    outfile_sheet_row = outfile_sheet_row + 1

                elif len(reg_i_QA1p3_array)>0:
                    print('here QA1.3 === ' + dam_name + '...' + dam_other_name + '...' + reservoir_name + ':::::::' + registry_dam_names[reg_i_QA1p3_array[0]])
                    OUT_sheet.write_row(outfile_sheet_row, 0, tuple(row + ['1.3', registry_lats[reg_i_QA1p3_array[0]], registry_lons[reg_i_QA1p3_array[0]], registry_IDs[reg_i_QA1p3_array[0]], \
                                                                           registry_dam_names[reg_i_QA1p3_array[0]], registry_rivers[reg_i_QA1p3_array[0]], registry_years[reg_i_QA1p3_array[0]], \
                                                                           registry_countries[reg_i_QA1p3_array[0]], \
                                                                           registry_addrs[reg_i_QA1p3_array[0]][1], registry_addrs[reg_i_QA1p3_array[0]][0], \
                                                                           registry_addrs[reg_i_QA1p3_array[0]][2][0], registry_addrs[reg_i_QA1p3_array[0]][2][2], \
                                                                           registry_addrs[reg_i_QA1p3_array[0]][2][4], registry_addrs[reg_i_QA1p3_array[0]][2][6], \
                                                                           registry_addrs[reg_i_QA1p3_array[0]][2][8], registry_addrs[reg_i_QA1p3_array[0]][2][10], \
                                                                           registry_addrs[reg_i_QA1p3_array[0]][2][12], registry_addrs[reg_i_QA1p3_array[0]][2][14], \
                                                                           registry_addrs[reg_i_QA1p3_array[0]][2][16] ]))
                    outfile_sheet_row = outfile_sheet_row + 1

                elif len(reg_i_QA1p4_array)>0:
                    print('here QA1.4 === ' + dam_name + '...' + dam_other_name + '...' + reservoir_name + ':::::::' + registry_dam_names[reg_i_QA1p4_array[0]])
                    OUT_sheet.write_row(outfile_sheet_row, 0, tuple(row + ['1.4', registry_lats[reg_i_QA1p4_array[0]], registry_lons[reg_i_QA1p4_array[0]], registry_IDs[reg_i_QA1p4_array[0]], \
                                                                           registry_dam_names[reg_i_QA1p4_array[0]], registry_rivers[reg_i_QA1p4_array[0]], registry_years[reg_i_QA1p4_array[0]], \
                                                                           registry_countries[reg_i_QA1p4_array[0]], \
                                                                           registry_addrs[reg_i_QA1p4_array[0]][1], registry_addrs[reg_i_QA1p4_array[0]][0], \
                                                                           registry_addrs[reg_i_QA1p4_array[0]][2][0], registry_addrs[reg_i_QA1p4_array[0]][2][2], \
                                                                           registry_addrs[reg_i_QA1p4_array[0]][2][4], registry_addrs[reg_i_QA1p4_array[0]][2][6], \
                                                                           registry_addrs[reg_i_QA1p4_array[0]][2][8], registry_addrs[reg_i_QA1p4_array[0]][2][10], \
                                                                           registry_addrs[reg_i_QA1p4_array[0]][2][12], registry_addrs[reg_i_QA1p4_array[0]][2][14], \
                                                                           registry_addrs[reg_i_QA1p4_array[0]][2][16] ]))
                    outfile_sheet_row = outfile_sheet_row + 1
                    
                elif len(reg_i_QA2_array)>0:
                    print('here QA2 === ' + dam_name + '...' + dam_other_name + '...' + reservoir_name + ':::::::' + registry_dam_names[reg_i_QA2_array[0]])
                    OUT_sheet.write_row(outfile_sheet_row, 0, tuple(row + ['2', registry_lats[reg_i_QA2_array[0]], registry_lons[reg_i_QA2_array[0]], registry_IDs[reg_i_QA2_array[0]], \
                                                                           registry_dam_names[reg_i_QA2_array[0]], registry_rivers[reg_i_QA2_array[0]], registry_years[reg_i_QA2_array[0]], \
                                                                           registry_countries[reg_i_QA2_array[0]], \
                                                                           registry_addrs[reg_i_QA2_array[0]][1], registry_addrs[reg_i_QA2_array[0]][0], \
                                                                           registry_addrs[reg_i_QA2_array[0]][2][0], registry_addrs[reg_i_QA2_array[0]][2][2], \
                                                                           registry_addrs[reg_i_QA2_array[0]][2][4], registry_addrs[reg_i_QA2_array[0]][2][6], \
                                                                           registry_addrs[reg_i_QA2_array[0]][2][8], registry_addrs[reg_i_QA2_array[0]][2][10], \
                                                                           registry_addrs[reg_i_QA2_array[0]][2][12], registry_addrs[reg_i_QA2_array[0]][2][14], \
                                                                           registry_addrs[reg_i_QA2_array[0]][2][16] ]))
                    outfile_sheet_row = outfile_sheet_row + 1
                elif len(reg_i_QA2p2_array)>0:
                    print('here QA2.2 === ' + dam_name + '...' + dam_other_name + '...' + reservoir_name + ':::::::' + registry_dam_names[reg_i_QA2p2_array[0]])
                    OUT_sheet.write_row(outfile_sheet_row, 0, tuple(row + ['2.2', registry_lats[reg_i_QA2p2_array[0]], registry_lons[reg_i_QA2p2_array[0]], registry_IDs[reg_i_QA2p2_array[0]], \
                                                                           registry_dam_names[reg_i_QA2p2_array[0]], registry_rivers[reg_i_QA2p2_array[0]], registry_years[reg_i_QA2p2_array[0]], \
                                                                           registry_countries[reg_i_QA2p2_array[0]], \
                                                                           registry_addrs[reg_i_QA2p2_array[0]][1], registry_addrs[reg_i_QA2p2_array[0]][0], \
                                                                           registry_addrs[reg_i_QA2p2_array[0]][2][0], registry_addrs[reg_i_QA2p2_array[0]][2][2], \
                                                                           registry_addrs[reg_i_QA2p2_array[0]][2][4], registry_addrs[reg_i_QA2p2_array[0]][2][6], \
                                                                           registry_addrs[reg_i_QA2p2_array[0]][2][8], registry_addrs[reg_i_QA2p2_array[0]][2][10], \
                                                                           registry_addrs[reg_i_QA2p2_array[0]][2][12], registry_addrs[reg_i_QA2p2_array[0]][2][14], \
                                                                           registry_addrs[reg_i_QA2p2_array[0]][2][16] ]))
                    outfile_sheet_row = outfile_sheet_row + 1

                elif len(reg_i_QA2p3_array)>0:
                    #match_count_2 = match_count_2 + 1
                    print('here QA2.3 === ' + dam_name + '...' + dam_other_name + '...' + reservoir_name + ':::::::' + registry_dam_names[reg_i_QA2p3_array[0]])
                    OUT_sheet.write_row(outfile_sheet_row, 0, tuple(row + ['2.3', registry_lats[reg_i_QA2p3_array[0]], registry_lons[reg_i_QA2p3_array[0]], registry_IDs[reg_i_QA2p3_array[0]], \
                                                                           registry_dam_names[reg_i_QA2p3_array[0]], registry_rivers[reg_i_QA2p3_array[0]], registry_years[reg_i_QA2p3_array[0]], \
                                                                           registry_countries[reg_i_QA2p3_array[0]], \
                                                                           registry_addrs[reg_i_QA2p3_array[0]][1], registry_addrs[reg_i_QA2p3_array[0]][0], \
                                                                           registry_addrs[reg_i_QA2p3_array[0]][2][0], registry_addrs[reg_i_QA2p3_array[0]][2][2], \
                                                                           registry_addrs[reg_i_QA2p3_array[0]][2][4], registry_addrs[reg_i_QA2p3_array[0]][2][6], \
                                                                           registry_addrs[reg_i_QA2p3_array[0]][2][8], registry_addrs[reg_i_QA2p3_array[0]][2][10], \
                                                                           registry_addrs[reg_i_QA2p3_array[0]][2][12], registry_addrs[reg_i_QA2p3_array[0]][2][14], \
                                                                           registry_addrs[reg_i_QA2p3_array[0]][2][16] ]))
                    outfile_sheet_row = outfile_sheet_row + 1

                elif len(reg_i_QA2p4_array)>0:
                    print('here QA2.4 === ' + dam_name + '...' + dam_other_name + '...' + reservoir_name + ':::::::' + registry_dam_names[reg_i_QA2p4_array[0]])
                    OUT_sheet.write_row(outfile_sheet_row, 0, tuple(row + ['2.4', registry_lats[reg_i_QA2p4_array[0]], registry_lons[reg_i_QA2p4_array[0]], registry_IDs[reg_i_QA2p4_array[0]], \
                                                                           registry_dam_names[reg_i_QA2p4_array[0]], registry_rivers[reg_i_QA2p4_array[0]], registry_years[reg_i_QA2p4_array[0]], \
                                                                           registry_countries[reg_i_QA2p4_array[0]], \
                                                                           registry_addrs[reg_i_QA2p4_array[0]][1], registry_addrs[reg_i_QA2p4_array[0]][0], \
                                                                           registry_addrs[reg_i_QA2p4_array[0]][2][0], registry_addrs[reg_i_QA2p4_array[0]][2][2], \
                                                                           registry_addrs[reg_i_QA2p4_array[0]][2][4], registry_addrs[reg_i_QA2p4_array[0]][2][6], \
                                                                           registry_addrs[reg_i_QA2p4_array[0]][2][8], registry_addrs[reg_i_QA2p4_array[0]][2][10], \
                                                                           registry_addrs[reg_i_QA2p4_array[0]][2][12], registry_addrs[reg_i_QA2p4_array[0]][2][14], \
                                                                           registry_addrs[reg_i_QA2p4_array[0]][2][16] ]))
                    outfile_sheet_row = outfile_sheet_row + 1
                    
                elif len(reg_i_QA3_array)>0:
                    print('here QA3 === ' + dam_name + '...' + dam_other_name + '...' + reservoir_name + ':::::::' + registry_dam_names[reg_i_QA3_array[0]])
                    OUT_sheet.write_row(outfile_sheet_row, 0, tuple(row + ['3', registry_lats[reg_i_QA3_array[0]], registry_lons[reg_i_QA3_array[0]], registry_IDs[reg_i_QA3_array[0]], \
                                                                           registry_dam_names[reg_i_QA3_array[0]], registry_rivers[reg_i_QA3_array[0]], registry_years[reg_i_QA3_array[0]], \
                                                                           registry_countries[reg_i_QA3_array[0]], \
                                                                           registry_addrs[reg_i_QA3_array[0]][1], registry_addrs[reg_i_QA3_array[0]][0], \
                                                                           registry_addrs[reg_i_QA3_array[0]][2][0], registry_addrs[reg_i_QA3_array[0]][2][2], \
                                                                           registry_addrs[reg_i_QA3_array[0]][2][4], registry_addrs[reg_i_QA3_array[0]][2][6], \
                                                                           registry_addrs[reg_i_QA3_array[0]][2][8], registry_addrs[reg_i_QA3_array[0]][2][10], \
                                                                           registry_addrs[reg_i_QA3_array[0]][2][12], registry_addrs[reg_i_QA3_array[0]][2][14], \
                                                                           registry_addrs[reg_i_QA3_array[0]][2][16] ]))
                    outfile_sheet_row = outfile_sheet_row + 1

                elif len(reg_i_QA3p2_array)>0:
                    print('here QA3.2 === ' + dam_name + '...' + dam_other_name + '...' + reservoir_name + ':::::::' + registry_dam_names[reg_i_QA3p2_array[0]])
                    OUT_sheet.write_row(outfile_sheet_row, 0, tuple(row + ['3.2', registry_lats[reg_i_QA3p2_array[0]], registry_lons[reg_i_QA3p2_array[0]], registry_IDs[reg_i_QA3p2_array[0]], \
                                                                           registry_dam_names[reg_i_QA3p2_array[0]], registry_rivers[reg_i_QA3p2_array[0]], registry_years[reg_i_QA3p2_array[0]], \
                                                                           registry_countries[reg_i_QA3p2_array[0]], \
                                                                           registry_addrs[reg_i_QA3p2_array[0]][1], registry_addrs[reg_i_QA3p2_array[0]][0], \
                                                                           registry_addrs[reg_i_QA3p2_array[0]][2][0], registry_addrs[reg_i_QA3p2_array[0]][2][2], \
                                                                           registry_addrs[reg_i_QA3p2_array[0]][2][4], registry_addrs[reg_i_QA3p2_array[0]][2][6], \
                                                                           registry_addrs[reg_i_QA3p2_array[0]][2][8], registry_addrs[reg_i_QA3p2_array[0]][2][10], \
                                                                           registry_addrs[reg_i_QA3p2_array[0]][2][12], registry_addrs[reg_i_QA3p2_array[0]][2][14], \
                                                                           registry_addrs[reg_i_QA3p2_array[0]][2][16] ]))
                    outfile_sheet_row = outfile_sheet_row + 1

                elif len(reg_i_QA3p3_array)>0:
                    print('here QA3.3 === ' + dam_name + '...' + dam_other_name + '...' + reservoir_name + ':::::::' + registry_dam_names[reg_i_QA3p3_array[0]])
                    OUT_sheet.write_row(outfile_sheet_row, 0, tuple(row + ['3.3', registry_lats[reg_i_QA3p3_array[0]], registry_lons[reg_i_QA3p3_array[0]], registry_IDs[reg_i_QA3p3_array[0]], \
                                                                           registry_dam_names[reg_i_QA3p3_array[0]], registry_rivers[reg_i_QA3p3_array[0]], registry_years[reg_i_QA3p3_array[0]], \
                                                                           registry_countries[reg_i_QA3p3_array[0]], \
                                                                           registry_addrs[reg_i_QA3p3_array[0]][1], registry_addrs[reg_i_QA3p3_array[0]][0], \
                                                                           registry_addrs[reg_i_QA3p3_array[0]][2][0], registry_addrs[reg_i_QA3p3_array[0]][2][2], \
                                                                           registry_addrs[reg_i_QA3p3_array[0]][2][4], registry_addrs[reg_i_QA3p3_array[0]][2][6], \
                                                                           registry_addrs[reg_i_QA3p3_array[0]][2][8], registry_addrs[reg_i_QA3p3_array[0]][2][10], \
                                                                           registry_addrs[reg_i_QA3p3_array[0]][2][12], registry_addrs[reg_i_QA3p3_array[0]][2][14], \
                                                                           registry_addrs[reg_i_QA3p3_array[0]][2][16] ]))
                    outfile_sheet_row = outfile_sheet_row + 1

                elif len(reg_i_QA3p4_array)>0:
                    print('here QA3.4 === ' + dam_name + '...' + dam_other_name + '...' + reservoir_name + ':::::::' + registry_dam_names[reg_i_QA3p4_array[0]])
                    OUT_sheet.write_row(outfile_sheet_row, 0, tuple(row + ['3.4', registry_lats[reg_i_QA3p4_array[0]], registry_lons[reg_i_QA3p4_array[0]], registry_IDs[reg_i_QA3p4_array[0]], \
                                                                           registry_dam_names[reg_i_QA3p4_array[0]], registry_rivers[reg_i_QA3p4_array[0]], registry_years[reg_i_QA3p4_array[0]], \
                                                                           registry_countries[reg_i_QA3p4_array[0]], \
                                                                           registry_addrs[reg_i_QA3p4_array[0]][1], registry_addrs[reg_i_QA3p4_array[0]][0], \
                                                                           registry_addrs[reg_i_QA3p4_array[0]][2][0], registry_addrs[reg_i_QA3p4_array[0]][2][2], \
                                                                           registry_addrs[reg_i_QA3p4_array[0]][2][4], registry_addrs[reg_i_QA3p4_array[0]][2][6], \
                                                                           registry_addrs[reg_i_QA3p4_array[0]][2][8], registry_addrs[reg_i_QA3p4_array[0]][2][10], \
                                                                           registry_addrs[reg_i_QA3p4_array[0]][2][12], registry_addrs[reg_i_QA3p4_array[0]][2][14], \
                                                                           registry_addrs[reg_i_QA3p4_array[0]][2][16] ]))
                    outfile_sheet_row = outfile_sheet_row + 1                   

# Close files
OUT_obj.close() # Save the output
ICOLD_obj.close() # Release the input

print("----- Module Completed -----")
print(datetime.datetime.now())
