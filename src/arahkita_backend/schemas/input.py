from pydantic import BaseModel, Field


class SubjectsScore(BaseModel):
    Matematika: int = Field(
        ..., ge=0, le=100, description="Skor nilai Matematika (0–100)"
    )
    IPA: int = Field(
        ..., ge=0, le=100, description="Skor nilai IPA (0–100)"
    )
    Bahasa_Inggris: int = Field(
        ..., ge=0, le=100, description="Skor nilai Bahasa Inggris (0–100)"
    )


class InputKeminatan(BaseModel):
    minat: str = Field(
        ..., min_length=1, description="Deskripsi minat atau bakat siswa"
    )
    nilai: SubjectsScore = Field(
        ..., description="Skor nilai mata pelajaran"
    )


SUBJECT_NAME_NORMALIZATION_MAP: dict[str, str] = {
    "Matematika": "Matematika",
    "IPA": "IPA",
    "Bahasa_Inggris": "Bahasa Inggris",
}


def normalize_subject_name(raw_name: str) -> str:
    """Menormalisasi nama mata pelajaran menjadi format standar human-readable."""
    return SUBJECT_NAME_NORMALIZATION_MAP.get(
        raw_name, raw_name.replace("_", " ").strip()
    )

