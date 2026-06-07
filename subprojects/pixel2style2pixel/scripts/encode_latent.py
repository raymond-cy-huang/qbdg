import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

import numpy as np
import torch
from PIL import Image

REPO_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_DIR))

from configs import data_configs
from models.psp import pSp
from utils.common import tensor2im


def collect_image_paths(path):
    """Returns one image path or all supported images under a directory."""
    path = Path(path)
    if path.is_file():
        return [path]

    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".ppm", ".tiff"}
    return sorted(
        image for image in path.rglob("*") if image.suffix.lower() in image_exts
    )


def load_opts(args):
    """Loads training options stored inside the pSp checkpoint."""
    ckpt = torch.load(args.checkpoint_path, map_location="cpu")
    opts = ckpt["opts"]
    opts.update(vars(args))
    if "learn_in_w" not in opts:
        opts["learn_in_w"] = False
    if "output_size" not in opts:
        opts["output_size"] = 1024
    if "dataset_type" not in opts:
        opts["dataset_type"] = "ffhq_encode"
    opts["device"] = "cuda" if torch.cuda.is_available() else "cpu"
    return Namespace(**opts)


def load_image(path, transform, label_nc):
    """Applies the same inference transform used by pSp reconstruction."""
    image = Image.open(path)
    image = image.convert("RGB") if label_nc == 0 else image.convert("L")
    return transform(image).unsqueeze(0)


def main():
    parser = ArgumentParser()
    parser.add_argument("--checkpoint_path", required=True, help="Path to pSp checkpoint.")
    parser.add_argument("--image_path", required=True, help="Input image file or directory.")
    parser.add_argument("--output_dir", default="latent_outputs", help="Where to save .npy files.")
    parser.add_argument(
        "--save_reconstruction",
        action="store_true",
        help="Also save the image reconstructed from the latent code.",
    )
    args = parser.parse_args()

    opts = load_opts(args)
    net = pSp(opts).eval().to(opts.device)

    dataset_args = data_configs.DATASETS[opts.dataset_type]
    transform = dataset_args["transforms"](opts).get_transforms()["transform_inference"]

    image_paths = collect_image_paths(opts.image_path)
    if not image_paths:
        raise RuntimeError(f"No images found under {opts.image_path}")

    output_dir = Path(opts.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for image_path in image_paths:
        input_tensor = load_image(image_path, transform, opts.label_nc).to(opts.device).float()

        with torch.no_grad():
            reconstruction, latent = net(
                input_tensor,
                randomize_noise=False,
                resize=False,
                return_latents=True,
            )

        stem = image_path.stem
        latent_path = output_dir / f"{stem}_latent.npy"
        np.save(latent_path, latent.detach().cpu().numpy())
        print(f"Saved latent: {latent_path} shape={tuple(latent.shape)}")

        if opts.save_reconstruction:
            image = tensor2im(reconstruction[0])
            recon_path = output_dir / f"{stem}_reconstruction.png"
            Image.fromarray(np.array(image)).save(recon_path)
            print(f"Saved reconstruction: {recon_path}")


if __name__ == "__main__":
    main()
