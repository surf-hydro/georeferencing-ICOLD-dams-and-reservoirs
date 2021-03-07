# [Description] ------------------------------
# Module name "Reverse_geocoding_register.py"
# This module performs reverse geocoding for each record in a georeferenced regional register or inventory
# using the geographic coordinates (latitude and longitude) provided in the register. 

# Reverse geocoding converts a pair of numeric coordinates (such as lat/lon) to a nominal address with an
# array of divisions at consecutive administrative levels. The multi-level divisions were then appended to
# the existing address components in the original regional register. The output of this module was used as
# an input in "Geomatching_ICOLD.py" for geo-matching records in the ICOLD World Register of Dams (WRD).
# See details in "Geomatching_ICOLD.py".

# In this module, reverse geocoding was implemented using the cloud-based geocoding service through Google
# Maps geocoding API (http://developers.google.com/maps). See more about reverse geocoding and Google Maps
# geocoding API at: https://developers.google.com/maps/documentation/geocoding/overview#ReverseGeocoding.

# Example in this module is given for Brazil.
# The original register for Brazil (before reverse geocoding) is Relatório de Segurança de Barragens
# (Dams Safety Report) (SNISB, 2017), accessed freely from
# http://www.snisb.gov.br/portal/snisb/relatorio-anual-de-seguranca-de-barragem/2017.
# The full reference of this register is: 
# Sistema Nacional de Informações sobre Segurança de Barragens (SNISB, Brazilian National Dam Safety
# Information System): Relatório de Segurança de Barragens 2017 (Dams Safety Report 2017) [data set],
# http://www.snisb.gov.br/portal/snisb/relatorio-anual-de-seguranca-de-barragem/2017, 2017.

# Also see Wang et al. (2021) for methods.
# Reference: Wang, J., Walter, B.A., Yao, F., Song, C., Ding, M., Maroof, M.A.S., Zhu, J., Fan, C., Xin, A.,
# McAlister, J.M., Sikder, M.S., Sheng, Y., Allen, G.H., Crétaux, J.-F., and Wada, Y., 2021. GeoDAR:
# Georeferenced global dam and reservoir database for bridging attributes and geolocations. Earth System
# Science Data, in review.

# Script written by: Jida Wang
# Last update: March 4, 2021
# Contact: jidawang@ksu.edu; gdbruins@ucla.edu
#---------------------------------------------


 
# [Setup] -----------------------------------
# Inputs
# 1. infile: full path of the original regional register. 
# The given example is "CadastroRSB2017_Portal_SNISB(v4).xlsx".
infile = r"...\CadastroRSB2017_Portal_SNISB(v4).xlsx"

# 2. geocoding_key: user-specific Google Maps API key.
# The API key can be created by following the instruction below:
# https://developers.google.com/maps/documentation/geocoding/get-api-key
geocoding_key = 'Google-Maps-API-Key'

# 3. initial_row_number: initial record index in the register that the geocoding will start with.
initial_row_number = 11 # for example, starting from the 11th record in the register

# 4. end_row_number: last record index in the register that the geocoding will end with.
end_row_number = 1000 # for example, ending at the 1000th record, meaning that 990 records will be geocoded.
# The settings of initial_row_number and end_row_number give control to the user so that the maximum request
# quota for this API will not be exceeded.

# Output
# outfile: full path of the reverse-geocoded register.
# The given example "CadastroRSB2017_Portal_SNISB(v4)_revgeo.xlsx" is used as the input of module
# "Geomatching_ICOLD.py".
outfile = r"...\CadastroRSB2017_Portal_SNISB(v4)_revgeo.xlsx"
#---------------------------------------------



# [Script] -----------------------------------
# Import built-in functions and tools
import http, urllib, csv, json, unicodedata, sys, datetime, xlsxwriter, openpyxl
import urllib.request

print("----- Module Started -----")
print(datetime.datetime.now())

