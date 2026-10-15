from fastapi import APIRouter

from arahkita_backend.schemas.recommendation_result import (
    MajorRecommendationResult,
    RecommendationResultsRequest,
)
from arahkita_backend.services.recommendation_result_service import (
    calculate_recommendation_leaderboard,
)

router = APIRouter(
    prefix="/recommendation-results",
    tags=["Recommendation Results"],
)


@router.post("", response_model=list[MajorRecommendationResult])
async def get_recommendation_results(
    payload: RecommendationResultsRequest,
) -> list[MajorRecommendationResult]:
    """Menyusun leaderboard rekomendasi jurusan berdasarkan matching_percentage.

    Mengurutkan major_node dari persentase kecocokan tertinggi ke terendah.
    Jika ada jurusan yang belum dikerjakan, nilainya tetap 0 dan diletakkan di bawah.
    Jika seluruh jurusan belum dikerjakan, semua jurusan dikembalikan dengan matching_percentage 0.
    """
    return calculate_recommendation_leaderboard(payload)
