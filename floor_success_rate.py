from typing import Dict, Any, Tuple, List
import logging, paho.mqtt.client as mqtt
import time, requests, json
import matplotlib.pyplot as plt
import numpy as np
import os

from get_tag_macs import tag_id_to_mac

"""
Anchor lists:
Tags downstairs: {62398, 33655, 34487, 27666, 42322, 16915, 45527, 21342, 37133, 4468, 54577, 15826, 47621, 43668, 19465, 42966, 4820, 62994, 24904, 28567, 34114, 13077, 1758, 44900, 28565, 25272, 49874, 18821, 23550, 59518}
Tags mezzanine: {53934, 48172, 52711, 24129, 13485, 28864, 1899, 58679, 47397, 32448, 60967, 65555, 64669, 28693, 28152, 35664, 62122, 55738, 20288, 22689, 6667, 59668, 47437, 64833, 52919, 2468, 38511, 63204, 62320, 34465}

Tag_mac_list: []

mezzanine map id: 682c66f08cde618ce127025e
downstairs map id: 682c66de8cde618ce1270230
"""


url = ""  # API endpoint (redacted)
headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}
#missing tag ids: ('47621', '19466', '1758')
TAG_MAC_LIST: List[str] = [
    'f8c6e10eb94d', 'e80511ee6f95', 'ebc3d8c27268', 'ea130331a7d6', 'e5618db03315', 'f53d908ae87e', 'faebae16f304', 'dcb814adee27', 'ee1ae8c0199b', 'e71ebc086c12', 'dc6fd1014985', 
    'e0187539099c', 'ed3dc76b5057', 'cfcba5a4aa8c', 'd2433d346da0', 'c3fdcfc7cde7', 'fbde6b71de2c', 'eed4934cb925', 'd55a17359cec', 'dd35e8065e41', 'de8a7eb407c5', 'c694e5297d8c', 
    'f7fb6d248542', 'f1465d4b34ad', 'c5d89d98d531', 'e3c858bb535e', 'e12a0889fc9d', 'f17508753dd2', 'eacbbb80d2ae', 'd908a64ff5c8', 'e0179d3286a1', 'ca70faad5185', 'eaf519e486b7', 
    'f260a59af3be', 'd1162b91f43c', 'c0c28a5250d1', 'e45428cd811f', 'f9cf5a96910d', 'e1221fc96df8', 'db87600e1088', 'ea0efa76b1d7', 'e75675d44213', 'cfa33b8f966f', 'e6a1121bd9ba', 
    'c61444ecfa21', 'cbafa76ff612', 'eabf49388a88', 'e6dee509ceb7', 'd31e40a36148', 'fe916ad112d4', 'dbd8f214e90c', 'f8e68ad462b8', 'ced95ba5af64', 'c07f2aebbfb2', 'dbdfe63c5bfe', 
    'eb7dd4251a0b', 'e9ee05861174', 'c48718b206de', 'dfe232164c0a', 'ccd6b409ba05'
]
payload: Dict[str, Any] = {
    "devices": TAG_MAC_LIST,
    "adv_type": "uwb",
    "adv_payload_settings": {
        "pattern": 0,
        "led": 0
    },
    "ble_settings": {
        "sync_interval": 10,
        "sync_ext_time": 1000,
        "duration": 1000,
        "adv_interval": 20
    },
    "timeout": 90
}

