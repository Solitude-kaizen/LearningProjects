import json


def load_profile(profile_path):
    with open(profile_path, "r") as file:
        profile = json.load(file)

    return profile