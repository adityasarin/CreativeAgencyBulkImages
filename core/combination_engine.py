import itertools
import uuid

from core.models import ComboModel, HookModel, PersonaModel


class CombinationEngine:
    def build_matrix(
        self,
        personas: list[PersonaModel],
        hooks: list[HookModel],
        max_hook_combo_size: int = 2,
    ) -> list[ComboModel]:
        combos = []
        for persona in personas:
            for size in range(1, max_hook_combo_size + 1):
                for hook_combo in itertools.combinations(hooks, size):
                    hook_list = list(hook_combo)
                    combos.append(ComboModel(
                        id=str(uuid.uuid4()),
                        persona=persona,
                        hooks=hook_list,
                        persona_text=self._format_persona(persona),
                        hooks_text=self._format_hooks(hook_list),
                    ))
        return combos

    def estimate_count(self, n_personas: int, n_hooks: int) -> dict:
        from math import comb
        single = n_personas * n_hooks
        double = n_personas * comb(n_hooks, 2) if n_hooks >= 2 else 0
        total_combos = single + double
        total_rows = total_combos * 3  # Safe + Bold + Minimal
        return {
            "single_hook_combos": single,
            "double_hook_combos": double,
            "total_combos": total_combos,
            "total_rows": total_rows,
        }

    @staticmethod
    def _format_persona(persona: PersonaModel) -> str:
        return f"{persona.name}: {persona.description}"

    @staticmethod
    def _format_hooks(hooks: list[HookModel]) -> str:
        if len(hooks) == 1:
            return f"{hooks[0].name} ({hooks[0].hook_type}): {hooks[0].description}"
        parts = []
        for h in hooks:
            parts.append(f"- {h.name} ({h.hook_type}): {h.description}")
        return "Combined hook strategy:\n" + "\n".join(parts)
