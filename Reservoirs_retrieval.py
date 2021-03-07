# [Description] ------------------------------
# Module name "Reservoir_retrieval.py"
# This module loops through the dam points to retrieve their associated reservoir polygons from a given
# water mask (such as HydroLAKES).The retrieval process involves two consecutive rounds, with the first
# using a 500-m spatial tolerance and the second using a 1-km tolerance. Each round consists of another
# three iterations to progressively optimize reservoir-dam association. The output is one-to-one
# relationship (one dam point associated with one reservoir polygon). Although the goal is to retrieve
# reservoirs as thoroughly as possible, there is no guarantee that reservoirs for all dam points can be
# assigned. Detailed methods are described in Wang et al. (2021).

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
# 1. work_dir: full path of the workspace or geodatabase
work_dir = r"...\workspace"

# 2. Dams: dam point feature class (such as GeoDAR_v11_dams)
Dams = "GeoDAR_v11_dams"

# 3. Water_mask: water polygon feature class (such as HydroLAKES)
# Since the following reservoir retrieval algorithm involves polygon area comparison, Water_mask must be
# first projected into an equal-area projection.
Water_mask = "HydroLAKES_nonGRanD_prj" 

# Output
# 1. matched_lakes: lake polygons (as in Water_mask) that are paired/matched with dams points (as in Dams).
matched_lakes = 'HydroLAKES_nonGRanD_GeoDARmatched'
# 2. notmatched_dams: the remaining dam points in Dams that are left unpaired with lake/reservoir polygons. 
notmatched_dams = 'GeoICOLDr1_v11_nonGRanDHydro'
#---------------------------------------------



# [Script] -----------------------------------
# Import built-in functions and tools.
import arcpy, numpy, os
from arcpy import env
from numpy import ndarray
from datetime import datetime

print("----- Module Started -----")
print(datetime.datetime.now())

# Define environment settings.
env.workspace = work_dir
env.overwriteOutput = "TRUE"

# Define intermediate files (which will be deleted later).
Lakes = 'lakes_in500m' # Water features within 500 m from the dam points
Lakes2 = 'lakes_in1000m' # Water features within 1000m from the dam points
Lakes_others = 'other_lakes_in1000m' # Water features that have not been paired with any dams after Round 1 (see below)
Dams_others = 'other_dams' # Dam points that have not been paired with any reservoirs after Round 1 (see below)
joined_table = "NearTab_in500m" # Near table listing dam-lake pairs within 500-m spatial tolerance
joined_table_others = "NearTab_in1000m" # Near table listing dam-lake pairs (using Lakes_others and Dams_others) within 1-km tolerance

# Make feature layers
arcpy.MakeFeatureLayer_management(Water_mask, 'all_lakes_lyr')
arcpy.MakeFeatureLayer_management(Dams, 'dams_lyr')

# Extract lakes from the water mask that are within 500 m of the dam points
arcpy.SelectLayerByLocation_management('all_lakes_lyr', 'WITHIN_A_DISTANCE_GEODESIC', 'dams_lyr', '500 Meters')
arcpy.CopyFeatures_management('all_lakes_lyr', Lakes)
arcpy.SelectLayerByAttribute_management("all_lakes_lyr", "CLEAR_SELECTION")
# Extract lakes from the water mask that are within 1000 m of the dam points
arcpy.SelectLayerByLocation_management('all_lakes_lyr', 'WITHIN_A_DISTANCE_GEODESIC', 'dams_lyr', '1000 Meters')
arcpy.CopyFeatures_management('all_lakes_lyr', Lakes2)
arcpy.SelectLayerByAttribute_management("all_lakes_lyr", "CLEAR_SELECTION")
print 'Initial lake selection done.'

# Add fields to Lakes2. The added fields will be later used to store information of the paired dams. 
fieldList = arcpy.ListFields(Lakes2)    
fieldName = [f.name for f in fieldList]
if ('Dam_officialID' in fieldName) == False:
    arcpy.AddField_management(Lakes2, 'Dam_officialID', "LONG")
if ('Dam_dist' in fieldName) == False:
    arcpy.AddField_management(Lakes2, 'Dam_dist', "DOUBLE") 
if ('MultiDams' in fieldName) == False:
    arcpy.AddField_management(Lakes2, 'MultiDams', "SHORT")

# Set required parameters for generate near table tool
location = 'NO_LOCATION'
angle = 'NO_ANGLE'
closest = 'ALL'
closest_count = 5
method = 'GEODESIC'

#===========================================================
# ROUND 1: Using a spatial tolerance/buffer of 500 m (Lakes)
print 'Round 1: Using a spatial tolerance of 500 m ...'
# Generate near table (find closest lakes for each dam). 
arcpy.GenerateNearTable_analysis(Dams, Lakes, joined_table, '500 Meters', location, angle, closest, closest_count, method)

# Join lake area information to joined_table
arcpy.JoinField_management (joined_table, "NEAR_FID", Lakes, "OBJECTID", ["Shape_Area"])

