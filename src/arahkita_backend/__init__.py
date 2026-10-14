from .types import InputKeminatan
from .llm import LLMService
mata_pelajaran: list[str] = ["Matematika", "IPA", "Bahasa Inggris"]

def get_input() -> tuple[str, list[int]]:
      
    minat: str = str(input("Masukkan minat anda: "))
    list_nilai: list[int] = []

    for i in range(len(mata_pelajaran)):
        nilai: int = int(input(f"Masukkan nilai {mata_pelajaran[i]}: "))
        list_nilai.append(nilai)

    return minat, list_nilai

def main() -> None:
    m, n = get_input()

    list_nilai: dict[str, int] = dict(zip(mata_pelajaran, n))

    llm: LLMService = LLMService()

    result: InputKeminatan = {
        "minat": m,
        "nilai": list_nilai,
    }

    counseling_results: str = llm.counseling_response(result)

    print(counseling_results)

if __name__ == "__main__":
    main()