tag_id_to_mac: Dict[str, str] = {
    '28064': 'd2433d346da0', '21342': 'e3c858bb535e', '53934': 'eacbbb80d2ae', '13485': 'f1465d4b34ad', '15826': 'f17508753dd2', '47397': 'eed4934cb925', 
    '34114': 'f7fb6d248542', '20869': 'ca70faad5185', '54577': 'c5d89d98d531', '32140': 'c694e5297d8c', '40172': 'd55a17359cec', '62920': 'd908a64ff5c8', '64669': 'e12a0889fc9d', 
    '24129': 'dd35e8065e41', '34465': 'e0179d3286a1', '34487': 'eaf519e486b7', '20689': 'c0c28a5250d1', '35464': 'eabf49388a88', '55738': 'e6a1121bd9ba', '37133': 'f9cf5a96910d', 
    '38511': 'cfa33b8f966f', '49074': 'c07f2aebbfb2', '62524': 'd1162b91f43c', '28152': 'e1221fc96df8', '23550': 'dbdfe63c5bfe', '24904': 'd31e40a36148', '25272': 'f8e68ad462b8', 
    '62994': 'cbafa76ff612', '4820': 'fe916ad112d4', '44900': 'ced95ba5af64', '62398': 'f260a59af3be', '45527': 'ea0efa76b1d7', '52919': 'e6dee509ceb7', '64033': 'c61444ecfa21', 
    '33055': 'e45428cd811f', '43660': 'cfcba5a4aa8c', '20567': 'ed3dc76b5057', '1989': 'de8a7eb407c5', '52711': 'c3fdcfc7cde7', '56876': 'fbde6b71de2c', '59660': 'dbd8f214e90c', 
    '4232': 'db87600e1088', '16915': 'e75675d44213', '1758': 'c48718b206de', '42966': 'ea130331a7d6', '28565': 'e80511ee6f95', '13077': 'e5618db03315', '59518': 'f53d908ae87e', 
    '29288': 'ebc3d8c27268', '19466': 'dfe232164c0a', '4468': 'e9ee05861174', '60967': 'dcb814adee27', '62212': 'faebae16f304', '6555': 'ee1ae8c0199b', '18821': 'dc6fd1014985', 
    '2460': 'e0187539099c', '6667': 'eb7dd4251a0b', '27666': 'e71ebc086c12', '47437': 'f8c6e10eb94d', '47621': 'ccd6b409ba05'
}
#success rate evaluater info:
TAG_POSITION_DICT: Dict[str, str] = {
    # Downstairs tags
    "62398": "682c66de8cde618ce1270230",
    "33055": "682c66de8cde618ce1270230",
    "34487": "682c66de8cde618ce1270230",
    "27666": "682c66de8cde618ce1270230",
    "4232": "682c66de8cde618ce1270230",
    "16915": "682c66de8cde618ce1270230",
    "45527": "682c66de8cde618ce1270230",
    "21342": "682c66de8cde618ce1270230",
    "37133": "682c66de8cde618ce1270230",
    "4468": "682c66de8cde618ce1270230",
    "54577": "682c66de8cde618ce1270230",
    "15826": "682c66de8cde618ce1270230",
    "47621": "682c66de8cde618ce1270230",
    "43660": "682c66de8cde618ce1270230",
    "19466": "682c66de8cde618ce1270230",
    "42966": "682c66de8cde618ce1270230",
    "4820": "682c66de8cde618ce1270230",
    "62994": "682c66de8cde618ce1270230",
    "24904": "682c66de8cde618ce1270230",
    "20567": "682c66de8cde618ce1270230",
    "34114": "682c66de8cde618ce1270230",
    "13077": "682c66de8cde618ce1270230",
    "1758": "682c66de8cde618ce1270230",
    "44900": "682c66de8cde618ce1270230",
    "28565": "682c66de8cde618ce1270230",
    "25272": "682c66de8cde618ce1270230",
    "49074": "682c66de8cde618ce1270230",
    "18821": "682c66de8cde618ce1270230",
    "23550": "682c66de8cde618ce1270230",
    "59518": "682c66de8cde618ce1270230",
    
    # Mezzanine tags
    "53934": "682c66f08cde618ce127025e",
    "40172": "682c66f08cde618ce127025e",
    "52711": "682c66f08cde618ce127025e",
    "24129": "682c66f08cde618ce127025e",
    "13485": "682c66f08cde618ce127025e",
    "28064": "682c66f08cde618ce127025e",
    "1989": "682c66f08cde618ce127025e",
    "56876": "682c66f08cde618ce127025e",
    "47397": "682c66f08cde618ce127025e",
    "32140": "682c66f08cde618ce127025e",
    "60967": "682c66f08cde618ce127025e",
    "6555": "682c66f08cde618ce127025e",
    "64669": "682c66f08cde618ce127025e",
    "20869": "682c66f08cde618ce127025e",
    "28152": "682c66f08cde618ce127025e",
    "35464": "682c66f08cde618ce127025e",
    "62212": "682c66f08cde618ce127025e",
    "55738": "682c66f08cde618ce127025e",
    "29288": "682c66f08cde618ce127025e",
    "20689": "682c66f08cde618ce127025e",
    "6667": "682c66f08cde618ce127025e",
    "59660": "682c66f08cde618ce127025e",
    "47437": "682c66f08cde618ce127025e",
    "64033": "682c66f08cde618ce127025e",
    "52919": "682c66f08cde618ce127025e",
    "2460": "682c66f08cde618ce127025e",
    "38511": "682c66f08cde618ce127025e",
    "62524": "682c66f08cde618ce127025e",
    "62920": "682c66f08cde618ce127025e",
    "34465": "682c66f08cde618ce127025e"
}

