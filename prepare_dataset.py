import os
import shutil
from pathlib import Path
from sklearn.model_selection import train_test_split

def find_folders(base):
    """Find all 'images' and 'labels'/'masks' folders recursively."""
    img_folders = []
    mask_folders = []
    for root, dirs, files in os.walk(base):
        if "images" in dirs:
            img_folders.append(Path(root) / "images")
        if "labels" in dirs:
            mask_folders.append(Path(root) / "labels")
        if "masks" in dirs:
            mask_folders.append(Path(root) / "masks")
    return img_folders, mask_folders

def prepare_dataset(raw_dir="data/raw", output_dir="data", val_size=0.15):
    raw_path = Path(raw_dir)
    if not raw_path.exists():
        print(f"❌ Raw directory not found: {raw_path}")
        return

    # Find all images and masks folders
    img_folders, mask_folders = find_folders(raw_path)
    print("Found image folders:", img_folders)
    print("Found mask folders:", mask_folders)

    # Identify train and test pairs by parent folder name
    train_img = None
    train_mask = None
    test_img = None
    test_mask = None

    for img in img_folders:
        parent = img.parent.name
        if parent == "train":
            train_img = img
        elif parent == "test":
            test_img = img

    for mask in mask_folders:
        parent = mask.parent.name
        if parent == "train":
            train_mask = mask
        elif parent == "test":
            test_mask = mask

    # If not found, try alternative: look for 'train' folder directly
    if train_img is None:
        # Try inside oil-spill
        oil_spill = raw_path / "oil-spill"
        if oil_spill.exists():
            train_img = oil_spill / "train" / "images"
            train_mask = oil_spill / "train" / "labels"
            if not train_mask.exists():
                train_mask = oil_spill / "train" / "masks"
            test_img = oil_spill / "test" / "images"
            test_mask = oil_spill / "test" / "labels"
            if not test_mask.exists():
                test_mask = oil_spill / "test" / "masks"

    # Verify
    if train_img is None or not train_img.exists():
        print("❌ Could not find train images folder.")
        print("   Please check your data/raw directory structure.")
        return
    if train_mask is None or not train_mask.exists():
        print("❌ Could not find train masks/labels folder.")
        return

    print(f"✅ Train images: {train_img}")
    print(f"✅ Train masks: {train_mask}")

    # Gather training pairs
    train_images = list(train_img.glob("*.png")) + list(train_img.glob("*.jpg"))
    train_pairs = []
    for img in train_images:
        mask = train_mask / f"{img.stem}.png"
        if not mask.exists():
            mask = train_mask / f"{img.stem}.jpg"
        if mask.exists():
            train_pairs.append((img, mask))
        else:
            print(f"⚠️ Missing mask for {img.name}")

    print(f"✅ Found {len(train_pairs)} training pairs")

    if len(train_pairs) == 0:
        print("❌ No valid pairs found. Check your images and masks.")
        return

    # Split train into train + val
    train_pairs, val_pairs = train_test_split(train_pairs, test_size=val_size, random_state=42)

    # Copy to output
    for split, pairs in [("train", train_pairs), ("val", val_pairs)]:
        out_img = Path(output_dir) / split / "images"
        out_mask = Path(output_dir) / split / "masks"
        out_img.mkdir(parents=True, exist_ok=True)
        out_mask.mkdir(parents=True, exist_ok=True)
        for img, msk in pairs:
            shutil.copy(img, out_img / img.name)
            shutil.copy(msk, out_mask / msk.name)

    # Copy test set if exists
    if test_img and test_img.exists() and test_mask and test_mask.exists():
        test_images = list(test_img.glob("*.png")) + list(test_img.glob("*.jpg"))
        test_pairs = []
        for img in test_images:
            mask = test_mask / f"{img.stem}.png"
            if not mask.exists():
                mask = test_mask / f"{img.stem}.jpg"
            if mask.exists():
                test_pairs.append((img, mask))
        if test_pairs:
            out_img = Path(output_dir) / "test" / "images"
            out_mask = Path(output_dir) / "test" / "masks"
            out_img.mkdir(parents=True, exist_ok=True)
            out_mask.mkdir(parents=True, exist_ok=True)
            for img, msk in test_pairs:
                shutil.copy(img, out_img / img.name)
                shutil.copy(msk, out_mask / msk.name)
            print(f"✅ Test: {len(test_pairs)} pairs")
        else:
            print("⚠️ Test folder exists but no valid pairs found.")
    else:
        print("⚠️ Test folder not found – skipping test set.")

    print(f"✅ Train: {len(train_pairs)}, Val: {len(val_pairs)}")
    print("   Data ready at data/train/, data/val/, data/test/ (if test existed).")

if __name__ == "__main__":
    prepare_dataset()