from .memory import (
    create_memory, forget_memory, format_memory, save_memories,
    validate_category, validate_importance,
)


def run_remember_memory(memory_path, memory_data, input_function=None, print_function=None):
    """Preview a new memory, then save before changing the shared list."""
    if input_function is None:
        input_function = input
    if print_function is None:
        print_function = print

    def read(prompt):
        value = input_function(prompt)
        if value.strip().casefold() == "/cancel":
            raise EOFError
        return value

    def cancelled():
        print_function("Cancelled. No memory was added.")
        return None

    print_function("Do not store passwords or API keys. /cancel cancels at any prompt.")
    try:
        text = read("What would you like me to remember? ")
        if not text.strip():
            return cancelled()
        if len(text) > 1000:
            print_function("Memory text must be at most 1000 characters. Nothing was added.")
            return None
        while True:
            category = validate_category(read("Memory category: "))
            if category is not None:
                break
            print_function("Please choose: learning, career, health, project, personal, or test.")
        while True:
            importance = validate_importance(read("How important is this memory? (1-5): "))
            if importance is not None:
                break
            print_function("Please enter a valid importance level between 1 and 5.")
        print_function("--- New memory preview ---")
        print_function("Text:", text)
        print_function("Category:", category)
        print_function("Importance:", importance)
        print_function("Relevant memories may be sent to your provider during chat, including cloud providers.")
        if read("Type 'yes' to save this memory, anything else to cancel: ").strip().casefold() != "yes":
            return cancelled()
    except (EOFError, KeyboardInterrupt):
        return cancelled()

    item = create_memory(text, category, importance)
    memories = memory_data["memories"]
    candidate = {**memory_data, "memories": memories + [item]}
    try:
        save_memories(memory_path, candidate)
    except (OSError, TypeError, ValueError):
        print_function("Could not save the memory. Nothing was added.")
        return None
    memories.append(item)
    print_function("I will remember that.")
    return item


def run_forget_memory(
    memory_path,
    memory_data,
    input_function=None,
    print_function=None,
):
    """Preview a selection and save its removal only after an explicit yes."""
    if input_function is None:
        input_function = input
    if print_function is None:
        print_function = print

    memories = memory_data["memories"]

    if not memories:
        print_function("I do not have any memories to forget.")
        return None

    print_function()
    print_function("--- Memories ---")
    for index, memory in enumerate(memories, start=1):
        print_function(index, "-", format_memory(memory))

    try:
        memory_number = input_function(
            "Enter the number of the memory to forget (/cancel to cancel): "
        )
    except (EOFError, KeyboardInterrupt):
        print_function("Cancelled. Nothing was forgotten.")
        return None
    if memory_number.strip().casefold() == "/cancel":
        print_function("Cancelled. Nothing was forgotten.")
        return None
    try:
        memory_index = int(memory_number) - 1
    except ValueError:
        print_function("Please enter a valid number.")
        return None

    if not 0 <= memory_index < len(memories):
        print_function("That memory number does not exist.")
        return None

    print_function()
    print_function("You are about to forget:")
    print_function("-", format_memory(memories[memory_index]))
    try:
        confirmation = input_function(
            "Type 'yes' to confirm, anything else to cancel: "
        )
    except (EOFError, KeyboardInterrupt):
        confirmation = ""

    if confirmation.strip().lower() != "yes":
        print_function("Cancelled. Nothing was forgotten.")
        return None

    updated_memories = memories.copy()
    forgotten_memory = forget_memory(updated_memories, memory_index)
    if forgotten_memory is not None:
        updated_data = {**memory_data, "memories": updated_memories}
        try:
            save_memories(memory_path, updated_data)
        except (OSError, ValueError, TypeError):
            print_function("Could not save the change. Nothing was forgotten.")
            return None
        memories[:] = updated_memories
        print_function("I forgot:", forgotten_memory)

    return forgotten_memory
