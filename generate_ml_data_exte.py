#!/usr/bin/env python3
"""
Extended ML Training Data Generation Script
Generates comprehensive RTLS positioning data with ~240 anchor MACs
Self-contained script that uses existing extended format files for anchor database
Includes detailed per-anchor information and appends to existing files
"""

from typing import Dict, Any, List, Set
import logging, paho.mqtt.client as mqtt
import time, requests, json, csv, os, math
from statistics import mean, stdev, median
import pandas as pd
import sys

#csv config
MAX_LINES: int = 8500

# Configuration - Updated for SSH tunnels
BROKER_HOST = ""  # MQTT broker address (redacted)
BROKER_PORTS = [0]  # MQTT broker ports (redacted)
TOPIC = "engine/+/positions"
OUTPUT_DIR = "ml_training_data_exte_new"

# API configuration - Use working tunneled endpoint
API_URLS = [
    ""  # API endpoint (redacted)
]
headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}

# Use the same 60 tags as in ml_training_data_new
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

# TAG_MAC_TO_MAP_ID for determining true_map_id
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

# Map IDs
MAP_IDS = ["682c66de8cde618ce1270230", "682c66f08cde618ce127025e"]

# Global variables
start_time = time.time()
message_count = 0
csv_writers = {}
csv_files = {}
tag_message_counts = {}  # Track messages per tag
last_stats_print = time.time()

# Global anchor database
ANCHOR_DATABASE: Dict[str, Dict[str, Any]] = {}

