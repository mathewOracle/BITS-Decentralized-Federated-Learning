import os
import json

def getConfigMap(pod_index):
    flagsdata = json.loads(os.environ.get("FEATURE_FLAGS_DATA", '{}'))
    print(flagsdata)
    if f"flags-{pod_index}" in flagsdata:
        flags = flagsdata[f"flags-{pod_index}"]
    else:
        print(f"No specific flags found for this pod {pod_index}, using default flags")
        flags={
            "subjectId": "4",
            "useSyncTraining": False,
            "enableDeepShallowFeaturesweightage": False,
            "enableTimeDistanceWeightage": False,
            "location":{
                "latitude": 12.9715987,
                "longitude": 77.594566
            }
        }
    
    print(f"Pod {pod_index} using flags: {flags}")
    if flags.get("useSyncTraining"):
        print("Sync Federated Learning enabled")
    if flags.get("enableDeepShallowFeaturesweightage"):
        print("Deep Shallow Features weightage enabled")
    if flags.get("enableTimeDistanceWeightage"):
        print("Time Distance Weightage enabled")
    return flags