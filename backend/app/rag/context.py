from .retriever import RetrievalResult

class ContextBuilder:
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens

    def build(self, results: list[RetrievalResult], include_metadata: bool = True) -> str:
        context_parts = []
        current_tokens = 0

        for result in results:
            formatted = self._format_result(result, include_metadata)
            result_tokens = len(formatted.split()) * 1.3

            if current_tokens + result_tokens > self.max_tokens:
                break

            context_parts.append(formatted)
            current_tokens += result_tokens

        return "\n\n---\n\n".join(context_parts)

    def _format_result(self, result: RetrievalResult, include_metadata: bool) -> str:
        header = f"[{result.source_type.upper()}] {result.date}" if include_metadata else ""
        return f"{header}\n{result.content}".strip()

context_builder = ContextBuilder()
