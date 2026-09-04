from .memory import (
    ensure_json_file,
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

from .conversation_cli import (
    run_clear_conversation,
    run_talk_to_companion,
    run_view_ai_provider,
    run_view_conversation_status,
)
from .research_cli import (
    run_collect_public_research,
    run_view_latest_kaizen_discovery,
    run_view_public_research_inbox,
)
from .learning_cli import (
    run_complete_current_learning_lesson,
    run_review_pending_learning_proposal,
    run_start_or_view_learning_lesson,
    run_view_learning_progress,
    run_view_proposal_review_history,
)
from .continuity_cli import (
    ContinuityPaths,
    run_create_continuity_backup,
    run_restore_latest_continuity_backup,
    run_verify_latest_continuity_backup,
)
from .continuous_learning import run_companion_startup


name = "Solitude-Kaizen"
version = "1.0"

profile_path = "src/solitude_kaizen/data/profile.json"
memory_path = "src/solitude_kaizen/data/memories.json"
database_path = "src/solitude_kaizen/data/solitude_kaizen.db"
identity_path = "SK_IDENTITY.md"
backup_directory = "src/solitude_kaizen/data/backups"

continuity_paths = ContinuityPaths(
    backup_directory=backup_directory,
    database_path=database_path,
    profile_path=profile_path,
    memory_path=memory_path,
    identity_path=identity_path,
)

ensure_json_file(
    profile_path,
    {
        "user_name": "User",
        "current_goal": "Build Solitude-Kaizen V1",
        "learning_goal": "Improve programming and AI skills",
        "career_goal": "",
        "health_goal": "",
    },
)

ensure_json_file(
    memory_path,
    {
        "memories": [],
    },
)

profile = load_profile(profile_path)
memory_data = load_memories(memory_path)

memories = [
    normalize_memory(memory)
    for memory in memory_data["memories"]
]

conversation_history = []
memory_data["memories"] = memories
save_memories(memory_path, memory_data)

startup_result = run_companion_startup(database_path)
kaizen_result = startup_result["kaizen"]
research_result = startup_result["research"]

user_name = profile["user_name"]
current_goal = profile.get("current_goal")
learning_goal = profile.get("learning_goal")
career_goal = profile.get("career_goal")
health_goal = profile.get("health_goal")

print(name, "V" + version)
print("Hello,", user_name + ".")

if current_goal:
    print("Your current goal is:", current_goal)

if kaizen_result["status"] == "completed":
    print("A new daily Kaizen discovery is ready for review.")
elif kaizen_result["status"] == "failed":
    print("The daily Kaizen discovery could not run today.")

if research_result["status"] == "completed":
    print("The public research inbox was updated.")
elif research_result["status"] == "partial":
    print("The public research inbox was partly updated.")
elif research_result["status"] == "failed":
    print("The public research collector could not run today.")

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
    print("12. Talk to Solitude-Kaizen")
    print("13. View Ai provider")
    print("14. clear conversation")
    print("15. View conversation status")
    print("16. View latest Kaizen discovery")
    print("17. Collect zero-cost public research")
    print("18. View public research inbox")
    print()
    print("Optional Learning Guide (not required for chat or research):")
    print("19. Start or view a short lesson")
    print("20. Complete the current lesson")
    print("21. View learning progress")
    print("22. Review pending improvement proposals")
    print("23. View proposal review history")
    print()
    print("Backups and exit:")
    print("24. Create and verify continuity backup")
    print("25. Verify latest continuity backup")
    print("26. Preview and restore latest continuity backup")
    print("27. Exit")

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
        run_talk_to_companion(
            conversation_history,
            memories,
        )

    elif choice == "13":
        run_view_ai_provider()

    elif choice == "14":
        run_clear_conversation(conversation_history)

    elif choice == "15":
        run_view_conversation_status(conversation_history)

    elif choice == "16":
        run_view_latest_kaizen_discovery(database_path)

    elif choice == "17":
        run_collect_public_research(database_path)

    elif choice == "18":
        run_view_public_research_inbox(database_path)

    elif choice == "19":
        run_start_or_view_learning_lesson(database_path)

    elif choice == "20":
        run_complete_current_learning_lesson(database_path)

    elif choice == "21":
        run_view_learning_progress(database_path)

    elif choice == "22":
        run_review_pending_learning_proposal(database_path)

    elif choice == "23":
        run_view_proposal_review_history(database_path)

    elif choice == "24":
        run_create_continuity_backup(continuity_paths)

    elif choice == "25":
        run_verify_latest_continuity_backup(continuity_paths)

    elif choice == "26":
        restore_result = run_restore_latest_continuity_backup(
            continuity_paths
        )

        if restore_result["status"] == "restored":
            break

    elif choice == "27":
        print("Goodbye!")
        break