# Loop through the joined table to acquire attributes
joined_table_records = arcpy.SearchCursor(joined_table)
IN_FID = [] # Dam FIDs found in the generate near table
NEAR_FID = [] # FIDs of all lakes within 1km of each dam in the generate near table
NEAR_DIST = [] # distance of lakes to dam
NEAR_RANK = [] # the ranking of the lake in distance to dam
NEAR_FID_AREA = [] #lake area
# Append values for each record in the table to the empty array defined above
for joined_table_record in joined_table_records:
    IN_FID.append(joined_table_record.IN_FID) 
    NEAR_FID.append(joined_table_record.NEAR_FID)  
    NEAR_DIST.append(joined_table_record.NEAR_DIST) 
    NEAR_RANK.append(joined_table_record.NEAR_RANK) 
    NEAR_FID_AREA.append(joined_table_record.SHAPE_AREA) 
del joined_table_record
del joined_table_records

# 1st iteration: loop through all dam FIDs with a lake within the buffer distance and select the biggest lake
print '1st iteration in process ...'
Dam_FIDs = arcpy.SearchCursor(Dams)
valid_DAM_FIDs = [] # FIDs of the dams that have at least one lake within the spatial tolerance
valid_DAM_BIGGEST_LAKE_FIDs = [] # FID of the largest lake associated with each valid dam (above)
distance_array = [] # Distance from each valid dam to its largest lake
dam_object_IDs = [] # Dam FIDs 
dam_official_IDs = [] # Dam IDs (previously added attribute that represents unique features)
for Dam_FID in Dam_FIDs:
    dam_object_IDs.append(Dam_FID.OBJECTID)
    dam_official_IDs.append(Dam_FID.dam_ID)
    this_DAM_FID = Dam_FID.OBJECTID # Modify this field based on whether "Dams" is shapefile or feature class

    # Check if this_DAM_FID is in IN_FID and extracts all indices of this_DAM_FID from the near table.
    all_records_for_this_DAM = [i for i, x in enumerate(IN_FID) if x == this_DAM_FID]
    # all_records_for_this_DAM returns the index location(s) from the joined table where IN_FID equals this_DAM_FID
    
    if len(all_records_for_this_DAM) > 0: # Indicating this dam has at least one lake within the spatial tolerance
        # Retrieve lake information associated with this_DAM_FID
        all_lakes_FID_for_this_dam = [x[1] for x in enumerate(NEAR_FID) if x[0] in all_records_for_this_DAM]
        all_lakes_area_for_this_dam = [x[1] for x in enumerate(NEAR_FID_AREA) if x[0] in all_records_for_this_DAM]
        all_lakes_distance_for_this_dam = [x[1] for x in enumerate(NEAR_DIST) if x[0] in all_records_for_this_DAM]
        
        # Select the biggest lake
        this_local_index = all_lakes_area_for_this_dam.index(max(all_lakes_area_for_this_dam))
        this_DAM_BIGGEST_LAKE_FID = all_lakes_FID_for_this_dam[this_local_index]
        this_DAM_distance = all_lakes_distance_for_this_dam[this_local_index]

        # Generate dam and lake FID pairs (both are FIDs)
        valid_DAM_FIDs.append(this_DAM_FID)
        valid_DAM_BIGGEST_LAKE_FIDs.append(this_DAM_BIGGEST_LAKE_FID)
        distance_array.append(this_DAM_distance)
del Dam_FID
del Dam_FIDs
print '1st iteration done: at ' + str(datetime.now())

# 2nd interation: loops through valid_DAM_FIDs and detect lakes associated with multiple dams. And if this happens,
# re-assign valid_DAM_FID to its closest lake
print '2nd iteration in process ...'
j = 0
for valid_DAM_FID in valid_DAM_FIDs:
    # Retrieve the lake associated with this valid DAM FID.
    this_dam_associated_lake_FID = valid_DAM_BIGGEST_LAKE_FIDs[j]
    # Check if this_dam_associated_lake_FID exists for some other dams or not
    this_dam_associated_lake_FID_indices = [i for i, x in enumerate(valid_DAM_BIGGEST_LAKE_FIDs) if x == this_dam_associated_lake_FID]
    if len(this_dam_associated_lake_FID_indices) > 1: # Indicating that this dam has an associated lake that appears more than once 
        # Query indices where this particular dam exists in the joined near table 
        all_records_for_this_DAM = [i for i, x in enumerate(IN_FID) if x == valid_DAM_FID]      
        # Retrieve lake information of this dam in the joined near table
        all_lakes_FID_for_this_dam = [x[1] for x in enumerate(NEAR_FID) if x[0] in all_records_for_this_DAM]
        all_lakes_distrank_for_this_dam = [x[1] for x in enumerate(NEAR_RANK) if x[0] in all_records_for_this_DAM]
        all_lakes_distance_for_this_dam = [x[1] for x in enumerate(NEAR_DIST) if x[0] in all_records_for_this_DAM]
        
        # Select the closest lake
        this_local_index = all_lakes_distrank_for_this_dam.index(min(all_lakes_distrank_for_this_dam))
        this_DAM_BIGGEST_LAKE_FID = all_lakes_FID_for_this_dam[this_local_index] # Note that this lake may not be the biggest one for this dam any more
        this_DAM_distance = all_lakes_distance_for_this_dam[this_local_index]
        
        # Generate dam and lake FID pairs (both are FIDs)
        valid_DAM_BIGGEST_LAKE_FIDs[j] = this_DAM_BIGGEST_LAKE_FID # Note that this lake may not be the biggest one for this dam any more despite this variable name
        distance_array[j] = this_DAM_distance
    j = j+1
