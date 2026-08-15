exercises = ["Push-ups", "Squats", "Pull-ups"]

new_exercise = input("Enter a new exercise: ")

if new_exercise in exercises:
    print("Exercise already exists")
else:
    exercises.append(new_exercise)
    print("Exercise added")

print(exercises)