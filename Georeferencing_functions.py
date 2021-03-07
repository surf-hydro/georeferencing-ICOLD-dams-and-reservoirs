# [Description] ------------------------------
# Script name "Georeferencing_functions.py"
# This script contains a list of customized functions used for georeferencing ICOLD World Register of
# Dams (WRD). See their names, purposes, inputs and outputs below. 


#---------------------------------------------
# Function name:
# remove_accents(input_str)

# Purpose:
# This function removes characters with umlauts and accents(such as in French, German, and Greek) and
# then replace them by non-accentuated counterparts.

# Input:
# -> input_str: a string with possible accents

# Output:
# -> a string where accentuated characters have been replaced by their non-accentuated counterparts. 
#---------------------------------------------


#---------------------------------------------
# Function name:
# year_similar(ICOLD_year, registry_year)

# Purpose:
# This function determines whether two "year" strings are considered to be equivalent. Here a one-year
# tolerance is employed as different inventories may show minor discrepancy in the completion/commission
# year of the same dam/reservoir. 

# Inputs:
# -> ICOLD_year: one of the two years (string type)
# -> registry_year: the other year (string type)

# Outputs:
# -> 1: indicating the two years are considered equivalent
# -> 0: indicating different years
#---------------------------------------------


#---------------------------------------------
# Function name:
# similar(a, b)

# Purpose:
# This function compares the similarity score of two strings with consideration of the character sequence.
# It was mainly used to compare the similarity of administrative names in between ICOLD WRD and the
# georeferenced inventory or register.

# Inputs:
# -> a and b: the two sequences (both in string type) to be compared

# Output:
# -> A float number in [0,1.0], with 1.0 indicating the two sequences being identical and 0 indicating no
# similarity between the two sequences. 
#---------------------------------------------


#---------------------------------------------
# Function name:
# damname_similar(similarity_t, dam_name_input, other_dam_name_input, reservoir_name_input,
# geocoded_name_input, this_country_ISO_input)

# Purpose:
# This function determines whether the names of two dam/reservoir records (e.g., Record A and Record B)
# are considered to be equivalent. If Record A has multiple names (such as different dam name and reservoir
# name), all names of Record A will be compared with the name of Record B. The names of the two records
# are considered equivalent as long as the score of similarity (calculated using the "similar" function)
# between the name of Record B and any of the names of Recorc A exceeds a customized similarity threshold
# (another input variable). This function was mainly used to compare dam/reservoir names in between ICOLD
# WRD and the georeferenced inventory/register. 

# Inputs:
# -> similarity_t: a minimum similarity threshold in [0, 1.0].
# -> dam_name_input: dam name of Record A (string)
# -> other_dam_name_input: other dam name of Record A (string). Enter '' if this is not available. 
# -> reservoir_name_input: reservoir name of Record A (string). Enter '' if this is not available.
# -> geocoded_name_input: dam/reservoir name of Record B (string). 
# -> this_country_ISO_input: country ISO 3166-2 codes .

# Outputs:
# -> 1: indicating a high confidence that the two records share the same dam or reservoir name.
# -> 0.5: indicating a medium confidence that the two records share the same dam or reservoir name
# -> 0: indicating otherwise
#---------------------------------------------


#---------------------------------------------
# Function name:
# river_similar(similarity_t, ICOLD_river, registry_river)
# Purpose:
# This function determines whether the names of two rivers are considered to be equivalent given a minimum
# similarity threshold.

# Inputs:
# -> similarity_t: a minimum similarity threshold in [0, 1.0].
# -> ICOLD_river: name of the first river
# -> registry_river: name of the other river

# Outputs:
# -> 1: indicating a high confidence that the two records share the same river name
# -> 0.5: indicating a medium confidence that the two records share the same river name
# -> 0: indicating otherwise
#---------------------------------------------


#---------------------------------------------
# Function name:
# similar_v2(a, b)

# Purpose:
# The same as function <similar>, except that this function was mainly used to compare the similarity of
# administrative names in between ICOLD WRD and the Google geocoding result. In comparison with <similar>,
# criteria in this function (v2) were overall more lenient considering that the outputs from the Google Maps
# geocoding API have already gone through a similarity measure.

# Inputs:
# -> a and b: the two sequences (both in string type) to be compared

# Output:
# -> A float number in [0,1.0], with 1.0 indicating the two sequences being identical and 0 indicating no
# similarity between the two sequences. 
#---------------------------------------------


#---------------------------------------------
# Function name:
# damname_similar_v2(similarity_t, dam_name_input, other_dam_name_input, reservoir_name_input,
# geocoded_name_input, this_country_ISO_input)

# Purpose:
# The same as function <damname_similar>, except that this function was used to compare dam/reservoir names
# in between ICOLD WRD and the geocoding output. In comparison with <damname_similar>, criteria in this
# function (v2) were overall more lenient considering that the outputs from the Google Maps geocoding API
# have already gone through a similarity measure.

# Inputs:
# -> similarity_t: a minimum similarity threshold in [0, 1.0].
# -> dam_name_input: dam name of Record A (string)
# -> other_dam_name_input: other dam name of Record A (string). Enter '' if this is not available. 
# -> reservoir_name_input: reservoir name of Record A (string). Enter '' if this is not available.
# -> geocoded_name_input: dam/reservoir name of Record B (string). 
# -> this_country_ISO_input: country ISO 3166-2 codes .

# Outputs:
# -> 1: indicating the two records share the same dam or reservoir name
# -> 0: indicating otherwise
#---------------------------------------------


#---------------------------------------------
# See detailed functions in [Scripts] below. 

# Reference: Wang, J., Walter, B.A., Yao, F., Song, C., Ding, M., Maroof, M.A.S., Zhu, J., Fan, C., Xin, A.,
# McAlister, J.M., Sikder, M.S., Sheng, Y., Allen, G.H., Crétaux, J.-F., and Wada, Y., 2021. GeoDAR:
# Georeferenced global dam and reservoir database for bridging attributes and geolocations. Earth System
# Science Data, in review.

# Script written by: Jida Wang
# Last update: March 4, 2021
# Contact: jidawang@ksu.edu; gdbruins@ucla.edu
#---------------------------------------------



# [Script] -----------------------------------
# Import built-in functions and tools
import unicodedata, re
from difflib import SequenceMatcher


def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])


def year_similar(ICOLD_year, registry_year): 
    year_similarity_pass = 0
    if str.isdigit(ICOLD_year) == False or str.isdigit(registry_year) == False:
        year_similarity_pass = 0
    else:
        if abs(int(ICOLD_year) - int(registry_year))<= 1:
            year_similarity_pass = 1
    return year_similarity_pass


def similar(a, b):
    a = a.lower().strip()
    b = b.lower().strip()
    if a == '-999' or b == '-999' or a == '' or b == '' or a == None or b == None or a == '/' or b == '/'  \
       or a == '-' or b == '-' or a == '..' or b == '..' or a == '_' or b == '_':
        return_sim = 0
    elif (len(a)>=7 and (a[0:7]=='unknown' or a[0:7]=='unnamed' or a[0:7]=='un-name')) or (len(b)>=7 and (b[0:7]=='unknown' or b[0:7]=='unnamed' or b[0:7]=='un-name')):
        return_sim = 0
    else:    
        if ('\\' in a) or ('\\' in b) or ('/' in a) or ('/' in b): # In case of two different names shared by the same object
            AA_good = []
            for this_AA_slash1 in a.split('/'):
                for this_AA_slash2 in this_AA_slash1.split('\\'):
                    if this_AA_slash2 != '':
                        AA_good.append(this_AA_slash2.strip())
            BB_good = []
            for this_BB_slash1 in b.split('/'):
                for this_BB_slash2 in this_BB_slash1.split('\\'):
                    if this_BB_slash2 != '':
                        BB_good.append(this_BB_slash2.strip())
            similar_value_array = []
            for this_AA_good in AA_good:
                for this_BB_good in BB_good:
                    similar_value_array.append(SequenceMatcher(None, this_AA_good, this_BB_good).ratio())
            return_sim = max(similar_value_array)
        else:
            return_sim = SequenceMatcher(None, a, b).ratio()
    return return_sim