# The 2nd iteration thus far may not eliminate ambiguous lakes. The closest lake can also be the largest lake.
# This is why we include a another of iteration below. 
# Select the closest dam that is located near a lake that shares multiple dams
lake_records = arcpy.SearchCursor(Lakes)
Lake_FIDs = [] # Lake FIDs
Lake_officialID = [] # Lake IDs (previously added attribute that represents unique features) 
DAM_FID_FOR_this_LAKE = []  # FID of the dam that is closest to this lake
DIST_to_its_dam = [] # Distance from this lake to its closest dam
MultiDams = [] # Array with binary values (1 or 0) indicating if this lake has multiple dams (1) or a unique done (0). 
Dammed_lakes = [] # FIDs of the lakes that have been paired with a dam ("-1" indicates otherwise). 
for lake_record in lake_records:
    this_lake_FID = lake_record.OBJECTID
    Lake_FIDs.append(this_lake_FID)
    Lake_officialID.append(lake_record.Hylak_id) # This attribute needs to be changed according to the input water mask dataset.
    # Query indices where this particular lake exists in valid_DAM_BIGGEST_LAKE_FIDs (lakes that are previously paired with dams)    
    lake_with_dam_indices = [i for i, x in enumerate(valid_DAM_BIGGEST_LAKE_FIDs) if x == this_lake_FID]

    if len(lake_with_dam_indices) == 1: # Meaning this lake was paired with only one dam.
        DAM_FID_FOR_this_LAKE.append(valid_DAM_FIDs[lake_with_dam_indices[0]])
        DIST_to_its_dam.append(distance_array[lake_with_dam_indices[0]])
        MultiDams.append(0) # This lake does not have multiple dams (only one unique dam). 
        Dammed_lakes.append(this_lake_FID) # This lake has been paired with a dam. 
    elif len(lake_with_dam_indices) > 1: # Meaning this lake was paired with multiple dams. 
        MultiDams.append(1) # This lake has multiple dams. 
        # Assign the closest dam to this lake
        thisLake_dist_to_all_its_dam = [] # Array recording the distance values from this lake to all associated dams.
        for lake_with_dam_index in lake_with_dam_indices:
            # Retrieve the distance between this dam and lake
            thisLake_dist_to_all_its_dam.append(distance_array[lake_with_dam_index])
        this_closest_dam_for_this_lake_index = thisLake_dist_to_all_its_dam.index(min(thisLake_dist_to_all_its_dam))
        DAM_FID_FOR_this_LAKE.append(valid_DAM_FIDs[lake_with_dam_indices[this_closest_dam_for_this_lake_index]])
        DIST_to_its_dam.append(min(thisLake_dist_to_all_its_dam))
        Dammed_lakes.append(this_lake_FID)
    else:
        # This lake may not be a reservoir (no dam paired yet). 
        DAM_FID_FOR_this_LAKE.append(-1)
        DIST_to_its_dam.append(-1)
        MultiDams.append(-1)
        Dammed_lakes.append(-1)
del lake_record
del lake_records
print '2nd iteration done: ... at ' + str(datetime.now())

# 3rd iteration: Loop through valid_DAM_FIDs again. For any dam without lakes assigned yet, pair it with its closest unassigned lake.
print '3rd iteration in process ...'
missing_dam_FIDs = [] # FIDs of the dams that have not been paired with any lakes but will be paired after this iteration.
missing_dam_associated_lakes_FIDs = [] # FID of the newly paired closest lake.
missing_dam_associated_lakes_dist_to_dam = [] # Distance of the newly paired closest lake.
for this_valid_DAM_FID in valid_DAM_FIDs:
    # Query indices where this particular dam exists in DAM_FID_FOR_this_LAKE.
    this_valid_DAM_FID_index = [i for i, x in enumerate(DAM_FID_FOR_this_LAKE) if x == this_valid_DAM_FID] 
    if len(this_valid_DAM_FID_index) == 0: # Meaning this dam is not paired with any lake.
        # Then assign the closest lake to this dam.
        
        # Retrieve all original lakes associated with this dam, and select the closest unassigned lake
        all_records_for_this_DAM_indices = [i for i, x in enumerate(IN_FID) if x == this_valid_DAM_FID] #indices
        all_lakes_FID_for_this_dam = [x[1] for x in enumerate(NEAR_FID) if x[0] in all_records_for_this_DAM_indices]
        all_lakes_distance_for_this_dam = [x[1] for x in enumerate(NEAR_DIST) if x[0] in all_records_for_this_DAM_indices]
        unassigned_lakes_FID_for_this_dam = []
        unassigned_lakes_dist_to_this_dam = []
        local_i = 0
        for a_lake_FID_for_this_dam in all_lakes_FID_for_this_dam:
            index_of_lakes_assigned = [i for i, x in enumerate(Dammed_lakes) if x == a_lake_FID_for_this_dam]
            if len(index_of_lakes_assigned) == 0: # Meaning this lake has not been taken by any dam yet
                unassigned_lakes_FID_for_this_dam.append(a_lake_FID_for_this_dam)
                unassigned_lakes_dist_to_this_dam.append(all_lakes_distance_for_this_dam[local_i])
            local_i = local_i + 1
        # Select the closest unassigned lake
        if len(unassigned_lakes_FID_for_this_dam) > 0:
            closest_index = unassigned_lakes_dist_to_this_dam.index(min(unassigned_lakes_dist_to_this_dam))
            this_closest_lake_FID = unassigned_lakes_FID_for_this_dam[closest_index]
            missing_dam_FIDs.append(this_valid_DAM_FID)
            missing_dam_associated_lakes_FIDs.append(this_closest_lake_FID)
            missing_dam_associated_lakes_dist_to_dam.append(min(unassigned_lakes_dist_to_this_dam))   