# Dictionary mapping MAC addresses to map IDs
TAG_MAC_TO_MAP_ID: Dict[str, str] = {
    # Downstairs tags (map_id: 682c66de8cde618ce1270230)
    'f260a59af3be': '682c66de8cde618ce1270230',  # 62398
    'e45428cd811f': '682c66de8cde618ce1270230',  # 33055
    'eaf519e486b7': '682c66de8cde618ce1270230',  # 34487
    'e71ebc086c12': '682c66de8cde618ce1270230',  # 27666
    'db87600e1088': '682c66de8cde618ce1270230',  # 4232
    'e75675d44213': '682c66de8cde618ce1270230',  # 16915
    'ea0efa76b1d7': '682c66de8cde618ce1270230',  # 45527
    'e3c858bb535e': '682c66de8cde618ce1270230',  # 21342
    'f9cf5a96910d': '682c66de8cde618ce1270230',  # 37133
    'e9ee05861174': '682c66de8cde618ce1270230',  # 4468
    'c5d89d98d531': '682c66de8cde618ce1270230',  # 54577
    'f17508753dd2': '682c66de8cde618ce1270230',  # 15826
    'ccd6b409ba05': '682c66de8cde618ce1270230',  # 47621
    'cfcba5a4aa8c': '682c66de8cde618ce1270230',  # 43660
    'dfe232164c0a': '682c66de8cde618ce1270230',  # 19466
    'ea130331a7d6': '682c66de8cde618ce1270230',  # 42966
    'fe916ad112d4': '682c66de8cde618ce1270230',  # 4820
    'cbafa76ff612': '682c66de8cde618ce1270230',  # 62994
    'd31e40a36148': '682c66de8cde618ce1270230',  # 24904
    'ed3dc76b5057': '682c66de8cde618ce1270230',  # 20567
    'f7fb6d248542': '682c66de8cde618ce1270230',  # 34114
    'e5618db03315': '682c66de8cde618ce1270230',  # 13077
    'c48718b206de': '682c66de8cde618ce1270230',  # 1758
    'ced95ba5af64': '682c66de8cde618ce1270230',  # 44900
    'e80511ee6f95': '682c66de8cde618ce1270230',  # 28565
    'f8e68ad462b8': '682c66de8cde618ce1270230',  # 25272
    'c07f2aebbfb2': '682c66de8cde618ce1270230',  # 49074
    'dc6fd1014985': '682c66de8cde618ce1270230',  # 18821
    'dbdfe63c5bfe': '682c66de8cde618ce1270230',  # 23550
    'f53d908ae87e': '682c66de8cde618ce1270230',  # 59518
    
    # Mezzanine tags (map_id: 682c66f08cde618ce127025e)
    'eacbbb80d2ae': '682c66f08cde618ce127025e',  # 53934
    'd55a17359cec': '682c66f08cde618ce127025e',  # 40172
    'c3fdcfc7cde7': '682c66f08cde618ce127025e',  # 52711
    'dd35e8065e41': '682c66f08cde618ce127025e',  # 24129
    'f1465d4b34ad': '682c66f08cde618ce127025e',  # 13485
    'd2433d346da0': '682c66f08cde618ce127025e',  # 28064
    'de8a7eb407c5': '682c66f08cde618ce127025e',  # 1989
    'fbde6b71de2c': '682c66f08cde618ce127025e',  # 56876
    'eed4934cb925': '682c66f08cde618ce127025e',  # 47397
    'c694e5297d8c': '682c66f08cde618ce127025e',  # 32140
    'dcb814adee27': '682c66f08cde618ce127025e',  # 60967
    'ee1ae8c0199b': '682c66f08cde618ce127025e',  # 6555
    'e12a0889fc9d': '682c66f08cde618ce127025e',  # 64669
    'ca70faad5185': '682c66f08cde618ce127025e',  # 20869
    'e1221fc96df8': '682c66f08cde618ce127025e',  # 28152
    'eabf49388a88': '682c66f08cde618ce127025e',  # 35464
    'faebae16f304': '682c66f08cde618ce127025e',  # 62212
    'e6a1121bd9ba': '682c66f08cde618ce127025e',  # 55738
    'ebc3d8c27268': '682c66f08cde618ce127025e',  # 29288
    'c0c28a5250d1': '682c66f08cde618ce127025e',  # 20689
    'eb7dd4251a0b': '682c66f08cde618ce127025e',  # 6667
    'dbd8f214e90c': '682c66f08cde618ce127025e',  # 59660
    'f8c6e10eb94d': '682c66f08cde618ce127025e',  # 47437
    'c61444ecfa21': '682c66f08cde618ce127025e',  # 64033
    'e6dee509ceb7': '682c66f08cde618ce127025e',  # 52919
    'e0187539099c': '682c66f08cde618ce127025e',  # 2460
    'cfa33b8f966f': '682c66f08cde618ce127025e',  # 38511
    'd1162b91f43c': '682c66f08cde618ce127025e',  # 62524
    'd908a64ff5c8': '682c66f08cde618ce127025e',  # 62920
    'e0179d3286a1': '682c66f08cde618ce127025e'   # 34465
}