def damname_similar(similarity_t, dam_name_input, other_dam_name_input, reservoir_name_input, geocoded_name_input, this_country_ISO_input):
    # Discard some of the ancillary titles in a dam or reservoir name. These titles are not considered as an essential part of the dam/reservoir names. 
    to_be_removed = [' lake ', ' dam ', ' reservoir ', ' barrage ', ' lago ', ' shuiku ', ' lac ', ' presa ', ' embalse ', ' barragem ', \
                     ' agua ', ' stuwal ', ' weir ', ' dike ', ' dyke ', ' levee ', ' structure ', ' canal ', ' tank ', \
                     ' lake ', ' dam ', ' reservoir ', ' barrage ', ' lago ', ' shuiku ', ' lac ', ' presa ', ' embalse ', ' barragem ', \
                     ' agua ', ' stuwal ', ' weir ', ' dike ', ' dyke ', ' levee ', ' structure ', ' canal ', ' tank ', \
                     ' lake ', ' dam ', ' reservoir ', ' barrage ', ' lago ', ' shuiku ', ' lac ', ' presa ', ' embalse ', ' barragem ', \
                     ' agua ', ' stuwal ', ' weir ', ' dike ', ' dyke ', ' levee ', ' structure ', ' canal ', ' tank '] # Repeat them for a thorough removal. 
    damname_similarity_final_pass = 0
    damname_similarity_pass = 0
    damname_similarity_pass_alt = 0
    if dam_name_input == '-999' or geocoded_name_input == '-999' or dam_name_input == '' or geocoded_name_input == '' or \
       dam_name_input == None or geocoded_name_input == None or dam_name_input == '/' or geocoded_name_input == '/'  or \
       dam_name_input == '-' or geocoded_name_input == '-' or dam_name_input == '..' or geocoded_name_input == '..' or \
       dam_name_input == '_' or geocoded_name_input == '_':
        damname_similarity_pass = 0
    elif (len(dam_name_input)>=7 and (dam_name_input[0:7]=='unknown' or dam_name_input[0:7]=='unnamed' or dam_name_input[0:7]=='un-name')) or \
         (len(geocoded_name_input)>=7 and (geocoded_name_input[0:7]=='unknown' or geocoded_name_input[0:7]=='unnamed' or geocoded_name_input[0:7]=='un-name')):
        damname_similarity_pass = 0
    elif geocoded_name_input == 'not found':
        damname_similarity_pass = -1
    else:
        dam_name_input_simple = remove_accents(dam_name_input)
        geocoded_name_input_simple = remove_accents(geocoded_name_input)
        # Remove ancillary titles.
        dam_name_input_simple = ' ' + dam_name_input_simple + ' '
        geocoded_name_input_simple = ' ' + geocoded_name_input_simple + ' '
        for this_to_be_removed in to_be_removed:
            if this_to_be_removed in dam_name_input_simple:
                dam_name_input_simple = dam_name_input_simple.replace(this_to_be_removed, ' ')
            if this_to_be_removed in geocoded_name_input_simple:
                geocoded_name_input_simple = geocoded_name_input_simple.replace(this_to_be_removed, ' ')
        dam_name_input_simple = dam_name_input_simple.strip()
        geocoded_name_input_simple = geocoded_name_input_simple.strip()
        if this_country_ISO_input == 'cn':
            if len(dam_name_input_simple) > 8 and dam_name_input_simple[-6:] == 'shuiku':
                dam_name_input_simple = (dam_name_input_simple[0:(len(dam_name_input_simple)-6)]).lower().strip()
            if len(geocoded_name_input_simple) > 8 and geocoded_name_input_simple[-6:] == 'shuiku':
                geocoded_name_input_simple = (geocoded_name_input_simple[0:(len(geocoded_name_input_simple)-6)]).lower().strip()
        # Extract Arabic numbers from both names.  
        continue_or_not = 1
        numbers_left = re.findall(r'\d+', dam_name_input_simple)
        numbers_right = re.findall(r'\d+', geocoded_name_input_simple)
        # Split the name by delimiters. 
        icold_spelling_splits = [] 
        for this_split_space in dam_name_input_simple.split():
            for this_split_comma in this_split_space.split(','):
                for this_split_period in this_split_comma.split('.'):
                    for this_split_hypen in this_split_period.split('-'):
                        for this_split_slash in this_split_hypen.split('/'):
                            for this_split_paren1 in this_split_slash.split('('):
                                for this_split_paren2 in this_split_paren1.split(')'):
                                    if this_split_paren2 != '':
                                        icold_spelling_splits.append(this_split_paren2)
        google_spelling_splits = []
        for this_split_space in geocoded_name_input_simple.split():
            for this_split_comma in this_split_space.split(','):
                for this_split_period in this_split_comma.split('.'):
                    for this_split_hypen in this_split_period.split('-'):
                        for this_split_slash in this_split_hypen.split('/'):
                            for this_split_paren1 in this_split_slash.split('('):
                                for this_split_paren2 in this_split_paren1.split(')'):
                                    if this_split_paren2 != '':
                                        google_spelling_splits.append(this_split_paren2)
        # To reduce ambiguity, check if each of the Arabic numbers in the first name is also included in the other name.
        # The assumption is that two equivalent names cannot contain different numbers.
        # For example, "Tuttle Creek #1" is not the same dam as "Tuttle Creek #2".
        if len(numbers_left)>0 and len(numbers_right)>0:
            for this_number_left in numbers_left:
                if this_number_left not in numbers_right:
                    continue_or_not = 0
                    break
            for this_numbers_right in numbers_right:
                if this_numbers_right not in numbers_left:
                    continue_or_not = 0
                    break 
        elif len(numbers_left)==0 and len(numbers_right)==0: # Also check other number formats. 
            if ((('i' in icold_spelling_splits) or ('one' in icold_spelling_splits)) and (('i' not in google_spelling_splits) and ('one' not in google_spelling_splits))) or \
               ((('ii' in icold_spelling_splits) or ('two' in icold_spelling_splits)) and (('ii' not in google_spelling_splits) and ('two' not in google_spelling_splits))) or \
               ((('iii' in icold_spelling_splits) or ('three' in icold_spelling_splits)) and (('iii' not in google_spelling_splits) and ('three' not in google_spelling_splits))) or \
               ((('iv' in icold_spelling_splits) or ('four' in icold_spelling_splits)) and (('iv' not in google_spelling_splits) and ('four' not in google_spelling_splits))) or \
               ((('v' in icold_spelling_splits) or ('five' in icold_spelling_splits)) and (('v' not in google_spelling_splits) and ('five' not in google_spelling_splits))) or \
               ((('vi' in icold_spelling_splits) or ('six' in icold_spelling_splits)) and (('vi' not in google_spelling_splits) and ('six' not in google_spelling_splits))) or \
               ((('vii' in icold_spelling_splits) or ('seven' in icold_spelling_splits)) and (('vii' not in google_spelling_splits) and ('seven' not in google_spelling_splits))) or \
               ((('viii' in icold_spelling_splits) or ('eight' in icold_spelling_splits)) and (('viii' not in google_spelling_splits) and ('eight' not in google_spelling_splits))) or \
               ((('ix' in icold_spelling_splits) or ('nine' in icold_spelling_splits)) and (('ix' not in google_spelling_splits) and ('nine' not in google_spelling_splits))) or \
               ((('x' in icold_spelling_splits) or ('ten' in icold_spelling_splits)) and (('x' not in google_spelling_splits) and ('ten' not in google_spelling_splits))) or \
               ((('xi' in icold_spelling_splits) or ('eleven' in icold_spelling_splits)) and (('xi' not in google_spelling_splits) and ('eleven' not in google_spelling_splits))) or \
               ((('xii' in icold_spelling_splits) or ('twelve' in icold_spelling_splits)) and (('xii' not in google_spelling_splits) and ('twelve' not in google_spelling_splits))) or \
               ((('xiii' in icold_spelling_splits) or ('thirteen' in icold_spelling_splits)) and (('xiii' not in google_spelling_splits) and ('thirteen' not in google_spelling_splits))) or \
               ((('xiv' in icold_spelling_splits) or ('fourteen' in icold_spelling_splits)) and (('xiv' not in google_spelling_splits) and ('fourteen' not in google_spelling_splits))) or \
               ((('xv' in icold_spelling_splits) or ('fifteen' in icold_spelling_splits)) and (('xv' not in google_spelling_splits) and ('fifteen' not in google_spelling_splits))) or \
               ((('xvi' in icold_spelling_splits) or ('sixteen' in icold_spelling_splits)) and (('xvi' not in google_spelling_splits) and ('sixteen' not in google_spelling_splits))) or \
               ((('xvii' in icold_spelling_splits) or ('seventeen' in icold_spelling_splits)) and (('xvii' not in google_spelling_splits) and ('seventeen' not in google_spelling_splits))) or \
               ((('xviii' in icold_spelling_splits) or ('eighteen' in icold_spelling_splits)) and (('xviii' not in google_spelling_splits) and ('eighteen' not in google_spelling_splits))) or \
               ((('xix' in icold_spelling_splits) or ('nineteen' in icold_spelling_splits)) and (('xix' not in google_spelling_splits) and ('nineteen' not in google_spelling_splits))) or \
               ((('xx' in icold_spelling_splits) or ('twenty' in icold_spelling_splits)) and (('xx' not in google_spelling_splits) and ('twenty' not in google_spelling_splits))) or \
               ((('i' in google_spelling_splits) or ('one' in google_spelling_splits)) and (('i' not in icold_spelling_splits) and ('one' not in icold_spelling_splits))) or \
               ((('ii' in google_spelling_splits) or ('two' in google_spelling_splits)) and (('ii' not in icold_spelling_splits) and ('two' not in icold_spelling_splits))) or \
               ((('iii' in google_spelling_splits) or ('three' in google_spelling_splits)) and (('iii' not in icold_spelling_splits) and ('three' not in icold_spelling_splits))) or \
               ((('iv' in google_spelling_splits) or ('four' in google_spelling_splits)) and (('iv' not in icold_spelling_splits) and ('four' not in icold_spelling_splits))) or \
               ((('v' in google_spelling_splits) or ('five' in google_spelling_splits)) and (('v' not in icold_spelling_splits) and ('five' not in icold_spelling_splits))) or \
               ((('vi' in google_spelling_splits) or ('six' in google_spelling_splits)) and (('vi' not in icold_spelling_splits) and ('six' not in icold_spelling_splits))) or \
               ((('vii' in google_spelling_splits) or ('seven' in google_spelling_splits)) and (('vii' not in icold_spelling_splits) and ('seven' not in icold_spelling_splits))) or \
               ((('viii' in google_spelling_splits) or ('eight' in google_spelling_splits)) and (('viii' not in icold_spelling_splits) and ('eight' not in icold_spelling_splits))) or \
               ((('ix' in google_spelling_splits) or ('nine' in google_spelling_splits)) and (('ix' not in icold_spelling_splits) and ('nine' not in icold_spelling_splits))) or \
               ((('x' in google_spelling_splits) or ('ten' in google_spelling_splits)) and (('x' not in icold_spelling_splits) and ('ten' not in icold_spelling_splits))) or \
               ((('xi' in google_spelling_splits) or ('eleven' in google_spelling_splits)) and (('xi' not in icold_spelling_splits) and ('eleven' not in icold_spelling_splits))) or \
               ((('xii' in google_spelling_splits) or ('twelve' in google_spelling_splits)) and (('xii' not in icold_spelling_splits) and ('twelve' not in icold_spelling_splits))) or \
               ((('xiii' in google_spelling_splits) or ('thirteen' in google_spelling_splits)) and (('xiii' not in icold_spelling_splits) and ('thirteen' not in icold_spelling_splits))) or \
               ((('xiv' in google_spelling_splits) or ('fourteen' in google_spelling_splits)) and (('xiv' not in icold_spelling_splits) and ('fourteen' not in icold_spelling_splits))) or \
               ((('xv' in google_spelling_splits) or ('fifteen' in google_spelling_splits)) and (('xv' not in icold_spelling_splits) and ('fifteen' not in icold_spelling_splits))) or \
               ((('xvi' in google_spelling_splits) or ('sixteen' in google_spelling_splits)) and (('xvi' not in icold_spelling_splits) and ('sixteen' not in icold_spelling_splits))) or \
               ((('xvii' in google_spelling_splits) or ('seventeen' in google_spelling_splits)) and (('xvii' not in icold_spelling_splits) and ('seventeen' not in icold_spelling_splits))) or \
               ((('xviii' in google_spelling_splits) or ('eighteen' in google_spelling_splits)) and (('xviii' not in icold_spelling_splits) and ('eighteen' not in icold_spelling_splits))) or \
               ((('xix' in google_spelling_splits) or ('nineteen' in google_spelling_splits)) and (('xix' not in icold_spelling_splits) and ('nineteen' not in icold_spelling_splits))) or \
               ((('xx' in google_spelling_splits) or ('twenty' in google_spelling_splits)) and (('xx' not in icold_spelling_splits) and ('twenty' not in icold_spelling_splits))):
                continue_or_not = 0
        elif len(numbers_left)==0 and len(numbers_right)==1:
            if ((('i' in icold_spelling_splits) or ('one' in icold_spelling_splits)) and ('1' in google_spelling_splits)) or \
               ((('ii' in icold_spelling_splits) or ('two' in icold_spelling_splits)) and ('2' in google_spelling_splits)) or \
               ((('iii' in icold_spelling_splits) or ('three' in icold_spelling_splits)) and ('3' in google_spelling_splits)) or \
               ((('iv' in icold_spelling_splits) or ('four' in icold_spelling_splits)) and ('4' in google_spelling_splits)) or \
               ((('v' in icold_spelling_splits) or ('five' in icold_spelling_splits)) and ('5' in google_spelling_splits)) or \
               ((('vi' in icold_spelling_splits) or ('six' in icold_spelling_splits)) and ('6' in google_spelling_splits)) or \
               ((('vii' in icold_spelling_splits) or ('seven' in icold_spelling_splits)) and ('7' in google_spelling_splits)) or \
               ((('viii' in icold_spelling_splits) or ('eight' in icold_spelling_splits)) and ('8' in google_spelling_splits)) or \
               ((('ix' in icold_spelling_splits) or ('nine' in icold_spelling_splits)) and ('9' in google_spelling_splits)) or \
               ((('x' in icold_spelling_splits) or ('ten' in icold_spelling_splits)) and ('10' in google_spelling_splits)) or \
               ((('xi' in icold_spelling_splits) or ('eleven' in icold_spelling_splits)) and ('11' in google_spelling_splits)) or \
               ((('xii' in icold_spelling_splits) or ('twelve' in icold_spelling_splits)) and ('12' in google_spelling_splits)) or \
               ((('xiii' in icold_spelling_splits) or ('thirteen' in icold_spelling_splits)) and ('13' in google_spelling_splits)) or \
               ((('xiv' in icold_spelling_splits) or ('fourteen' in icold_spelling_splits)) and ('14' in google_spelling_splits)) or \
               ((('xv' in icold_spelling_splits) or ('fifteen' in icold_spelling_splits)) and ('15' in google_spelling_splits)) or \
               ((('xvi' in icold_spelling_splits) or ('sixteen' in icold_spelling_splits)) and ('16' in google_spelling_splits)) or \
               ((('xvii' in icold_spelling_splits) or ('seventeen' in icold_spelling_splits)) and ('17' in google_spelling_splits)) or \
               ((('xviii' in icold_spelling_splits) or ('eighteen' in icold_spelling_splits)) and ('18' in google_spelling_splits)) or \
               ((('xix' in icold_spelling_splits) or ('nineteen' in icold_spelling_splits)) and ('19' in google_spelling_splits)) or \
               ((('xx' in icold_spelling_splits) or ('twenty' in icold_spelling_splits)) and ('20' in google_spelling_splits)):
                continue_or_not = 1
            else:
                continue_or_not = 0
        elif len(numbers_left)==1 and len(numbers_right)==0:
            if ((('i' in google_spelling_splits) or ('one' in google_spelling_splits)) and ('1' in icold_spelling_splits)) or \
               ((('ii' in google_spelling_splits) or ('two' in google_spelling_splits)) and ('2' in icold_spelling_splits)) or \
               ((('iii' in google_spelling_splits) or ('three' in google_spelling_splits)) and ('3' in icold_spelling_splits)) or \
               ((('iv' in google_spelling_splits) or ('four' in google_spelling_splits)) and ('4' in icold_spelling_splits)) or \
               ((('v' in google_spelling_splits) or ('five' in google_spelling_splits)) and ('5' in icold_spelling_splits)) or \
               ((('vi' in google_spelling_splits) or ('six' in google_spelling_splits)) and ('6' in icold_spelling_splits)) or \
               ((('vii' in google_spelling_splits) or ('seven' in google_spelling_splits)) and ('7' in icold_spelling_splits)) or \
               ((('viii' in google_spelling_splits) or ('eight' in google_spelling_splits)) and ('8' in icold_spelling_splits)) or \
               ((('ix' in google_spelling_splits) or ('nine' in google_spelling_splits)) and ('9' in icold_spelling_splits)) or \
               ((('x' in google_spelling_splits) or ('ten' in google_spelling_splits)) and ('10' in icold_spelling_splits)) or \
               ((('xi' in google_spelling_splits) or ('eleven' in google_spelling_splits)) and ('11' in icold_spelling_splits)) or \
               ((('xii' in google_spelling_splits) or ('twelve' in google_spelling_splits)) and ('12' in icold_spelling_splits)) or \
               ((('xiii' in google_spelling_splits) or ('thirteen' in google_spelling_splits)) and ('13' in icold_spelling_splits)) or \
               ((('xiv' in google_spelling_splits) or ('fourteen' in google_spelling_splits)) and ('14' in icold_spelling_splits)) or \
               ((('xv' in google_spelling_splits) or ('fifteen' in google_spelling_splits)) and ('15' in icold_spelling_splits)) or \
               ((('xvi' in google_spelling_splits) or ('sixteen' in google_spelling_splits)) and ('16' in icold_spelling_splits)) or \
               ((('xvii' in google_spelling_splits) or ('seventeen' in google_spelling_splits)) and ('17' in icold_spelling_splits)) or \
               ((('xviii' in google_spelling_splits) or ('eighteen' in google_spelling_splits)) and ('18' in icold_spelling_splits)) or \
               ((('xix' in google_spelling_splits) or ('nineteen' in google_spelling_splits)) and ('19' in icold_spelling_splits)) or \
               ((('xx' in google_spelling_splits) or ('twenty' in google_spelling_splits)) and ('20' in icold_spelling_splits)):
                continue_or_not = 1
            else:
                continue_or_not = 0
        else:
            continue_or_not = 0
        # To further reduce ambiguity, check if any of the following elements in the first name is also included in the other name.
        # The assumption is that two equivalent names cannot contain different direction adjectives or letters.
        # For example, "Tuttle Creek East" is not the same dam as "Tuttle Creek West".
        if (('east' in icold_spelling_splits) and ('east' not in google_spelling_splits)) or (('east' in google_spelling_splits) and ('east' not in icold_spelling_splits)) or \
           (('west' in icold_spelling_splits) and ('west' not in google_spelling_splits)) or (('west' in google_spelling_splits) and ('west' not in icold_spelling_splits)) or \
           (('north' in icold_spelling_splits) and ('north' not in google_spelling_splits)) or (('north' in google_spelling_splits) and ('north' not in icold_spelling_splits)) or \
           (('south' in icold_spelling_splits) and ('south' not in google_spelling_splits)) or (('south' in google_spelling_splits) and ('south' not in icold_spelling_splits)) or \
           (('upper' in icold_spelling_splits) and ('upper' not in google_spelling_splits)) or (('upper' in google_spelling_splits) and ('upper' not in icold_spelling_splits)) or \
           (('lower' in icold_spelling_splits) and ('lower' not in google_spelling_splits)) or (('lower' in google_spelling_splits) and ('lower' not in icold_spelling_splits)) or \
           (('a' in icold_spelling_splits) and ('a' not in google_spelling_splits)) or (('a' in google_spelling_splits) and ('a' not in icold_spelling_splits)) or \
           (('b' in icold_spelling_splits) and ('b' not in google_spelling_splits)) or (('b' in google_spelling_splits) and ('b' not in icold_spelling_splits)) or \
           (('c' in icold_spelling_splits) and ('c' not in google_spelling_splits)) or (('c' in google_spelling_splits) and ('c' not in icold_spelling_splits)) or \
           (('d' in icold_spelling_splits) and ('d' not in google_spelling_splits)) or (('d' in google_spelling_splits) and ('d' not in icold_spelling_splits)) or \
           (('auxiliar' in icold_spelling_splits) and ('auxiliar' not in google_spelling_splits)) or (('auxiliar' in google_spelling_splits) and ('auxiliar' not in icold_spelling_splits)) or \
           (('auxiliary' in icold_spelling_splits) and ('auxiliary' not in google_spelling_splits)) or (('auxiliary' in google_spelling_splits) and ('auxiliary' not in icold_spelling_splits)):
            continue_or_not = 0
        # Continue the comparison if none of the situations above happens. 
        if continue_or_not == 0:
            damname_similarity_pass = 0
        elif (dam_name_input_simple != '' and geocoded_name_input_simple != ''):
            similarity_value = similar(dam_name_input_simple, geocoded_name_input_simple)
            if similarity_value >= similarity_t:
                damname_similarity_pass = 1
            if damname_similarity_pass != 1:
                # Check containment relations
                if (dam_name_input_simple in geocoded_name_input_simple) == True and (dam_name_input_simple != geocoded_name_input_simple) == True: #ICOLD contained by Google
                    if geocoded_name_input_simple.find(dam_name_input_simple) == 0: #'manhattan city': 'manhattan'
                        if geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)+len(dam_name_input_simple)] == ' ' or \
                           geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)+len(dam_name_input_simple)] == '-':
                            damname_similarity_pass = 1
                    elif (geocoded_name_input_simple.find(dam_name_input_simple)+len(dam_name_input_simple)) == len(geocoded_name_input_simple): #'city of manhattan': 'manhattan'
                        if geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)-1] == ' ' or \
                           geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)-1] == '-':
                            damname_similarity_pass = 1
                elif (geocoded_name_input_simple in dam_name_input_simple) == True and (dam_name_input_simple != geocoded_name_input_simple) == True: #ICOLD containing Google
                    if dam_name_input_simple.find(geocoded_name_input_simple) == 0: #'manhattan city': 'manhattan'
                        if dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)+len(geocoded_name_input_simple)] == ' ' or \
                           dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)+len(geocoded_name_input_simple)] == '-':
                            damname_similarity_pass = 1
                    elif (dam_name_input_simple.find(geocoded_name_input_simple)+len(geocoded_name_input_simple)) == len(dam_name_input_simple): #'city of manhattan': 'manhattan'
                        if dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)-1] == ' ' or \
                           dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)-1] == '-':
                            damname_similarity_pass = 1
            if damname_similarity_pass != 1:
                for icold_split in icold_spelling_splits:
                    for google_split in google_spelling_splits:
                        # Further eliminate possibly ancillary information from the name.
                        if len(google_split)>3 and len(icold_split)>3 and \
                           google_split != 'main' and icold_split != 'main' and \
                           google_split != 'tank' and icold_split != 'tank' and \
                           google_split != 'dyke' and icold_split != 'dyke' and google_split != 'canal' and icold_split != 'canal' and \
                           google_split != 'canyon' and icold_split != 'canyon' and google_split != 'diversion' and icold_split != 'diversion' and \
                           google_split != 'city' and icold_split != 'city' and google_split != 'town' and icold_split != 'town' and \
                           google_split != 'fall' and icold_split != 'fall' and google_split != 'falls' and icold_split != 'falls' and \
                           google_split != 'west' and icold_split != 'west' and google_split != 'east' and icold_split != 'east' and \
                           google_split != 'south' and icold_split != 'south' and google_split != 'norht' and icold_split != 'north' and \
                           google_split != 'storage' and icold_split != 'storage' and google_split != 'river' and icold_split != 'river' and \
                           google_split != 'saint' and icold_split != 'saint' and google_split != 'kloof' and icold_split != 'kloof' and \
                           google_split != 'berg' and icold_split != 'berg' and google_split != 'santa' and icold_split != 'santa' and \
                           google_split != 'valley' and icold_split != 'valley' and google_split != 'upper' and icold_split != 'upper' and \
                           google_split != 'lower' and icold_split != 'lower' and google_split != 'creek' and icold_split != 'creek' and \
                           google_split != 'lake' and icold_split != 'lake' and google_split != 'reservoir' and icold_split != 'reservoir' and \
                           google_split != 'lock' and icold_split != 'lock' and google_split != 'barrage' and icold_split != 'barrage' and \
                           google_split != 'lago' and icold_split != 'lago' and google_split != 'shuiku' and icold_split != 'shuiku' and \
                           google_split != 'presa' and icold_split != 'presa' and google_split != 'embalse' and icold_split != 'embalse' and \
                           google_split != 'barragem' and icold_split != 'barragem' and google_split != 'agua' and icold_split != 'agua' and \
                           google_split != 'stuwal' and icold_split != 'stuwal' and google_split != 'weir' and icold_split != 'weir' and \
                           google_split != 'dike' and icold_split != 'dike' and google_split != 'levee' and icold_split != 'levee' and \
                           google_split != 'mountain' and icold_split != 'mountain' and google_split != 'hill' and icold_split != 'hill' and \
                           google_split != 'auxiliar' and icold_split != 'auxiliar' and google_split != 'auxiliary' and icold_split != 'auxiliary' and \
                           google_split != 'riacho' and icold_split != 'riacho' and google_split != 'ribeirao' and icold_split != 'ribeirao' and \
                           google_split != 'ribeiro' and icold_split != 'ribeiro' and google_split != 'ribeira' and icold_split != 'ribeira' and \
                           google_split != 'riviere' and icold_split != 'riviere': 
                            if similar(icold_split, google_split) >= similarity_t:
                                damname_similarity_pass_alt = 1
                                break
                    if damname_similarity_pass_alt ==1:
                        break
    # If the similary test has not been passed, continue to check the other dam if any.
    if damname_similarity_pass != 1:
        if other_dam_name_input == '-999' or geocoded_name_input == '-999' or other_dam_name_input == '' or geocoded_name_input == '' or \
           other_dam_name_input == None or geocoded_name_input == None or other_dam_name_input == '/' or geocoded_name_input == '/'  or \
           other_dam_name_input == '-' or geocoded_name_input == '-' or other_dam_name_input == '..' or geocoded_name_input == '..' or \
           other_dam_name_input == '_' or geocoded_name_input == '_':
            damname_similarity_pass = 0
        elif (len(other_dam_name_input)>=7 and (other_dam_name_input[0:7]=='unknown' or other_dam_name_input[0:7]=='unnamed' or other_dam_name_input[0:7]=='un-name')) or \
             (len(geocoded_name_input)>=7 and (geocoded_name_input[0:7]=='unknown' or geocoded_name_input[0:7]=='unnamed' or geocoded_name_input[0:7]=='un-name')):
            damname_similarity_pass = 0
        elif geocoded_name_input == 'not found':
            damname_similarity_pass = -1
        else:
            dam_name_input_simple = remove_accents(other_dam_name_input)
            dam_name_input_simple = ' ' + dam_name_input_simple + ' '
            # Remove ancillary titles.
            for this_to_be_removed in to_be_removed:
                if this_to_be_removed in dam_name_input_simple:
                    dam_name_input_simple = dam_name_input_simple.replace(this_to_be_removed, ' ')
            dam_name_input_simple = dam_name_input_simple.strip()
            if this_country_ISO_input == 'cn':
                if len(dam_name_input_simple) > 8 and dam_name_input_simple[-6:] == 'shuiku':
                    dam_name_input_simple = (dam_name_input_simple[0:(len(dam_name_input_simple)-6)]).lower().strip()
            # Extract Arabic numbers from both names.
            continue_or_not = 1
            numbers_left = re.findall(r'\d+', dam_name_input_simple)
            numbers_right = re.findall(r'\d+', geocoded_name_input_simple)
            # Split the name by delimiters. 
            icold_spelling_splits = [] 
            for this_split_space in dam_name_input_simple.split():
                for this_split_comma in this_split_space.split(','):
                    for this_split_period in this_split_comma.split('.'):
                        for this_split_hypen in this_split_period.split('-'):
                            for this_split_slash in this_split_hypen.split('/'):
                                for this_split_paren1 in this_split_slash.split('('):
                                    for this_split_paren2 in this_split_paren1.split(')'):
                                        if this_split_paren2 != '':
                                            icold_spelling_splits.append(this_split_paren2)
            google_spelling_splits = []
            for this_split_space in geocoded_name_input_simple.split():
                for this_split_comma in this_split_space.split(','):
                    for this_split_period in this_split_comma.split('.'):
                        for this_split_hypen in this_split_period.split('-'):
                            for this_split_slash in this_split_hypen.split('/'):
                                for this_split_paren1 in this_split_slash.split('('):
                                    for this_split_paren2 in this_split_paren1.split(')'):
                                        if this_split_paren2 != '':
                                            google_spelling_splits.append(this_split_paren2)
            # To reduce ambiguity, check if each of the Arabic numbers in the first name is also included in the other name.
            # The assumption is that two equivalent names cannot contain different numbers.
            # For example, "Tuttle Creek #1" is not the same dam as "Tuttle Creek #2".
            if len(numbers_left)>0 and len(numbers_right)>0:
                for this_number_left in numbers_left:
                    if this_number_left not in numbers_right:
                        continue_or_not = 0
                        break
                for this_numbers_right in numbers_right:
                    if this_numbers_right not in numbers_left:
                        continue_or_not = 0
                        break
            elif len(numbers_left)==0 and len(numbers_right)==0: # Also check other number formats.
                if ((('i' in icold_spelling_splits) or ('one' in icold_spelling_splits)) and (('i' not in google_spelling_splits) and ('one' not in google_spelling_splits))) or \
                   ((('ii' in icold_spelling_splits) or ('two' in icold_spelling_splits)) and (('ii' not in google_spelling_splits) and ('two' not in google_spelling_splits))) or \
                   ((('iii' in icold_spelling_splits) or ('three' in icold_spelling_splits)) and (('iii' not in google_spelling_splits) and ('three' not in google_spelling_splits))) or \
                   ((('iv' in icold_spelling_splits) or ('four' in icold_spelling_splits)) and (('iv' not in google_spelling_splits) and ('four' not in google_spelling_splits))) or \
                   ((('v' in icold_spelling_splits) or ('five' in icold_spelling_splits)) and (('v' not in google_spelling_splits) and ('five' not in google_spelling_splits))) or \
                   ((('vi' in icold_spelling_splits) or ('six' in icold_spelling_splits)) and (('vi' not in google_spelling_splits) and ('six' not in google_spelling_splits))) or \
                   ((('vii' in icold_spelling_splits) or ('seven' in icold_spelling_splits)) and (('vii' not in google_spelling_splits) and ('seven' not in google_spelling_splits))) or \
                   ((('viii' in icold_spelling_splits) or ('eight' in icold_spelling_splits)) and (('viii' not in google_spelling_splits) and ('eight' not in google_spelling_splits))) or \
                   ((('ix' in icold_spelling_splits) or ('nine' in icold_spelling_splits)) and (('ix' not in google_spelling_splits) and ('nine' not in google_spelling_splits))) or \
                   ((('x' in icold_spelling_splits) or ('ten' in icold_spelling_splits)) and (('x' not in google_spelling_splits) and ('ten' not in google_spelling_splits))) or \
                   ((('xi' in icold_spelling_splits) or ('eleven' in icold_spelling_splits)) and (('xi' not in google_spelling_splits) and ('eleven' not in google_spelling_splits))) or \
                   ((('xii' in icold_spelling_splits) or ('twelve' in icold_spelling_splits)) and (('xii' not in google_spelling_splits) and ('twelve' not in google_spelling_splits))) or \
                   ((('xiii' in icold_spelling_splits) or ('thirteen' in icold_spelling_splits)) and (('xiii' not in google_spelling_splits) and ('thirteen' not in google_spelling_splits))) or \
                   ((('xiv' in icold_spelling_splits) or ('fourteen' in icold_spelling_splits)) and (('xiv' not in google_spelling_splits) and ('fourteen' not in google_spelling_splits))) or \
                   ((('xv' in icold_spelling_splits) or ('fifteen' in icold_spelling_splits)) and (('xv' not in google_spelling_splits) and ('fifteen' not in google_spelling_splits))) or \
                   ((('xvi' in icold_spelling_splits) or ('sixteen' in icold_spelling_splits)) and (('xvi' not in google_spelling_splits) and ('sixteen' not in google_spelling_splits))) or \
                   ((('xvii' in icold_spelling_splits) or ('seventeen' in icold_spelling_splits)) and (('xvii' not in google_spelling_splits) and ('seventeen' not in google_spelling_splits))) or \
                   ((('xviii' in icold_spelling_splits) or ('eighteen' in icold_spelling_splits)) and (('xviii' not in google_spelling_splits) and ('eighteen' not in google_spelling_splits))) or \
                   ((('xix' in icold_spelling_splits) or ('nineteen' in icold_spelling_splits)) and (('xix' not in google_spelling_splits) and ('nineteen' not in google_spelling_splits))) or \
                   ((('xx' in icold_spelling_splits) or ('twenty' in icold_spelling_splits)) and (('xx' not in google_spelling_splits) and ('twenty' not in google_spelling_splits))) or \
                   ((('i' in google_spelling_splits) or ('one' in google_spelling_splits)) and (('i' not in icold_spelling_splits) and ('one' not in icold_spelling_splits))) or \
                   ((('ii' in google_spelling_splits) or ('two' in google_spelling_splits)) and (('ii' not in icold_spelling_splits) and ('two' not in icold_spelling_splits))) or \
                   ((('iii' in google_spelling_splits) or ('three' in google_spelling_splits)) and (('iii' not in icold_spelling_splits) and ('three' not in icold_spelling_splits))) or \
                   ((('iv' in google_spelling_splits) or ('four' in google_spelling_splits)) and (('iv' not in icold_spelling_splits) and ('four' not in icold_spelling_splits))) or \
                   ((('v' in google_spelling_splits) or ('five' in google_spelling_splits)) and (('v' not in icold_spelling_splits) and ('five' not in icold_spelling_splits))) or \
                   ((('vi' in google_spelling_splits) or ('six' in google_spelling_splits)) and (('vi' not in icold_spelling_splits) and ('six' not in icold_spelling_splits))) or \
                   ((('vii' in google_spelling_splits) or ('seven' in google_spelling_splits)) and (('vii' not in icold_spelling_splits) and ('seven' not in icold_spelling_splits))) or \
                   ((('viii' in google_spelling_splits) or ('eight' in google_spelling_splits)) and (('viii' not in icold_spelling_splits) and ('eight' not in icold_spelling_splits))) or \
                   ((('ix' in google_spelling_splits) or ('nine' in google_spelling_splits)) and (('ix' not in icold_spelling_splits) and ('nine' not in icold_spelling_splits))) or \
                   ((('x' in google_spelling_splits) or ('ten' in google_spelling_splits)) and (('x' not in icold_spelling_splits) and ('ten' not in icold_spelling_splits))) or \
                   ((('xi' in google_spelling_splits) or ('eleven' in google_spelling_splits)) and (('xi' not in icold_spelling_splits) and ('eleven' not in icold_spelling_splits))) or \
                   ((('xii' in google_spelling_splits) or ('twelve' in google_spelling_splits)) and (('xii' not in icold_spelling_splits) and ('twelve' not in icold_spelling_splits))) or \
                   ((('xiii' in google_spelling_splits) or ('thirteen' in google_spelling_splits)) and (('xiii' not in icold_spelling_splits) and ('thirteen' not in icold_spelling_splits))) or \
                   ((('xiv' in google_spelling_splits) or ('fourteen' in google_spelling_splits)) and (('xiv' not in icold_spelling_splits) and ('fourteen' not in icold_spelling_splits))) or \
                   ((('xv' in google_spelling_splits) or ('fifteen' in google_spelling_splits)) and (('xv' not in icold_spelling_splits) and ('fifteen' not in icold_spelling_splits))) or \
                   ((('xvi' in google_spelling_splits) or ('sixteen' in google_spelling_splits)) and (('xvi' not in icold_spelling_splits) and ('sixteen' not in icold_spelling_splits))) or \
                   ((('xvii' in google_spelling_splits) or ('seventeen' in google_spelling_splits)) and (('xvii' not in icold_spelling_splits) and ('seventeen' not in icold_spelling_splits))) or \
                   ((('xviii' in google_spelling_splits) or ('eighteen' in google_spelling_splits)) and (('xviii' not in icold_spelling_splits) and ('eighteen' not in icold_spelling_splits))) or \
                   ((('xix' in google_spelling_splits) or ('nineteen' in google_spelling_splits)) and (('xix' not in icold_spelling_splits) and ('nineteen' not in icold_spelling_splits))) or \
                   ((('xx' in google_spelling_splits) or ('twenty' in google_spelling_splits)) and (('xx' not in icold_spelling_splits) and ('twenty' not in icold_spelling_splits))):
                    continue_or_not = 0
            elif len(numbers_left)==0 and len(numbers_right)==1:
                if ((('i' in icold_spelling_splits) or ('one' in icold_spelling_splits)) and ('1' in google_spelling_splits)) or \
                   ((('ii' in icold_spelling_splits) or ('two' in icold_spelling_splits)) and ('2' in google_spelling_splits)) or \
                   ((('iii' in icold_spelling_splits) or ('three' in icold_spelling_splits)) and ('3' in google_spelling_splits)) or \
                   ((('iv' in icold_spelling_splits) or ('four' in icold_spelling_splits)) and ('4' in google_spelling_splits)) or \
                   ((('v' in icold_spelling_splits) or ('five' in icold_spelling_splits)) and ('5' in google_spelling_splits)) or \
                   ((('vi' in icold_spelling_splits) or ('six' in icold_spelling_splits)) and ('6' in google_spelling_splits)) or \
                   ((('vii' in icold_spelling_splits) or ('seven' in icold_spelling_splits)) and ('7' in google_spelling_splits)) or \
                   ((('viii' in icold_spelling_splits) or ('eight' in icold_spelling_splits)) and ('8' in google_spelling_splits)) or \
                   ((('ix' in icold_spelling_splits) or ('nine' in icold_spelling_splits)) and ('9' in google_spelling_splits)) or \
                   ((('x' in icold_spelling_splits) or ('ten' in icold_spelling_splits)) and ('10' in google_spelling_splits)) or \
                   ((('xi' in icold_spelling_splits) or ('eleven' in icold_spelling_splits)) and ('11' in google_spelling_splits)) or \
                   ((('xii' in icold_spelling_splits) or ('twelve' in icold_spelling_splits)) and ('12' in google_spelling_splits)) or \
                   ((('xiii' in icold_spelling_splits) or ('thirteen' in icold_spelling_splits)) and ('13' in google_spelling_splits)) or \
                   ((('xiv' in icold_spelling_splits) or ('fourteen' in icold_spelling_splits)) and ('14' in google_spelling_splits)) or \
                   ((('xv' in icold_spelling_splits) or ('fifteen' in icold_spelling_splits)) and ('15' in google_spelling_splits)) or \
                   ((('xvi' in icold_spelling_splits) or ('sixteen' in icold_spelling_splits)) and ('16' in google_spelling_splits)) or \
                   ((('xvii' in icold_spelling_splits) or ('seventeen' in icold_spelling_splits)) and ('17' in google_spelling_splits)) or \
                   ((('xviii' in icold_spelling_splits) or ('eighteen' in icold_spelling_splits)) and ('18' in google_spelling_splits)) or \
                   ((('xix' in icold_spelling_splits) or ('nineteen' in icold_spelling_splits)) and ('19' in google_spelling_splits)) or \
                   ((('xx' in icold_spelling_splits) or ('twenty' in icold_spelling_splits)) and ('20' in google_spelling_splits)):
                    continue_or_not = 1
                else:
                    continue_or_not = 0
            elif len(numbers_left)==1 and len(numbers_right)==0:
                if ((('i' in google_spelling_splits) or ('one' in google_spelling_splits)) and ('1' in icold_spelling_splits)) or \
                   ((('ii' in google_spelling_splits) or ('two' in google_spelling_splits)) and ('2' in icold_spelling_splits)) or \
                   ((('iii' in google_spelling_splits) or ('three' in google_spelling_splits)) and ('3' in icold_spelling_splits)) or \
                   ((('iv' in google_spelling_splits) or ('four' in google_spelling_splits)) and ('4' in icold_spelling_splits)) or \
                   ((('v' in google_spelling_splits) or ('five' in google_spelling_splits)) and ('5' in icold_spelling_splits)) or \
                   ((('vi' in google_spelling_splits) or ('six' in google_spelling_splits)) and ('6' in icold_spelling_splits)) or \
                   ((('vii' in google_spelling_splits) or ('seven' in google_spelling_splits)) and ('7' in icold_spelling_splits)) or \
                   ((('viii' in google_spelling_splits) or ('eight' in google_spelling_splits)) and ('8' in icold_spelling_splits)) or \
                   ((('ix' in google_spelling_splits) or ('nine' in google_spelling_splits)) and ('9' in icold_spelling_splits)) or \
                   ((('x' in google_spelling_splits) or ('ten' in google_spelling_splits)) and ('10' in icold_spelling_splits)) or \
                   ((('xi' in google_spelling_splits) or ('eleven' in google_spelling_splits)) and ('11' in icold_spelling_splits)) or \
                   ((('xii' in google_spelling_splits) or ('twelve' in google_spelling_splits)) and ('12' in icold_spelling_splits)) or \
                   ((('xiii' in google_spelling_splits) or ('thirteen' in google_spelling_splits)) and ('13' in icold_spelling_splits)) or \
                   ((('xiv' in google_spelling_splits) or ('fourteen' in google_spelling_splits)) and ('14' in icold_spelling_splits)) or \
                   ((('xv' in google_spelling_splits) or ('fifteen' in google_spelling_splits)) and ('15' in icold_spelling_splits)) or \
                   ((('xvi' in google_spelling_splits) or ('sixteen' in google_spelling_splits)) and ('16' in icold_spelling_splits)) or \
                   ((('xvii' in google_spelling_splits) or ('seventeen' in google_spelling_splits)) and ('17' in icold_spelling_splits)) or \
                   ((('xviii' in google_spelling_splits) or ('eighteen' in google_spelling_splits)) and ('18' in icold_spelling_splits)) or \
                   ((('xix' in google_spelling_splits) or ('nineteen' in google_spelling_splits)) and ('19' in icold_spelling_splits)) or \
                   ((('xx' in google_spelling_splits) or ('twenty' in google_spelling_splits)) and ('20' in icold_spelling_splits)):
                    continue_or_not = 1
                else:
                    continue_or_not = 0
            else:
                continue_or_not = 0
            # To further reduce ambiguity, check if any of the following elements in the first name is also included in the other name.
            # The assumption is that two equivalent names cannot contain different direction adjectives or letters.
            # For example, "Tuttle Creek East" is not the same dam as "Tuttle Creek West".
            if (('east' in icold_spelling_splits) and ('east' not in google_spelling_splits)) or (('east' in google_spelling_splits) and ('east' not in icold_spelling_splits)) or \
               (('west' in icold_spelling_splits) and ('west' not in google_spelling_splits)) or (('west' in google_spelling_splits) and ('west' not in icold_spelling_splits)) or \
               (('north' in icold_spelling_splits) and ('north' not in google_spelling_splits)) or (('north' in google_spelling_splits) and ('north' not in icold_spelling_splits)) or \
               (('south' in icold_spelling_splits) and ('south' not in google_spelling_splits)) or (('south' in google_spelling_splits) and ('south' not in icold_spelling_splits)) or \
               (('upper' in icold_spelling_splits) and ('upper' not in google_spelling_splits)) or (('upper' in google_spelling_splits) and ('upper' not in icold_spelling_splits)) or \
               (('lower' in icold_spelling_splits) and ('lower' not in google_spelling_splits)) or (('lower' in google_spelling_splits) and ('lower' not in icold_spelling_splits)) or \
               (('a' in icold_spelling_splits) and ('a' not in google_spelling_splits)) or (('a' in google_spelling_splits) and ('a' not in icold_spelling_splits)) or \
               (('b' in icold_spelling_splits) and ('b' not in google_spelling_splits)) or (('b' in google_spelling_splits) and ('b' not in icold_spelling_splits)) or \
               (('c' in icold_spelling_splits) and ('c' not in google_spelling_splits)) or (('c' in google_spelling_splits) and ('c' not in icold_spelling_splits)) or \
               (('d' in icold_spelling_splits) and ('d' not in google_spelling_splits)) or (('d' in google_spelling_splits) and ('d' not in icold_spelling_splits)) or \
               (('auxiliar' in icold_spelling_splits) and ('auxiliar' not in google_spelling_splits)) or (('auxiliar' in google_spelling_splits) and ('auxiliar' not in icold_spelling_splits)) or \
               (('auxiliary' in icold_spelling_splits) and ('auxiliary' not in google_spelling_splits)) or (('auxiliary' in google_spelling_splits) and ('auxiliary' not in icold_spelling_splits)):
                continue_or_not = 0
            # Continue the comparison if none of the situations above happens. 
            if continue_or_not == 0:
                damname_similarity_pass = 0
            elif (dam_name_input_simple != '' and geocoded_name_input_simple != ''):
                similarity_value = similar(dam_name_input_simple, geocoded_name_input_simple)
                if similarity_value >= similarity_t:
                    damname_similarity_pass = 1
                if damname_similarity_pass != 1: #not passed
                    # Check containment relations
                    if (dam_name_input_simple in geocoded_name_input_simple) == True and (dam_name_input_simple != geocoded_name_input_simple) == True: #ICOLD contained by Google
                        if geocoded_name_input_simple.find(dam_name_input_simple) == 0: #'manhattan city': 'manhattan'
                            if geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)+len(dam_name_input_simple)] == ' ' or \
                               geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)+len(dam_name_input_simple)] == '-':
                                damname_similarity_pass = 1
                        elif (geocoded_name_input_simple.find(dam_name_input_simple)+len(dam_name_input_simple)) == len(geocoded_name_input_simple): #'city of manhattan': 'manhattan'
                            if geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)-1] == ' ' or \
                               geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)-1] == '-':
                                damname_similarity_pass = 1
                    elif (geocoded_name_input_simple in dam_name_input_simple) == True and (dam_name_input_simple != geocoded_name_input_simple) == True: #ICOLD containing Google
                        if dam_name_input_simple.find(geocoded_name_input_simple) == 0: #'manhattan city': 'manhattan'
                            if dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)+len(geocoded_name_input_simple)] == ' ' or \
                               dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)+len(geocoded_name_input_simple)] == '-':
                                damname_similarity_pass = 1
                        elif (dam_name_input_simple.find(geocoded_name_input_simple)+len(geocoded_name_input_simple)) == len(dam_name_input_simple): #'city of manhattan': 'manhattan'
                            if dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)-1] == ' ' or \
                               dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)-1] == '-':
                                damname_similarity_pass = 1
                if damname_similarity_pass != 1:
                    for icold_split in icold_spelling_splits:
                        for google_split in google_spelling_splits:
                            # Further eliminate possibly ancillary information from the name.
                            if len(google_split)>3 and len(icold_split)>3 and \
                               google_split != 'main' and icold_split != 'main' and \
                               google_split != 'tank' and icold_split != 'tank' and \
                               google_split != 'dyke' and icold_split != 'dyke' and google_split != 'canal' and icold_split != 'canal' and \
                               google_split != 'canyon' and icold_split != 'canyon' and google_split != 'diversion' and icold_split != 'diversion' and \
                               google_split != 'city' and icold_split != 'city' and google_split != 'town' and icold_split != 'town' and \
                               google_split != 'fall' and icold_split != 'fall' and google_split != 'falls' and icold_split != 'falls' and \
                               google_split != 'west' and icold_split != 'west' and google_split != 'east' and icold_split != 'east' and \
                               google_split != 'south' and icold_split != 'south' and google_split != 'norht' and icold_split != 'north' and \
                               google_split != 'storage' and icold_split != 'storage' and google_split != 'river' and icold_split != 'river' and \
                               google_split != 'saint' and icold_split != 'saint' and google_split != 'kloof' and icold_split != 'kloof' and \
                               google_split != 'berg' and icold_split != 'berg' and google_split != 'santa' and icold_split != 'santa' and \
                               google_split != 'valley' and icold_split != 'valley' and google_split != 'upper' and icold_split != 'upper' and \
                               google_split != 'lower' and icold_split != 'lower' and google_split != 'creek' and icold_split != 'creek' and \
                               google_split != 'lake' and icold_split != 'lake' and google_split != 'reservoir' and icold_split != 'reservoir' and \
                               google_split != 'lock' and icold_split != 'lock' and google_split != 'barrage' and icold_split != 'barrage' and \
                               google_split != 'lago' and icold_split != 'lago' and google_split != 'shuiku' and icold_split != 'shuiku' and \
                               google_split != 'presa' and icold_split != 'presa' and google_split != 'embalse' and icold_split != 'embalse' and \
                               google_split != 'barragem' and icold_split != 'barragem' and google_split != 'agua' and icold_split != 'agua' and \
                               google_split != 'stuwal' and icold_split != 'stuwal' and google_split != 'weir' and icold_split != 'weir' and \
                               google_split != 'dike' and icold_split != 'dike' and google_split != 'levee' and icold_split != 'levee' and \
                               google_split != 'mountain' and icold_split != 'mountain' and google_split != 'hill' and icold_split != 'hill' and \
                               google_split != 'auxiliar' and icold_split != 'auxiliar' and google_split != 'auxiliary' and icold_split != 'auxiliary' and \
                               google_split != 'riacho' and icold_split != 'riacho' and google_split != 'ribeirao' and icold_split != 'ribeirao' and \
                               google_split != 'ribeiro' and icold_split != 'ribeiro' and google_split != 'ribeira' and icold_split != 'ribeira' and \
                               google_split != 'riviere' and icold_split != 'riviere': 
                                if similar(icold_split, google_split) >= similarity_t:
                                    damname_similarity_pass_alt = 1
                                    break
                        if damname_similarity_pass_alt==1:
                            break
    # If the similary test has not been passed, continue to check the reservoir dam if any.
    if damname_similarity_pass != 1:
        if reservoir_name_input == '-999' or geocoded_name_input == '-999' or reservoir_name_input == '' or geocoded_name_input == '' or \
           reservoir_name_input == None or geocoded_name_input == None or reservoir_name_input == '/' or geocoded_name_input == '/'  or \
           reservoir_name_input == '-' or geocoded_name_input == '-' or reservoir_name_input == '..' or geocoded_name_input == '..' or \
           reservoir_name_input == '_' or geocoded_name_input == '_':
            damname_similarity_pass = 0
        elif (len(reservoir_name_input)>=7 and (reservoir_name_input[0:7]=='unknown' or reservoir_name_input[0:7]=='unnamed' or reservoir_name_input[0:7]=='un-name')) or \
             (len(geocoded_name_input)>=7 and (geocoded_name_input[0:7]=='unknown' or geocoded_name_input[0:7]=='unnamed' or geocoded_name_input[0:7]=='un-name')):
            damname_similarity_pass = 0
        elif geocoded_name_input == 'not found':
            damname_similarity_pass = -1
        else:
            dam_name_input_simple = remove_accents(reservoir_name_input)
            dam_name_input_simple = ' ' + dam_name_input_simple + ' '
            # Remove ancillary titles.
            for this_to_be_removed in to_be_removed:
                if this_to_be_removed in dam_name_input_simple:
                    dam_name_input_simple = dam_name_input_simple.replace(this_to_be_removed, ' ')
            dam_name_input_simple = dam_name_input_simple.strip()
            if this_country_ISO_input == 'cn':
                if len(dam_name_input_simple) > 8 and dam_name_input_simple[-6:] == 'shuiku':
                    dam_name_input_simple = (dam_name_input_simple[0:(len(dam_name_input_simple)-6)]).lower().strip()
            # Extract Arabic numbers from both names.  
            continue_or_not = 1
            numbers_left = re.findall(r'\d+', dam_name_input_simple)
            numbers_right = re.findall(r'\d+', geocoded_name_input_simple)
            # Split the name by delimiters.
            icold_spelling_splits = [] 
            for this_split_space in dam_name_input_simple.split():
                for this_split_comma in this_split_space.split(','):
                    for this_split_period in this_split_comma.split('.'):
                        for this_split_hypen in this_split_period.split('-'):
                            for this_split_slash in this_split_hypen.split('/'): ###
                                for this_split_paren1 in this_split_slash.split('('):
                                    for this_split_paren2 in this_split_paren1.split(')'):
                                        if this_split_paren2 != '':
                                            icold_spelling_splits.append(this_split_paren2)
            google_spelling_splits = []
            for this_split_space in geocoded_name_input_simple.split():
                for this_split_comma in this_split_space.split(','):
                    for this_split_period in this_split_comma.split('.'):
                        for this_split_hypen in this_split_period.split('-'):
                            for this_split_slash in this_split_hypen.split('/'):
                                for this_split_paren1 in this_split_slash.split('('):
                                    for this_split_paren2 in this_split_paren1.split(')'):
                                        if this_split_paren2 != '':
                                            google_spelling_splits.append(this_split_paren2)
            # To reduce ambiguity, check if each of the Arabic numbers in the first name is also included in the other name.
            # The assumption is that two equivalent names cannot contain different numbers.
            # For example, "Tuttle Creek #1" is not the same dam as "Tuttle Creek #2".
            if len(numbers_left)>0 and len(numbers_right)>0:
                for this_number_left in numbers_left:
                    if this_number_left not in numbers_right:
                        continue_or_not = 0
                        break
                for this_numbers_right in numbers_right:
                    if this_numbers_right not in numbers_left:
                        continue_or_not = 0
                        break
            elif len(numbers_left)==0 and len(numbers_right)==0: # Also check other number formats.
                if ((('i' in icold_spelling_splits) or ('one' in icold_spelling_splits)) and (('i' not in google_spelling_splits) and ('one' not in google_spelling_splits))) or \
                   ((('ii' in icold_spelling_splits) or ('two' in icold_spelling_splits)) and (('ii' not in google_spelling_splits) and ('two' not in google_spelling_splits))) or \
                   ((('iii' in icold_spelling_splits) or ('three' in icold_spelling_splits)) and (('iii' not in google_spelling_splits) and ('three' not in google_spelling_splits))) or \
                   ((('iv' in icold_spelling_splits) or ('four' in icold_spelling_splits)) and (('iv' not in google_spelling_splits) and ('four' not in google_spelling_splits))) or \
                   ((('v' in icold_spelling_splits) or ('five' in icold_spelling_splits)) and (('v' not in google_spelling_splits) and ('five' not in google_spelling_splits))) or \
                   ((('vi' in icold_spelling_splits) or ('six' in icold_spelling_splits)) and (('vi' not in google_spelling_splits) and ('six' not in google_spelling_splits))) or \
                   ((('vii' in icold_spelling_splits) or ('seven' in icold_spelling_splits)) and (('vii' not in google_spelling_splits) and ('seven' not in google_spelling_splits))) or \
                   ((('viii' in icold_spelling_splits) or ('eight' in icold_spelling_splits)) and (('viii' not in google_spelling_splits) and ('eight' not in google_spelling_splits))) or \
                   ((('ix' in icold_spelling_splits) or ('nine' in icold_spelling_splits)) and (('ix' not in google_spelling_splits) and ('nine' not in google_spelling_splits))) or \
                   ((('x' in icold_spelling_splits) or ('ten' in icold_spelling_splits)) and (('x' not in google_spelling_splits) and ('ten' not in google_spelling_splits))) or \
                   ((('xi' in icold_spelling_splits) or ('eleven' in icold_spelling_splits)) and (('xi' not in google_spelling_splits) and ('eleven' not in google_spelling_splits))) or \
                   ((('xii' in icold_spelling_splits) or ('twelve' in icold_spelling_splits)) and (('xii' not in google_spelling_splits) and ('twelve' not in google_spelling_splits))) or \
                   ((('xiii' in icold_spelling_splits) or ('thirteen' in icold_spelling_splits)) and (('xiii' not in google_spelling_splits) and ('thirteen' not in google_spelling_splits))) or \
                   ((('xiv' in icold_spelling_splits) or ('fourteen' in icold_spelling_splits)) and (('xiv' not in google_spelling_splits) and ('fourteen' not in google_spelling_splits))) or \
                   ((('xv' in icold_spelling_splits) or ('fifteen' in icold_spelling_splits)) and (('xv' not in google_spelling_splits) and ('fifteen' not in google_spelling_splits))) or \
                   ((('xvi' in icold_spelling_splits) or ('sixteen' in icold_spelling_splits)) and (('xvi' not in google_spelling_splits) and ('sixteen' not in google_spelling_splits))) or \
                   ((('xvii' in icold_spelling_splits) or ('seventeen' in icold_spelling_splits)) and (('xvii' not in google_spelling_splits) and ('seventeen' not in google_spelling_splits))) or \
                   ((('xviii' in icold_spelling_splits) or ('eighteen' in icold_spelling_splits)) and (('xviii' not in google_spelling_splits) and ('eighteen' not in google_spelling_splits))) or \
                   ((('xix' in icold_spelling_splits) or ('nineteen' in icold_spelling_splits)) and (('xix' not in google_spelling_splits) and ('nineteen' not in google_spelling_splits))) or \
                   ((('xx' in icold_spelling_splits) or ('twenty' in icold_spelling_splits)) and (('xx' not in google_spelling_splits) and ('twenty' not in google_spelling_splits))) or \
                   ((('i' in google_spelling_splits) or ('one' in google_spelling_splits)) and (('i' not in icold_spelling_splits) and ('one' not in icold_spelling_splits))) or \
                   ((('ii' in google_spelling_splits) or ('two' in google_spelling_splits)) and (('ii' not in icold_spelling_splits) and ('two' not in icold_spelling_splits))) or \
                   ((('iii' in google_spelling_splits) or ('three' in google_spelling_splits)) and (('iii' not in icold_spelling_splits) and ('three' not in icold_spelling_splits))) or \
                   ((('iv' in google_spelling_splits) or ('four' in google_spelling_splits)) and (('iv' not in icold_spelling_splits) and ('four' not in icold_spelling_splits))) or \
                   ((('v' in google_spelling_splits) or ('five' in google_spelling_splits)) and (('v' not in icold_spelling_splits) and ('five' not in icold_spelling_splits))) or \
                   ((('vi' in google_spelling_splits) or ('six' in google_spelling_splits)) and (('vi' not in icold_spelling_splits) and ('six' not in icold_spelling_splits))) or \
                   ((('vii' in google_spelling_splits) or ('seven' in google_spelling_splits)) and (('vii' not in icold_spelling_splits) and ('seven' not in icold_spelling_splits))) or \
                   ((('viii' in google_spelling_splits) or ('eight' in google_spelling_splits)) and (('viii' not in icold_spelling_splits) and ('eight' not in icold_spelling_splits))) or \
                   ((('ix' in google_spelling_splits) or ('nine' in google_spelling_splits)) and (('ix' not in icold_spelling_splits) and ('nine' not in icold_spelling_splits))) or \
                   ((('x' in google_spelling_splits) or ('ten' in google_spelling_splits)) and (('x' not in icold_spelling_splits) and ('ten' not in icold_spelling_splits))) or \
                   ((('xi' in google_spelling_splits) or ('eleven' in google_spelling_splits)) and (('xi' not in icold_spelling_splits) and ('eleven' not in icold_spelling_splits))) or \
                   ((('xii' in google_spelling_splits) or ('twelve' in google_spelling_splits)) and (('xii' not in icold_spelling_splits) and ('twelve' not in icold_spelling_splits))) or \
                   ((('xiii' in google_spelling_splits) or ('thirteen' in google_spelling_splits)) and (('xiii' not in icold_spelling_splits) and ('thirteen' not in icold_spelling_splits))) or \
                   ((('xiv' in google_spelling_splits) or ('fourteen' in google_spelling_splits)) and (('xiv' not in icold_spelling_splits) and ('fourteen' not in icold_spelling_splits))) or \
                   ((('xv' in google_spelling_splits) or ('fifteen' in google_spelling_splits)) and (('xv' not in icold_spelling_splits) and ('fifteen' not in icold_spelling_splits))) or \
                   ((('xvi' in google_spelling_splits) or ('sixteen' in google_spelling_splits)) and (('xvi' not in icold_spelling_splits) and ('sixteen' not in icold_spelling_splits))) or \
                   ((('xvii' in google_spelling_splits) or ('seventeen' in google_spelling_splits)) and (('xvii' not in icold_spelling_splits) and ('seventeen' not in icold_spelling_splits))) or \
                   ((('xviii' in google_spelling_splits) or ('eighteen' in google_spelling_splits)) and (('xviii' not in icold_spelling_splits) and ('eighteen' not in icold_spelling_splits))) or \
                   ((('xix' in google_spelling_splits) or ('nineteen' in google_spelling_splits)) and (('xix' not in icold_spelling_splits) and ('nineteen' not in icold_spelling_splits))) or \
                   ((('xx' in google_spelling_splits) or ('twenty' in google_spelling_splits)) and (('xx' not in icold_spelling_splits) and ('twenty' not in icold_spelling_splits))):
                    continue_or_not = 0
            elif len(numbers_left)==0 and len(numbers_right)==1:
                if ((('i' in icold_spelling_splits) or ('one' in icold_spelling_splits)) and ('1' in google_spelling_splits)) or \
                   ((('ii' in icold_spelling_splits) or ('two' in icold_spelling_splits)) and ('2' in google_spelling_splits)) or \
                   ((('iii' in icold_spelling_splits) or ('three' in icold_spelling_splits)) and ('3' in google_spelling_splits)) or \
                   ((('iv' in icold_spelling_splits) or ('four' in icold_spelling_splits)) and ('4' in google_spelling_splits)) or \
                   ((('v' in icold_spelling_splits) or ('five' in icold_spelling_splits)) and ('5' in google_spelling_splits)) or \
                   ((('vi' in icold_spelling_splits) or ('six' in icold_spelling_splits)) and ('6' in google_spelling_splits)) or \
                   ((('vii' in icold_spelling_splits) or ('seven' in icold_spelling_splits)) and ('7' in google_spelling_splits)) or \
                   ((('viii' in icold_spelling_splits) or ('eight' in icold_spelling_splits)) and ('8' in google_spelling_splits)) or \
                   ((('ix' in icold_spelling_splits) or ('nine' in icold_spelling_splits)) and ('9' in google_spelling_splits)) or \
                   ((('x' in icold_spelling_splits) or ('ten' in icold_spelling_splits)) and ('10' in google_spelling_splits)) or \
                   ((('xi' in icold_spelling_splits) or ('eleven' in icold_spelling_splits)) and ('11' in google_spelling_splits)) or \
                   ((('xii' in icold_spelling_splits) or ('twelve' in icold_spelling_splits)) and ('12' in google_spelling_splits)) or \
                   ((('xiii' in icold_spelling_splits) or ('thirteen' in icold_spelling_splits)) and ('13' in google_spelling_splits)) or \
                   ((('xiv' in icold_spelling_splits) or ('fourteen' in icold_spelling_splits)) and ('14' in google_spelling_splits)) or \
                   ((('xv' in icold_spelling_splits) or ('fifteen' in icold_spelling_splits)) and ('15' in google_spelling_splits)) or \
                   ((('xvi' in icold_spelling_splits) or ('sixteen' in icold_spelling_splits)) and ('16' in google_spelling_splits)) or \
                   ((('xvii' in icold_spelling_splits) or ('seventeen' in icold_spelling_splits)) and ('17' in google_spelling_splits)) or \
                   ((('xviii' in icold_spelling_splits) or ('eighteen' in icold_spelling_splits)) and ('18' in google_spelling_splits)) or \
                   ((('xix' in icold_spelling_splits) or ('nineteen' in icold_spelling_splits)) and ('19' in google_spelling_splits)) or \
                   ((('xx' in icold_spelling_splits) or ('twenty' in icold_spelling_splits)) and ('20' in google_spelling_splits)):
                    continue_or_not = 1
                else:
                    continue_or_not = 0
            elif len(numbers_left)==1 and len(numbers_right)==0:
                if ((('i' in google_spelling_splits) or ('one' in google_spelling_splits)) and ('1' in icold_spelling_splits)) or \
                   ((('ii' in google_spelling_splits) or ('two' in google_spelling_splits)) and ('2' in icold_spelling_splits)) or \
                   ((('iii' in google_spelling_splits) or ('three' in google_spelling_splits)) and ('3' in icold_spelling_splits)) or \
                   ((('iv' in google_spelling_splits) or ('four' in google_spelling_splits)) and ('4' in icold_spelling_splits)) or \
                   ((('v' in google_spelling_splits) or ('five' in google_spelling_splits)) and ('5' in icold_spelling_splits)) or \
                   ((('vi' in google_spelling_splits) or ('six' in google_spelling_splits)) and ('6' in icold_spelling_splits)) or \
                   ((('vii' in google_spelling_splits) or ('seven' in google_spelling_splits)) and ('7' in icold_spelling_splits)) or \
                   ((('viii' in google_spelling_splits) or ('eight' in google_spelling_splits)) and ('8' in icold_spelling_splits)) or \
                   ((('ix' in google_spelling_splits) or ('nine' in google_spelling_splits)) and ('9' in icold_spelling_splits)) or \
                   ((('x' in google_spelling_splits) or ('ten' in google_spelling_splits)) and ('10' in icold_spelling_splits)) or \
                   ((('xi' in google_spelling_splits) or ('eleven' in google_spelling_splits)) and ('11' in icold_spelling_splits)) or \
                   ((('xii' in google_spelling_splits) or ('twelve' in google_spelling_splits)) and ('12' in icold_spelling_splits)) or \
                   ((('xiii' in google_spelling_splits) or ('thirteen' in google_spelling_splits)) and ('13' in icold_spelling_splits)) or \
                   ((('xiv' in google_spelling_splits) or ('fourteen' in google_spelling_splits)) and ('14' in icold_spelling_splits)) or \
                   ((('xv' in google_spelling_splits) or ('fifteen' in google_spelling_splits)) and ('15' in icold_spelling_splits)) or \
                   ((('xvi' in google_spelling_splits) or ('sixteen' in google_spelling_splits)) and ('16' in icold_spelling_splits)) or \
                   ((('xvii' in google_spelling_splits) or ('seventeen' in google_spelling_splits)) and ('17' in icold_spelling_splits)) or \
                   ((('xviii' in google_spelling_splits) or ('eighteen' in google_spelling_splits)) and ('18' in icold_spelling_splits)) or \
                   ((('xix' in google_spelling_splits) or ('nineteen' in google_spelling_splits)) and ('19' in icold_spelling_splits)) or \
                   ((('xx' in google_spelling_splits) or ('twenty' in google_spelling_splits)) and ('20' in icold_spelling_splits)):
                    continue_or_not = 1
                else:
                    continue_or_not = 0
            else:
                continue_or_not = 0
            # To further reduce ambiguity, check if any of the following elements in the first name is also included in the other name.
            # The assumption is that two equivalent names cannot contain different direction adjectives or letters.
            # For example, "Tuttle Creek East" is not the same dam as "Tuttle Creek West".
            if (('east' in icold_spelling_splits) and ('east' not in google_spelling_splits)) or (('east' in google_spelling_splits) and ('east' not in icold_spelling_splits)) or \
               (('west' in icold_spelling_splits) and ('west' not in google_spelling_splits)) or (('west' in google_spelling_splits) and ('west' not in icold_spelling_splits)) or \
               (('north' in icold_spelling_splits) and ('north' not in google_spelling_splits)) or (('north' in google_spelling_splits) and ('north' not in icold_spelling_splits)) or \
               (('south' in icold_spelling_splits) and ('south' not in google_spelling_splits)) or (('south' in google_spelling_splits) and ('south' not in icold_spelling_splits)) or \
               (('upper' in icold_spelling_splits) and ('upper' not in google_spelling_splits)) or (('upper' in google_spelling_splits) and ('upper' not in icold_spelling_splits)) or \
               (('lower' in icold_spelling_splits) and ('lower' not in google_spelling_splits)) or (('lower' in google_spelling_splits) and ('lower' not in icold_spelling_splits)) or \
               (('a' in icold_spelling_splits) and ('a' not in google_spelling_splits)) or (('a' in google_spelling_splits) and ('a' not in icold_spelling_splits)) or \
               (('b' in icold_spelling_splits) and ('b' not in google_spelling_splits)) or (('b' in google_spelling_splits) and ('b' not in icold_spelling_splits)) or \
               (('c' in icold_spelling_splits) and ('c' not in google_spelling_splits)) or (('c' in google_spelling_splits) and ('c' not in icold_spelling_splits)) or \
               (('d' in icold_spelling_splits) and ('d' not in google_spelling_splits)) or (('d' in google_spelling_splits) and ('d' not in icold_spelling_splits)) or \
               (('auxiliar' in icold_spelling_splits) and ('auxiliar' not in google_spelling_splits)) or (('auxiliar' in google_spelling_splits) and ('auxiliar' not in icold_spelling_splits)) or \
               (('auxiliary' in icold_spelling_splits) and ('auxiliary' not in google_spelling_splits)) or (('auxiliary' in google_spelling_splits) and ('auxiliary' not in icold_spelling_splits)):
                continue_or_not = 0
            # Continue the comparison if none of the situations above happens.
            if continue_or_not == 0:
                damname_similarity_pass = 0
            elif (dam_name_input_simple != '' and geocoded_name_input_simple != ''):
                similarity_value = similar(dam_name_input_simple, geocoded_name_input_simple)
                if similarity_value >= similarity_t:
                    damname_similarity_pass = 1
                if damname_similarity_pass != 1:
                    # Check containment relations
                    if (dam_name_input_simple in geocoded_name_input_simple) == True and (dam_name_input_simple != geocoded_name_input_simple) == True: #ICOLD contained by Google
                        if geocoded_name_input_simple.find(dam_name_input_simple) == 0: #'manhattan city': 'manhattan'
                            if geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)+len(dam_name_input_simple)] == ' ' or \
                               geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)+len(dam_name_input_simple)] == '-':
                                damname_similarity_pass = 1
                        elif (geocoded_name_input_simple.find(dam_name_input_simple)+len(dam_name_input_simple)) == len(geocoded_name_input_simple): #'city of manhattan': 'manhattan'
                            if geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)-1] == ' ' or \
                               geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)-1] == '-':
                                damname_similarity_pass = 1
                    elif (geocoded_name_input_simple in dam_name_input_simple) == True and (dam_name_input_simple != geocoded_name_input_simple) == True: #ICOLD containing Google
                        if dam_name_input_simple.find(geocoded_name_input_simple) == 0: #'manhattan city': 'manhattan'
                            if dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)+len(geocoded_name_input_simple)] == ' ' or \
                               dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)+len(geocoded_name_input_simple)] == '-':
                                damname_similarity_pass = 1
                        elif (dam_name_input_simple.find(geocoded_name_input_simple)+len(geocoded_name_input_simple)) == len(dam_name_input_simple): #'city of manhattan': 'manhattan'
                            if dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)-1] == ' ' or \
                               dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)-1] == '-':
                                damname_similarity_pass = 1
                if damname_similarity_pass != 1:
                    for icold_split in icold_spelling_splits:
                        for google_split in google_spelling_splits:
                            # Further eliminate possibly ancillary information from the name.
                            if len(google_split)>3 and len(icold_split)>3 and \
                               google_split != 'main' and icold_split != 'main' and \
                               google_split != 'tank' and icold_split != 'tank' and \
                               google_split != 'dyke' and icold_split != 'dyke' and google_split != 'canal' and icold_split != 'canal' and \
                               google_split != 'canyon' and icold_split != 'canyon' and google_split != 'diversion' and icold_split != 'diversion' and \
                               google_split != 'city' and icold_split != 'city' and google_split != 'town' and icold_split != 'town' and \
                               google_split != 'fall' and icold_split != 'fall' and google_split != 'falls' and icold_split != 'falls' and \
                               google_split != 'west' and icold_split != 'west' and google_split != 'east' and icold_split != 'east' and \
                               google_split != 'south' and icold_split != 'south' and google_split != 'norht' and icold_split != 'north' and \
                               google_split != 'storage' and icold_split != 'storage' and google_split != 'river' and icold_split != 'river' and \
                               google_split != 'saint' and icold_split != 'saint' and google_split != 'kloof' and icold_split != 'kloof' and \
                               google_split != 'berg' and icold_split != 'berg' and google_split != 'santa' and icold_split != 'santa' and \
                               google_split != 'valley' and icold_split != 'valley' and google_split != 'upper' and icold_split != 'upper' and \
                               google_split != 'lower' and icold_split != 'lower' and google_split != 'creek' and icold_split != 'creek' and \
                               google_split != 'lake' and icold_split != 'lake' and google_split != 'reservoir' and icold_split != 'reservoir' and \
                               google_split != 'lock' and icold_split != 'lock' and google_split != 'barrage' and icold_split != 'barrage' and \
                               google_split != 'lago' and icold_split != 'lago' and google_split != 'shuiku' and icold_split != 'shuiku' and \
                               google_split != 'presa' and icold_split != 'presa' and google_split != 'embalse' and icold_split != 'embalse' and \
                               google_split != 'barragem' and icold_split != 'barragem' and google_split != 'agua' and icold_split != 'agua' and \
                               google_split != 'stuwal' and icold_split != 'stuwal' and google_split != 'weir' and icold_split != 'weir' and \
                               google_split != 'dike' and icold_split != 'dike' and google_split != 'levee' and icold_split != 'levee' and \
                               google_split != 'mountain' and icold_split != 'mountain' and google_split != 'hill' and icold_split != 'hill' and \
                               google_split != 'auxiliar' and icold_split != 'auxiliar' and google_split != 'auxiliary' and icold_split != 'auxiliary' and \
                               google_split != 'riacho' and icold_split != 'riacho' and google_split != 'ribeirao' and icold_split != 'ribeirao' and \
                               google_split != 'ribeiro' and icold_split != 'ribeiro' and google_split != 'ribeira' and icold_split != 'ribeira' and \
                               google_split != 'riviere' and icold_split != 'riviere':
                                if similar(icold_split, google_split) >= similarity_t:
                                    damname_similarity_pass_alt = 1
                                    break
                        if damname_similarity_pass_alt ==1:
                            break
    if damname_similarity_pass == 1:
        damname_similarity_final_pass = 1
    elif damname_similarity_pass_alt == 1:
        damname_similarity_final_pass = 0.5
    return damname_similarity_final_pass


