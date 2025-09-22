import pandas as pd
from collections import defaultdict, Counter

df = pd.read_csv("parsed_cowrie_commands.csv")


def split_commands(cmd):
    result = []
    current = ''
    i = 0
    length = len(cmd)
    in_single_quote = False
    in_double_quote = False
    brace_level = 0

    while i < length:
        char = cmd[i]


        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif char == '{' and not in_single_quote and not in_double_quote:
            brace_level += 1
        elif char == '}' and not in_single_quote and not in_double_quote:
            brace_level = max(0, brace_level - 1)


        if not in_single_quote and not in_double_quote and brace_level == 0:

            if cmd[i:i+2] == '&&':
                result.append(current.strip())
                current = ''
                i += 2
                continue

            elif cmd[i:i+2] == '||':
                result.append(current.strip())
                current = ''
                i += 2
                continue

            elif char in [';', '|']:
                result.append(current.strip())
                current = ''
                i += 1
                continue


        current += char
        i += 1

    if current.strip():
        result.append(current.strip())

    return result


def parse_command(cmd):
    """
    input: sub command (string)
    output: List of commands as states
    """

    cmd = cmd.replace('(', '').replace(')', '')


    commands = split_commands(cmd)
    return [command.strip() for command in commands if command.strip()]



session_vectors = defaultdict(list)

for _, row in df.iterrows():
    session = row["session"]
    input_cmd = row["input"] if pd.notnull(row["input"]) else "unknown"
    parsed = parse_command(input_cmd)
    session_vectors[session].extend(parsed)

print("✅ generated all session vectors")


investigated_sessions = list(session_vectors.keys())[-10:]

for session in investigated_sessions:
    print(f"\n🔍 Session: {session}")
    for i, command in enumerate(session_vectors[session]):
        print(f"{i+1}. Command: {command}")


def calculate_transition_matrix(session_vectors):

    transitions = []
    all_states = set()

    for session, commands in session_vectors.items():
        for i in range(len(commands) - 1):
            from_state = commands[i]
            to_state = commands[i + 1]
            all_states.add(from_state)
            all_states.add(to_state)
            transitions.append((from_state, to_state))


    state_list = sorted(list(all_states))
    transition_matrix = pd.DataFrame(0, index=state_list, columns=state_list)


    for from_state, to_state in transitions:
        transition_matrix.at[from_state, to_state] += 1

    return transition_matrix


def calculate_transition_probabilities(transition_matrix, epsilon=4.48e-8):
    state_list = transition_matrix.index

    row_sums = transition_matrix.sum(axis=1)
    transition_matrix = transition_matrix.astype('float64')

    for state in state_list:
        row_sum = row_sums[state]
        if row_sum > 0:

            transition_matrix.loc[state] = transition_matrix.loc[state] * (1 - epsilon)
            transition_matrix.loc[state] = transition_matrix.loc[state] / row_sum


            zero_columns = transition_matrix.loc[state] == 0
            transition_matrix.loc[state, zero_columns] = epsilon / (len(state_list) - row_sum)
        else:
            transition_matrix.loc[state] = 1 / len(state_list)

    return transition_matrix



transition_matrix = calculate_transition_matrix(session_vectors)
transition_probabilities = calculate_transition_probabilities(transition_matrix)



print("\nTransition Probabilities Matrix:")
print(transition_probabilities)
print("Transition Counts Matrix:")
print(transition_matrix)


transition_probabilities.to_csv("transition_probabilities_matrix.csv", encoding="utf-8-sig")
transition_matrix.to_csv("transition_counts_matrix.csv", encoding="utf-8-sig")
print("✅ Transition matrices saved successfully.")