from .memory import forget_memory, format_memory, save_memories


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
