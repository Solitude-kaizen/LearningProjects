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

if current_goal:
    print("Your current goal is:", current_goal)

while True:
    print()
    print("What would you like to do?")
    print("1. View current goal")
    print("2. Change current goal")
    print("3. Exit")

    choice = input("Choose an option: ")

    if choice == "1":
        if current_goal:
            print("Your current goal is:", current_goal)
        else:
            print("You do not have a current goal saved.")

    elif choice == "2":
        new_goal = input("Enter your new goal: ")

        profile["current_goal"] = new_goal
        current_goal = new_goal

        with open(profile_path, "w") as file:
            json.dump(profile, file, indent=4)

        print("Your goal has been updated.")

    elif choice == "3":
        print("Goodbye!")
        break

    else:
        print("Invalid option. Please choose again.")