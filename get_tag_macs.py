from typing import Dict, Any, Tuple, List
import logging, paho.mqtt.client as mqtt
import time, urllib3, requests, json

"""
Anchor lists:
Tags downstairs: {62398, 33655, 34487, 27666, 42322, 16915, 45527, 21342, 37133, 4468, 54577, 15826, 47621, 43668, 19465, 42966, 4820, 62994, 24904, 28567, 34114, 13077, 1758, 44900, 28565, 25272, 49874, 18821, 23550, 59518}
Tags mezzanine: {53934, 48172, 52711, 24129, 13485, 28864, 1899, 58679, 47397, 32448, 60967, 65555, 64669, 28693, 28152, 35664, 62122, 55738, 20288, 22689, 6667, 59668, 47437, 64833, 52919, 2468, 38511, 63204, 62320, 34465}

Tag_mac_list: []

mezzanine map id: 682c66f08cde618ce127025e
downstairs map id: 682c66de8cde618ce1270230
"""

BROKER_HOST = ""  # MQTT broker address (redacted)
BROKER_PORT = 0  # MQTT broker port (redacted)
TOPIC        = "engine/+/positions"           # the same pattern you used in mosquitto_sub
MAX_MESSAGES_ACCEPTED: int = 1

# Counters for tracking success/failure
total_count: int = 0
tag_id_to_mac: Dict[str, str] = {}

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

all_tag_ids: List[str] = list(tag_message_counts.keys())


def get_key_info(position_data: Dict[str, Any]) -> Tuple[str, str]:
    tag_id: str = position_data["tag"]["id"]
    tag_mac: str = position_data["tag"]["mac"]
    return (tag_id, tag_mac)

def on_connect(client, userdata, flags, rc, properties=None):
    print("🔌 on_connect rc =", rc)          # 0 means OK
    if rc == 0:
        client.subscribe(TOPIC)
    else:
        print("❌ Connect failed")

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("✅ Subscribed, waiting for messages…")

def on_message(client, userdata, msg):
    global total_count, tag_message_counts, tag_id_to_mac, all_tag_ids
    
    try:
        payload = msg.payload.decode("utf-8", errors="replace")
        position_data = json.loads(payload)
        key_info = get_key_info(position_data)
        
        if key_info[0] in tag_message_counts.keys():
            if tag_message_counts[key_info[0]] < MAX_MESSAGES_ACCEPTED:
                tag_id, tag_mac = key_info
                total_count += 1
                print(f"{tag_id} : {tag_mac} | Num found: {total_count}")
                tag_message_counts[tag_id] += 1
                tag_id_to_mac[tag_id] = tag_mac

                if total_count >= 55:
                    remaining_ids: List[str] = []
                    for tag_id in all_tag_ids: 
                        if tag_id not in tag_id_to_mac.keys(): 
                            remaining_ids.append(tag_id)
                    print(remaining_ids)
                    
            
    except (json.JSONDecodeError, KeyError) as e:
        print(f"❌ Error parsing message: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def runner():

    client = mqtt.Client(protocol=mqtt.MQTTv311)   
    client.enable_logger()                         
    client.on_connect   = on_connect
    client.on_subscribe = on_subscribe
    client.on_message   = on_message

    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
        print("Tag ID to MAC mapping:")
        print(tag_id_to_mac)
        clist = [72.88, 70.91, 75.44, 68.4, 72.41, 74.6, 72.41, 70.18, 72.41]
        print(sum(clist)/len(clist))
        client.disconnect()
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    runner()
