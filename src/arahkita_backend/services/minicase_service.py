from arahkita_backend.adapters.openrouter_adapter import OpenRouterAdapter
from arahkita_backend.schemas.essay_eval import (
    EssayEvaluationRequest,
    EssayEvaluationResult,
)
from arahkita_backend.schemas.minicase_node import (
    GenerateMinicasesRequest,
    MinicaseNode,
)
from arahkita_backend.utils.ids import generate_uuid


def sanitize_title(raw_title: str) -> str:
    """Memastikan judul minicase interaktif maksimal terdiri dari 2 kata."""
    words = raw_title.strip().split()
    if len(words) > 2:
        return " ".join(words[:2])
    return raw_title.strip() or "Studi Kasus"


async def generate_minicases_tree(
    request: GenerateMinicasesRequest,
    adapter: OpenRouterAdapter,
) -> list[MinicaseNode]:
    """Men-generate rantai node minicase dari mata kuliah dasar yang dipilihkan LLM.

    Alur:
    1. Memanggil LLM adapter untuk mendapatkan 3–5 mata kuliah dasar berserta studi kasusnya.
    2. Merakit node-node trial secara berpasangan per mata kuliah (1 PG + 1 Esai).
    3. Memberikan UUID v4, menetapkan parent_id = major_id (relasi 1:N).
    4. Menerapkan warna seragam mengikuti circle_color milik major_node.
    5. Menghubungkan rantai child_id dari node ke-i ke node ke-(i+1).
    6. Node terakhir memiliki is_parent = False dan child_id = None.
    7. Mengembalikan list[MinicaseNode] terurut (node [0] langsung mengisi child_id major_node).
    """
    subjects = await adapter.fetch_minicases_generation(request)

    # Flatten ke list draft node
    raw_nodes_data: list[dict[str, object]] = []
    for subject in subjects:
        # Node 1: Pilihan Ganda (Objektif)
        raw_nodes_data.append(
            {
                "subject_name": subject.subject_name,
                "node_type": "multiple_choice",
                "minicase_title": sanitize_title(subject.mcq.minicase_title),
                "question": subject.mcq.question,
                "options": subject.mcq.options,
                "correct_answer": subject.mcq.correct_answer,
                "evaluation_hint": None,
            }
        )
        # Node 2: Esai Reflektif
        raw_nodes_data.append(
            {
                "subject_name": subject.subject_name,
                "node_type": "essay",
                "minicase_title": sanitize_title(subject.essay.minicase_title),
                "question": subject.essay.question,
                "options": None,
                "correct_answer": None,
                "evaluation_hint": subject.essay.evaluation_hint,
            }
        )

    total_nodes = len(raw_nodes_data)
    node_ids: list[str] = [generate_uuid() for _ in range(total_nodes)]

    assembled_nodes: list[MinicaseNode] = []
    for idx, data in enumerate(raw_nodes_data):
        is_last = idx == total_nodes - 1
        child_id = None if is_last else node_ids[idx + 1]

        options_val = data["options"]
        typed_options: list[str] | None = (
            [str(opt) for opt in options_val]
            if isinstance(options_val, list)
            else None
        )

        assembled_nodes.append(
            MinicaseNode(
                id=node_ids[idx],
                parent_id=request.major_id,
                minicase_number=idx + 1,
                minicase_title=str(data["minicase_title"]),
                subject_name=str(data["subject_name"]),
                node_type="multiple_choice" if data["node_type"] == "multiple_choice" else "essay",
                question=str(data["question"]),
                options=typed_options,
                correct_answer=str(data["correct_answer"]) if data["correct_answer"] is not None else None,
                evaluation_hint=str(data["evaluation_hint"]) if data["evaluation_hint"] is not None else None,
                is_parent=not is_last,
                circle_color=request.circle_color,
                is_done=False,
                child_id=child_id,
            )
        )

    return assembled_nodes


async def evaluate_student_essay(
    request: EssayEvaluationRequest,
    adapter: OpenRouterAdapter,
) -> EssayEvaluationResult:
    """Mengevaluasi esai siswa menggunakan adapter AI."""
    return await adapter.evaluate_essay_answer(request)
