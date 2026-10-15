import unittest
from fastapi.testclient import TestClient

from arahkita_backend.main import app
from arahkita_backend.schemas.major_node import MajorNode
from arahkita_backend.schemas.preview import (
    MajorNodeCareerPath,
    MajorNodePreview,
)
from arahkita_backend.schemas.recommendation_result import (
    MajorRecommendationResult,
    RecommendationResultsRequest,
)
from arahkita_backend.services.recommendation_result_service import (
    calculate_recommendation_leaderboard,
)


class TestRecommendationResultsService(unittest.TestCase):
    def setUp(self) -> None:
        self.node_ti = MajorNode(
            id="11111111-1111-4111-8111-111111111111",
            major_name="Teknik Informatika",
            circle_color="#4F46E5",
        )
        self.node_si = MajorNode(
            id="22222222-2222-4222-8222-222222222222",
            major_name="Sistem Informasi",
            circle_color="#06B6D4",
        )
        self.node_dkv = MajorNode(
            id="33333333-3333-4333-8333-333333333333",
            major_name="Desain Komunikasi Visual",
            circle_color="#EC4899",
        )

        self.preview_ti = MajorNodePreview(
            id="aaaa1111-1111-4111-8111-111111111111",
            major_node_id=self.node_ti.id,
            preview="Evaluasi Teknik Informatika sangat memuaskan.",
            matching_percentage=95,
            career_paths=[
                MajorNodeCareerPath(
                    id="cccc1111-1111-4111-8111-111111111111",
                    major_node_preview_id="aaaa1111-1111-4111-8111-111111111111",
                    title="Software Engineer",
                    detail="Mengembangkan arsitektur perangkat lunak scalable.",
                )
            ],
        )
        self.preview_si = MajorNodePreview(
            id="aaaa2222-2222-4222-8222-222222222222",
            major_node_id=self.node_si.id,
            preview="Evaluasi Sistem Informasi cukup baik.",
            matching_percentage=78,
            career_paths=[
                MajorNodeCareerPath(
                    id="cccc2222-2222-4222-8222-222222222222",
                    major_node_preview_id="aaaa2222-2222-4222-8222-222222222222",
                    title="Product Manager",
                    detail="Menjembatani bisnis dan teknologi dalam produk digital.",
                )
            ],
        )

    def test_empty_major_nodes(self) -> None:
        request = RecommendationResultsRequest(
            major_nodes=[],
            previews=[self.preview_ti],
        )
        results = calculate_recommendation_leaderboard(request)
        self.assertEqual(results, [])

    def test_all_uncompleted_nodes(self) -> None:
        request = RecommendationResultsRequest(
            major_nodes=[self.node_ti, self.node_si, self.node_dkv],
            previews=[],
        )
        results = calculate_recommendation_leaderboard(request)
        self.assertEqual(len(results), 3)

        for item in results:
            self.assertEqual(item.matching_percentage, 0)
            self.assertFalse(item.is_completed)
            self.assertIsNone(item.preview)

        # Mempertahankan urutan input semula
        self.assertEqual(results[0].major_name, "Teknik Informatika")
        self.assertEqual(results[1].major_name, "Sistem Informasi")
        self.assertEqual(results[2].major_name, "Desain Komunikasi Visual")

    def test_partially_completed_nodes_sorted_descending(self) -> None:
        # Input order: DKV, SI, TI
        # TI has 95%, SI has 78%, DKV has no preview (0%)
        request = RecommendationResultsRequest(
            major_nodes=[self.node_dkv, self.node_si, self.node_ti],
            previews=[self.preview_si, self.preview_ti],
        )
        results = calculate_recommendation_leaderboard(request)
        self.assertEqual(len(results), 3)

        # Rank 1: TI (95%)
        self.assertEqual(results[0].id, self.node_ti.id)
        self.assertEqual(results[0].matching_percentage, 95)
        self.assertTrue(results[0].is_completed)
        self.assertIsNotNone(results[0].preview)

        # Rank 2: SI (78%)
        self.assertEqual(results[1].id, self.node_si.id)
        self.assertEqual(results[1].matching_percentage, 78)
        self.assertTrue(results[1].is_completed)
        self.assertIsNotNone(results[1].preview)

        # Rank 3: DKV (0% - belum dikerjakan)
        self.assertEqual(results[2].id, self.node_dkv.id)
        self.assertEqual(results[2].matching_percentage, 0)
        self.assertFalse(results[2].is_completed)
        self.assertIsNone(results[2].preview)

    def test_duplicate_previews_picks_highest_score(self) -> None:
        preview_ti_lower = MajorNodePreview(
            id="aaaa3333-3333-4333-8333-333333333333",
            major_node_id=self.node_ti.id,
            preview="Skor percobaan awal.",
            matching_percentage=60,
            career_paths=[
                MajorNodeCareerPath(
                    id="cccc3333-3333-4333-8333-333333333333",
                    major_node_preview_id="aaaa3333-3333-4333-8333-333333333333",
                    title="Junior Dev",
                    detail="Pemrograman dasar.",
                )
            ],
        )
        request = RecommendationResultsRequest(
            major_nodes=[self.node_ti],
            previews=[preview_ti_lower, self.preview_ti],
        )
        results = calculate_recommendation_leaderboard(request)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].matching_percentage, 95)

    def test_orphan_preview_ignored(self) -> None:
        orphan_preview = MajorNodePreview(
            id="aaaa9999-9999-4999-8999-999999999999",
            major_node_id="99999999-9999-4999-8999-999999999999",
            preview="Preview jurusan tidak dikenal.",
            matching_percentage=99,
            career_paths=[
                MajorNodeCareerPath(
                    id="cccc9999-9999-4999-8999-999999999999",
                    major_node_preview_id="aaaa9999-9999-4999-8999-999999999999",
                    title="Unknown Career",
                    detail="Unknown detail.",
                )
            ],
        )
        request = RecommendationResultsRequest(
            major_nodes=[self.node_ti],
            previews=[orphan_preview],
        )
        results = calculate_recommendation_leaderboard(request)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].matching_percentage, 0)
        self.assertFalse(results[0].is_completed)

    def test_stable_sort_on_equal_percentage(self) -> None:
        preview_si_equal = MajorNodePreview(
            id="aaaa4444-4444-4444-8444-444444444444",
            major_node_id=self.node_si.id,
            preview="Skor TI dan SI seimbang.",
            matching_percentage=95,
            career_paths=[
                MajorNodeCareerPath(
                    id="cccc4444-4444-4444-8444-444444444444",
                    major_node_preview_id="aaaa4444-4444-4444-8444-444444444444",
                    title="Solution Architect",
                    detail="Merancang arsitektur terintegrasi.",
                )
            ],
        )
        # Urutan input: SI duluan, baru TI. Keduanya bernilai 95%.
        request = RecommendationResultsRequest(
            major_nodes=[self.node_si, self.node_ti],
            previews=[preview_si_equal, self.preview_ti],
        )
        results = calculate_recommendation_leaderboard(request)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].id, self.node_si.id)
        self.assertEqual(results[1].id, self.node_ti.id)


