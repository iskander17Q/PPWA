import os
import uuid
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from typing import Dict, Any, Tuple


EPS = 1e-6


def _load_image_rgb(path: str) -> np.ndarray:
    img = Image.open(path).convert('RGB')
    arr = np.array(img).astype(np.float32)
    # Normalize to 0..1
    arr /= 255.0
    return arr


def compute_exg(arr: np.ndarray) -> np.ndarray:
    # ExG = 2G - R - B
    R = arr[:, :, 0]
    G = arr[:, :, 1]
    B = arr[:, :, 2]
    exg = 2 * G - R - B
    # Normalize to 0..1 by clipping and scaling
    # first shift to have min 0
    exg_min = exg.min()
    exg = exg - exg_min
    exg_max = exg.max() + EPS
    exg = exg / exg_max
    return exg


def compute_vari(arr: np.ndarray) -> np.ndarray:
    R = arr[:, :, 0]
    G = arr[:, :, 1]
    B = arr[:, :, 2]
    vari = (G - R) / (G + R - B + EPS)
    # Clip to reasonable range and normalize to 0..1 for heatmap
    vari = np.nan_to_num(vari, nan=0.0, posinf=0.0, neginf=0.0)
    vmin = np.percentile(vari, 2)
    vmax = np.percentile(vari, 98)
    vari = (vari - vmin) / (vmax - vmin + EPS)
    vari = np.clip(vari, 0.0, 1.0)
    return vari


def make_mask_from_exg(exg: np.ndarray, threshold: float = 0.15) -> np.ndarray:
    mask = exg > threshold
    return mask


def _save_heatmap(img: np.ndarray, path: str, cmap: str = 'RdYlGn'):
    plt.figure(figsize=(6, 4))
    plt.axis('off')
    plt.imshow(img, cmap=cmap)
    plt.tight_layout(pad=0)
    plt.savefig(path, bbox_inches='tight', pad_inches=0)
    plt.close()


def _overlay_mask_on_image(orig_arr: np.ndarray, mask: np.ndarray) -> Image.Image:
    img = (orig_arr * 255).astype(np.uint8)
    pil = Image.fromarray(img)
    overlay = Image.new('RGBA', pil.size, (0, 0, 0, 0))
    mask_img = Image.fromarray((mask.astype(np.uint8) * 255).astype(np.uint8))
    # create green overlay where mask
    green = Image.new('RGBA', pil.size, (0, 255, 0, 100))
    overlay.paste(green, (0, 0), mask_img)
    combined = Image.alpha_composite(pil.convert('RGBA'), overlay)
    return combined


def analyze_image(path: str, workdir: str) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Analyze image and produce metrics and paths to generated images.

    Returns (metrics, assets) where assets contain paths to heatmap_exg, heatmap_vari, overlay.
    """
    arr = _load_image_rgb(path)

    exg = compute_exg(arr)
    vari = compute_vari(arr)
    mask = make_mask_from_exg(exg)

    coverage = float(mask.mean() * 100.0)
    # metrics derived on masked area; if mask empty, be robust
    if mask.sum() > 0:
        exg_mean = float(exg[mask].mean())
        vari_mean = float(vari[mask].mean())
    else:
        exg_mean = 0.0
        vari_mean = 0.0

    # health score simple heuristic: combine exg_mean and vari_mean with coverage
    score = (0.5 * exg_mean + 0.5 * vari_mean) * 100.0
    # blend with coverage (weight 0.7 for score, 0.3 for coverage fraction)
    health_score = float(0.7 * score + 0.3 * coverage)
    health_score = max(0.0, min(100.0, health_score))

    # Generate assets
    uid = uuid.uuid4().hex[:8]
    os.makedirs(workdir, exist_ok=True)
    heat_exg_path = os.path.join(workdir, f'exg_{uid}.png')
    heat_vari_path = os.path.join(workdir, f'vari_{uid}.png')
    overlay_path = os.path.join(workdir, f'overlay_{uid}.png')

    _save_heatmap(exg, heat_exg_path, cmap='RdYlGn')
    _save_heatmap(vari, heat_vari_path, cmap='viridis')
    overlay = _overlay_mask_on_image(arr, mask)
    overlay.save(overlay_path)

    metrics = {
        'vegetation_coverage_percent': coverage,
        'exg_mean': exg_mean,
        'vari_mean': vari_mean,
        'health_score': health_score,
    }
    assets = {
        'heat_exg': heat_exg_path,
        'heat_vari': heat_vari_path,
        'overlay': overlay_path,
    }
    return metrics, assets
