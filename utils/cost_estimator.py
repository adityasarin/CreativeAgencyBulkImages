COST_PER_IMAGE_USD = 0.08
AVG_SECONDS_PER_IMAGE = 15


def estimate(n_images: int) -> dict:
    cost = n_images * COST_PER_IMAGE_USD
    seconds = n_images * AVG_SECONDS_PER_IMAGE
    minutes, secs = divmod(seconds, 60)
    return {
        "provider": "dalle3",
        "n_images": n_images,
        "cost_usd": round(cost, 2),
        "time_str": f"~{minutes}m {secs}s" if minutes else f"~{secs}s",
    }
