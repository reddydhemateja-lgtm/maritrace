import os
import sys
import argparse
import logging
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.ml.segmentation import UNet
from training.dataset import OilSpillDataset
from training.metrics import MetricsCalculator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Trainer:
    def __init__(self, model, device, lr=1e-4, epochs=50, batch_size=8, save_dir="models"):
        self.model = model.to(device)
        self.device = device
        self.epochs = epochs
        self.batch_size = batch_size
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)

        self.criterion = nn.BCELoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=lr)
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(self.optimizer, mode='min', factor=0.5, patience=10)
        self.metrics = MetricsCalculator()

        self.history = {"train_loss": [], "val_loss": [], "val_iou": [], "val_dice": []}

    def train_epoch(self, loader):
        self.model.train()
        total_loss = 0.0
        all_preds, all_targets = [], []
        for images, masks in loader:
            images, masks = images.to(self.device), masks.to(self.device)
            outputs = self.model(images)
            loss = self.criterion(outputs, masks)
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            total_loss += loss.item()
            all_preds.append(outputs.detach().cpu().numpy())
            all_targets.append(masks.cpu().numpy())
        all_preds = np.concatenate(all_preds)
        all_targets = np.concatenate(all_targets)
        metrics = self.metrics.calculate_all(all_preds, all_targets)
        return {"loss": total_loss / len(loader), **metrics}

    def validate(self, loader):
        self.model.eval()
        total_loss = 0.0
        all_preds, all_targets = [], []
        with torch.no_grad():
            for images, masks in loader:
                images, masks = images.to(self.device), masks.to(self.device)
                outputs = self.model(images)
                loss = self.criterion(outputs, masks)
                total_loss += loss.item()
                all_preds.append(outputs.cpu().numpy())
                all_targets.append(masks.cpu().numpy())
        all_preds = np.concatenate(all_preds)
        all_targets = np.concatenate(all_targets)
        metrics = self.metrics.calculate_all(all_preds, all_targets)
        return {"loss": total_loss / len(loader), **metrics}

    def train(self, train_loader, val_loader):
        best_val_loss = float('inf')
        for epoch in range(self.epochs):
            logger.info(f"Epoch {epoch+1}/{self.epochs}")
            train_metrics = self.train_epoch(train_loader)
            val_metrics = self.validate(val_loader)
            self.scheduler.step(val_metrics["loss"])
            logger.info(f"Train Loss: {train_metrics['loss']:.4f} | Val Loss: {val_metrics['loss']:.4f} | Val IoU: {val_metrics['iou']:.4f}")
            self.history["train_loss"].append(train_metrics["loss"])
            self.history["val_loss"].append(val_metrics["loss"])
            self.history["val_iou"].append(val_metrics["iou"])
            self.history["val_dice"].append(val_metrics["dice"])
            if val_metrics["loss"] < best_val_loss:
                best_val_loss = val_metrics["loss"]
                torch.save({
                    "model_state_dict": self.model.state_dict(),
                    "optimizer_state_dict": self.optimizer.state_dict(),
                    "history": self.history,
                }, self.save_dir / "best_model.pth")
                logger.info(f"Saved best model (loss: {best_val_loss:.4f})")
        return self.history

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="data", help="Path to data folder containing train/val/test")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    parser.add_argument("--save_dir", default="models")
    args = parser.parse_args()

    device = torch.device(args.device if torch.cuda.is_available() and args.device == "cuda" else "cpu")
    model = UNet(n_channels=3, n_classes=1)

    train_dataset = OilSpillDataset(os.path.join(args.data_dir, "train"), augment=True)
    val_dataset = OilSpillDataset(os.path.join(args.data_dir, "val"), augment=False)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=0)

    trainer = Trainer(model, device, lr=args.lr, epochs=args.epochs, batch_size=args.batch_size, save_dir=args.save_dir)
    trainer.train(train_loader, val_loader)

if __name__ == "__main__":
    main()