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
    print("6. Forget a memory")
    print("7. Search for a memory")
    print("8. Exit")

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

        save_profile(profile_path, profile)

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
        category = input("What category does this memory belong to?")
        importance = input("How important is this memory? (1-5) ")

        memory_item = {
            "text" : new_memory,    
            "category" : category,
            "importance" : importance 
        }

        memories.append(memory_item)
        save_memories(memory_path, memory_data)

        print("I will remember that.")

    elif choice == "5":
        print()
        print("--- Memories ---")

        if memories:
            for memory in memories:
                if isinstance(memory, dict):
                    importance = memory.get("importance", "not set")

                    print(
                        "-",
                        memory["text"],
                        "[Category:",
                        memory["category"],
                       "| Importance:",
        str(importance) + "]"
    )
                else:
                     print("-", memory)
        else:
            print("I do not have any memories saved yet.")

    elif choice == "6":
        if memories:
            print()
            print("--- Memories ---")

            for index, memory in enumerate(memories, start=1):
                if isinstance(memory, dict):
                    print(
                        index,
                        "-",
                        memory["text"],
                        "[Category:",
                        memory["category"] + "]"
                    )
                else:
                    print(index, "-", memory)

            memory_number = input(
                "Enter the number of the memory to forget: "
            )

            if memory_number.isdigit():
                memory_index = int(memory_number) - 1

                if 0 <= memory_index < len(memories):
                    forgotten_memory = memories.pop(memory_index)

                    save_memories(memory_path, memory_data)

                    print("I forgot:", forgotten_memory)
                else:
                    print("That memory number does not exist.")
            else:
                print("Please enter a valid number.")
        else:
            print("I do not have any memories to forget.")

    elif choice == "7":
        search_term = input("Search memories for: ").lower()

        matches = []

        for memory in memories:
            if isinstance(memory, dict):
                memory_text = memory["text"]
                memory_category = memory["category"]

                if (
                    search_term in memory_text.lower()
                    or search_term in memory_category.lower()
                ):
                    matches.append(memory)
            else:
                if search_term in memory.lower():
                    matches.append(memory)

        if matches:
            print()
            print("--- Matching Memories ---")

            for memory in matches:
                if isinstance(memory, dict):
                    importance = memory.get("importance", "not set")

                    print(
                        "-",
                        memory["text"],
                        "[Category:",
                        memory["category"],
                        "| Importance:",
                        str(importance) + "]"
                    )
                else:
                    print("-", memory)
        else:
            print("I could not find a matching memory.")

    elif choice == "8":
        print("Goodbye!")
        break

    else:
        print("Invalid option. Please choose again.")