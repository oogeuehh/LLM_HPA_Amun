import os, codecs

VALID_COMMANDS = set()
valid_file = os.path.join(os.path.dirname(__file__), "valid_commands.txt")
with codecs.open(valid_file, "r", "utf-8") as f:
    for line in f:
        cmd = line.strip()
        if cmd:
            VALID_COMMANDS.add(cmd)

print(repr(VALID_COMMANDS))