# Define input spreadsheet (original register) and output spreadsheet (reverse-geocoded register).
infile_obj = openpyxl.load_workbook(infile) 
infile_sheet = infile_obj.active
outfile_obj = xlsxwriter.Workbook(outfile)
outfile_sheet = outfile_obj.add_worksheet("Reverse-geocoded")
          
# Reverse geocode each record in the register
row_number = 0 # Initiate the record index number in the input
row_number_write = 0 # Initiate the record index number in the output
load_number = 0 # Initiate the number of request using this API key
for each_row in infile_sheet:
    row_number = row_number + 1
    if row_number == 1: # Header
        # Read attribute values for this record.
        row = []
        for cell in each_row:
            if cell.value == None:
                row.append('')
            else:
                row.append(str(cell.value)) 
        # Write header
        header_new = tuple(row + ['reg_adr', 'reg_cntry', 'reg_cntry_s', \
                                  'reg_admin1', 'reg_admin1_s', \
                                  'reg_admin2', 'reg_admin2_s', \
                                  'reg_admin3', 'reg_admin3_s', \
                                  'reg_admin4', 'reg_admin4_s', \
                                  'reg_admin5', 'reg_admin5_s', \
                                  'reg_local', 'reg_local_s', \
                                  'reg_local1', 'reg_local1_s', \
                                  'reg_local2', 'reg_local2_s', \
                                  'lat_d','lon_d'])
        outfile_sheet.write_row(row_number_write, 0, header_new)
        row_number_write = row_number_write + 1
    else:
        if (row_number >= initial_row_number and row_number <= end_row_number):
            # Initiate each reverse-geocoded address component by a flag value -999.
            # The flag value will be replaced by the geocoded result if the geocoding is successful. 
            re_adr = '-999'
            re_cntry = '-999'
            re_cntry_s = '-999'
            re_admin1 = '-999'
            re_admin1_s = '-999'
            re_admin2 = '-999'
            re_admin2_s = '-999'
            re_admin3 = '-999'
            re_admin3_s = '-999'
            re_admin4 = '-999'
            re_admin4_s = '-999'
            re_admin5 = '-999'
            re_admin5_s = '-999'
            re_local = '-999'
            re_local_s = '-999'
            re_local1 = '-999'
            re_local1_s = '-999'
            re_local2 = '-999'
            re_local2_s = '-999'
            lat = '-999'
            lon = '-999'
            # Read attribute values for this record.
            row = []
            for cell in each_row:
                if cell.value == None:
                    row.append('')
                else:
                    row.append(str(cell.value))
            # Retrieve lat/lon numbers from the original register.
            lat = str(row[15])
            lon = str(row[16])
            if lat == '' or lon == '': # Invalid lat/lon coordinates (this may happen for some of the records).
                # Write flag values the output. 
                outfile_sheet.write_row(row_number_write, 0, tuple(row+[re_adr,re_cntry,re_cntry_s,re_admin1,re_admin1_s,re_admin2,re_admin2_s,re_admin3,re_admin3_s,\
                                                                    re_admin4,re_admin4_s,re_admin5,re_admin5_s,re_local,re_local_s,\
                                                                    re_local1,re_local1_s,re_local2,re_local2_s,lat,lon]))
                row_number_write = row_number_write + 1
            else:                
                # Reverse-geocode this pair of lat/lon coordinates. 
                this_URL = 'https://maps.googleapis.com/maps/api/geocode/json?latlng=' + lat + ',' + lon + '&key=' + geocoding_key
                geodata = json.load(urllib.request.urlopen(this_URL))               
                load_number = load_number + 1
                if geodata == {'error_message': \
                               'You have exceeded your daily request quota for this API. If you did not set a custom daily request quota, verify your project has an active billing account: http://g.co/dev/maps-no-account',\
                               'results': [], 'status': 'OVER_QUERY_LIMIT'}: # Indicating the maximum quota has been exceeded.
                    print(geodata)
                    print(row)
                    print(load_number)
                    outfile_obj.close() # Save the output.
                    sys.exit('exceeding requests') # Quite this module. 
                if geodata["status"] == 'OK': # Indicating geocoding result exists.
                    # The result may contain multiple solutions (or components).
                    # The first result or solution seems to be usually the most accurate, but this is not always the case.
                    # We assume that the solution that has the most components/elements in "address_components" is the best solution. 
                    max_component_number = 0
                    this_component_index = 0
                    max_component_index = this_component_index
                    for this_geodata in geodata["results"]: 
                        a = this_geodata["address_components"] 
                        if len(a) > max_component_number:
                            max_component_number = len(a)
                            max_component_index = this_component_index
                        this_component_index = this_component_index + 1
                    # Retrieve the best formatted address.
                    re_adr = geodata["results"][max_component_index]["formatted_address"]
                    # Retrieve the best parsed address (with different administrative components).
                    good_geodata_address = geodata["results"][max_component_index]["address_components"]
                    # Retrieve values for individual administrative levels. 
                    for a_i in good_geodata_address:
                        if a_i["types"] == ['country', 'political']:
                            re_cntry = (a_i["long_name"]).lower().strip()
                            re_cntry_s = (a_i["short_name"]).lower().strip()
                            break
                    for a_i in good_geodata_address:
                        if a_i["types"] == ['administrative_area_level_1', 'political']:
                            re_admin1 = (a_i["long_name"]).lower().strip()
                            re_admin1_s = (a_i["short_name"]).lower().strip()
                            break
                    for a_i in good_geodata_address:
                        if a_i["types"] == ['administrative_area_level_2', 'political']:
                            re_admin2 = (a_i["long_name"]).lower().strip()
                            re_admin2_s = (a_i["short_name"]).lower().strip()
                            break
                    for a_i in good_geodata_address:
                        if a_i["types"] == ['administrative_area_level_3', 'political']:
                            re_admin3 = (a_i["long_name"]).lower().strip()
                            re_admin3_s = (a_i["short_name"]).lower().strip()
                            break
                    for a_i in good_geodata_address:
                        if a_i["types"] == ['administrative_area_level_4', 'political']:
                            re_admin4 = (a_i["long_name"]).lower().strip()
                            re_admin4_s = (a_i["short_name"]).lower().strip()
                            break
                    for a_i in good_geodata_address:
                        if a_i["types"] == ['administrative_area_level_5', 'political']:
                            re_admin5 = (a_i["long_name"]).lower().strip()
                            re_admin5_s = (a_i["short_name"]).lower().strip()
                            break
                    for a_i in good_geodata_address:
                        if a_i["types"] == ['locality', 'political']:
                            re_local = (a_i["long_name"]).lower().strip()
                            re_local_s = (a_i["short_name"]).lower().strip()
                            break
                    for a_i in good_geodata_address:
                        if a_i["types"] == ['political', 'sublocality', 'sublocality_level_1']:
                            re_local1 = (a_i["long_name"]).lower().strip()
                            re_local1_s = (a_i["short_name"]).lower().strip()
                            break
                    for a_i in good_geodata_address:
                        if a_i["types"] == ['political', 'sublocality', 'sublocality_level_2']:
                            re_local2 = (a_i["long_name"]).lower().strip()
                            re_local2_s = (a_i["short_name"]).lower().strip()
                            break
                # Write this geocoded result to the output
                outfile_sheet.write_row(row_number_write, 0, tuple(row+[re_adr,re_cntry,re_cntry_s,re_admin1,re_admin1_s,re_admin2,re_admin2_s,re_admin3,re_admin3_s,\
                                                                        re_admin4,re_admin4_s,re_admin5,re_admin5_s,re_local,re_local_s,\
                                                                        re_local1,re_local1_s,re_local2,re_local2_s,lat,lon]))
                row_number_write = row_number_write + 1
                print('load number: ' + str(load_number))
print('total load number: ' + str(load_number))

# Close files
outfile_obj.close() # Save the output
infile_obj.close() # Release the input

print("----- Module Completed -----")
print(datetime.datetime.now())
