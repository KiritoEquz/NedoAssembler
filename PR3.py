import argparse
from typing import Dict, List
import csv
import os

class InstructionSpec:
    name: str
    code: int
    fields: Dict[str, tuple];

    def __init__(self, name: str, code: int, fields: Dict[str, tuple]):
        self.name = name
        self.fields = fields
        self.code = code

COMMANDS = {
    "LOAD_CONST": InstructionSpec(
        name="LOAD_CONST",
        code = 57,
        fields={
            "A": (0, 5),
            "B": (6, 19),
            "C": (20, 47),
        }
    ),
    "LOAD_MEM": InstructionSpec(
        name="LOAD_MEM",
        code = 46,
        fields={
            "A": (0, 5),
            "B": (6, 19),
            "C": (20, 33),
        }
    ),
    "STORE_MEM": InstructionSpec(
        name="STORE_MEM",
        code = 11,
        fields={
            "A": (0, 5),
            "B": (6, 19),
            "C": (20, 33),
        }
    ),
    "ROR": InstructionSpec(
        name="ROR",
        code = 10,
        fields={
            "A": (0, 5),
            "B": (6, 19),
            "C": (20, 33),
            "D": (34, 44),
            "E": (45, 58),
        }
    ),
}


def encode_instruction(spec: InstructionSpec, values: Dict[str, int]) -> int:
    word = 0
    for field, (lo, hi) in spec.fields.items():
        v = values[field]
        width = hi - lo + 1
        if v >= (1 << width):
            raise ValueError(f"Value {v} too large for field {field}")
        word |= (v << lo)
    return word


def parse_csv_program(path: str) -> List[int]:
    result = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            op = row[0].strip()
            spec = COMMANDS[op]
            fields = {}
            fields['A'] = spec.code
            for part in row[1:]:
                if (not("=" in part)):
                    break
                key, val = part.split("=")
                fields[key.strip()] = int(val)
            word = encode_instruction(spec, fields)
            result.append(word)
    return result

def save_binary(filename: str, program: List[int]):
    with open(filename, "wb") as f:
        for w in program:
            f.write(w.to_bytes(8, "little"))

def detect_opcode(word: int) -> InstructionSpec:
    opcode = word & 0x3F
    for spec in COMMANDS.values():
        if spec.code == opcode:
            return spec
    raise ValueError(f"Unknown opcode: {opcode}")




def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("out")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    program = parse_csv_program(args.src)

    if args.test:
        for w in program:
            inbytes = f"{w:016X}"
            inbyteslist = []
            while (inbytes):
                inbyteslist.append("0x" +inbytes[-2:])
                inbytes = inbytes[:len(inbytes) - 2]
            print(inbyteslist)
            print()

    else:
        save_binary(args.out, program)
        print("The file size is: ", os.path.getsize(args.out))

if __name__ == "__main__":
    main()