# Loop through these closest unassigned lakes and secure its closest dam
local_i = 0
for missing_dam_associated_lakes_FID in missing_dam_associated_lakes_FIDs:
    # Query indices where this lake FID exists in missing_dam_associated_lakes_FIDs (if there are multiple indices,
    # this means this previously unassigned lake is shared by several previously unpaired dams. This needs to be fixed below.
    this_lake_indices = [i for i, x in enumerate(missing_dam_associated_lakes_FIDs) if x == missing_dam_associated_lakes_FID]
    # Retrieve this lake FID
    this_lake = missing_dam_associated_lakes_FIDs[this_lake_indices[0]]
    # Retrieve the index of this lake in the original layer
    this_lake_index_in_LAKE_LAYER = [i for i, x in enumerate(Lake_FIDs) if x == this_lake]
    
    if len(this_lake_indices) == 1: # Meaning this missing dam has a unique unassigned lake (this unassigned lake is not claimed by any other dam)
        # Update DAM_FID_FOR_this_LAKE, DIST_to_its_damn, and MultiDams
        DAM_FID_FOR_this_LAKE[this_lake_index_in_LAKE_LAYER[0]] = missing_dam_FIDs[local_i]
        DIST_to_its_dam[this_lake_index_in_LAKE_LAYER[0]] = missing_dam_associated_lakes_dist_to_dam[local_i]
        MultiDams[this_lake_index_in_LAKE_LAYER[0]] = 0
    else: # This means this unassigned lake is shared by more than one missing dams
        # If so, update DAM_FID_FOR_this_LAKE, DIST_to_its_damn, and MultiDams by the information of the closest one dam. 
        dam_distances_to_this_lake = []
        for this_lake_index in this_lake_indices:
            dam_distances_to_this_lake.append(missing_dam_associated_lakes_dist_to_dam[this_lake_index])
        index_of_closer_dam_within_array_dam_distances_to_this_lake = dam_distances_to_this_lake.index(min(dam_distances_to_this_lake))
        this_selected_dam_FID = missing_dam_FIDs[this_lake_indices[index_of_closer_dam_within_array_dam_distances_to_this_lake]]
        DAM_FID_FOR_this_LAKE[this_lake_index_in_LAKE_LAYER[0]] = this_selected_dam_FID
        DIST_to_its_dam[this_lake_index_in_LAKE_LAYER[0]] = min(dam_distances_to_this_lake)
        MultiDams[this_lake_index_in_LAKE_LAYER[0]] = 1
    local_i = local_i + 1
print '3rd iteration done: ... at ' + str(datetime.now())

# Generating DAM_officialID_FOR_this_LAKE: translate DAM_FID_FOR_this_LAKE (FIDs) to the original dam IDs that are not subject to change. 
DAM_officialID_FOR_this_LAKE = []
for DAM_FID_FOR_this_LAKE_i in DAM_FID_FOR_this_LAKE:
    if DAM_FID_FOR_this_LAKE_i == -1:
        DAM_officialID_FOR_this_LAKE.append(-1)
    else:      
        this_index = [i for i, x in enumerate(dam_object_IDs) if x == DAM_FID_FOR_this_LAKE_i]
        DAM_officialID_FOR_this_LAKE.append(dam_official_IDs[this_index[0]])

# To assign DAM_FID_FOR_LAKES back to LAKES2 (with a spatial tolerance of 1000m)
# Update fields within the lake layer
lake_records = arcpy.UpdateCursor(Lakes2)
for lake_record in lake_records:
    this_lake_official_ID = lake_record.Hylak_id
    this_index = [i for i, x in enumerate(Lake_officialID) if x == this_lake_official_ID]
    if len(this_index)==1:
        if DAM_FID_FOR_this_LAKE[this_index[0]] != -1:
            lake_record.Dam_officialID = DAM_officialID_FOR_this_LAKE[this_index[0]]
            lake_record.Dam_dist = DIST_to_its_dam[this_index[0]]
            lake_record.MultiDams = MultiDams[this_index[0]]
            lake_records.updateRow(lake_record)
