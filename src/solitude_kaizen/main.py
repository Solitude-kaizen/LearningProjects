from memory import load_profile, save_profile, load_memories, save_memories

name = "Solitude-Kaizen"
version = "0.1"

profile_path = "src/solitude_kaizen/data/profile.json"
memory_path = "src/solitude_kaizen/data/memories.json"

profile = load_profile(profile_path)
memory_data = load_memories(memory_path)
memories = memory_data["memories"]

user_name = profile["user_name"]
current_goal = profile.get("current_goal")
learning_goal = profile.get("learning_goal")
career_goal = profile.get("career_goal")
health_goal = profile.get("health_goal")

print(name, "V" + version)
print("Hello,", user_name + ".")

if current_goal:
    print("Your current goal is:", current_goal)

while True:
    print("1. View current goal")
    print("2. Change current goal")
    print("3. View my profile")
    print("4. Remember something")
    print("5. View memories")
    print("6. Exit")

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

        print("Your goal has been updated.")

    elif choice == "3":
        print()
        print("--- My Profile ---")
        print("Name:", user_name)
        print("Current Goal:", current_goal)
        print("Learning Goal:", learning_goal)
        print("Career Goal:", career_goal)
        print("Health Goal:", health_goal)

    elif choice == "4":
        new_memory = input("What would you like me to remember? ")

        memories.append(new_memory)
        save_memories(memory_path, memory_data)

        print("I will remember that.")

    elif choice == "5":
        print()
        print("--- Memories ---")

        if memories:
            for memory in memories:
                print("-", memory)
        else:
            print("I do not have any memories saved yet.")

    elif choice == "6":
        print("Goodbye!")
        break

    else:
        print("Invalid option. Please choose again.")