def river_similar(similarity_t, ICOLD_river, registry_river):
    # Discard some of the ancillary titles in a river name. These titles are not considered as an essential part of the river names.
    to_be_removed = [' river ', ' creek ', ' stream ', ' rio ', ' brook ', ' run ', ' bay ', ' branch ', ' slough ', ' lake ', ' pond ', ' canyon ', ' canal ', ' dike ', ' dyke ', \
                     ' gulch ', ' tributary ', ' drain ', ' draw ', ' channel ', ' arroyo ', ' ditch ', ' offstream ', ' riv. ', ' bayou ', ' coulee ', ' fork ', \
                     ' riacho ', ' ribeirao ', ' ribeiro ', ' ribeira ', ' riviere ', \
                     ' river ', ' creek ', ' stream ', ' rio ', ' brook ', ' run ', ' bay ', ' branch ', ' slough ', ' lake ', ' pond ', ' canyon ', ' canal ', ' dike ', ' dyke ', \
                     ' gulch ', ' tributary ', ' drain ', ' draw ', ' channel ', ' arroyo ', ' ditch ', ' offstream ', ' riv. ', ' bayou ', ' coulee ', ' fork ', \
                     ' riacho ', ' ribeirao ', ' ribeiro ', ' ribeira ', ' riviere ', \
                     ' river ', ' creek ', ' stream ', ' rio ', ' brook ', ' run ', ' bay ', ' branch ', ' slough ', ' lake ', ' pond ', ' canyon ', ' canal ', ' dike ', ' dyke ', \
                     ' gulch ', ' tributary ', ' drain ', ' draw ', ' channel ', ' arroyo ', ' ditch ', ' offstream ', ' riv. ', ' bayou ', ' coulee ', ' fork ', \
                     ' riacho ', ' ribeirao ', ' ribeiro ', ' ribeira ', ' riviere '] # Repeat them for a thorough removal.         
    river_similarity_final_pass = 0
    river_similarity_pass = 0
    river_similarity_pass_alt = 0
    if ICOLD_river == '-999' or registry_river == '-999' or ICOLD_river == '' or registry_river == '' or \
       ICOLD_river == None or registry_river == None or ICOLD_river == '/' or registry_river == '/'  or \
       ICOLD_river == '-' or registry_river == '-' or ICOLD_river == '..' or registry_river == '..' or \
       ICOLD_river == '_' or registry_river == '_' or registry_river == 'sem denominação':
        river_similarity_pass = 0
    elif (len(ICOLD_river)>=7 and (ICOLD_river[0:7]=='unknown' or ICOLD_river[0:7]=='unnamed' or ICOLD_river[0:7]=='un-name')) or \
         (len(registry_river)>=7 and (registry_river[0:7]=='unknown' or registry_river[0:7]=='unnamed' or registry_river[0:7]=='un-name')):
        river_similarity_pass = 0
    else:
        ICOLD_river_simple = remove_accents(ICOLD_river)
        registry_river_simple = remove_accents(registry_river)
        # Remove ancillary titles.
        ICOLD_river_simple = ' ' + ICOLD_river_simple + ' '
        registry_river_simple = ' ' + registry_river_simple + ' '
        for this_to_be_removed in to_be_removed:
            if this_to_be_removed in ICOLD_river_simple:
                ICOLD_river_simple = ICOLD_river_simple.replace(this_to_be_removed, ' ')
            if this_to_be_removed in registry_river_simple:
                registry_river_simple = registry_river_simple.replace(this_to_be_removed, ' ')
        ICOLD_river_simple = ICOLD_river_simple.strip()
        registry_river_simple = registry_river_simple.strip()
        # Extract Arabic numbers from both names.  
        continue_or_not = 1
        numbers_left = re.findall(r'\d+', ICOLD_river_simple)
        numbers_right = re.findall(r'\d+', registry_river_simple)
        # Split the name by delimiters.
        icold_spelling_splits = [] 
        for this_split_space in ICOLD_river_simple.split():
            for this_split_comma in this_split_space.split(','):
                for this_split_period in this_split_comma.split('.'):
                    for this_split_hypen in this_split_period.split('-'):
                        for this_split_slash in this_split_hypen.split('/'):
                            for this_split_paren1 in this_split_slash.split('('):
                                for this_split_paren2 in this_split_paren1.split(')'):
                                    if this_split_paren2 != '':
                                        icold_spelling_splits.append(this_split_paren2)
        google_spelling_splits = []
        for this_split_space in registry_river_simple.split():
            for this_split_comma in this_split_space.split(','):
                for this_split_period in this_split_comma.split('.'):
                    for this_split_hypen in this_split_period.split('-'):
                        for this_split_slash in this_split_hypen.split('/'):
                            for this_split_paren1 in this_split_slash.split('('):
                                for this_split_paren2 in this_split_paren1.split(')'):
                                    if this_split_paren2 != '':
                                        google_spelling_splits.append(this_split_paren2)
        # To reduce ambiguity, check if each of the Arabic numbers in the first name is also included in the other name.
        # The assumption is that two equivalent names cannot contain different numbers.
        # For example, "Tuttle Creek #1" is not the same dam as "Tuttle Creek #2".
        if len(numbers_left)>0 and len(numbers_right)>0:
            for this_number_left in numbers_left:
                if this_number_left not in numbers_right:
                    continue_or_not = 0
                    break
            for this_numbers_right in numbers_right:
                if this_numbers_right not in numbers_left:
                    continue_or_not = 0
                    break
        elif len(numbers_left)==0 and len(numbers_right)==0: # Also check other number formats. 
            if ((('i' in icold_spelling_splits) or ('one' in icold_spelling_splits)) and (('i' not in google_spelling_splits) and ('one' not in google_spelling_splits))) or \
               ((('ii' in icold_spelling_splits) or ('two' in icold_spelling_splits)) and (('ii' not in google_spelling_splits) and ('two' not in google_spelling_splits))) or \
               ((('iii' in icold_spelling_splits) or ('three' in icold_spelling_splits)) and (('iii' not in google_spelling_splits) and ('three' not in google_spelling_splits))) or \
               ((('iv' in icold_spelling_splits) or ('four' in icold_spelling_splits)) and (('iv' not in google_spelling_splits) and ('four' not in google_spelling_splits))) or \
               ((('v' in icold_spelling_splits) or ('five' in icold_spelling_splits)) and (('v' not in google_spelling_splits) and ('five' not in google_spelling_splits))) or \
               ((('vi' in icold_spelling_splits) or ('six' in icold_spelling_splits)) and (('vi' not in google_spelling_splits) and ('six' not in google_spelling_splits))) or \
               ((('vii' in icold_spelling_splits) or ('seven' in icold_spelling_splits)) and (('vii' not in google_spelling_splits) and ('seven' not in google_spelling_splits))) or \
               ((('viii' in icold_spelling_splits) or ('eight' in icold_spelling_splits)) and (('viii' not in google_spelling_splits) and ('eight' not in google_spelling_splits))) or \
               ((('ix' in icold_spelling_splits) or ('nine' in icold_spelling_splits)) and (('ix' not in google_spelling_splits) and ('nine' not in google_spelling_splits))) or \
               ((('x' in icold_spelling_splits) or ('ten' in icold_spelling_splits)) and (('x' not in google_spelling_splits) and ('ten' not in google_spelling_splits))) or \
               ((('xi' in icold_spelling_splits) or ('eleven' in icold_spelling_splits)) and (('xi' not in google_spelling_splits) and ('eleven' not in google_spelling_splits))) or \
               ((('xii' in icold_spelling_splits) or ('twelve' in icold_spelling_splits)) and (('xii' not in google_spelling_splits) and ('twelve' not in google_spelling_splits))) or \
               ((('xiii' in icold_spelling_splits) or ('thirteen' in icold_spelling_splits)) and (('xiii' not in google_spelling_splits) and ('thirteen' not in google_spelling_splits))) or \
               ((('xiv' in icold_spelling_splits) or ('fourteen' in icold_spelling_splits)) and (('xiv' not in google_spelling_splits) and ('fourteen' not in google_spelling_splits))) or \
               ((('xv' in icold_spelling_splits) or ('fifteen' in icold_spelling_splits)) and (('xv' not in google_spelling_splits) and ('fifteen' not in google_spelling_splits))) or \
               ((('xvi' in icold_spelling_splits) or ('sixteen' in icold_spelling_splits)) and (('xvi' not in google_spelling_splits) and ('sixteen' not in google_spelling_splits))) or \
               ((('xvii' in icold_spelling_splits) or ('seventeen' in icold_spelling_splits)) and (('xvii' not in google_spelling_splits) and ('seventeen' not in google_spelling_splits))) or \
               ((('xviii' in icold_spelling_splits) or ('eighteen' in icold_spelling_splits)) and (('xviii' not in google_spelling_splits) and ('eighteen' not in google_spelling_splits))) or \
               ((('xix' in icold_spelling_splits) or ('nineteen' in icold_spelling_splits)) and (('xix' not in google_spelling_splits) and ('nineteen' not in google_spelling_splits))) or \
               ((('xx' in icold_spelling_splits) or ('twenty' in icold_spelling_splits)) and (('xx' not in google_spelling_splits) and ('twenty' not in google_spelling_splits))) or \
               ((('i' in google_spelling_splits) or ('one' in google_spelling_splits)) and (('i' not in icold_spelling_splits) and ('one' not in icold_spelling_splits))) or \
               ((('ii' in google_spelling_splits) or ('two' in google_spelling_splits)) and (('ii' not in icold_spelling_splits) and ('two' not in icold_spelling_splits))) or \
               ((('iii' in google_spelling_splits) or ('three' in google_spelling_splits)) and (('iii' not in icold_spelling_splits) and ('three' not in icold_spelling_splits))) or \
               ((('iv' in google_spelling_splits) or ('four' in google_spelling_splits)) and (('iv' not in icold_spelling_splits) and ('four' not in icold_spelling_splits))) or \
               ((('v' in google_spelling_splits) or ('five' in google_spelling_splits)) and (('v' not in icold_spelling_splits) and ('five' not in icold_spelling_splits))) or \
               ((('vi' in google_spelling_splits) or ('six' in google_spelling_splits)) and (('vi' not in icold_spelling_splits) and ('six' not in icold_spelling_splits))) or \
               ((('vii' in google_spelling_splits) or ('seven' in google_spelling_splits)) and (('vii' not in icold_spelling_splits) and ('seven' not in icold_spelling_splits))) or \
               ((('viii' in google_spelling_splits) or ('eight' in google_spelling_splits)) and (('viii' not in icold_spelling_splits) and ('eight' not in icold_spelling_splits))) or \
               ((('ix' in google_spelling_splits) or ('nine' in google_spelling_splits)) and (('ix' not in icold_spelling_splits) and ('nine' not in icold_spelling_splits))) or \
               ((('x' in google_spelling_splits) or ('ten' in google_spelling_splits)) and (('x' not in icold_spelling_splits) and ('ten' not in icold_spelling_splits))) or \
               ((('xi' in google_spelling_splits) or ('eleven' in google_spelling_splits)) and (('xi' not in icold_spelling_splits) and ('eleven' not in icold_spelling_splits))) or \
               ((('xii' in google_spelling_splits) or ('twelve' in google_spelling_splits)) and (('xii' not in icold_spelling_splits) and ('twelve' not in icold_spelling_splits))) or \
               ((('xiii' in google_spelling_splits) or ('thirteen' in google_spelling_splits)) and (('xiii' not in icold_spelling_splits) and ('thirteen' not in icold_spelling_splits))) or \
               ((('xiv' in google_spelling_splits) or ('fourteen' in google_spelling_splits)) and (('xiv' not in icold_spelling_splits) and ('fourteen' not in icold_spelling_splits))) or \
               ((('xv' in google_spelling_splits) or ('fifteen' in google_spelling_splits)) and (('xv' not in icold_spelling_splits) and ('fifteen' not in icold_spelling_splits))) or \
               ((('xvi' in google_spelling_splits) or ('sixteen' in google_spelling_splits)) and (('xvi' not in icold_spelling_splits) and ('sixteen' not in icold_spelling_splits))) or \
               ((('xvii' in google_spelling_splits) or ('seventeen' in google_spelling_splits)) and (('xvii' not in icold_spelling_splits) and ('seventeen' not in icold_spelling_splits))) or \
               ((('xviii' in google_spelling_splits) or ('eighteen' in google_spelling_splits)) and (('xviii' not in icold_spelling_splits) and ('eighteen' not in icold_spelling_splits))) or \
               ((('xix' in google_spelling_splits) or ('nineteen' in google_spelling_splits)) and (('xix' not in icold_spelling_splits) and ('nineteen' not in icold_spelling_splits))) or \
               ((('xx' in google_spelling_splits) or ('twenty' in google_spelling_splits)) and (('xx' not in icold_spelling_splits) and ('twenty' not in icold_spelling_splits))):
                continue_or_not = 0
        elif len(numbers_left)==0 and len(numbers_right)==1:
            if ((('i' in icold_spelling_splits) or ('one' in icold_spelling_splits)) and ('1' in google_spelling_splits)) or \
               ((('ii' in icold_spelling_splits) or ('two' in icold_spelling_splits)) and ('2' in google_spelling_splits)) or \
               ((('iii' in icold_spelling_splits) or ('three' in icold_spelling_splits)) and ('3' in google_spelling_splits)) or \
               ((('iv' in icold_spelling_splits) or ('four' in icold_spelling_splits)) and ('4' in google_spelling_splits)) or \
               ((('v' in icold_spelling_splits) or ('five' in icold_spelling_splits)) and ('5' in google_spelling_splits)) or \
               ((('vi' in icold_spelling_splits) or ('six' in icold_spelling_splits)) and ('6' in google_spelling_splits)) or \
               ((('vii' in icold_spelling_splits) or ('seven' in icold_spelling_splits)) and ('7' in google_spelling_splits)) or \
               ((('viii' in icold_spelling_splits) or ('eight' in icold_spelling_splits)) and ('8' in google_spelling_splits)) or \
               ((('ix' in icold_spelling_splits) or ('nine' in icold_spelling_splits)) and ('9' in google_spelling_splits)) or \
               ((('x' in icold_spelling_splits) or ('ten' in icold_spelling_splits)) and ('10' in google_spelling_splits)) or \
               ((('xi' in icold_spelling_splits) or ('eleven' in icold_spelling_splits)) and ('11' in google_spelling_splits)) or \
               ((('xii' in icold_spelling_splits) or ('twelve' in icold_spelling_splits)) and ('12' in google_spelling_splits)) or \
               ((('xiii' in icold_spelling_splits) or ('thirteen' in icold_spelling_splits)) and ('13' in google_spelling_splits)) or \
               ((('xiv' in icold_spelling_splits) or ('fourteen' in icold_spelling_splits)) and ('14' in google_spelling_splits)) or \
               ((('xv' in icold_spelling_splits) or ('fifteen' in icold_spelling_splits)) and ('15' in google_spelling_splits)) or \
               ((('xvi' in icold_spelling_splits) or ('sixteen' in icold_spelling_splits)) and ('16' in google_spelling_splits)) or \
               ((('xvii' in icold_spelling_splits) or ('seventeen' in icold_spelling_splits)) and ('17' in google_spelling_splits)) or \
               ((('xviii' in icold_spelling_splits) or ('eighteen' in icold_spelling_splits)) and ('18' in google_spelling_splits)) or \
               ((('xix' in icold_spelling_splits) or ('nineteen' in icold_spelling_splits)) and ('19' in google_spelling_splits)) or \
               ((('xx' in icold_spelling_splits) or ('twenty' in icold_spelling_splits)) and ('20' in google_spelling_splits)):
                continue_or_not = 1
            else:
                continue_or_not = 0
        elif len(numbers_left)==1 and len(numbers_right)==0:
            if ((('i' in google_spelling_splits) or ('one' in google_spelling_splits)) and ('1' in icold_spelling_splits)) or \
               ((('ii' in google_spelling_splits) or ('two' in google_spelling_splits)) and ('2' in icold_spelling_splits)) or \
               ((('iii' in google_spelling_splits) or ('three' in google_spelling_splits)) and ('3' in icold_spelling_splits)) or \
               ((('iv' in google_spelling_splits) or ('four' in google_spelling_splits)) and ('4' in icold_spelling_splits)) or \
               ((('v' in google_spelling_splits) or ('five' in google_spelling_splits)) and ('5' in icold_spelling_splits)) or \
               ((('vi' in google_spelling_splits) or ('six' in google_spelling_splits)) and ('6' in icold_spelling_splits)) or \
               ((('vii' in google_spelling_splits) or ('seven' in google_spelling_splits)) and ('7' in icold_spelling_splits)) or \
               ((('viii' in google_spelling_splits) or ('eight' in google_spelling_splits)) and ('8' in icold_spelling_splits)) or \
               ((('ix' in google_spelling_splits) or ('nine' in google_spelling_splits)) and ('9' in icold_spelling_splits)) or \
               ((('x' in google_spelling_splits) or ('ten' in google_spelling_splits)) and ('10' in icold_spelling_splits)) or \
               ((('xi' in google_spelling_splits) or ('eleven' in google_spelling_splits)) and ('11' in icold_spelling_splits)) or \
               ((('xii' in google_spelling_splits) or ('twelve' in google_spelling_splits)) and ('12' in icold_spelling_splits)) or \
               ((('xiii' in google_spelling_splits) or ('thirteen' in google_spelling_splits)) and ('13' in icold_spelling_splits)) or \
               ((('xiv' in google_spelling_splits) or ('fourteen' in google_spelling_splits)) and ('14' in icold_spelling_splits)) or \
               ((('xv' in google_spelling_splits) or ('fifteen' in google_spelling_splits)) and ('15' in icold_spelling_splits)) or \
               ((('xvi' in google_spelling_splits) or ('sixteen' in google_spelling_splits)) and ('16' in icold_spelling_splits)) or \
               ((('xvii' in google_spelling_splits) or ('seventeen' in google_spelling_splits)) and ('17' in icold_spelling_splits)) or \
               ((('xviii' in google_spelling_splits) or ('eighteen' in google_spelling_splits)) and ('18' in icold_spelling_splits)) or \
               ((('xix' in google_spelling_splits) or ('nineteen' in google_spelling_splits)) and ('19' in icold_spelling_splits)) or \
               ((('xx' in google_spelling_splits) or ('twenty' in google_spelling_splits)) and ('20' in icold_spelling_splits)):
                continue_or_not = 1
            else:
                continue_or_not = 0
        else:
            continue_or_not = 0
        # To further reduce ambiguity, check if any of the following elements in the first name is also included in the other name.
        # The assumption is that two equivalent names cannot contain different direction adjectives or letters.
        # For example, "Tuttle Creek East" is not the same dam as "Tuttle Creek West".
        if (('east' in icold_spelling_splits) and ('east' not in google_spelling_splits)) or (('east' in google_spelling_splits) and ('east' not in icold_spelling_splits)) or \
           (('west' in icold_spelling_splits) and ('west' not in google_spelling_splits)) or (('west' in google_spelling_splits) and ('west' not in icold_spelling_splits)) or \
           (('north' in icold_spelling_splits) and ('north' not in google_spelling_splits)) or (('north' in google_spelling_splits) and ('north' not in icold_spelling_splits)) or \
           (('south' in icold_spelling_splits) and ('south' not in google_spelling_splits)) or (('south' in google_spelling_splits) and ('south' not in icold_spelling_splits)) or \
           (('upper' in icold_spelling_splits) and ('upper' not in google_spelling_splits)) or (('upper' in google_spelling_splits) and ('upper' not in icold_spelling_splits)) or \
           (('lower' in icold_spelling_splits) and ('lower' not in google_spelling_splits)) or (('lower' in google_spelling_splits) and ('lower' not in icold_spelling_splits)) or \
           (('a' in icold_spelling_splits) and ('a' not in google_spelling_splits)) or (('a' in google_spelling_splits) and ('a' not in icold_spelling_splits)) or \
           (('b' in icold_spelling_splits) and ('b' not in google_spelling_splits)) or (('b' in google_spelling_splits) and ('b' not in icold_spelling_splits)) or \
           (('c' in icold_spelling_splits) and ('c' not in google_spelling_splits)) or (('c' in google_spelling_splits) and ('c' not in icold_spelling_splits)) or \
           (('d' in icold_spelling_splits) and ('d' not in google_spelling_splits)) or (('d' in google_spelling_splits) and ('d' not in icold_spelling_splits)) or \
           (('auxiliar' in icold_spelling_splits) and ('auxiliar' not in google_spelling_splits)) or (('auxiliar' in google_spelling_splits) and ('auxiliar' not in icold_spelling_splits)) or \
           (('auxiliary' in icold_spelling_splits) and ('auxiliary' not in google_spelling_splits)) or (('auxiliary' in google_spelling_splits) and ('auxiliary' not in icold_spelling_splits)):
            continue_or_not = 0
        # Continue the comparison if none of the situations above happens.
        similarity_value = similar(ICOLD_river_simple, registry_river_simple)
        if similarity_value >= similarity_t and continue_or_not==1:
            river_similarity_pass = 1
        if river_similarity_pass != 1 and (ICOLD_river_simple != '' and registry_river_simple != '') and continue_or_not==1:
            # Check containment relations
            if (ICOLD_river_simple in registry_river_simple) == True and (ICOLD_river_simple != registry_river_simple) == True: #ICOLD contained by Google
                if registry_river_simple.find(ICOLD_river_simple) == 0: #'manhattan city': 'manhattan'
                    if registry_river_simple[registry_river_simple.find(ICOLD_river_simple)+len(ICOLD_river_simple)] == ' ' or \
                       registry_river_simple[registry_river_simple.find(ICOLD_river_simple)+len(ICOLD_river_simple)] == '-':
                        river_similarity_pass = 1
                elif (registry_river_simple.find(ICOLD_river_simple)+len(ICOLD_river_simple)) == len(registry_river_simple): #'city of manhattan': 'manhattan'
                    if registry_river_simple[registry_river_simple.find(ICOLD_river_simple)-1] == ' ' or \
                       registry_river_simple[registry_river_simple.find(ICOLD_river_simple)-1] == '-':
                        river_similarity_pass = 1
            elif (registry_river_simple in ICOLD_river_simple) == True and (ICOLD_river_simple != registry_river_simple) == True: #ICOLD containing Google
                if ICOLD_river_simple.find(registry_river_simple) == 0: #'manhattan city': 'manhattan'
                    if ICOLD_river_simple[ICOLD_river_simple.find(registry_river_simple)+len(registry_river_simple)] == ' ' or \
                       ICOLD_river_simple[ICOLD_river_simple.find(registry_river_simple)+len(registry_river_simple)] == '-':
                        river_similarity_pass = 1
                elif (ICOLD_river_simple.find(registry_river_simple)+len(registry_river_simple)) == len(ICOLD_river_simple): #'city of manhattan': 'manhattan'
                    if ICOLD_river_simple[ICOLD_river_simple.find(registry_river_simple)-1] == ' ' or \
                       ICOLD_river_simple[ICOLD_river_simple.find(registry_river_simple)-1] == '-':
                        river_similarity_pass = 1
        if river_similarity_pass != 1 and (ICOLD_river_simple != '' and registry_river_simple != '') and continue_or_not==1:
            for icold_split in icold_spelling_splits:
                for google_split in google_spelling_splits:
                    # Further eliminate possibly ancillary information from the name.
                    if len(google_split)>3 and len(icold_split)>3 and \
                       google_split != 'main' and icold_split != 'main' and \
                       google_split != 'tank' and icold_split != 'tank' and \
                       google_split != 'diversion' and icold_split != 'diversion' and \
                       google_split != 'dike' and icold_split != 'dike' and \
                       google_split != 'dyke' and icold_split != 'dyke' and google_split != 'canal' and icold_split != 'canal' and \
                       google_split != 'city' and icold_split != 'city' and google_split != 'town' and icold_split != 'town' and \
                       google_split != 'fall' and icold_split != 'fall' and google_split != 'falls' and icold_split != 'falls' and \
                       google_split != 'west' and icold_split != 'west' and google_split != 'east' and icold_split != 'east' and \
                       google_split != 'south' and icold_split != 'south' and google_split != 'norht' and icold_split != 'north' and \
                       google_split != 'saint' and icold_split != 'saint' and google_split != 'kloof' and icold_split != 'kloof' and \
                       google_split != 'berg' and icold_split != 'berg' and google_split != 'santa' and icold_split != 'santa' and \
                       google_split != 'valley' and icold_split != 'valley' and google_split != 'upper' and icold_split != 'upper' and \
                       google_split != 'lower' and icold_split != 'lower' and google_split != 'river' and icold_split != 'river' and \
                       google_split != 'creek' and icold_split != 'creek' and google_split != 'stream' and icold_split != 'stream' and \
                       google_split != 'brook' and icold_split != 'brook' and google_split != 'branch' and icold_split != 'branch' and \
                       google_split != 'slough' and icold_split != 'slough' and google_split != 'lake' and icold_split != 'lake' and \
                       google_split != 'pond' and icold_split != 'pond' and google_split != 'canyon' and icold_split != 'canyon' and \
                       google_split != 'gulch' and icold_split != 'gulch' and google_split != 'tributary' and icold_split != 'tributary' and \
                       google_split != 'drain' and icold_split != 'drain' and google_split != 'draw' and icold_split != 'draw' and \
                       google_split != 'channel' and icold_split != 'channel' and google_split != 'arroyo' and icold_split != 'arroyo' and \
                       google_split != 'ditch' and icold_split != 'ditch' and google_split != 'offstream' and icold_split != 'offstream' and \
                       google_split != 'bayou' and icold_split != 'bayou' and google_split != 'coulee' and icold_split != 'coulee' and \
                       google_split != 'fork' and icold_split != 'fork' and google_split != 'mountain' and icold_split != 'mountain' and \
                       google_split != 'hill' and icold_split != 'hill' and google_split != 'auxiliar' and icold_split != 'auxiliar' and \
                       google_split != 'auxiliary' and icold_split != 'auxiliary' and \
                       google_split != 'riacho' and icold_split != 'riacho' and google_split != 'ribeirao' and icold_split != 'ribeirao' and \
                       google_split != 'ribeiro' and icold_split != 'ribeiro' and google_split != 'ribeira' and icold_split != 'ribeira' and \
                       google_split != 'riviere' and icold_split != 'riviere':
                        if similar(icold_split, google_split) >= similarity_t:
                            river_similarity_pass_alt = 1
                            break
                if river_similarity_pass_alt==1:
                    break
    if river_similarity_pass == 1:
        river_similarity_final_pass = 1
    elif river_similarity_pass_alt == 1:
        river_similarity_final_pass = 0.5
    return river_similarity_final_pass       