del lake_record
del lake_records
print 'Round 1: Using a spatial tolerance of 500 m. Completed!'


#===========================================================
# ROUND 2: Using a spatial tolerance/buffer of 1000 m (Lakes2)
# Thus far, lakes that have not been paired yet are those where lake_record.Dam_officialID" IS NULL,
# and dams that have NOT been used or joined are those NOT in the valid values of Dam_officialID.
# Retrieve unpaired lakes from Lakes2, and save them to Lakes_others.
arcpy.MakeFeatureLayer_management(Lakes2, 'Lakes2')
FID_lakes_delimiter = arcpy.AddFieldDelimiters(Lakes2, "Dam_officialID")
arcpy.SelectLayerByAttribute_management("Lakes2", "NEW_SELECTION", FID_lakes_delimiter + " IS NULL")
# "Lakes_others" contains water features that have not been paired with any dams after Round 1.
arcpy.CopyFeatures_management('Lakes2', Lakes_others) 
arcpy.SelectLayerByAttribute_management("Lakes2", "CLEAR_SELECTION")

# Retrieve unpaired dam points, and save them to Dams_others.
#search unique values in DAM_officialID_FOR_this_LAKE (except "-1" indicating no dams for this lake)
unique_Dam_OBJECTID = list(set(DAM_officialID_FOR_this_LAKE))
FID_dams_delimiter = arcpy.AddFieldDelimiters(Dams, "dam_ID")
for this_unique_Dam_OBJECTID in unique_Dam_OBJECTID:
    if this_unique_Dam_OBJECTID != -1:
        arcpy.SelectLayerByAttribute_management("dams_lyr", "ADD_TO_SELECTION", FID_dams_delimiter + " = " + str(this_unique_Dam_OBJECTID))
# Flip the selection and export the unpaired dam points to Dams_others
arcpy.SelectLayerByAttribute_management ("dams_lyr", "SWITCH_SELECTION")
arcpy.CopyFeatures_management('dams_lyr', Dams_others)
arcpy.SelectLayerByAttribute_management("dams_lyr", "CLEAR_SELECTION")
print 'Unpaired lakes and dams retrieved ...'

# Generate near table (find closest lakes for each dam). 
arcpy.GenerateNearTable_analysis(Dams_others, Lakes_others, joined_table_others, '1000 Meters', location, angle, closest, closest_count, method)

# Join lake area information to joined_table_others
arcpy.JoinField_management (joined_table_others, "NEAR_FID", Lakes_others, "OBJECTID", ["Shape_Area"])

# Loop through the joined table (joined_table_others) to acquire attributes.
joined_table_records = arcpy.SearchCursor(joined_table_others)
IN_FID = [] # Dam FIDs found in the generate near table
NEAR_FID = [] # FIDs of all lakes within 1km of each dam in the generate near table
NEAR_DIST = [] # distance of lakes to dam
NEAR_RANK = [] # the ranking of the lake in distance to dam
NEAR_FID_AREA = [] #lake area
# Append values for each record in the table to the empty array defined above
for joined_table_record in joined_table_records:
    IN_FID.append(joined_table_record.IN_FID)
    NEAR_FID.append(joined_table_record.NEAR_FID)
    NEAR_DIST.append(joined_table_record.NEAR_DIST)
    NEAR_RANK.append(joined_table_record.NEAR_RANK)
    NEAR_FID_AREA.append(joined_table_record.SHAPE_AREA)
del joined_table_record
del joined_table_records

# 1st iteration: loop through all dam FIDs with a lake within the buffer distance and select the biggest lake
print '1st iteration in process ...'
Dam_FIDs = arcpy.SearchCursor(Dams_others)
valid_DAM_FIDs = [] # FIDs of the dams that have at least one lake within the spatial tolerance
valid_DAM_BIGGEST_LAKE_FIDs = [] # FID of the largest lake associated with each valid dam (above)
distance_array = [] # Distance from each valid dam to its largest lake
dam_object_IDs = [] # Dam FIDs 
dam_official_IDs = [] # Dam IDs (previously added attribute that represents unique features)
for Dam_FID in Dam_FIDs:
    dam_object_IDs.append(Dam_FID.OBJECTID)
    dam_official_IDs.append(Dam_FID.dam_ID)
    this_DAM_FID = Dam_FID.OBJECTID
    
    # Check if this_DAM_FID is in IN_FID and extracts all indices of this_DAM_FID from the near table.
    all_records_for_this_DAM = [i for i, x in enumerate(IN_FID) if x == this_DAM_FID]
    # all_records_for_this_DAM returns the index location(s) from the joined table where IN_FID equals this_DAM_FID
    
    if len(all_records_for_this_DAM) > 0: # Indicating this dam has at least one lake within the spatial tolerance
        # Retrieve lake information associated with this_DAM_FID
        all_lakes_FID_for_this_dam = [x[1] for x in enumerate(NEAR_FID) if x[0] in all_records_for_this_DAM]
        all_lakes_area_for_this_dam = [x[1] for x in enumerate(NEAR_FID_AREA) if x[0] in all_records_for_this_DAM]
        all_lakes_distance_for_this_dam = [x[1] for x in enumerate(NEAR_DIST) if x[0] in all_records_for_this_DAM]
        
        # Select the bigger lake
        this_local_index = all_lakes_area_for_this_dam.index(max(all_lakes_area_for_this_dam))
        this_DAM_BIGGEST_LAKE_FID = all_lakes_FID_for_this_dam[this_local_index]
        this_DAM_distance = all_lakes_distance_for_this_dam[this_local_index]

        # Generate dam and lake FID pairs (both are FIDs)
        valid_DAM_FIDs.append(this_DAM_FID)
        valid_DAM_BIGGEST_LAKE_FIDs.append(this_DAM_BIGGEST_LAKE_FID)
        distance_array.append(this_DAM_distance)
