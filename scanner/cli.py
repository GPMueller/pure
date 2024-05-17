import argparse
import enum
from pathlib import Path as Path
import clang.cindex
from clang.cindex import CursorKind
from dataclasses import dataclass

class SideEffectKind(enum.Enum):
    DEREFERENCE_NON_CONST_POINTER = 1
    ASSIGN_TO_POINTER_OR_REFERENCE = 2
    DYNAMIC_MEMORY_ALLOCATION = 3
    THROW_EXCEPTION = 4
    OTHER = 5

@dataclass
class SideEffectInfo:
    kind: SideEffectKind
    location: clang.cindex.SourceRange
    code: str

def full_name_from_cursor(cursor, filename):
    content = ""
    with Path(filename).open("r") as file:
        content = file.read()

    full_name = ""
    if cursor.extent.start.line == cursor.extent.end.line:
        full_name = content.splitlines()[cursor.location.line - 1][
            cursor.extent.start.column - 1 : cursor.extent.end.column - 1
        ].strip()
    else:
        full_name = content.splitlines()[cursor.extent.start.line - 1].strip()
        for l in range(cursor.extent.start.line, cursor.extent.end.line - 1):
            full_name += " " + content.splitlines()[l].strip()
        full_name += " " + content.splitlines()[cursor.extent.end.line - 1].strip()
    if full_name.endswith(";"):
        full_name = full_name[:-1].strip()
    return full_name

def has_side_effects(cursor, translation_unit):
    if cursor.kind == CursorKind.UNARY_OPERATOR:
        if cursor.canonical.spelling == "operator*":
            pointee_type = cursor.type.get_pointee().canonical
            if not pointee_type.is_const_qualified():
                return SideEffectInfo(
                    SideEffectKind.DEREFERENCE_NON_CONST_POINTER,
                    cursor.extent,
                    full_name_from_cursor(cursor, translation_unit.spelling)
                )
    elif cursor.kind == CursorKind.BINARY_OPERATOR:
        if cursor.canonical.spelling in ["operator=", "operator&="]:
            lhs_type = cursor.canonical.type.get_pointee().canonical
            if lhs_type.kind in [CursorKind.POINTER_TYPE, CursorKind.LVALUE_REFERENCE]:
                return SideEffectInfo(
                    SideEffectKind.ASSIGN_TO_POINTER_OR_REFERENCE,
                    cursor.extent,
                    full_name_from_cursor(cursor, translation_unit.spelling)
                )
    elif cursor.kind == CursorKind.CXX_NEW_EXPR:
        return SideEffectInfo(
            SideEffectKind.DYNAMIC_MEMORY_ALLOCATION,
            cursor.extent,
            full_name_from_cursor(cursor, translation_unit.spelling)
        )
    elif cursor.kind == CursorKind.CXX_THROW_EXPR:
        return SideEffectInfo(
            SideEffectKind.THROW_EXCEPTION,
            cursor.extent,
            full_name_from_cursor(cursor, translation_unit.spelling)
        )

    for child in cursor.get_children():
        side_effect = has_side_effects(child, translation_unit)
        if side_effect:
            return side_effect

    return None

def scan_function(cursor, translation_unit):
    side_effects = []
    for child in cursor.get_children():
        side_effect = has_side_effects(child, translation_unit)
        if side_effect:
            side_effects.append(side_effect)
    return side_effects

def print_side_effect_info(function_name, side_effects):
    print(f"Funciton: {function_name}")
    for side_effect in side_effects:
        location = side_effect.location
        start_line, start_column = location.start.line, location.start.column
        end_line, end_column = location.end.line, location.end.column

        print(f"Side effect found: {side_effect.kind.name}")
        print(f"Location: {location.start.file.name}:{start_line}:{start_column} - {end_line}:{end_column}")
        print(f"Code: {side_effect.code}")
        print()

def main():
    parser = argparse.ArgumentParser(description="Scan a C++ file for side effects.")
    parser.add_argument("--file", type=str, required=True, help="The C++ file to scan.")

    args = parser.parse_args()

    index = clang.cindex.Index.create()
    translation_unit = index.parse(args.file, args=['-std=c++20'])

    no_side_effects = True
    for cursor in translation_unit.cursor.get_children():
        if cursor.kind == CursorKind.CXX_METHOD or cursor.kind == CursorKind.FUNCTION_DECL:
            side_effects = scan_function(cursor, translation_unit)
            if side_effects:
                no_side_effects = False
                print_side_effect_info(cursor.spelling, side_effects)
    if no_side_effects:
        print("No side effects found.")

if __name__ == "__main__":
    main()