# Tag MAC to floor level mapping (0 = downstairs, 1 = upstairs/mezzanine)
TAG_MAC_TO_FLOOR: Dict[str, int] = {
    # Downstairs tags (floor = 0)
    'f260a59af3be': 0,  # 62398
    'e45428cd811f': 0,  # 33055
    'eaf519e486b7': 0,  # 34487
    'e71ebc086c12': 0,  # 27666
    'db87600e1088': 0,  # 4232
    'e75675d44213': 0,  # 16915
    'ea0efa76b1d7': 0,  # 45527
    'e3c858bb535e': 0,  # 21342
    'f9cf5a96910d': 0,  # 37133
    'e9ee05861174': 0,  # 4468
    'c5d89d98d531': 0,  # 54577
    'f17508753dd2': 0,  # 15826
    'ccd6b409ba05': 0,  # 47621
    'cfcba5a4aa8c': 0,  # 43660
    'dfe232164c0a': 0,  # 19466
    'ea130331a7d6': 0,  # 42966
    'fe916ad112d4': 0,  # 4820
    'cbafa76ff612': 0,  # 62994
    'd31e40a36148': 0,  # 24904
    'ed3dc76b5057': 0,  # 20567
    'f7fb6d248542': 0,  # 34114
    'e5618db03315': 0,  # 13077
    'c48718b206de': 0,  # 1758
    'ced95ba5af64': 0,  # 44900
    'e80511ee6f95': 0,  # 28565
    'f8e68ad462b8': 0,  # 25272
    'c07f2aebbfb2': 0,  # 49074
    'dc6fd1014985': 0,  # 18821
    'dbdfe63c5bfe': 0,  # 23550
    'f53d908ae87e': 0,  # 59518
    
    # Mezzanine/upstairs tags (floor = 1)
    'eacbbb80d2ae': 1,  # 53934
    'd55a17359cec': 1,  # 40172
    'c3fdcfc7cde7': 1,  # 52711
    'dd35e8065e41': 1,  # 24129
    'f1465d4b34ad': 1,  # 13485
    'd2433d346da0': 1,  # 28064
    'de8a7eb407c5': 1,  # 1989
    'fbde6b71de2c': 1,  # 56876
    'eed4934cb925': 1,  # 47397
    'c694e5297d8c': 1,  # 32140
    'dcb814adee27': 1,  # 60967
    'ee1ae8c0199b': 1,  # 6555
    'e12a0889fc9d': 1,  # 64669
    'ca70faad5185': 1,  # 20869
    'e1221fc96df8': 1,  # 28152
    'eabf49388a88': 1,  # 35464
    'faebae16f304': 1,  # 62212
    'e6a1121bd9ba': 1,  # 55738
    'ebc3d8c27268': 1,  # 29288
    'c0c28a5250d1': 1,  # 20689
    'eb7dd4251a0b': 1,  # 6667
    'dbd8f214e90c': 1,  # 59660
    'f8c6e10eb94d': 1,  # 47437
    'c61444ecfa21': 1,  # 64033
    'e6dee509ceb7': 1,  # 52919
    'e0187539099c': 1,  # 2460
    'cfa33b8f966f': 1,  # 38511
    'd1162b91f43c': 1,  # 62524
    'd908a64ff5c8': 1,  # 62920
    'e0179d3286a1': 1   # 34465
}

BROKER_HOST = ""  # MQTT broker address (redacted)
BROKER_PORT = 0  # MQTT broker port (redacted)
TOPIC        = "engine/+/positions"           # the same pattern you used in mosquitto_sub
MAX_MESSAGES_ACCEPTED: int = 1