del Dam_FID
del Dam_FIDs
print '1st iteration done: at ' + str(datetime.now())

# 2nd interation: loops through valid_DAM_FIDs and detect lakes associated with multiple dams. And if this happens,
# re-assign valid_DAM_FID to its closest lake
print '2nd iteration in process ...'
j = 0
for valid_DAM_FID in valid_DAM_FIDs:
    # Retrieve the lake associated with this valid DAM FID.
    this_dam_associated_lake_FID = valid_DAM_BIGGEST_LAKE_FIDs[j]
    # Check if this_dam_associated_lake_FID exists for some other dams or not.
    this_dam_associated_lake_FID_indices = [i for i, x in enumerate(valid_DAM_BIGGEST_LAKE_FIDs) if x == this_dam_associated_lake_FID]
    if len(this_dam_associated_lake_FID_indices) > 1: # Indicating that this dam has an associated lake that appears more than once 
        # Query indices where this particular dam exists in the joined near table 
        all_records_for_this_DAM = [i for i, x in enumerate(IN_FID) if x == valid_DAM_FID]  #this is to query indices where this particular dam exists in the joined near table      
        # Retrieve lake information of this dam in the joined near table
        all_lakes_FID_for_this_dam = [x[1] for x in enumerate(NEAR_FID) if x[0] in all_records_for_this_DAM]
        all_lakes_distrank_for_this_dam = [x[1] for x in enumerate(NEAR_RANK) if x[0] in all_records_for_this_DAM]
        all_lakes_distance_for_this_dam = [x[1] for x in enumerate(NEAR_DIST) if x[0] in all_records_for_this_DAM]
        
        # Select the closest lake
        this_local_index = all_lakes_distrank_for_this_dam.index(min(all_lakes_distrank_for_this_dam))
        this_DAM_BIGGEST_LAKE_FID = all_lakes_FID_for_this_dam[this_local_index] #note that this lake may not be the BIGGEST one for this dam any more
        this_DAM_distance = all_lakes_distance_for_this_dam[this_local_index]
        
        # Generate dam and lake FID pairs (both are FIDs)
        valid_DAM_BIGGEST_LAKE_FIDs[j] = this_DAM_BIGGEST_LAKE_FID #note that this lake may not be the BIGGEST one for this dam any more although it is called BIGGEST in the variable name
        distance_array[j] = this_DAM_distance
    j= j+1
# The 2nd iteration thus far may not eliminate ambiguous lakes. The closest lake can also be the largest lake.
# This is why we include a another of iteration below. 
# Select the closest dam that is located near a lake that shares multiple dams.
lake_records = arcpy.SearchCursor(Lakes_others)
Lake_FIDs = [] # Lake FIDs
Lake_officialID = [] # Lake IDs (previously added attribute that represents unique features) 
DAM_FID_FOR_this_LAKE = [] # FID of the dam that is closest to this lake
DIST_to_its_dam = [] # Distance from this lake to its closest dam
MultiDams = [] # Array with binary values (1 or 0) indicating if this lake has multiple dams (1) or a unique done (0). 
Dammed_lakes = [] # FIDs of the lakes that have been paired with a dam ("-1" indicates otherwise). 
for lake_record in lake_records:
    this_lake_FID = lake_record.OBJECTID
    Lake_FIDs.append(this_lake_FID)
    Lake_officialID.append(lake_record.Hylak_id) # This attribute needs to be changed according to the input water mask dataset.
    # Query indices where this particular lake exists in valid_DAM_BIGGEST_LAKE_FIDs (lakes that are previously paired with dams)   
    lake_with_dam_indices = [i for i, x in enumerate(valid_DAM_BIGGEST_LAKE_FIDs) if x == this_lake_FID]

    if len(lake_with_dam_indices) == 1: # Meaning this lake was paired with only one dam.
        DAM_FID_FOR_this_LAKE.append(valid_DAM_FIDs[lake_with_dam_indices[0]])
        DIST_to_its_dam.append(distance_array[lake_with_dam_indices[0]])
        MultiDams.append(0) # This lake does not have multiple dams (only one unique dam). 
        Dammed_lakes.append(this_lake_FID) # This lake has been paired with a dam. 
    elif len(lake_with_dam_indices) > 1: # Meaning this lake was paired with multiple dams.
        MultiDams.append(1) # This lake has multiple dams. 
        # Assign the closest dam to this lake
        thisLake_dist_to_all_its_dam = [] # Array recording the distance values from this lake to all associated dams.
        for lake_with_dam_index in lake_with_dam_indices: #this dam
            # Retrieve the distance between this dam and this lake
            thisLake_dist_to_all_its_dam.append(distance_array[lake_with_dam_index])
        this_closest_dam_for_this_lake_index = thisLake_dist_to_all_its_dam.index(min(thisLake_dist_to_all_its_dam))
        DAM_FID_FOR_this_LAKE.append(valid_DAM_FIDs[lake_with_dam_indices[this_closest_dam_for_this_lake_index]])
        DIST_to_its_dam.append(min(thisLake_dist_to_all_its_dam))
        Dammed_lakes.append(this_lake_FID)
    else:
        # This lake may not be a reservoir (no dam paired yet). 
        DAM_FID_FOR_this_LAKE.append(-1)
        DIST_to_its_dam.append(-1)
        MultiDams.append(-1)
        Dammed_lakes.append(-1)