def similar_v2(a, b):
    return SequenceMatcher(None, a, b).ratio()

 
# See comments in <damname_similar>
def damname_similar_v2(similarity_t, dam_name_input, other_dam_name_input, reservoir_name_input, geocoded_name_input, this_country_ISO_input):
    to_be_removed = [' lake ', ' dam ', ' reservoir ', ' barrage ', ' lago ', ' shuiku ', ' lac ', ' presa ', ' embalse ', \
                     ' lake ', ' dam ', ' reservoir ', ' barrage ', ' lago ', ' shuiku ', ' lac ', ' presa ', ' embalse ', \
                     ' lake ', ' dam ', ' reservoir ', ' barrage ', ' lago ', ' shuiku ', ' lac ', ' presa ', ' embalse ']
    damname_similarity_pass = 0
    if dam_name_input == '' or geocoded_name_input == '':
        damname_similarity_pass = 0
    elif geocoded_name_input == 'not found':
        damname_similarity_pass = -1
    else:
        dam_name_input_simple = remove_accents(dam_name_input)
        geocoded_name_input_simple = remove_accents(geocoded_name_input)
        dam_name_input_simple = ' ' + dam_name_input_simple + ' '
        geocoded_name_input_simple = ' ' + geocoded_name_input_simple + ' '
        for this_to_be_removed in to_be_removed:
            if this_to_be_removed in dam_name_input_simple:
                dam_name_input_simple = dam_name_input_simple.replace(this_to_be_removed, ' ')
            if this_to_be_removed in geocoded_name_input_simple:
                geocoded_name_input_simple = geocoded_name_input_simple.replace(this_to_be_removed, ' ')
        dam_name_input_simple = dam_name_input_simple.strip()
        geocoded_name_input_simple = geocoded_name_input_simple.strip()
        if this_country_ISO_input == 'cn':
            if len(dam_name_input_simple) > 8 and dam_name_input_simple[-6:] == 'shuiku':
                dam_name_input_simple = (dam_name_input_simple[0:(len(dam_name_input_simple)-6)]).lower().strip()
            if len(geocoded_name_input_simple) > 8 and geocoded_name_input_simple[-6:] == 'shuiku':
                geocoded_name_input_simple = (geocoded_name_input_simple[0:(len(geocoded_name_input_simple)-6)]).lower().strip()
        similarity_value = similar_v2(dam_name_input_simple, geocoded_name_input_simple)
        if similarity_value >= similarity_t:
            damname_similarity_pass = 1
        if damname_similarity_pass != 1:
            if (dam_name_input_simple in geocoded_name_input_simple) == True and (dam_name_input_simple != geocoded_name_input_simple) == True: #ICOLD contained by Google
                if geocoded_name_input_simple.find(dam_name_input_simple) == 0: #'manhattan city': 'manhattan'
                    if geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)+len(dam_name_input_simple)] == ' ' or \
                       geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)+len(dam_name_input_simple)] == '-':
                        damname_similarity_pass = 1
                elif (geocoded_name_input_simple.find(dam_name_input_simple)+len(dam_name_input_simple)) == len(geocoded_name_input_simple): #'city of manhattan': 'manhattan'
                    if geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)-1] == ' ' or \
                       geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)-1] == '-':
                        damname_similarity_pass = 1
            elif (geocoded_name_input_simple in dam_name_input_simple) == True and (dam_name_input_simple != geocoded_name_input_simple) == True: #ICOLD containing Google
                if dam_name_input_simple.find(geocoded_name_input_simple) == 0: #'manhattan city': 'manhattan'
                    if dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)+len(geocoded_name_input_simple)] == ' ' or \
                       dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)+len(geocoded_name_input_simple)] == '-':
                        damname_similarity_pass = 1
                elif (dam_name_input_simple.find(geocoded_name_input_simple)+len(geocoded_name_input_simple)) == len(dam_name_input_simple): #'city of manhattan': 'manhattan'
                    if dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)-1] == ' ' or \
                       dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)-1] == '-':
                        damname_similarity_pass = 1
        if damname_similarity_pass != 1:
            icold_spelling_splits = [] 
            for this_split_space in dam_name_input_simple.split(): # Ignore multiple space automatically
                for this_split_comma in this_split_space.split(','):
                    for this_split_period in this_split_comma.split('.'):
                        for this_split_hypen in this_split_period.split('-'):
                            for this_split_slash in this_split_hypen.split('/'):
                                if this_split_slash != '':
                                    icold_spelling_splits.append(this_split_slash)
            google_spelling_splits = []
            for this_split_space in geocoded_name_input_simple.split(): # Ignore multiple space automatically
                for this_split_comma in this_split_space.split(','):
                    for this_split_period in this_split_comma.split('.'):
                        for this_split_hypen in this_split_period.split('-'):
                            for this_split_slash in this_split_hypen.split('/'):
                                if this_split_slash != '':
                                    google_spelling_splits.append(this_split_slash)
            for icold_split in icold_spelling_splits:
                for google_split in google_spelling_splits:
                    if len(google_split)>3 and len(icold_split)>3 and \
                        google_split != 'west' and icold_split != 'west' and google_split != 'east' and icold_split != 'east' and \
                        google_split != 'south' and icold_split != 'south' and google_split != 'norht' and icold_split != 'north' and \
                        google_split != 'storage' and icold_split != 'storage':
                        if similar_v2(icold_split, google_split) >= similarity_t:
                            damname_similarity_pass = 1
                            break
                if damname_similarity_pass == 1:
                    break
    if damname_similarity_pass != 1:
        if other_dam_name_input == '' or geocoded_name_input == '':
            damname_similarity_pass = 0
        elif geocoded_name_input == 'not found':
            damname_similarity_pass = -1
        else:
            dam_name_input_simple = remove_accents(other_dam_name_input)
            dam_name_input_simple = ' ' + dam_name_input_simple + ' '
            for this_to_be_removed in to_be_removed:
                if this_to_be_removed in dam_name_input_simple:
                    dam_name_input_simple = dam_name_input_simple.replace(this_to_be_removed, ' ')
            dam_name_input_simple = dam_name_input_simple.strip()
            if this_country_ISO_input == 'cn':
                if len(dam_name_input_simple) > 8 and dam_name_input_simple[-6:] == 'shuiku':
                    dam_name_input_simple = (dam_name_input_simple[0:(len(dam_name_input_simple)-6)]).lower().strip()
            similarity_value = similar_v2(dam_name_input_simple, geocoded_name_input_simple)
            if similarity_value >= similarity_t:
                damname_similarity_pass = 1
            if damname_similarity_pass != 1:
                if (dam_name_input_simple in geocoded_name_input_simple) == True and (dam_name_input_simple != geocoded_name_input_simple) == True: #ICOLD contained by Google
                    if geocoded_name_input_simple.find(dam_name_input_simple) == 0: #'manhattan city': 'manhattan'
                        if geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)+len(dam_name_input_simple)] == ' ' or \
                           geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)+len(dam_name_input_simple)] == '-':
                            damname_similarity_pass = 1
                    elif (geocoded_name_input_simple.find(dam_name_input_simple)+len(dam_name_input_simple)) == len(geocoded_name_input_simple): #'city of manhattan': 'manhattan'
                        if geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)-1] == ' ' or \
                           geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)-1] == '-':
                            damname_similarity_pass = 1
                elif (geocoded_name_input_simple in dam_name_input_simple) == True and (dam_name_input_simple != geocoded_name_input_simple) == True: #ICOLD containing Google
                    if dam_name_input_simple.find(geocoded_name_input_simple) == 0: #'manhattan city': 'manhattan'
                        if dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)+len(geocoded_name_input_simple)] == ' ' or \
                           dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)+len(geocoded_name_input_simple)] == '-':
                            damname_similarity_pass = 1
                    elif (dam_name_input_simple.find(geocoded_name_input_simple)+len(geocoded_name_input_simple)) == len(dam_name_input_simple): #'city of manhattan': 'manhattan'
                        if dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)-1] == ' ' or \
                           dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)-1] == '-':
                            damname_similarity_pass = 1
            if damname_similarity_pass != 1:
                icold_spelling_splits = [] 
                for this_split_space in dam_name_input_simple.split():
                    for this_split_comma in this_split_space.split(','):
                        for this_split_period in this_split_comma.split('.'):
                            for this_split_hypen in this_split_period.split('-'):
                                for this_split_slash in this_split_hypen.split('/'):
                                    if this_split_slash != '':
                                        icold_spelling_splits.append(this_split_slash)
                google_spelling_splits = []
                for this_split_space in geocoded_name_input_simple.split():
                    for this_split_comma in this_split_space.split(','):
                        for this_split_period in this_split_comma.split('.'):
                            for this_split_hypen in this_split_period.split('-'):
                                for this_split_slash in this_split_hypen.split('/'):
                                    if this_split_slash != '':
                                        google_spelling_splits.append(this_split_slash)
                for icold_split in icold_spelling_splits:
                    for google_split in google_spelling_splits:
                        if len(google_split)>3 and len(icold_split)>3 and \
                            google_split != 'west' and icold_split != 'west' and google_split != 'east' and icold_split != 'east' and \
                            google_split != 'south' and icold_split != 'south' and google_split != 'norht' and icold_split != 'north' and \
                            google_split != 'storage' and icold_split != 'storage':
                            if similar_v2(icold_split, google_split) >= similarity_t:
                                damname_similarity_pass = 1
                                break
                    if damname_similarity_pass == 1:
                        break
    if damname_similarity_pass != 1:
        if reservoir_name_input == '' or geocoded_name_input == '':
            damname_similarity_pass = 0
        elif geocoded_name_input == 'not found':
            damname_similarity_pass = -1
        else:
            dam_name_input_simple = remove_accents(reservoir_name_input)
            dam_name_input_simple = ' ' + dam_name_input_simple + ' '
            for this_to_be_removed in to_be_removed:
                if this_to_be_removed in dam_name_input_simple:
                    dam_name_input_simple = dam_name_input_simple.replace(this_to_be_removed, ' ')
            dam_name_input_simple = dam_name_input_simple.strip()          
            if this_country_ISO_input == 'cn':
                if len(dam_name_input_simple) > 8 and dam_name_input_simple[-6:] == 'shuiku':
                    dam_name_input_simple = (dam_name_input_simple[0:(len(dam_name_input_simple)-6)]).lower().strip()
            similarity_value = similar_v2(dam_name_input_simple, geocoded_name_input_simple)
            if similarity_value >= similarity_t:
                damname_similarity_pass = 1
            if damname_similarity_pass != 1:
                # Check containment relations
                if (dam_name_input_simple in geocoded_name_input_simple) == True and (dam_name_input_simple != geocoded_name_input_simple) == True: #ICOLD contained by Google
                    if geocoded_name_input_simple.find(dam_name_input_simple) == 0: #'manhattan city': 'manhattan'
                        if geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)+len(dam_name_input_simple)] == ' ' or \
                           geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)+len(dam_name_input_simple)] == '-':
                            damname_similarity_pass = 1
                    elif (geocoded_name_input_simple.find(dam_name_input_simple)+len(dam_name_input_simple)) == len(geocoded_name_input_simple): #'city of manhattan': 'manhattan'
                        if geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)-1] == ' ' or \
                           geocoded_name_input_simple[geocoded_name_input_simple.find(dam_name_input_simple)-1] == '-':
                            damname_similarity_pass = 1
                elif (geocoded_name_input_simple in dam_name_input_simple) == True and (dam_name_input_simple != geocoded_name_input_simple) == True: #ICOLD containing Google
                    if dam_name_input_simple.find(geocoded_name_input_simple) == 0: #'manhattan city': 'manhattan'
                        if dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)+len(geocoded_name_input_simple)] == ' ' or \
                           dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)+len(geocoded_name_input_simple)] == '-':
                            damname_similarity_pass = 1
                    elif (dam_name_input_simple.find(geocoded_name_input_simple)+len(geocoded_name_input_simple)) == len(dam_name_input_simple): #'city of manhattan': 'manhattan'
                        if dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)-1] == ' ' or \
                           dam_name_input_simple[dam_name_input_simple.find(geocoded_name_input_simple)-1] == '-':
                            damname_similarity_pass = 1
            if damname_similarity_pass != 1:
                icold_spelling_splits = [] 
                for this_split_space in dam_name_input_simple.split():
                    for this_split_comma in this_split_space.split(','):
                        for this_split_period in this_split_comma.split('.'):
                            for this_split_hypen in this_split_period.split('-'):
                                for this_split_slash in this_split_hypen.split('/'):
                                    if this_split_slash != '':
                                        icold_spelling_splits.append(this_split_slash)
                google_spelling_splits = []
                for this_split_space in geocoded_name_input_simple.split():
                    for this_split_comma in this_split_space.split(','):
                        for this_split_period in this_split_comma.split('.'):
                            for this_split_hypen in this_split_period.split('-'):
                                for this_split_slash in this_split_hypen.split('/'):
                                    if this_split_slash != '':
                                        google_spelling_splits.append(this_split_slash)
                for icold_split in icold_spelling_splits:
                    for google_split in google_spelling_splits:
                        if len(google_split)>3 and len(icold_split)>3 and \
                            google_split != 'west' and icold_split != 'west' and google_split != 'east' and icold_split != 'east' and \
                            google_split != 'south' and icold_split != 'south' and google_split != 'norht' and icold_split != 'north' and \
                            google_split != 'storage' and icold_split != 'storage':
                            if similar_v2(icold_split, google_split) >= similarity_t:
                                damname_similarity_pass = 1
                                break
                    if damname_similarity_pass == 1:
                        break
    return damname_similarity_pass