class TestRecommendationResultsAPI(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_post_recommendation_results_success(self) -> None:
        payload = {
            "major_nodes": [
                {
                    "id": "11111111-1111-4111-8111-111111111111",
                    "major_name": "Teknik Informatika",
                    "circle_color": "#4F46E5",
                    "child_id": None,
                },
                {
                    "id": "22222222-2222-4222-8222-222222222222",
                    "major_name": "Sistem Informasi",
                    "circle_color": "#06B6D4",
                    "child_id": None,
                },
            ],
            "previews": [
                {
                    "id": "aaaa1111-1111-4111-8111-111111111111",
                    "major_node_id": "11111111-1111-4111-8111-111111111111",
                    "preview": "Sangat cocok dengan bakat komputasi.",
                    "matching_percentage": 90,
                    "career_paths": [
                        {
                            "id": "cccc1111-1111-4111-8111-111111111111",
                            "major_node_preview_id": "aaaa1111-1111-4111-8111-111111111111",
                            "title": "Data Scientist",
                            "detail": "Analisis data dan model prediktif.",
                        }
                    ],
                }
            ],
        }

        response = self.client.post("/api/v1/recommendation-results", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)

        # Leaderboard rank 1: TI (90%)
        self.assertEqual(data[0]["major_name"], "Teknik Informatika")
        self.assertEqual(data[0]["matching_percentage"], 90)
        self.assertTrue(data[0]["is_completed"])
        self.assertIsNotNone(data[0]["preview"])
        self.assertEqual(data[0]["preview"]["matching_percentage"], 90)

        # Leaderboard rank 2: SI (0%)
        self.assertEqual(data[1]["major_name"], "Sistem Informasi")
        self.assertEqual(data[1]["matching_percentage"], 0)
        self.assertFalse(data[1]["is_completed"])
        self.assertIsNone(data[1]["preview"])

    def test_post_recommendation_results_empty(self) -> None:
        payload = {"major_nodes": [], "previews": []}
        response = self.client.post("/api/v1/recommendation-results", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_post_recommendation_results_invalid_uuid(self) -> None:
        payload = {
            "major_nodes": [
                {
                    "id": "bukan-uuid",
                    "major_name": "Teknik Informatika",
                    "circle_color": "#4F46E5",
                }
            ],
            "previews": [],
        }
        response = self.client.post("/api/v1/recommendation-results", json=payload)
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