del lake_record
del lake_records
print '2nd iteration done: ... at ' + str(datetime.now())

# 3rd iteration: Loop through valid_DAM_FIDs again. For any dam without lakes assigned yet, pair it with its closest unassigned lake.
print '3rd iteration in process ...'
missing_dam_FIDs = [] # FIDs of the dams that have not been paired with any lakes but will be paired after this iteration.
missing_dam_associated_lakes_FIDs = [] # FID of the newly paired closest lake.
missing_dam_associated_lakes_dist_to_dam = [] # Distance of the newly paired closest lake.
for this_valid_DAM_FID in valid_DAM_FIDs:
    # Query indices where this particular dam exists in DAM_FID_FOR_this_LAKE.
    this_valid_DAM_FID_index = [i for i, x in enumerate(DAM_FID_FOR_this_LAKE) if x == this_valid_DAM_FID] 
    if len(this_valid_DAM_FID_index) == 0: # Meaning this dam is not paired with any lake.
        # Then assign the closest lake to this dam 

        # Retrieve all original lakes associated with this dam, and select the closest unassigned lake
        all_records_for_this_DAM_indices = [i for i, x in enumerate(IN_FID) if x == this_valid_DAM_FID]
        all_lakes_FID_for_this_dam = [x[1] for x in enumerate(NEAR_FID) if x[0] in all_records_for_this_DAM_indices]
        all_lakes_distance_for_this_dam = [x[1] for x in enumerate(NEAR_DIST) if x[0] in all_records_for_this_DAM_indices]
        unassigned_lakes_FID_for_this_dam = []
        unassigned_lakes_dist_to_this_dam = []
        local_i = 0
        for a_lake_FID_for_this_dam in all_lakes_FID_for_this_dam:
            index_of_lakes_assigned = [i for i, x in enumerate(Dammed_lakes) if x == a_lake_FID_for_this_dam]
            if len(index_of_lakes_assigned) == 0: # Meaning this lake has not been taken by any dam yet
                unassigned_lakes_FID_for_this_dam.append(a_lake_FID_for_this_dam)
                unassigned_lakes_dist_to_this_dam.append(all_lakes_distance_for_this_dam[local_i])
            local_i = local_i + 1
        # Select the closest unassigned lake
        if len(unassigned_lakes_FID_for_this_dam) > 0:
            closest_index = unassigned_lakes_dist_to_this_dam.index(min(unassigned_lakes_dist_to_this_dam))
            this_closest_lake_FID = unassigned_lakes_FID_for_this_dam[closest_index]
            missing_dam_FIDs.append(this_valid_DAM_FID)
            missing_dam_associated_lakes_FIDs.append(this_closest_lake_FID)
            missing_dam_associated_lakes_dist_to_dam.append(min(unassigned_lakes_dist_to_this_dam))
# Loop through these closest unassigned lakes and secure its closest dam
local_i = 0
for missing_dam_associated_lakes_FID in missing_dam_associated_lakes_FIDs:
    # Query indices where this lake FID exists in missing_dam_associated_lakes_FIDs (if there are multiple indices,
    # this means this previously unassigned lake is shared by several previously unpaired dams. This needs to be fixed below.
    this_lake_indices = [i for i, x in enumerate(missing_dam_associated_lakes_FIDs) if x == missing_dam_associated_lakes_FID]
    # Retrieve this lake FID
    this_lake = missing_dam_associated_lakes_FIDs[this_lake_indices[0]]
    # Retrieve the index of this lake in the original layer
    this_lake_index_in_LAKE_LAYER = [i for i, x in enumerate(Lake_FIDs) if x == this_lake]
    
    if len(this_lake_indices) == 1: # Meaning this missing dam has a unique unassigned lake (this unassigned lake is not claimed by any other dam)
        # Update DAM_FID_FOR_this_LAKE, DIST_to_its_damn, and MultiDams
        DAM_FID_FOR_this_LAKE[this_lake_index_in_LAKE_LAYER[0]] = missing_dam_FIDs[local_i]
        DIST_to_its_dam[this_lake_index_in_LAKE_LAYER[0]] = missing_dam_associated_lakes_dist_to_dam[local_i]
        MultiDams[this_lake_index_in_LAKE_LAYER[0]] = 0
    else: # This means this unassigned lake is shared by more than one missing dams
        # If so, update DAM_FID_FOR_this_LAKE, DIST_to_its_damn, and MultiDams by the information of the closest one dam. 
        dam_distances_to_this_lake = []
        for this_lake_index in this_lake_indices:
            dam_distances_to_this_lake.append(missing_dam_associated_lakes_dist_to_dam[this_lake_index])
        index_of_closer_dam_within_array_dam_distances_to_this_lake = dam_distances_to_this_lake.index(min(dam_distances_to_this_lake))
        this_selected_dam_FID = missing_dam_FIDs[this_lake_indices[index_of_closer_dam_within_array_dam_distances_to_this_lake]]
        DAM_FID_FOR_this_LAKE[this_lake_index_in_LAKE_LAYER[0]] = this_selected_dam_FID
        DIST_to_its_dam[this_lake_index_in_LAKE_LAYER[0]] = min(dam_distances_to_this_lake)
        MultiDams[this_lake_index_in_LAKE_LAYER[0]] = 1
    local_i = local_i + 1
