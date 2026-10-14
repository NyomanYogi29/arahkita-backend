from arahkita_backend.system_prompt import system_prompt
from .types import InputKeminatan
from .tools import TOOL_MAP
from ollama import Client, Message, ChatResponse
import json

MAX_STEPS = 5

class LLMService:
    def __init__(self, model: str ="qwen3.5:9b", system_prompt: str = system_prompt()) -> None:
        self.model: str = model
        self.system_prompt: str = system_prompt
        self.client: Client = Client()

    def counseling_response(self, profile: InputKeminatan) -> str:
        json_payload: str = json.dumps(profile, indent=2, ensure_ascii=False)

        user_message: str = (
            "Halo konselor, ini adalah keminatan dan nilai 3 mata pelajaran saya:\n"
            f"```json\n{json_payload}```"
            "Tolong berikan pandangan anda terhadap masa depan karir saya sebagai siswa SMA akhir berdasarkan data yang saya lampirkan tanpa bias"
        )

        messages: list[Message] = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=user_message)
        ]

        for _ in range(MAX_STEPS):
            response: ChatResponse = self.client.chat(  # pyright: ignore[reportUnknownMemberType]
                model=self.model,
                messages=messages,
                stream=False
            )
            messages.append(response.message)

            if not response.message.tool_calls:
                return response.message.content or ""

            for call in response.message.tool_calls:
                fn = TOOL_MAP.get(call.function.name)
                try:
                    result = fn(**call.function.arguments) if fn else "Tool tidak ditemukan"
                except Exception as e:
                    result = f"Error: {e}"

                messages.append(
                    Message(role="tool", tool_name=call.function.name, content=str(result))
                )
        return "Terjadi kesalahan saat memproses permintaan"

    def generate(self, user_input: str) -> str:
        messages: list[Message] = []

        if self.system_prompt:
            messages.append(
                Message(role="system", content=self.system_prompt)
            )

        messages.append(
            Message(role="user", content=user_input)
        )

        response: ChatResponse = self.client.chat(  # pyright: ignore[reportUnknownMemberType]
            model=self.model,
            messages=messages,
            stream=False
        )

        return response.message.content or ""