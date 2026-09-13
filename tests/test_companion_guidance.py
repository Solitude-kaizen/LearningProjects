from src.solitude_kaizen.prompt import build_system_prompt


def test_companion_guidance_distinguishes_retrieval_training_and_evidence():
    prompt = build_system_prompt("Synthetic memory", "Synthetic conversation")
    assert "do not train or update a model's weights" in prompt
    assert "separate optimization process" in prompt
    assert "context can help answer quality without changing model weights" in prompt
    assert "State missing information" in prompt
    assert "do not append an estimated word count" in prompt
    assert "Synthetic memory" in prompt
    assert "Synthetic conversation" in prompt


def test_profit_guidance_checks_revenue_costs_and_budget_distinction():
    prompt = build_system_prompt("Fictional budget")
    assert "selling price and quantity sold" in prompt
    assert "total costs" in prompt
    assert "not proof of actual costs or revenue" in prompt
    assert "do not promise guaranteed profit" in prompt
