from memory import (
    load_profile,
    save_profile,
    load_memories,
    save_memories,
    create_memory,
    search_memories,
    forget_memory,
    format_memory,
    validate_importance,
    validate_category,
    normalize_memory,
    filter_memories_by_category,
    sort_memories_by_importance,
    sort_memories_by_recency,
    rank_memories,
)

name = "Solitude-Kaizen"
version = "0.1"

profile_path = "src/solitude_kaizen/data/profile.json"
memory_path = "src/solitude_kaizen/data/memories.json"

profile = load_profile(profile_path)
memory_data = load_memories(memory_path)

memories = [
    normalize_memory(memory)
    for memory in memory_data["memories"]
]

memory_data["memories"] = memories
save_memories(memory_path, memory_data)

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
    print("8. View memories by category")
    print("9. View memories by importance")
    print("10. View memories by recency")
    print("11. View memories by rank")
    print("12. Exit")

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

        while True:
            category_input = input(
                "What category does this memory belong to? "
            )

            category = validate_category(category_input)

            if category is not None:
                break

            print(
                "Please choose: learning, career, health, "
                "project, personal, or test."
            )

        while True:
            importance_input = input(
                "How important is this memory? (1-5): "
            )

            importance = validate_importance(importance_input)

            if importance is not None:
                break

            print("Please enter a valid importance level between 1 and 5.")

        memory_item = create_memory(
            new_memory,
            category,
            importance
        )

        memories.append(memory_item)
        save_memories(memory_path, memory_data)

        print("I will remember that.")
    elif choice == "5":
        print()
        print("--- Memories ---")

        if memories:
            for memory in memories:
                print("-", format_memory(memory))
        else:
            print("I do not have any memories saved yet.")

    elif choice == "6":
        if memories:
            print()
            print("--- Memories ---")

            for index, memory in enumerate(memories, start=1):
               print(index, "-", format_memory(memory))

            memory_number = input(
                "Enter the number of the memory to forget: "
            )

            if memory_number.isdigit():
                memory_index = int(memory_number) - 1

                forgotten_memory = forget_memory(
                    memories,
                    memory_index
                )

                if forgotten_memory is not None:
                    save_memories(memory_path, memory_data)
                    print("I forgot:", forgotten_memory)
                else:
                    print("That memory number does not exist.")
            else:
                print("Please enter a valid number.")
        else:
            print("I do not have any memories to forget.")

    elif choice == "7":
        search_term = input("Search memories for: ")

        matches = search_memories(memories, search_term)

        if matches:
            print()
            print("--- Matching Memories ---")

            for memory in matches:
                print("-", format_memory(memory))
        else:
            print("I could not find a matching memory.")

    elif choice == "8":
        category_input = input(
            "Which category would you like to view? "
        )

        category = validate_category(category_input)

        if category is None:
            print(
                "Please choose: learning, career, health, "
                "project, personal, or test."
            )
        else:
            matches = filter_memories_by_category(
                memories,
                category
            )

            if matches:
                print()
                print("---", category.title(), "Memories ---")

                for memory in matches:
                    print("-", format_memory(memory))
            else:
                print("I do not have memories in that category.")

    elif choice == "9":
        sorted_memories = sort_memories_by_importance(memories)

        print()
        print("--- Memories Sorted by Importance ---")

        for memory in sorted_memories:
            print("-", format_memory(memory))

    elif choice == "10":
        sorted_memories = sort_memories_by_recency(memories)

        print()
        print("--- Memories by Recency ---")

        for memory in sorted_memories:
            print("-", format_memory(memory))

    elif choice == "11":
        sorted_memories = rank_memories(memories)

        print()
        print("--- Memories Ranked ---")

        for memory in sorted_memories:
            print("-", format_memory(memory))

    elif choice == "12":
        print("Goodbye!")
        break

    else:
        print("Invalid option. Please choose again.")