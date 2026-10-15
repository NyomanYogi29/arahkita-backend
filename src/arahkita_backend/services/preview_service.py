from arahkita_backend.adapters.openrouter_adapter import OpenRouterAdapter
from arahkita_backend.schemas.preview import (
    GeneratePreviewRequest,
    MajorNodeCareerPath,
    MajorNodePreview,
)
from arahkita_backend.utils.ids import generate_uuid


def calculate_matching_percentage(
    mcq_accuracy: float,
    essay_analytical_score: float,
    essay_interest_score: float,
) -> int:
    """Menghitung persentase kecocokan keminatan (1–100%) menggunakan formula terbobot:

    MCQ = mcq_accuracy (0–100)
    Analytical = (essay_analytical_score / 5.0) * 100
    Interest = (essay_interest_score / 5.0) * 100
    Matching Percentage = round(0.30 * MCQ + 0.35 * Analytical + 0.35 * Interest)
    Batas nilai clamped: max(1, min(100, score))
    """
    mcq = mcq_accuracy
    analytical = (essay_analytical_score / 5.0) * 100.0
    interest = (essay_interest_score / 5.0) * 100.0

    raw_percentage = round(0.30 * mcq + 0.35 * analytical + 0.35 * interest)
    return max(1, min(100, int(raw_percentage)))


def sanitize_career_title(raw_title: str) -> str:
    """Memastikan judul profesi karir maksimal terdiri dari 2 kata."""
    words = raw_title.strip().split()
    if not words:
        return "Praktisi Terkait"
    if len(words) > 2:
        return " ".join(words[:2])
    return raw_title.strip()


def sanitize_preview_text(raw_preview: str, max_words: int = 200) -> str:
    """Memastikan teks rangkuman evaluasi maksimal terdiri dari max_words kata."""
    words = raw_preview.strip().split()
    if not words:
        return "Belum ada evaluasi."
    if len(words) > max_words:
        truncated = " ".join(words[:max_words])
        if not truncated.endswith((".", "!", "?")):
            truncated += "..."
        return truncated
    return raw_preview.strip()


async def generate_major_preview(
    major_node_id: str,
    request: GeneratePreviewRequest,
    adapter: OpenRouterAdapter,
) -> MajorNodePreview:
    """Men-generate rangkuman evaluasi (preview) dan 1–4 jalur karir untuk suatu major_node.

    Tahapan:
    1. Menghitung matching_percentage secara deterministik menggunakan formula terbobot.
    2. Memanggil LLM untuk menyusun narasi evaluasi (maks. 200 kata) dan rekomendasi karir.
    3. Membuat UUID v4 untuk entity preview (relasi 1:1 ke major_node_id).
    4. Merakit 1–4 entity career path (relasi 1:N ke major_node_preview_id) dengan judul maks 2 kata.
    5. Mengembalikan MajorNodePreview nested siap simpan di IndexedDB (Dexie.js).
    """
    matching_percentage = calculate_matching_percentage(
        mcq_accuracy=request.mcq_accuracy,
        essay_analytical_score=request.essay_analytical_score,
        essay_interest_score=request.essay_interest_score,
    )

    llm_response = await adapter.fetch_preview_generation(
        request=request,
        matching_percentage=matching_percentage,
    )

    preview_id = generate_uuid()
    sanitized_preview = sanitize_preview_text(llm_response.preview, max_words=200)

    # Filter dan batasi 1–4 pilihan karir
    candidate_titles = [
        title.strip() for title in llm_response.career_paths if title and title.strip()
    ]
    if not candidate_titles:
        candidate_titles = [request.major_name]

    chosen_titles = candidate_titles[:4]

    career_paths: list[MajorNodeCareerPath] = [
        MajorNodeCareerPath(
            id=generate_uuid(),
            major_node_preview_id=preview_id,
            title=sanitize_career_title(title),
        )
        for title in chosen_titles
    ]

    return MajorNodePreview(
        id=preview_id,
        major_node_id=major_node_id,
        preview=sanitized_preview,
        matching_percentage=matching_percentage,
        career_paths=career_paths,
    )
