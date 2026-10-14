from typing import TypedDict

class SubjectsScore(TypedDict):
    Matematika: int
    IPA: int
    Bahasa_Inggris: int

class InputKeminatan(TypedDict):
    minat: str
    nilai: dict[str, int]
