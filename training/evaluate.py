import sys
import os
import argparse
import torch
import numpy as np
from torch.utils.data import DataLoader

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from segmentation import UNet
from training.dataset import OilSpillDataset
from training.metrics import MetricsCalculator

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="models/best_model.pth")
    parser.add_argument("--test_dir", default="data/test")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--batch_size", type=int, default=8)
    args = parser.parse_args()

    device = torch.device(args.device if torch.cuda.is_available() and args.device == "cuda" else "cpu")
    model = UNet(n_channels=3, n_classes=1)
    checkpoint = torch.load(args.model, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    test_dataset = OilSpillDataset(args.test_dir, augment=False)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False)

    metrics_calc = MetricsCalculator()
    all_preds, all_targets = [], []
    with torch.no_grad():
        for images, masks in test_loader:
            images = images.to(device)
            outputs = model(images)
            all_preds.append(outputs.cpu().numpy())
            all_targets.append(masks.numpy())
    all_preds = np.concatenate(all_preds)
    all_targets = np.concatenate(all_targets)
    metrics = metrics_calc.calculate_all(all_preds, all_targets)

    print("\n" + "="*50)
    print("TEST EVALUATION RESULTS")
    print("="*50)
    for k, v in metrics.items():
        print(f"{k.upper()}: {v:.4f}")
    print("="*50)

if __name__ == "__main__":
    main()