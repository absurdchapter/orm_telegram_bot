def calculate_one_rep_max(weight, reps, sets, muscle_group):
    assert float(weight) == weight
    assert type(reps) == int
    assert type(sets) == int
    assert muscle_group in ['upper', 'lower']

    if muscle_group == 'upper':
        return weight / (1 - 0.02 * reps - 0.01 * sets - 0.002 * reps * sets) * 0.97
    else:
        return weight / (1 - 0.03 * reps - 0.01 * sets - 0.002 * reps * sets) * 0.96


def calculate_worker(onerepmax, reps, sets, muscle_group):
    assert float(onerepmax) == onerepmax
    assert type(reps) == int
    assert type(sets) == int
    assert muscle_group in ['upper', 'lower']

    if muscle_group == 'upper':
        return onerepmax * (1 - 0.02 * reps - 0.01 * sets - 0.002 * reps * sets) / 0.97
    else:
        return onerepmax * (1 - 0.03 * reps - 0.01 * sets - 0.002 * reps * sets) / 0.96
