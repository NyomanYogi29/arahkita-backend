import json
import logging
from openai import AsyncOpenAI

from arahkita_backend.config.settings import Settings
from arahkita_backend.schemas.input import InputKeminatan
from arahkita_backend.schemas.major_node import MajorRecommendationLLMResponse

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Kamu adalah konsultan peminatan jurusan kuliah untuk siswa SMA/SMK di Indonesia.
Tugasmu adalah menganalisis minat dan nilai mata pelajaran siswa, lalu merekomendasikan antara 2 hingga 6 nama jurusan kuliah yang paling relevan dan realistis.

Aturan Wajib:
1. Kembalikan HANYA format JSON valid berikut:
{"recommendations": ["Nama Jurusan 1", "Nama Jurusan 2", ...]}
2. Berikan minimal 2 dan maksimal 6 rekomendasi nama jurusan.
3. Gunakan nama jurusan resmi dalam bahasa Indonesia yang lazim di perguruan tinggi (misal: "Teknik Informatika", "Sistem Informasi", "Teknik Elektro").
4. Jangan sertakan teks penjelasan, markdown formatting tambahan, ataupun basa-basi di luar format JSON tersebut.
"""


def format_user_prompt(profile: InputKeminatan) -> str:
    """Memformat profil keminatan dan nilai siswa menjadi prompt teks untuk LLM."""
    return (
        f"Data Siswa:\n"
        f"- Minat: {profile.minat}\n"
        f"- Nilai Matematika: {profile.nilai.Matematika}\n"
        f"- Nilai IPA: {profile.nilai.IPA}\n"
        f"- Nilai Bahasa Inggris: {profile.nilai.Bahasa_Inggris}\n\n"
        f"Berikan 2 hingga 6 rekomendasi nama jurusan kuliah dalam format JSON."
    )


def clean_json_response(raw_text: str) -> str:
    """Membersihkan markdown fences jika LLM mengembalikan kode blok markdown."""
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


async def fetch_major_recommendations(
    profile: InputKeminatan,
    settings: Settings,
    client: AsyncOpenAI | None = None,
) -> list[str]:
    """Mengirim request ke OpenRouter untuk mendapatkan daftar 2–6 nama rekomendasi jurusan."""
    ai_client = client or AsyncOpenAI(
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
    )

    user_content = format_user_prompt(profile)

    response = await ai_client.chat.completions.create(
        model=settings.openrouter_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
        max_tokens=500,
        extra_body={"reasoning": {"exclude": True}},
    )

    raw_content = response.choices[0].message.content
    if not raw_content:
        raise ValueError("OpenRouter mengembalikan respons kosong.")

    cleaned_json = clean_json_response(raw_content)

    try:
        parsed = MajorRecommendationLLMResponse.model_validate_json(cleaned_json)
    except Exception as exc:
        logger.error("Gagal melakukan parsing output LLM: %s. Raw: %s", exc, raw_content)
        raise ValueError(f"Gagal mem-parsing rekomendasi jurusan dari LLM: {exc}") from exc

    recommendations = [r.strip() for r in parsed.recommendations if r and r.strip()]

    # Batasi maksimal 6 item sesuai spesifikasi
    return recommendations[:6]


class OpenRouterAdapter:
    """Adapter untuk berkomunikasi dengan model AI di OpenRouter."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = AsyncOpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
        )

    async def fetch_major_recommendations(self, profile: InputKeminatan) -> list[str]:
        """Mengambil rekomendasi jurusan menggunakan konfigurasi client adapter."""
        return await fetch_major_recommendations(
            profile=profile,
            settings=self.settings,
            client=self.client,
        )
