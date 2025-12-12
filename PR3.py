import argparse
import struct
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

def decode_instruction(word: int):
    opcode = word & 0x3F
    spec = None
    for s in COMMANDS.values():
        if s.code == opcode:
            spec = s
            break
    if spec is None:
        raise ValueError(f"Unknown opcode: {opcode}")

    fields = {}
    for k, (lo, hi) in spec.fields.items():
        width = hi - lo + 1
        fields[k] = (word >> lo) & ((1 << width) - 1)

    return spec, fields


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


def load_binary(filename: str) -> List[int]:
    program = []
    with open(filename, "rb") as f:
        while True:
            data = f.read(8)
            if not data:
                break
            if len(data) != 8:
                raise ValueError("Invalid binary file: instruction not 8 bytes")
            word = int.from_bytes(data, byteorder="little", signed=False)
            program.append(word)
    return program

def save_csv(out: str, start: int, end: int, memory: List[int]):
    with open(out, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for i in range(start, end+1):
            writer.writerow([i, memory[i]])


def assembly(src: str, out: str, test: bool):
    program = parse_csv_program(src)

    if test:
        for w in program:
            inbytes = f"{w:016X}"
            inbyteslist = []
            while inbytes:
                inbyteslist.append("0x" +inbytes[-2:])
                inbytes = inbytes[:len(inbytes) - 2]
            for byte in inbyteslist:
                print(byte, end=" ")
            print()

    else:
        save_binary(out, program)
        print("The file size is: ", os.path.getsize(out), "bytes")


def interpret(src: str, out: str, start: int, end: int):
    progMemory = []
    registers = [0]*2048
    program = load_binary(src)
    for p in program:
        progMemory.append(decode_instruction(p))

    for (p, op) in progMemory:
        if p.code == 57:
            registers[op['B']] = op['C']

        elif p.code == 46:
            registers[op['B']] = registers[op['C']]

        elif p.code == 11:
            registers[op['C']] = registers[op['B']]

    save_csv(out, start, end, registers)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("op")
    parser.add_argument("src")
    parser.add_argument("out")
    parser.add_argument("--test", action="store_true")
    parser.add_argument('-s', '--start', type = int, required = False)
    parser.add_argument('-e', '--end', type = int, required = False)


    args = parser.parse_args()
    if args.op == "a":
        assembly(args.src, args.out, args.test)
    if args.op == "i":
        interpret(args.src, args.out, args.start, args.end)

if __name__ == "__main__":
    main()