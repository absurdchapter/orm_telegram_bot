OPTION_LIST = ["Calculate one-rep max", "Calculate rep weight"]
OPTION_DICT = {OPTION_LIST[0]: "orm", OPTION_LIST[1]: "worker"}
assert set(OPTION_LIST) == set(OPTION_DICT)

EXERCISE_LIST = ["Bench press", "Squat or deadlift"]
EXERCISE_DICT = {EXERCISE_LIST[0]: "upper", EXERCISE_LIST[1]: "lower"}
assert set(EXERCISE_LIST) == set(EXERCISE_DICT)

RESTART_WORDS = ["Calculate again"]