# Counters for tracking success/failure
success_count = 0
failure_count = 0

# Separate counters for downstairs and mezzanine
downstairs_success_count = 0
downstairs_failure_count = 0
mezzanine_success_count = 0
mezzanine_failure_count = 0

# Map IDs for reference
DOWNSTAIRS_MAP_ID = "682c66de8cde618ce1270230"
MEZZANINE_MAP_ID = "682c66f08cde618ce127025e"

# Track start time for runtime calculation
start_time = time.time()

# Dictionary to track message counts for each tag ID
tag_message_counts: Dict[str, int] = {
    # Downstairs tags
    "62398": 0, "33055": 0, "34487": 0, "27666": 0, "4232": 0,
    "16915": 0, "45527": 0, "21342": 0, "37133": 0, "4468": 0,
    "54577": 0, "15826": 0, "47621": 0, "43660": 0, "19466": 0,
    "42966": 0, "4820": 0, "62994": 0, "24904": 0, "20567": 0,
    "34114": 0, "13077": 0, "1758": 0, "44900": 0, "28565": 0,
    "25272": 0, "49074": 0, "18821": 0, "23550": 0, "59518": 0,
    
    # Mezzanine tags
    "53934": 0, "40172": 0, "52711": 0, "24129": 0, "13485": 0,
    "28064": 0, "1989": 0, "56876": 0, "47397": 0, "32140": 0,
    "60967": 0, "6555": 0, "64669": 0, "20869": 0, "28152": 0,
    "35464": 0, "62212": 0, "55738": 0, "29288": 0, "20689": 0,
    "6667": 0, "59660": 0, "47437": 0, "64033": 0, "52919": 0,
    "2460": 0, "38511": 0, "62524": 0, "62920": 0, "34465": 0
}

# Track failed tags and their failure counts
failed_tags: Dict[str, int] = {}  # tag_id -> failure_count

# Spatial tracking data structures - separate successful and failed positions
downstairs_success_positions: List[Tuple[float, float]] = []  # Green positions
downstairs_fail_positions: List[Tuple[float, float]] = []     # Red positions
mezzanine_success_positions: List[Tuple[float, float]] = []   # Green positions
mezzanine_fail_positions: List[Tuple[float, float]] = []      # Red positions

# Data collection control variables
TOTAL_RUNS = 20
EXPECTED_UNIQUE_TAGS_PER_RUN = 56  # Wait for 56 different tags to publish once each
current_run = 0
tags_published_in_current_run = set()  # Track which tags have published in current run

# Floor plan vertices (from plotter.py)
verts_floor_1 = [
    [12.0, 45.6, 0.0], 
    [12.0, 40.1, 0.0], 
    [22.5, 40.1, 0.0], 
    [22.5, 36.3, 0.0], 
    [52.7, 36.3, 0.0], 
    [52.7, 37.3, 0.0], 
    [66.6, 37.3, 0.0], 
    [66.6, 45.6, 0.0]
]

