"""Bounded, exact arithmetic on explicitly supplied decimal numbers."""

from fractions import Fraction
import re


def parse_number(text):
    value = text.strip()
    if len(value) > 50 or not re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)", value):
        raise ValueError("Use a decimal number of at most 50 characters, without commas, units, or exponents.")
    return Fraction(value)


def format_exact(value):
    denominator = value.denominator
    twos = fives = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        return str(value)  # Preserve repeating decimals as exact fractions.
    places = max(twos, fives)
    scaled = abs(value.numerator) * (10 ** places // value.denominator)
    if not places:
        return str(value.numerator)
    digits = str(scaled).zfill(places + 1)
    return ("-" if value < 0 else "") + digits[:-places] + "." + digits[-places:]


def calculate(left, operation, right):
    first, second = parse_number(left), parse_number(right)
    if operation not in {"+", "-", "*", "/"}:
        raise ValueError("Choose +, -, *, or /.")
    if operation == "/" and second == 0:
        raise ValueError("Cannot divide by zero.")
    if operation == "+":
        result = first + second
    elif operation == "-":
        result = first - second
    elif operation == "*":
        result = first * second
    else:
        result = first / second
    return format_exact(result)


def run_calculator(input_function=None, print_function=print):
    if input_function is None:
        input_function = input
    print_function("--- Exact Calculator ---")
    print_function("Local arithmetic only. Nothing is sent, saved, or added to chat.")
    print_function("Enter numbers without units or commas. Blank or /cancel cancels.")
    answers = []
    for prompt in ("First number: ", "Operation (+, -, *, /): ", "Second number: "):
        try:
            answer = input_function(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            answer = ""
        if not answer or answer.casefold() == "/cancel":
            print_function("Calculation canceled.")
            return {"status": "canceled"}
        answers.append(answer)
    try:
        result = calculate(*answers)
    except ValueError as error:
        print_function(str(error))
        return {"status": "invalid"}
    print_function(f"({answers[0]}) {answers[1]} ({answers[2]}) = {result}")
    print_function("Exact result; repeating decimals stay as fractions. No currency rounding is applied.")
    print_function("This checks arithmetic, not whether your inputs or assumptions are correct.")
    return {"status": "completed", "result": result}
