import json

name = "Solitude-Kaizen"
version = "0.1"

profile_path = "src/solitude_kaizen/data/profile.json"

with open(profile_path, "r") as file:
    profile = json.load(file)

user_name = profile["user_name"]
current_goal = profile.get("current_goal")

print(name, "V" + version)
print("Hello,", user_name + ".")
print("I remembered your name from my local memory.")

if current_goal:
    print("Your current goal is:", current_goal)
else:
    print("I don't have a current goal saved yet.")