from .learning import (
    LEARNING_PURPOSE,
    create_next_learning_lesson,
    finish_active_learning_lesson,
    get_active_learning_lesson,
    list_pending_learning_proposals,
    read_learning_progress,
    read_proposal_review_history,
    review_learning_proposal,
)


def print_learning_lesson(lesson, print_function=print):
    print_function()
    print_function("--- SK Learning Brain ---")
    print_function("Purpose:", LEARNING_PURPOSE)
    print_function()
    print_function("Topic:", lesson["topic"])
    print_function("Source:", lesson["source"])
    print_function("Link:", lesson["source_url"])
    print_function("Evidence status:", lesson["evidence_status"])
    print_function()
    print_function("Why it matters:")
    print_function(lesson["why_it_matters"])
    print_function()
    print_function("What the public metadata says:")
    print_function(lesson["evidence_summary"])
    print_function()
    print_function("Your baby step:")
    print_function(lesson["baby_step"])
    print_function()
    print_function("Reflection question:")
    print_function(lesson["reflection_question"])
    print_function()
    print_function("Pending improvement proposal:")
    print_function(lesson["improvement_proposal"])
    print_function("Proposal status:", lesson["proposal_status"])


def print_learning_proposal(proposal, print_function=print):
    print_function()
    print_function("--- Improvement Proposal ---")
    print_function("Proposal ID:", proposal["id"])
    print_function("Topic:", proposal["topic"])
    print_function("Source:", proposal["source"])
    print_function("Link:", proposal["source_url"])
    print_function()
    print_function(proposal["improvement_proposal"])
    print_function()
    print_function("Your lesson reflection:")
    print_function(proposal["user_reflection"])
    print_function("Current status:", proposal["proposal_status"])


def run_start_or_view_learning_lesson(
    database_path,
    print_function=print,
):
    result = create_next_learning_lesson(database_path)

    if result["status"] == "no_research":
        print_function()
        print_function("SK needs research before creating a lesson.")
        print_function(
            "Choose option 17 to collect public research first."
        )

        return result

    if result["status"] == "existing":
        print_function()
        print_function("One lesson is already waiting for you.")
    else:
        print_function()
        print_function("SK prepared one new baby-step lesson.")

    print_learning_lesson(
        result["lesson"],
        print_function=print_function,
    )

    return result


def run_complete_current_learning_lesson(
    database_path,
    input_function=input,
    print_function=print,
):
    active_lesson = get_active_learning_lesson(database_path)

    if active_lesson is None:
        print_function("There is no active lesson to complete.")

        return {
            "status": "no_active_lesson",
            "lesson": None,
        }

    print_function()
    print_function("Reflection question:")
    print_function(active_lesson["reflection_question"])
    reflection = input_function(
        "What did you learn, and what remains uncertain? "
    )

    try:
        result = finish_active_learning_lesson(
            database_path,
            reflection,
        )
    except ValueError as error:
        print_function(str(error))

        return {
            "status": "invalid_reflection",
            "error": str(error),
        }

    if result["status"] != "completed":
        print_function("The lesson could not be completed.")

        return result

    print_function("Your reflection was stored locally.")
    print_function(
        "The improvement proposal still requires human review."
    )

    return result


def run_view_learning_progress(
    database_path,
    print_function=print,
):
    progress = read_learning_progress(database_path)

    print_function()
    print_function("--- Learning Progress ---")
    print_function("Lessons prepared:", progress["total"])
    print_function("Ready now:", progress["ready"])
    print_function("Completed:", progress["completed"])
    print_function(
        "Proposals awaiting review:",
        progress["pending_proposals"],
    )

    return progress


def run_review_pending_learning_proposal(
    database_path,
    input_function=input,
    print_function=print,
):
    proposals = list_pending_learning_proposals(database_path)

    print_function()
    print_function("--- Proposals Awaiting Your Review ---")

    if not proposals:
        print_function(
            "There are no completed lessons awaiting review."
        )

        return {
            "status": "no_pending_proposals",
        }

    for proposal in proposals:
        print_function()
        print_function(
            proposal["id"],
            "-",
            proposal["topic"],
        )

        if proposal["latest_review_action"] == "postponed":
            print_function("  Previously postponed; still pending.")

    proposal_input = input_function(
        "Enter the proposal ID to review: "
    )

    if not proposal_input.isdigit():
        print_function("Please enter a valid proposal ID.")

        return {
            "status": "invalid_proposal_id",
        }

    proposal_id = int(proposal_input)
    selected_proposal = next(
        (
            proposal
            for proposal in proposals
            if proposal["id"] == proposal_id
        ),
        None,
    )

    if selected_proposal is None:
        print_function("That proposal is not in the pending list.")

        return {
            "status": "proposal_not_pending",
        }

    print_learning_proposal(
        selected_proposal,
        print_function=print_function,
    )
    action = input_function(
        "Choose approve, reject, or postpone: "
    )
    reason = input_function(
        "Give a short reason for your decision: "
    )

    try:
        result = review_learning_proposal(
            database_path,
            proposal_id,
            action,
            reason,
        )
    except ValueError as error:
        print_function(str(error))

        return {
            "status": "invalid_review",
            "error": str(error),
        }

    if result["status"] == "already_decided":
        print_function(
            "This proposal already has a final decision:",
            result["proposal_status"],
        )

        return result

    if result["status"] != "recorded":
        print_function("The proposal review could not be recorded.")

        return result

    if result["action"] == "approved":
        print_function(
            "Approved for separate planning. No code was changed."
        )
    elif result["action"] == "rejected":
        print_function("Rejected and closed. No code was changed.")
    else:
        print_function("Postponed. The proposal remains pending.")

    return result


def run_view_proposal_review_history(
    database_path,
    print_function=print,
):
    history = read_proposal_review_history(database_path)

    print_function()
    print_function("--- Proposal Review History ---")

    if not history:
        print_function("No proposal reviews have been recorded yet.")

        return history

    for review in history:
        print_function()
        print_function("Topic:", review["topic"])
        print_function("Action:", review["action"])
        print_function("Reason:", review["reason"])
        print_function("Recorded:", review["created_at"])
        print_function("Current status:", review["proposal_status"])

    return history
