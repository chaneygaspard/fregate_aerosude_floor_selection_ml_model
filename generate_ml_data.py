from typing import Dict, Any, List, Set
import logging, paho.mqtt.client as mqtt
import time, requests, json, csv, os, math
from statistics import mean, stdev, median

# Configuration
BROKER_HOST = ""  # MQTT broker address (redacted)
BROKER_PORT = 0  # MQTT broker port (redacted)
TOPIC = "engine/+/positions"
OUTPUT_DIR = "ml_training_data_new"

# API configuration
url = ""  # API endpoint (redacted)
headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}

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

def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate Euclidean distance between two points"""
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def get_all_anchor_macs() -> Set[str]:
    """Get all unique anchor MACs from the existing CSV files to ensure compatibility"""
    anchor_macs = set()
    
    # Read one of the existing CSV files to extract anchor MACs from the header
    try:
        sample_file = "ml_training_data/c0a9266bb706.csv"
        with open(sample_file, 'r') as f:
            header = f.readline().strip().split(',')
            
        # Extract anchor MACs from column names (columns ending with _rssi)
        for col in header:
            if col.endswith('_rssi'):
                anchor_mac = col[:-5]  # Remove '_rssi' suffix
                if len(anchor_mac) == 12:  # Valid MAC address length
                    anchor_macs.add(anchor_mac)
                    
    except FileNotFoundError:
        print("Warning: Could not find sample CSV file to extract anchor MACs")
        
    return anchor_macs

def generate_csv_header(anchor_macs: Set[str]) -> List[str]:
    """Generate the CSV header based on the same format as existing files"""
    header = [
        "map_id", "position_timestamp", "tag_x", "tag_y", 
        "cov_xx", "cov_xy", "cov_yx", "cov_yy", "true_map_id"
    ]
    
    # Add per-map statistics columns
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
    
    # Add per-anchor columns (sorted for consistency)
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
    print(f"🔧 CSV header has {len(header)} columns")
    
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
        
        # Collect all anchors (used + unused)
        all_anchors = {}
        
        # Process used anchors
        for anchor in pos.get("used_anchors", []):
            anchor_mac = anchor["mac"]
            # Some used anchors may not have x,y coordinates
            if "x" in anchor and "y" in anchor:
                distance = calculate_distance(tag_x, tag_y, anchor["x"], anchor["y"])
                anchor_x = anchor["x"]
                anchor_y = anchor["y"]
            else:
                # Use cart_d if available, otherwise 0
                distance = anchor.get("cart_d", 0)
                anchor_x = 0
                anchor_y = 0
                
            all_anchors[anchor_mac] = {
                "rssi": anchor["rssi"],
                "used": 1,
                "x": anchor_x,
                "y": anchor_y, 
                "map_id": anchor["map_id"],
                "distance": distance,
                "signal_quality": anchor.get("signal_quality", "")
            }
            
        # Process unused anchors
        for anchor in pos.get("unused_anchors", []):
            anchor_mac = anchor["mac"]
            distance = anchor.get("cart_d", 0)  # Distance already calculated
            all_anchors[anchor_mac] = {
                "rssi": anchor["rssi"],
                "used": 0,
                "x": anchor.get("x", 0),
                "y": anchor.get("y", 0),
                "map_id": anchor["map_id"], 
                "distance": distance,
                "signal_quality": ""
            }
        
        # Calculate per-map statistics
        map_stats = {}
        for mid in MAP_IDS:
            anchors_for_map = [a for a in all_anchors.values() if a["map_id"] == mid]
            
            if anchors_for_map:
                rssi_values = [a["rssi"] for a in anchors_for_map]
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
        
        # Add per-anchor data (in sorted order)
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
                # Empty values for anchors not present
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

def on_connect(client, userdata, flags, rc, properties=None):
    print("🔌 on_connect rc =", rc)
    if rc == 0:
        client.subscribe(TOPIC)
    else:
        print("❌ Connect failed")

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
    print(f"📈 PERIODIC STATS REPORT (Runtime: {runtime_minutes:.1f} minutes)")
    print(f"{'='*60}")
    print(f"Total messages processed: {message_count}")
    
    if message_count > 0:
        msg_per_minute = message_count / runtime_minutes if runtime_minutes > 0 else 0
        print(f"Average rate: {msg_per_minute:.1f} messages/minute")
        
        # Tag-specific stats
        active_tags = [tag for tag, count in tag_message_counts.items() if count > 0]
        print(f"Active tags: {len(active_tags)}/{len(tag_message_counts)}")
        
        if active_tags:
            active_counts = [count for count in tag_message_counts.values() if count > 0]
            max_count = max(active_counts)
            min_count = min(active_counts)
            avg_count = sum(tag_message_counts.values()) / len(active_tags)
            median_count = median(active_counts)
            
            print(f"Messages per tag - Max: {max_count}, Min: {min_count}, Avg: {avg_count:.1f}, Median: {median_count:.1f}")
            
            # Show top 5 most active tags
            top_tags = sorted(tag_message_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"Top 5 most active tags: {', '.join([f'{tag[:6]}:{count}' for tag, count in top_tags])}")
            
            # Show top 5 least active tags (among active tags)
            least_active_tags = sorted(tag_message_counts.items(), key=lambda x: x[1])[:5]
            least_active_tags = [(tag, count) for tag, count in least_active_tags if count > 0][:5]
            if least_active_tags:
                print(f"Top 5 least active tags: {', '.join([f'{tag[:6]}:{count}' for tag, count in least_active_tags])}")
        
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
    last_stats_print = current_time

def cleanup_files():
    """Close all CSV files"""
    for file_handle in csv_files.values():
        file_handle.close()
    
    # Final statistics
    print(f"\n{'='*60}")
    print(f"📁 FINAL CLEANUP REPORT")
    print(f"{'='*60}")
    print(f"Total messages processed: {message_count}")
    print(f"CSV files closed: {len(csv_files)}")
    
    # Count lines in each file
    try:
        total_lines = 0
        for tag_mac in csv_files.keys():
            filepath = os.path.join(OUTPUT_DIR, f"{tag_mac}.csv")
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    lines = sum(1 for _ in f) - 1  # Subtract header
                total_lines += lines
                if lines > 0:
                    print(f"  {tag_mac}.csv: {lines} data rows")
        
        print(f"Total data rows written: {total_lines}")
    except Exception as e:
        print(f"Could not count file lines: {e}")
    
    print(f"{'='*60}")

def runner():
    global start_time
    
    print("🚀 Starting ML data generation...")
    
    # Get anchor MACs from existing data
    anchor_macs = get_all_anchor_macs()
    print(f"📡 Found {len(anchor_macs)} anchor MACs from existing data")
    
    # Setup CSV files
    setup_csv_files(anchor_macs)
    
    # Track when we last made an API request
    last_api_request = 0
    api_interval = 100  # Make API request every 100 seconds
    
    client = mqtt.Client(protocol=mqtt.MQTTv311)
    client.enable_logger()
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    client.user_data_set({"anchor_macs": anchor_macs})
    
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
            current_time = time.time()
            
            # Check if we need to make another API request
            if current_time - last_api_request >= api_interval:
                print(f"⏰ {api_interval}s elapsed, making another API request...")
                make_api_request()
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