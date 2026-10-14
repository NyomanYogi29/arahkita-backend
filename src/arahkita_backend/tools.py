from typing import Any, Callable

def finding_major_suggestion(minat: str, matematika: float, ipa: float, inggris: float) -> None:
    """Memberikan minimal 2 sampai maksimal 6 rekomendasi jurusan berdasarkan miant dan nilai siswa

    Panggil tool ini ketika siswa sudah menyebutkan minat dan ketiga nilainya.

    Return jawaban berupa list jurusan dengan contoh output:

    "1. Teknologi Informasi\n2. Sistem Informasi\n dan seterusnya..."

    Args: 
        minat: Bidang yang diminati siswa, misal "teknologi, sipil, politik".
        matematika: Nilai matematika kelas akhir (0 - 100).
        ipa: Nilai ipa kelas akhir (0 - 100)
        inggris: Nilai Bahasa Inggris kelas akhir (0 - 100)
    """

TOOLS: list[Callable[..., Any]] = [finding_major_suggestion]
TOOL_MAP: dict[str, Callable[..., Any]] = {t.__name__: t for t in TOOLS}