print '3rd iteration done: ... at ' + str(datetime.now())

# Generating DAM_officialID_FOR_this_LAKE: translate DAM_FID_FOR_this_LAKE (FIDs) to the original dam IDs that are not subject to change. 
DAM_officialID_FOR_this_LAKE = []
for DAM_FID_FOR_this_LAKE_i in DAM_FID_FOR_this_LAKE:
    if DAM_FID_FOR_this_LAKE_i == -1:
        DAM_officialID_FOR_this_LAKE.append(-1)
    else:      
        this_index = [i for i, x in enumerate(dam_object_IDs) if x == DAM_FID_FOR_this_LAKE_i]
        DAM_officialID_FOR_this_LAKE.append(  dam_official_IDs[this_index[0]])

# To assign DAM_FID_FOR_LAKES back to LAKES2 (with a spatial tolerance of 1000m)
# Update fields within the lake layer
lake_records = arcpy.UpdateCursor(Lakes2)
for lake_record in lake_records:
    this_lake_official_ID = lake_record.Hylak_id
    this_index = [i for i, x in enumerate(Lake_officialID) if x == this_lake_official_ID]
    if len(this_index)==1:
        if DAM_FID_FOR_this_LAKE[this_index[0]] != -1:
            lake_record.Dam_officialID = DAM_officialID_FOR_this_LAKE[this_index[0]]
            lake_record.Dam_dist = DIST_to_its_dam[this_index[0]]
            lake_record.MultiDams = MultiDams[this_index[0]]
            lake_records.updateRow(lake_record)
del lake_record
del lake_records
print 'Round 2: Using a spatial tolerance of 1000 m. Completed!'


#===========================================================
# Final step: export paired lakes and export unpaired dams 
arcpy.MakeFeatureLayer_management(Lakes2, 'Lakes2')
FID_lakes_delimiter = arcpy.AddFieldDelimiters(Lakes2, "Dam_officialID")
arcpy.SelectLayerByAttribute_management("Lakes2", "NEW_SELECTION", FID_lakes_delimiter + " IS NOT NULL")
arcpy.CopyFeatures_management('Lakes2', matched_lakes)
arcpy.SelectLayerByAttribute_management("Lakes2", "CLEAR_SELECTION")
# Table join dam information to lakes based on official dam ID
arcpy.JoinField_management(matched_lakes, "Dam_officialID", Dams, "dam_ID")
print 'Pair lakes exported.'

# Export the dams that are left unpaired.
arcpy.MakeFeatureLayer_management(Dams_others, 'dams_others_lyr')
# Search unique values in DAM_officialID_FOR_this_LAKE (except -1)
unique_Dam_OBJECTID = list(set(DAM_officialID_FOR_this_LAKE))
FID_dams_delimiter = arcpy.AddFieldDelimiters(Dams_others, "dam_ID")
for this_unique_Dam_OBJECTID in unique_Dam_OBJECTID:
    if this_unique_Dam_OBJECTID != -1:
        arcpy.SelectLayerByAttribute_management("dams_others_lyr", "ADD_TO_SELECTION", FID_dams_delimiter + " = " + str(this_unique_Dam_OBJECTID))
# Flip the selection
arcpy.SelectLayerByAttribute_management ("dams_others_lyr", "SWITCH_SELECTION")
arcpy.CopyFeatures_management('dams_others_lyr', notmatched_dams)
arcpy.SelectLayerByAttribute_management("dams_others_lyr", "CLEAR_SELECTION")
print 'Unpaired dams exported.'

# Delete intermediate files
arcpy.management.Delete(Lakes)
arcpy.management.Delete(Lakes2)
arcpy.management.Delete(Lakes_others)
arcpy.management.Delete(Dams_others)
arcpy.management.Delete(joined_table)
arcpy.management.Delete(joined_table_others)

print("----- Module Completed -----")
print(datetime.datetime.now())
