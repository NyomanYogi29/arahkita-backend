from arahkita_backend.schemas.preview import MajorNodePreview
from arahkita_backend.schemas.recommendation_result import (
    MajorRecommendationResult,
    RecommendationResultsRequest,
)


def calculate_recommendation_leaderboard(
    request: RecommendationResultsRequest,
) -> list[MajorRecommendationResult]:
    """Menyusun dan mengurutkan leaderboard jurusan berdasarkan matching_percentage.

    Aturan & Alur:
    1. Jika request.major_nodes kosong, mengembalikan list kosong [].
    2. Memetakan previews berdasarkan major_node_id. Jika terdapat beberapa preview
       untuk major_node yang sama, pilih preview dengan matching_percentage tertinggi.
    3. Preview yang tidak merujuk ke major_node manapun diabaikan.
    4. Untuk setiap major_node:
       - Jika memiliki preview yang cocok: matching_percentage diambil dari preview,
         is_completed disetel True, dan objek preview disertakan.
       - Jika belum ada preview: matching_percentage = 0, is_completed = False,
         dan preview bernilai None.
    5. Melakukan stable sort descending berdasarkan matching_percentage.
       Jurusan dengan persentase sama akan mempertahankan urutan input semula.
    """
    if not request.major_nodes:
        return []

    # Petakan preview terbaik (skor tertinggi) per major_node_id
    best_previews: dict[str, MajorNodePreview] = {}
    for preview in request.previews:
        existing = best_previews.get(preview.major_node_id)
        if (
            existing is None
            or preview.matching_percentage > existing.matching_percentage
        ):
            best_previews[preview.major_node_id] = preview

    # Bangun entitas MajorRecommendationResult
    results: list[MajorRecommendationResult] = []
    for node in request.major_nodes:
        matched_preview = best_previews.get(node.id)
        if matched_preview is not None:
            results.append(
                MajorRecommendationResult(
                    id=node.id,
                    major_name=node.major_name,
                    circle_color=node.circle_color,
                    child_id=node.child_id,
                    matching_percentage=matched_preview.matching_percentage,
                    is_completed=True,
                    preview=matched_preview,
                )
            )
        else:
            results.append(
                MajorRecommendationResult(
                    id=node.id,
                    major_name=node.major_name,
                    circle_color=node.circle_color,
                    child_id=node.child_id,
                    matching_percentage=0,
                    is_completed=False,
                    preview=None,
                )
            )

    # Stable sort descending berdasarkan matching_percentage
    results.sort(key=lambda item: item.matching_percentage, reverse=True)
    return results
