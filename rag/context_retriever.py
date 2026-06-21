from rag.chroma_store import ChromaStore

CAMPAIGNS = "campaigns"
PROMPTS = "prompts"


class ContextRetriever:
    def __init__(self, store: ChromaStore):
        self._store = store

    def retrieve_similar_campaigns(self, client_brief: str, n: int = 3) -> str:
        results = self._store.query(CAMPAIGNS, client_brief, n_results=n)
        if not results:
            return ""
        lines = []
        for i, r in enumerate(results, 1):
            meta = r["metadata"]
            lines.append(
                f"Past campaign {i} ({meta.get('client_name','?')}, {meta.get('run_date','?')[:10]}): "
                f"{r['document'][:200]}"
            )
        return "Similar past campaigns for context:\n" + "\n".join(lines)

    def retrieve_similar_prompts(self, combo_description: str, n: int = 2) -> str:
        results = self._store.query(PROMPTS, combo_description, n_results=n)
        if not results:
            return ""
        lines = []
        for i, r in enumerate(results, 1):
            meta = r["metadata"]
            lines.append(
                f"[Reference prompt {i} — {meta.get('persona_name','?')}]: "
                f"{r['document'][:300]}"
            )
        return "Reference prompts from similar past campaigns:\n" + "\n".join(lines)