def create_spatial_visualization():
    """Create spatial distribution visualization of tag positions"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Downstairs plot
    if downstairs_success_positions:
        x_coords_success, y_coords_success = zip(*downstairs_success_positions)
        ax1.scatter(x_coords_success, y_coords_success, c='green', alpha=0.6, s=20, label='Success')
    if downstairs_fail_positions:
        x_coords_fail, y_coords_fail = zip(*downstairs_fail_positions)
        ax1.scatter(x_coords_fail, y_coords_fail, c='red', alpha=0.6, s=20, label='Failure')
    
    # Draw floor plan outline for downstairs
    floor_x = [v[0] for v in verts_floor_1]
    floor_y = [v[1] for v in verts_floor_1]
    floor_x.append(floor_x[0])  # Close the polygon
    floor_y.append(floor_y[0])
    ax1.plot(floor_x, floor_y, 'k-', linewidth=2, label='Floor Plan')
    ax1.fill(floor_x, floor_y, alpha=0.1, color='gray')
    
    ax1.set_xlabel('X Position (meters)')
    ax1.set_ylabel('Y Position (meters)')
    ax1.set_title('Floor Success Rate - Downstairs: Spatial Distribution')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.invert_yaxis()  # Invert Y-axis to match expected orientation
    
    # Mezzanine plot
    if mezzanine_success_positions:
        x_coords_success, y_coords_success = zip(*mezzanine_success_positions)
        ax2.scatter(x_coords_success, y_coords_success, c='green', alpha=0.6, s=20, label='Success')
    if mezzanine_fail_positions:
        x_coords_fail, y_coords_fail = zip(*mezzanine_fail_positions)
        ax2.scatter(x_coords_fail, y_coords_fail, c='red', alpha=0.6, s=20, label='Failure')
    
    # Draw floor plan outline for mezzanine (same shape)
    ax2.plot(floor_x, floor_y, 'k-', linewidth=2, label='Floor Plan')
    ax2.fill(floor_x, floor_y, alpha=0.1, color='gray')
    
    ax2.set_xlabel('X Position (meters)')
    ax2.set_ylabel('Y Position (meters)')
    ax2.set_title('Floor Success Rate - Mezzanine: Spatial Distribution')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.invert_yaxis()  # Invert Y-axis to match expected orientation
    
    plt.tight_layout()
    
    # Create output directory
    os.makedirs('spatial_analysis', exist_ok=True)
    
    # Save the plot
    plt.savefig('spatial_analysis/floor_success_spatial_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"🗺️  Spatial distribution saved to spatial_analysis/floor_success_spatial_distribution.png")
    print(f"   Downstairs Success: {len(downstairs_success_positions)}")
    print(f"   Downstairs Failure: {len(downstairs_fail_positions)}")
    print(f"   Mezzanine Success: {len(mezzanine_success_positions)}")
    print(f"   Mezzanine Failure: {len(mezzanine_fail_positions)}")

def add_position_to_tracking(tag_mac: str, x: float, y: float, success: bool):
    """Add a position to the appropriate floor tracking list"""
    # Determine floor based on tag MAC and TAG_POSITION_DICT
    # First, find the tag_id for this MAC
    tag_id = None
    for tid, mac in tag_id_to_mac.items():
        if mac == tag_mac:
            tag_id = tid
            break
    
    if tag_id and tag_id in TAG_POSITION_DICT:
        expected_map_id = TAG_POSITION_DICT[tag_id]
        
        # Add to appropriate floor list based on expected map_id
        if expected_map_id == DOWNSTAIRS_MAP_ID:
            if success:
                downstairs_success_positions.append((x, y))
            else:
                downstairs_fail_positions.append((x, y))
        elif expected_map_id == MEZZANINE_MAP_ID:
            if success:
                mezzanine_success_positions.append((x, y))
            else:
                mezzanine_fail_positions.append((x, y))

#code:
def get_key_info(position_data: Dict[str, Any]) -> Tuple[str, str]:
    tag_id: str = position_data["tag"]["id"]
    map_id: str = position_data["location"]["map_id"]
    return (tag_id, map_id)

def on_connect(client, userdata, flags, rc, properties=None):
    print("🔌 on_connect rc =", rc)          # 0 means OK
    if rc == 0:
        client.subscribe(TOPIC)
    else:
        print("❌ Connect failed")

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("✅ Subscribed, waiting for messages…")

def on_message(client, userdata, msg):
    global success_count, failure_count, tag_message_counts, failed_tags
    global downstairs_success_count, downstairs_failure_count
    global mezzanine_success_count, mezzanine_failure_count
    global current_run, tags_published_in_current_run
    
    try:
        payload = msg.payload.decode("utf-8", errors="replace")
        position_data = json.loads(payload)
        key_info = get_key_info(position_data)
        
        if key_info[0] in TAG_POSITION_DICT.keys():
            tag_id, actual_map_id = key_info
            expected_map_id = TAG_POSITION_DICT[tag_id]
            
            # ONLY process the FIRST message from each tag per run
            if tag_id not in tags_published_in_current_run:
                tags_published_in_current_run.add(tag_id)
                tag_message_counts[tag_id] += 1
                
                # Extract position data for spatial tracking
                tag_mac = position_data["tag"]["mac"]
                location = position_data["location"]
                position = location["position"]
                x = position["x"]
                y = position["y"]
                
                # Add position to spatial tracking
                add_position_to_tracking(tag_mac, x, y, actual_map_id == expected_map_id)
                
                if actual_map_id == expected_map_id:
                    success_count += 1
                    print(f"✅ SUCCESS: {key_info} (Expected: {expected_map_id})")
                    
                    # Track separate floor success rates
                    if expected_map_id == DOWNSTAIRS_MAP_ID:
                        downstairs_success_count += 1
                    elif expected_map_id == MEZZANINE_MAP_ID:
                        mezzanine_success_count += 1
                        
                else:
                    failure_count += 1
                    
                    # Track failed tags
                    if tag_id not in failed_tags:
                        failed_tags[tag_id] = 0
                    failed_tags[tag_id] += 1
                    
                    print(f"❌ FAILURE: {key_info} (Expected: {expected_map_id})")
                    
                    # Track separate floor failure rates
                    if expected_map_id == DOWNSTAIRS_MAP_ID:
                        downstairs_failure_count += 1
                    elif expected_map_id == MEZZANINE_MAP_ID:
                        mezzanine_failure_count += 1
            else:
                # This tag already published in current run, ignore this message
                #print(f"🔄 IGNORING: Tag {tag_id} already published in current run")
                return
            
            # Print current stats
            total = success_count + failure_count
            success_rate = (success_count / total * 100) if total > 0 else 0
            unique_tags_in_run = len(tags_published_in_current_run)
            print(f"📊 Stats: {success_count} successes, {failure_count} failures, {success_rate:.1f}% success rate")
            print(f"📍 Position: ({x:.1f}, {y:.1f}) | Tag: {tag_mac[:6]}... | Floor: {'Downstairs' if expected_map_id == DOWNSTAIRS_MAP_ID else 'Mezzanine'}")
            print(f"🔄 Run {current_run + 1}/{TOTAL_RUNS} | Unique tags in current run: {unique_tags_in_run}/{EXPECTED_UNIQUE_TAGS_PER_RUN}\n")
            
            # Check if we've completed the current run (all 58 unique tags have published)
            if unique_tags_in_run >= EXPECTED_UNIQUE_TAGS_PER_RUN:
                current_run += 1
                tags_published_in_current_run.clear()  # Reset for next run
                
                print(f"🎯 COMPLETED RUN {current_run}/{TOTAL_RUNS}")
                print(f"📊 Run Summary: All {EXPECTED_UNIQUE_TAGS_PER_RUN} unique tags published once")
                print(f"📊 Total stats so far: {success_count} successes, {failure_count} failures")
                print(f"🔄 Starting next run, waiting for all {EXPECTED_UNIQUE_TAGS_PER_RUN} tags again...\n")
                
                # Check if we've completed all runs
                if current_run >= TOTAL_RUNS:
                    print(f"🏁 ALL {TOTAL_RUNS} RUNS COMPLETED!")
                    print(f"📊 Final Summary: {success_count} total successes, {failure_count} total failures")
                    print(f"🎯 Each of the {EXPECTED_UNIQUE_TAGS_PER_RUN} tags published exactly {TOTAL_RUNS} times")
                    print(f"🎯 Stopping data collection...\n")
                    # Disconnect and exit
                    client.disconnect()
                    return
            
    except (json.JSONDecodeError, KeyError) as e:
        print(f"❌ Error parsing message: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def print_final_stats():
    global success_count, failure_count, tag_message_counts, failed_tags
    global downstairs_success_count, downstairs_failure_count
    global mezzanine_success_count, mezzanine_failure_count
    global current_run, tags_published_in_current_run
    
    total = success_count + failure_count
    call_counts = tag_message_counts.values()
    max_calls = max(call_counts)
    min_calls = min(call_counts)
    avg_calls = sum(call_counts) / len(call_counts)
    
    # Calculate runtime
    end_time = time.time()
    runtime_seconds = end_time - start_time
    runtime_minutes = runtime_seconds / 60

    #generate non-pinged tags
    non_pinged: List[str] = []
    for tag_id in tag_message_counts.keys():
        if tag_message_counts[tag_id] == 0:
            non_pinged.append(tag_id)

    
    if total > 0:
        success_rate = success_count / total * 100
        
        # Calculate separate floor stats
        downstairs_total = downstairs_success_count + downstairs_failure_count
        downstairs_rate = (downstairs_success_count / downstairs_total * 100) if downstairs_total > 0 else 0
        
        mezzanine_total = mezzanine_success_count + mezzanine_failure_count
        mezzanine_rate = (mezzanine_success_count / mezzanine_total * 100) if mezzanine_total > 0 else 0

        #key info
        print(f"\n{'='*50}")
        print(f"FINAL RESULTS:")
        print(f"Runtime: {runtime_minutes:.2f} minutes ({runtime_seconds:.1f} seconds)")
        print(f"Runs completed: {current_run}/{TOTAL_RUNS}")
        print(f"Expected messages per tag: {TOTAL_RUNS} (one per run)")
        print(f"Total unique messages processed: {total} (from {EXPECTED_UNIQUE_TAGS_PER_RUN} unique tags)")
        print(f"Overall success rate: {success_rate:.2f}%")
        print(f"🏢 Downstairs success rate: {downstairs_rate:.2f}% ({downstairs_success_count}/{downstairs_total})")
        print(f"🏗️  Mezzanine success rate: {mezzanine_rate:.2f}% ({mezzanine_success_count}/{mezzanine_total})")

        #debuggers
        print(f"\n{'='*50}")
        print(f"Average tag message amt: {avg_calls}")
        print(f"Tag most messages amt: {max_calls}")
        print(f"Tag least messages amt: {min_calls}")
        print(f"Non pinged tags: {non_pinged}")
        print(f"{'='*50}")
        
        # Display failed tags analysis
        if failed_tags:
            print(f"\n❌ FAILED TAGS ANALYSIS:")
            print(f"{'='*50}")
            
            # Sort failed tags by failure count (highest first)
            sorted_failed_tags = sorted(failed_tags.items(), key=lambda x: x[1], reverse=True)
            
            downstairs_failed = []
            mezzanine_failed = []
            
            for tag_id, failure_count in sorted_failed_tags:
                expected_map_id = TAG_POSITION_DICT.get(tag_id, "UNKNOWN")
                floor_name = "Downstairs" if expected_map_id == DOWNSTAIRS_MAP_ID else "Mezzanine"
                tag_mac = tag_id_to_mac.get(tag_id, "UNKNOWN_MAC")
                
                if expected_map_id == DOWNSTAIRS_MAP_ID:
                    downstairs_failed.append((tag_mac, failure_count))
                elif expected_map_id == MEZZANINE_MAP_ID:
                    mezzanine_failed.append((tag_mac, failure_count))
                
                print(f"  Tag {tag_id} ({tag_mac}): {failure_count} failures | Floor: {floor_name}")
            
            print(f"\n📊 FAILURE BREAKDOWN:")
            print(f"  Downstairs failed tags: {len(downstairs_failed)}")
            print(f"  Mezzanine failed tags: {len(mezzanine_failed)}")
            
            if downstairs_failed:
                print(f"\n🏢 Downstairs Failed Tags:")
                for tag_mac, count in downstairs_failed:
                    print(f"    {tag_mac}: {count} failures")
            
            if mezzanine_failed:
                print(f"\n🏗️  Mezzanine Failed Tags:")
                for tag_mac, count in mezzanine_failed:
                    print(f"    {tag_mac}: {count} failures")
        else:
            print(f"\n✅ No failed tags detected!")
        
        # Generate spatial visualization
        print(f"\n🗺️  Generating spatial distribution visualization...")
        create_spatial_visualization()
        
    else:
        print("No messages were processed.")


def make_api_request():
    """Make the API POST request to trigger tag broadcasting"""
    try:
        response = requests.post(url, headers=headers, json=payload, verify=False)
        print(f"🔄 API Request - Status: {response.status_code}")
        if response.status_code == 201:
            print("✅ API Request successful - Tags should start broadcasting")
        else:
            print(f"⚠️  API Response: {response.text}")
        return response.status_code == 201
    except requests.exceptions.RequestException as e:
        print(f"❌ API Request failed: {e}")
        return False

def runner():
    global start_time
    
    # Track when we last made an API request
    last_api_request = 0
    api_interval = 100  # Make API request every 80 seconds (timeout is 90s, so slight overlap)
    
    client = mqtt.Client(protocol=mqtt.MQTTv311)   
    client.enable_logger()                         
    client.on_connect   = on_connect
    client.on_subscribe = on_subscribe
    client.on_message   = on_message

    try:
        # Make initial API request
        print("🚀 Making initial API request...")
        make_api_request()
        last_api_request = time.time()
        
        # Connect to MQTT
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        
        # Start the loop with periodic API requests
        print("🔄 Starting MQTT loop with periodic API requests...")
        while True:
            # Check if we need to make another API request
            current_time = time.time()
            if current_time - last_api_request >= api_interval:
                print(f"⏰ {api_interval}s elapsed, making another API request...")
                make_api_request()
                last_api_request = current_time
            
            # Process MQTT messages for a short time
            client.loop(timeout=1.0)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
        client.disconnect()
        print_final_stats()
    except Exception as e:
        print(f"❌ Connection error: {e}")
        client.disconnect()
        print_final_stats()
    
if __name__ == "__main__":
    runner()
