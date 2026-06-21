import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Optional

from core.models import ExcelRowModel, GenerationResultModel, ProcessedProductImage
from image_gen.base_provider import BaseImageProvider
from image_gen.compositor import AdCompositor
from utils.naming_utils import make_image_filename


class BatchRunner:
    def __init__(self, provider: BaseImageProvider):
        self._provider = provider
        self._max_workers = int(os.getenv("IMAGE_GEN_WORKERS", "3"))
        self._max_retries = int(os.getenv("IMAGE_GEN_MAX_RETRIES", "2"))
        self._compositor = AdCompositor()

    def run(
        self,
        rows: list[ExcelRowModel],
        output_dir: str,
        progress_callback: Callable[[GenerationResultModel], None],
        stop_check: Callable[[], bool],
        product_image: Optional[ProcessedProductImage] = None,
    ) -> list[GenerationResultModel]:
        results = []
        futures_map = {}

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            for seq, row in enumerate(rows, start=1):
                if stop_check():
                    break
                future = executor.submit(
                    self._generate_single, row, output_dir, seq, product_image
                )
                futures_map[future] = row

            for future in as_completed(futures_map):
                if stop_check():
                    future.cancel()
                    continue
                result = future.result()
                results.append(result)
                progress_callback(result)

        return results

    def _generate_single(
        self,
        row: ExcelRowModel,
        output_dir: str,
        seq: int,
        product_image: Optional[ProcessedProductImage],
    ) -> GenerationResultModel:
        filename = make_image_filename(seq, row)
        image_path = str(Path(output_dir) / filename)
        start = time.time()

        for attempt in range(self._max_retries + 1):
            try:
                img_bytes = self._provider.generate(row.prompt, row.negative_prompt)

                # Composite product if provided
                if product_image and product_image.cleaned_png_bytes:
                    img_bytes = self._compositor.composite(
                        ad_image_bytes=img_bytes,
                        product_png_bytes=product_image.cleaned_png_bytes,
                        placement_zone=row.product_placement_zone,
                    )

                Path(image_path).write_bytes(img_bytes)
                elapsed = round(time.time() - start, 2)
                return GenerationResultModel(
                    row_id=row.row_id,
                    client_name=row.client_name,
                    persona_name=row.persona_name,
                    hooks_text=row.hooks_text,
                    prompt=row.prompt,
                    negative_prompt=row.negative_prompt,
                    image_path=image_path,
                    image_filename=filename,
                    provider=self._provider.get_provider_name(),
                    status="success",
                    generation_time_sec=elapsed,
                    cost_usd=self._provider.get_cost_per_image_usd(),
                )
            except Exception as exc:
                if attempt < self._max_retries:
                    time.sleep(5 * (attempt + 1))  # 5s, 10s
                else:
                    elapsed = round(time.time() - start, 2)
                    return GenerationResultModel(
                        row_id=row.row_id,
                        client_name=row.client_name,
                        persona_name=row.persona_name,
                        hooks_text=row.hooks_text,
                        prompt=row.prompt,
                        negative_prompt=row.negative_prompt,
                        image_path="",
                        image_filename=filename,
                        provider=self._provider.get_provider_name(),
                        status="failed",
                        error_message=str(exc),
                        generation_time_sec=elapsed,
                        cost_usd=0.0,
                    )