def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate Euclidean distance between two points"""
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def check_tunnel_connections():
    """Check if SSH tunnels are active and accessible"""
    import socket
    
    print("🔍 Checking SSH tunnel connections...")
    
    # Check API tunnels
    api_ports = [0]  # API tunnel ports (redacted)
    active_api_ports = []
    for port in api_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                print(f"✅ API tunnel (port {port}) is active")
                active_api_ports.append(port)
            else:
                print(f"❌ API tunnel (port {port}) is not accessible")
        except Exception as e:
            print(f"❌ Error checking API tunnel port {port}: {e}")
    
    # Check MQTT tunnels
    mqtt_ports = [0]  # MQTT tunnel ports (redacted)
    active_mqtt_ports = []
    for port in mqtt_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                print(f"✅ MQTT tunnel (port {port}) is active")
                active_mqtt_ports.append(port)
            else:
                print(f"❌ MQTT tunnel (port {port}) is not accessible")
        except Exception as e:
            print(f"❌ Error checking MQTT tunnel port {port}: {e}")
    
    if not active_api_ports:
        print("💡 Start API tunnels with: ./start_tunnels.sh")
    if not active_mqtt_ports:
        print("💡 Start MQTT tunnels with: ./start_tunnels.sh")
    
    print()
    return active_api_ports, active_mqtt_ports

def build_anchor_database() -> Dict[str, Dict[str, Any]]:
    """Build comprehensive anchor database from existing CSV files in ml_training_data_exte_new/"""
    anchor_db = {}
    
    import glob
    exte_csv_files = glob.glob(f"{OUTPUT_DIR}/*.csv")
    
    if not exte_csv_files:
        print("❌ No CSV files found in ml_training_data_exte_new/ directory")
        return anchor_db
    
    print(f"🏗️  Building anchor database from {len(exte_csv_files)} existing extended files...")
    
    # Process multiple files to get comprehensive anchor data
    for i, csv_file in enumerate(exte_csv_files[:10]):  # Process first 10 files for good coverage
        try:
            print(f"  📖 Reading {os.path.basename(csv_file)} ({i+1}/10)...")
            
            # Read first few rows to get anchor data
            df = pd.read_csv(csv_file, nrows=5)
            
            # Extract anchor data from columns
            for col in df.columns:
                if col.endswith('_x'):
                    anchor_mac = col[:-2]  # Remove '_x' suffix
                    
                    # Check if we have all required columns for this anchor
                    required_cols = [f"{anchor_mac}_x", f"{anchor_mac}_y", f"{anchor_mac}_map_id"]
                    if all(col in df.columns for col in required_cols):
                        
                        # Get anchor data from first non-empty row
                        for _, row in df.iterrows():
                            x_val = row[f"{anchor_mac}_x"]
                            y_val = row[f"{anchor_mac}_y"] 
                            map_id_val = row[f"{anchor_mac}_map_id"]
                            
                            # Only use if we have valid position data
                            if pd.notna(x_val) and pd.notna(y_val) and x_val != "" and y_val != "":
                                anchor_db[anchor_mac] = {
                                    "x": float(x_val),
                                    "y": float(y_val),
                                    "map_id": str(map_id_val) if pd.notna(map_id_val) else ""
                                }
                                break
                        
        except Exception as e:
            print(f"Warning: Could not process {csv_file}: {e}")
            continue
    
    print(f"🎯 Built anchor database with {len(anchor_db)} anchors")
    
    # Show sample of anchors
    sample_anchors = list(anchor_db.items())[:3]
    for anchor_mac, data in sample_anchors:
        print(f"   📍 {anchor_mac}: ({data['x']:.1f}, {data['y']:.1f}) on map {data['map_id']}")
    
    return anchor_db

def get_all_anchor_macs() -> Set[str]:
    """Get all unique anchor MACs from the existing CSV files in ml_training_data_exte_new/"""
    anchor_macs = set()
    
    # Read from existing files in ml_training_data_exte_new to get comprehensive anchor list
    import glob
    exte_csv_files = glob.glob(f"{OUTPUT_DIR}/*.csv")
    
    if not exte_csv_files:
        print("❌ No CSV files found in ml_training_data_exte_new/ directory")
        return anchor_macs
    
    print(f"📡 Scanning {len(exte_csv_files)} files in ml_training_data_exte_new/ for anchor MACs...")
    
    # Read headers from existing files to get all possible anchor MACs
    for csv_file in exte_csv_files[:5]:  # Sample first 5 files to get anchor list
        try:
            with open(csv_file, 'r') as f:
                header = f.readline().strip().split(',')
                
            # Extract anchor MACs from column names (columns ending with _rssi)
            for col in header:
                if col.endswith('_rssi'):
                    anchor_mac = col[:-5]  # Remove '_rssi' suffix
                    if len(anchor_mac) == 12:  # Valid MAC address length
                        anchor_macs.add(anchor_mac)
                        
        except Exception as e:
            print(f"Warning: Could not read {csv_file}: {e}")
            continue
    
    print(f"📡 Found {len(anchor_macs)} unique anchor MACs from extended data format")
    return anchor_macs

def generate_csv_header(anchor_macs: Set[str]) -> List[str]:
    """Generate the CSV header matching the exact format of ml_training_data/"""
    header = [
        "map_id", "position_timestamp", "tag_x", "tag_y", 
        "cov_xx", "cov_xy", "cov_yx", "cov_yy", "true_map_id"
    ]
    
    # Add per-map statistics columns (same as old format)
    for map_id in MAP_IDS:
        header.extend([
            f"{map_id}_total_anchors",
            f"{map_id}_anchors_used", 
            f"{map_id}_anchors_hearing",
            f"{map_id}_avg_rssi",
            f"{map_id}_max_rssi",
            f"{map_id}_min_rssi", 
            f"{map_id}_rssi_std",
            f"{map_id}_rssi_range"
        ])
    
    # Add per-anchor columns (sorted for consistency) - matching old format exactly
    for anchor_mac in sorted(anchor_macs):
        header.extend([
            f"{anchor_mac}_rssi",
            f"{anchor_mac}_used",
            f"{anchor_mac}_x", 
            f"{anchor_mac}_y",
            f"{anchor_mac}_map_id",
            f"{anchor_mac}_distance",
            f"{anchor_mac}_signal_quality"
        ])
    
    return header

def setup_csv_files(anchor_macs: Set[str]):
    """Initialize CSV files for each tag MAC"""
    global csv_writers, csv_files, tag_message_counts
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    header = generate_csv_header(anchor_macs)
    print(f"🔧 Extended CSV header has {len(header)} columns (matching old format)")
    
    for tag_mac in TAG_MAC_TO_MAP_ID.keys():
        filename = os.path.join(OUTPUT_DIR, f"{tag_mac}.csv")
        
        # Check if file exists and is non-empty
        file_exists = os.path.exists(filename)
        write_header = True
        existing_rows = 0
        
        if file_exists:
            try:
                with open(filename, 'r') as check_file:
                    existing_rows = sum(1 for _ in check_file)
                    write_header = existing_rows == 0  # Only write header if file is empty
            except:
                write_header = True  # If error reading, assume we need header
        
        # Open in append mode
        file_handle = open(filename, 'a', newline='')
        writer = csv.writer(file_handle)
        
        # Only write header if file is new or empty
        if write_header:
            writer.writerow(header)
        
        csv_files[tag_mac] = file_handle
        csv_writers[tag_mac] = writer
        tag_message_counts[tag_mac] = existing_rows - 1 if existing_rows > 0 else 0  # Account for header
        
    new_files = sum(1 for tag_mac in TAG_MAC_TO_MAP_ID.keys() 
                    if not os.path.exists(os.path.join(OUTPUT_DIR, f"{tag_mac}.csv")) 
                    or os.path.getsize(os.path.join(OUTPUT_DIR, f"{tag_mac}.csv")) == 0)
    existing_files = len(TAG_MAC_TO_MAP_ID) - new_files
    
    print(f"✅ Setup complete: {new_files} new CSV files, {existing_files} existing files (appending)")
    print(f"📁 All files in {OUTPUT_DIR}/")
    print(f"📋 Sample file names: {list(TAG_MAC_TO_MAP_ID.keys())[:3]}.csv, ...")

def process_position_message(position_data: Dict[str, Any], anchor_macs: Set[str]):
    """Process a single position message and write to appropriate CSV"""
    global message_count, tag_message_counts
    
    try:
        tag_mac = position_data["tag"]["mac"]
        
        # Only process if it's one of our 60 tags
        if tag_mac not in TAG_MAC_TO_MAP_ID:
            return
        
        # Check if this tag has reached the maximum row limit
        if tag_message_counts[tag_mac] >= MAX_LINES:
            # Skip processing for this tag to allow others to catch up
            #if tag_message_counts[tag_mac] == MAX_LINES:
                #print(f"⏸️  Tag {tag_mac[:6]}... reached maximum {MAX_LINES} rows - pausing to balance dataset")
            return
            
        message_count += 1
        tag_message_counts[tag_mac] += 1
        
        # Extract basic position data
        location = position_data["location"]
        map_id = location["map_id"]
        timestamp = position_data["timestamp"]
        pos = location["position"]
        tag_x = pos["x"]
        tag_y = pos["y"]
        
        # Extract covariance matrix
        cov = pos["covariance"]
        cov_xx = cov[0][0]
        cov_xy = cov[0][1] 
        cov_yx = cov[1][0]
        cov_yy = cov[1][1]
        
        true_map_id = TAG_MAC_TO_MAP_ID[tag_mac]
        
        # Collect all anchors (used + unused) - following new MQTT format
        all_anchors = {}
        
        # Process used anchors
        for anchor in pos.get("used_anchors", []):
            anchor_mac = anchor["mac"]
            distance = anchor.get("cart_d", 0)
            
            # Get x,y from MQTT if available, otherwise use database
            anchor_x = anchor.get("x", None)
            anchor_y = anchor.get("y", None)
            anchor_map_id = anchor.get("map_id", "")
            
            # If MQTT doesn't have position, use database
            if (anchor_x is None or anchor_x == 0) and anchor_mac in ANCHOR_DATABASE:
                db_data = ANCHOR_DATABASE[anchor_mac]
                anchor_x = db_data["x"]
                anchor_y = db_data["y"]
                if not anchor_map_id:
                    anchor_map_id = db_data["map_id"]
            
            all_anchors[anchor_mac] = {
                "rssi": anchor.get("rssi", ""),  # Handle missing RSSI
                "used": 1,
                "x": anchor_x if anchor_x is not None else 0,
                "y": anchor_y if anchor_y is not None else 0,
                "map_id": anchor_map_id,
                "distance": distance,
                "signal_quality": anchor.get("signal_quality", "")
            }
            
        # Process unused anchors
        for anchor in pos.get("unused_anchors", []):
            anchor_mac = anchor["mac"]
            distance = anchor.get("cart_d", 0)
            
            # Get x,y from MQTT if available, otherwise use database
            anchor_x = anchor.get("x", None)
            anchor_y = anchor.get("y", None)
            anchor_map_id = anchor.get("map_id", "")
            
            # If MQTT doesn't have position, use database
            if (anchor_x is None or anchor_x == 0) and anchor_mac in ANCHOR_DATABASE:
                db_data = ANCHOR_DATABASE[anchor_mac]
                anchor_x = db_data["x"]
                anchor_y = db_data["y"]
                if not anchor_map_id:
                    anchor_map_id = db_data["map_id"]
            
            all_anchors[anchor_mac] = {
                "rssi": anchor.get("rssi", ""),  # Handle missing RSSI
                "used": 0,
                "x": anchor_x if anchor_x is not None else 0,
                "y": anchor_y if anchor_y is not None else 0,
                "map_id": anchor_map_id, 
                "distance": distance,
                "signal_quality": ""
            }
        
        # Calculate per-map statistics
        map_stats = {}
        for mid in MAP_IDS:
            anchors_for_map = [a for a in all_anchors.values() if a["map_id"] == mid]
            
            if anchors_for_map:
                # Filter out empty RSSI values for statistics
                rssi_values = [a["rssi"] for a in anchors_for_map if a["rssi"] != ""]
                
                if rssi_values:
                    map_stats[mid] = {
                        "total_anchors": len(anchors_for_map),
                        "anchors_used": sum(1 for a in anchors_for_map if a["used"] == 1),
                        "anchors_hearing": len(anchors_for_map),
                        "avg_rssi": mean(rssi_values),
                        "max_rssi": max(rssi_values),
                        "min_rssi": min(rssi_values),
                        "rssi_std": stdev(rssi_values) if len(rssi_values) > 1 else 0,
                        "rssi_range": max(rssi_values) - min(rssi_values)
                    }
                else:
                    # No valid RSSI values
                    map_stats[mid] = {
                        "total_anchors": len(anchors_for_map),
                        "anchors_used": sum(1 for a in anchors_for_map if a["used"] == 1),
                        "anchors_hearing": len(anchors_for_map),
                        "avg_rssi": "",
                        "max_rssi": "",
                        "min_rssi": "",
                        "rssi_std": "",
                        "rssi_range": ""
                    }
            else:
                map_stats[mid] = {
                    "total_anchors": 0,
                    "anchors_used": 0, 
                    "anchors_hearing": 0,
                    "avg_rssi": "",
                    "max_rssi": "",
                    "min_rssi": "",
                    "rssi_std": "",
                    "rssi_range": ""
                }
        
        # Build CSV row
        row = [
            map_id, timestamp, tag_x, tag_y,
            cov_xx, cov_xy, cov_yx, cov_yy, true_map_id
        ]
        
        # Add per-map statistics
        for mid in MAP_IDS:
            stats = map_stats[mid]
            row.extend([
                stats["total_anchors"],
                stats["anchors_used"],
                stats["anchors_hearing"], 
                stats["avg_rssi"],
                stats["max_rssi"],
                stats["min_rssi"],
                stats["rssi_std"],
                stats["rssi_range"]
            ])
        
        # Add per-anchor data (in sorted order) - ALL ~240 anchors
        for anchor_mac in sorted(anchor_macs):
            if anchor_mac in all_anchors:
                anchor = all_anchors[anchor_mac]
                row.extend([
                    anchor["rssi"],
                    anchor["used"],
                    anchor["x"],
                    anchor["y"],
                    anchor["map_id"],
                    anchor["distance"],
                    anchor["signal_quality"]
                ])
            else:
                # For anchors not present: get position from database, leave RSSI and signal_quality empty
                if anchor_mac in ANCHOR_DATABASE:
                    db_anchor = ANCHOR_DATABASE[anchor_mac]
                    row.extend([
                        "",  # rssi - empty
                        0,   # used - not used
                        db_anchor["x"],  # actual x position from database
                        db_anchor["y"],  # actual y position from database  
                        db_anchor["map_id"],  # actual map_id from database
                        0,   # distance - not calculated for unused anchors
                        ""   # signal_quality - empty
                    ])
                else:
                    # Anchor not in database either - use empty values
                    row.extend(["", 0, "", "", "", "", ""])
        
        # Write to appropriate CSV file
        csv_writers[tag_mac].writerow(row)
        csv_files[tag_mac].flush()  # Ensure data is written
        
        # Debug output for first few messages of each tag
        if tag_message_counts[tag_mac] <= 3:
            print(f"🔍 Tag {tag_mac}: Message #{tag_message_counts[tag_mac]} - Map: {map_id}, Pos: ({tag_x:.1f}, {tag_y:.1f}), Anchors: {len(all_anchors)}")
        
        if message_count % 50 == 0:
            print(f"📊 Processed {message_count} position messages total")
            
    except Exception as e:
        print(f"❌ Error processing message for tag {tag_mac if 'tag_mac' in locals() else 'unknown'}: {e}")
        import traceback
        traceback.print_exc()

def make_api_request():
    """Make the API POST request to trigger tag broadcasting via SSH tunnel"""
    import ssl
    import urllib3
    
    # Disable SSL warnings for tunneled connection
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Try each API URL
    for url_idx, url in enumerate(API_URLS, 1):
        print(f"🔄 Trying API URL {url_idx}/{len(API_URLS)}: {url}")
        
        # For SSH tunneled connections, we need to be more careful with SSL
        approaches = [
            {"verify": False, "timeout": 30},
            {"verify": False, "timeout": 60, "allow_redirects": True},
            {"verify": False, "timeout": 10, "stream": False}
        ]
        
        for i, config in enumerate(approaches, 1):
            try:
                print(f"🔄 API Request attempt {i}/{len(approaches)} for URL {url_idx}...")
                
                response = requests.post(
                    url, 
                    headers=headers, 
                    json=payload, 
                    **config
                )
                
                print(f"🔄 API Request - Status: {response.status_code}")
                if response.status_code == 201:
                    print("✅ API Request successful - Tags should start broadcasting")
                    return True
                else:
                    print(f"⚠️  API Response: {response.text}")
                    if i < len(approaches):
                        print("💡 Trying next approach...")
                        continue
                    # Try next URL
                    break
                    
            except requests.exceptions.SSLError as e:
                print(f"❌ SSL Error (URL {url_idx}, attempt {i}): {e}")
                if i < len(approaches):
                    print("💡 Trying next approach...")
                    continue
                # Try next URL
                break
            except requests.exceptions.ConnectionError as e:
                print(f"❌ Connection Error (URL {url_idx}, attempt {i}): {e}")
                if i < len(approaches):
                    print("💡 Trying next approach...")
                    continue
                # Try next URL
                break
            except requests.exceptions.RequestException as e:
                print(f"❌ API Request failed (URL {url_idx}, attempt {i}): {e}")
                if i < len(approaches):
                    print("💡 Trying next approach...")
                    continue
                # Try next URL
                break
        
        if url_idx < len(API_URLS):
            print("💡 Trying next API URL...")
    
    print("❌ All API request attempts failed")
    print("💡 Start tunnels with: ./start_tunnels.sh")
    return False

def on_connect(client, userdata, flags, rc, properties=None):
    print("🔌 on_connect rc =", rc)
    if rc == 0:
        client.subscribe(TOPIC)
        print("✅ MQTT connected via SSH tunnel")
    else:
        print("❌ MQTT Connect failed")
        print("💡 Make sure SSH tunnel is active (redacted)")

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("✅ Subscribed, waiting for messages…")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8", errors="replace")
        position_data = json.loads(payload)
        process_position_message(position_data, userdata["anchor_macs"])
    except (json.JSONDecodeError, KeyError) as e:
        print(f"❌ Error parsing message: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def print_periodic_stats():
    """Print detailed statistics every few minutes"""
    global last_stats_print
    
    current_time = time.time()
    runtime_minutes = (current_time - start_time) / 60
    
    print(f"\n{'='*60}")
    print(f"📈 EXTENDED PERIODIC STATS REPORT (Runtime: {runtime_minutes:.1f} minutes)")
    print(f"{'='*60}")
    print(f"Total messages processed: {message_count}")
    
    if message_count > 0:
        msg_per_minute = message_count / runtime_minutes if runtime_minutes > 0 else 0
        print(f"Average rate: {msg_per_minute:.1f} messages/minute")
        
        # Tag-specific stats
        active_tags = [tag for tag, count in tag_message_counts.items() if count > 0]
        capped_tags = [tag for tag, count in tag_message_counts.items() if count >= MAX_LINES]
        print(f"Active tags: {len(active_tags)}/{len(tag_message_counts)} | Capped tags: {len(capped_tags)}/{len(tag_message_counts)}")
        
        if active_tags:
            active_counts = [count for count in tag_message_counts.values() if count > 0]
            max_count = max(active_counts)
            min_count = min(active_counts)
            avg_count = sum(tag_message_counts.values()) / len(active_tags)
            median_count = median(active_counts)
            
            print(f"Messages per tag - Max: {max_count}, Min: {min_count}, Avg: {avg_count:.1f}, Median: {median_count:.1f}")
            print(f"Dataset balance - Cap: {MAX_LINES}, Progress: {(len(capped_tags)/len(tag_message_counts)*100):.1f}% complete")
            
            # Show top 5 most active tags
            top_tags = sorted(tag_message_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"Top 5 most active tags: {', '.join([f'{tag[:6]}:{count}' for tag, count in top_tags])}")
            
            # Show top 5 least active tags (among active tags)
            least_active_tags = sorted(tag_message_counts.items(), key=lambda x: x[1])[:5]
            least_active_tags = [(tag, count) for tag, count in least_active_tags if count > 0][:5]
            if least_active_tags:
                print(f"Top 5 least active tags: {', '.join([f'{tag[:6]}:{count}' for tag, count in least_active_tags])}")
            
            # Check if all tags have reached the cap
            if len(capped_tags) == len(tag_message_counts):
                print("🎯 ALL TAGS HAVE REACHED THE CAP - Dataset is fully balanced!")
                print("   Consider stopping data collection or increasing MAX_LINES if more data is needed.")
        
        # File size check
        try:
            total_size = 0
            for tag_mac in csv_files.keys():
                filepath = os.path.join(OUTPUT_DIR, f"{tag_mac}.csv")
                if os.path.exists(filepath):
                    size = os.path.getsize(filepath)
                    total_size += size
            
            total_size_mb = total_size / (1024 * 1024)
            print(f"Total data written: {total_size_mb:.1f} MB")
        except Exception as e:
            print(f"Could not calculate file sizes: {e}")
    
    print(f"{'='*60}\n")
    
    # Visualization generation removed
    
    last_stats_print = current_time

def cleanup_files():
    """Close all CSV files"""
    for file_handle in csv_files.values():
        file_handle.close()
    
    # Final statistics
    print(f"\n{'='*60}")
    print(f"📁 EXTENDED FINAL CLEANUP REPORT")
    print(f"{'='*60}")
    print(f"Total messages processed: {message_count}")
    print(f"CSV files closed: {len(csv_files)}")
    
    # Count lines in each file and show balance status
    try:
        total_lines = 0
        capped_tags = 0
        tag_counts = []
        
        for tag_mac in csv_files.keys():
            filepath = os.path.join(OUTPUT_DIR, f"{tag_mac}.csv")
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    lines = sum(1 for _ in f) - 1  # Subtract header
                total_lines += lines
                tag_counts.append(lines)
                if lines >= MAX_LINES:
                    capped_tags += 1
                if lines > 0:
                    print(f"  {tag_mac}.csv: {lines} data rows")
        
        print(f"Total data rows written: {total_lines}")
        
        # Show final balance statistics
        if tag_counts:
            print(f"\n📊 FINAL DATASET BALANCE:")
            print(f"   Max lines per tag: {max(tag_counts)}")
            print(f"   Min lines per tag: {min(tag_counts)}")
            print(f"   Average lines per tag: {sum(tag_counts)/len(tag_counts):.1f}")
            print(f"   Tags at cap ({MAX_LINES}): {capped_tags}/{len(tag_counts)} ({capped_tags/len(tag_counts)*100:.1f}%)")
            
            balance_ratio = min(tag_counts) / max(tag_counts) if max(tag_counts) > 0 else 0
            print(f"   Balance ratio (min/max): {balance_ratio:.3f} {'✅ Excellent' if balance_ratio > 0.8 else '⚠️ Needs improvement' if balance_ratio > 0.5 else '❌ Poor'}")
            
    except Exception as e:
        print(f"Could not count file lines: {e}")
    
    # Final visualization generation removed
    
    print(f"{'='*60}")

def runner():
    global start_time, ANCHOR_DATABASE
    
    print("🚀 Starting Extended ML data generation...")
    print("📊 Using existing extended format with all anchor MACs")
    
    # Check SSH tunnel connections first
    active_api_ports, active_mqtt_ports = check_tunnel_connections()
    
    if not active_mqtt_ports:
        print("❌ No MQTT tunnels are active. Cannot proceed.")
        print("💡 Start tunnels with: ./start_tunnels.sh")
        return
    
    # Get anchor MACs from existing extended data or create basic set
    anchor_macs = get_all_anchor_macs()
    if not anchor_macs:
        print("⚠️  No existing files found. Creating basic anchor set for first run...")
        # Create a basic set of common anchor MACs for first run
        anchor_macs = set([
            "c32a723f0621", "e9548d1fa907", "f0294170f2dd", "c653bed3c63b",
            "eb20694cea84", "d5cf265b9ea7", "f82c16fc561d", "cae44fdd1e32"
        ])
        print(f"📡 Using {len(anchor_macs)} basic anchor MACs for first run")
    
    # Build anchor database from existing files (or start empty for first run)
    ANCHOR_DATABASE = build_anchor_database()
    if not ANCHOR_DATABASE:
        print("⚠️  Starting with empty anchor database. Will be populated as data arrives.")
        ANCHOR_DATABASE = {}
    
    print(f"📡 Using {len(anchor_macs)} anchor MACs for data generation")
    print(f"🎯 Anchor database contains {len(ANCHOR_DATABASE)} anchors with position data")
    
    # Setup CSV files
    setup_csv_files(anchor_macs)
    
    # Initial visualization generation removed
    
    # Track when we last made an API request
    last_api_request = 0
    api_interval = 100  # Make API request every 100 seconds
    api_failures = 0  # Track consecutive API failures
    max_api_failures = 5  # Stop trying after 5 consecutive failures
    
    # Try to connect to MQTT using available ports
    mqtt_connected = False
    for port in active_mqtt_ports:
        try:
            print(f"🔄 Trying MQTT connection on port {port}...")
            client = mqtt.Client(protocol=mqtt.MQTTv311)
            client.enable_logger()
            client.on_connect = on_connect
            client.on_subscribe = on_subscribe
            client.on_message = on_message
            client.user_data_set({"anchor_macs": anchor_macs})
            
            client.connect(BROKER_HOST, port, keepalive=60)
            mqtt_connected = True
            print(f"✅ MQTT connected on port {port}")
            break
        except Exception as e:
            print(f"❌ MQTT connection failed on port {port}: {e}")
            continue
    
    if not mqtt_connected:
        print("❌ Could not connect to MQTT on any available port")
        print("💡 Start tunnels with: ./start_tunnels.sh")
        return
    
    try:
        # Make initial API request
        print("🚀 Making initial API request...")
        if make_api_request():
            api_failures = 0  # Reset failure counter on success
        else:
            api_failures += 1
        last_api_request = time.time()
        
        # Start the loop with periodic API requests
        print("🔄 Starting MQTT loop with periodic API requests...")
        while True:
            current_time = time.time()
            
            # Check if we need to make another API request
            if current_time - last_api_request >= api_interval and api_failures < max_api_failures:
                print(f"⏰ {api_interval}s elapsed, making another API request...")
                if make_api_request():
                    api_failures = 0  # Reset failure counter on success
                    print("✅ API request successful - tags should be broadcasting")
                else:
                    api_failures += 1
                    print(f"❌ API request failed ({api_failures}/{max_api_failures} consecutive failures)")
                    if api_failures >= max_api_failures:
                        print("🛑 Too many API failures - continuing with MQTT only (tags may already be broadcasting)")
                last_api_request = current_time
            elif api_failures >= max_api_failures:
                # Still print periodic stats even if API is failing
                if current_time - last_api_request >= api_interval:
                    print(f"⏰ {api_interval}s elapsed, but API requests disabled due to failures")
                    last_api_request = current_time
            
            # Print periodic stats every 5 minutes
            if current_time - last_stats_print >= 300:  # 5 minutes
                print_periodic_stats()
            
            # Process MQTT messages for a short time
            client.loop(timeout=1.0)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
        client.disconnect()
        cleanup_files()
        
        # Print final stats
        end_time = time.time()
        runtime_minutes = (end_time - start_time) / 60
        print(f"⏱️  Runtime: {runtime_minutes:.2f} minutes")
        print(f"📊 Total messages processed: {message_count}")
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        client.disconnect()
        cleanup_files()

if __name__ == "__main__":
    runner() 