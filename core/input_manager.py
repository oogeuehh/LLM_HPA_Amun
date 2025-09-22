### DF: input_manager.py

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
            # &&
            if cmd[i:i+2] == '&&':
                if current.strip():
                    result.append(current.strip())
                current = ''
                i += 2
                continue
            # ||
            elif cmd[i:i+2] == '||':
                if current.strip():
                    result.append(current.strip())
                current = ''
                i += 2
                continue
            # ; or |
            elif char in [';', '|']:
                if current.strip():
                    result.append(current.strip())
                current = ''
                i += 1
                continue

        current += char
        i += 1

    if current.strip():
        result.append(current.strip())

    return result
