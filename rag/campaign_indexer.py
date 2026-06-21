import uuid
from datetime import datetime

from core.models import GenerationResultModel
from rag.chroma_store import ChromaStore

CAMPAIGNS = "campaigns"
PROMPTS = "prompts"


class CampaignIndexer:
    def __init__(self, store: ChromaStore):
        self._store = store

    def index_campaign(
        self,
        client_brief: str,
        client_name: str,
        results: list[GenerationResultModel],
    ) -> None:
        if not results:
            return
        persona_names = list({r.persona_name for r in results})
        hook_names = list({r.hooks_text for r in results})
        n_success = sum(1 for r in results if r.status == "success")
        provider = results[0].provider if results else ""

        doc = f"{client_brief} | Personas: {', '.join(persona_names)} | Hooks: {', '.join(hook_names)}"
        meta = {
            "client_name": client_name,
            "run_date": datetime.now().isoformat(),
            "n_images": n_success,
            "provider": provider,
        }
        doc_id = str(uuid.uuid4())
        self._store.upsert(CAMPAIGNS, [doc], [meta], [doc_id])

    def index_prompts(self, results: list[GenerationResultModel]) -> None:
        docs, metas, ids = [], [], []
        for r in results:
            if r.status != "success":
                continue
            docs.append(r.prompt)
            metas.append({
                "persona_name": r.persona_name,
                "hooks_text": r.hooks_text,
                "provider": r.provider,
            })
            ids.append(r.row_id)
        if docs:
            self._store.upsert(PROMPTS, docs, metas, ids)
