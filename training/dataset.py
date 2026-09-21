import os
import cv2
import numpy as np
from torch.utils.data import Dataset
from pathlib import Path
from typing import Tuple, Optional
import albumentations as A

class OilSpillDataset(Dataset):
    def __init__(
        self,
        data_dir: str,
        image_size: Tuple[int, int] = (256, 256),
        augment: bool = False
    ):
        self.data_dir = Path(data_dir)
        self.image_size = image_size
        self.augment = augment

        self.image_paths = sorted(list((self.data_dir / "images").glob("*.png")) +
                                  list((self.data_dir / "images").glob("*.jpg")))
        self.mask_paths = [self.data_dir / "masks" / f"{p.stem}.png" for p in self.image_paths]

        # If masks are .jpg, try that too
        self.mask_paths = [p if p.exists() else p.with_suffix(".jpg") for p in self.mask_paths]
        self.mask_paths = [p for p in self.mask_paths if p.exists()]

        # Filter pairs where mask exists
        valid = []
        for img, msk in zip(self.image_paths, self.mask_paths):
            if msk.exists():
                valid.append((img, msk))
        self.image_paths = [p[0] for p in valid]
        self.mask_paths = [p[1] for p in valid]

        print(f"[Dataset] Loaded {len(self.image_paths)} images from {data_dir}")

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        mask_path = self.mask_paths[idx]

        image = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)

        if image is None:
            raise ValueError(f"Could not load image: {img_path}")
        if mask is None:
            mask = np.zeros(image.shape, dtype=np.uint8)

        # Convert to 3‑channel (U‑Net expects 3 channels)
        image_3ch = np.stack([image] * 3, axis=2)
        mask = (mask > 127).astype(np.float32)

        # Augmentations
        transforms = [
            A.Resize(height=self.image_size[0], width=self.image_size[1]),
            A.Normalize(mean=0.5, std=0.5),
        ]
        if self.augment:
            transforms.extend([
                A.HorizontalFlip(p=0.5),
                A.VerticalFlip(p=0.5),
                A.RandomRotate90(p=0.5),
                A.ShiftScaleRotate(shift_limit=0.05, scale_limit=0.1, rotate_limit=15, p=0.5),
                A.GaussNoise(var_limit=(10.0, 50.0), p=0.3),
            ])
        aug = A.Compose(transforms)

        transformed = aug(image=image_3ch, mask=mask)
        image = transformed["image"]
        mask = transformed["mask"]

        # Convert to (C, H, W)
        image = np.transpose(image, (2, 0, 1))
        mask = np.expand_dims(mask, axis=0)

        return image.astype(np.float32), mask.astype(np.float32)