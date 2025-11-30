import os
from typing import List, Tuple
import torch
import torch.nn.functional as F
from torch import nn
from torchvision import transforms
from torchvision.transforms import InterpolationMode as IM
from PIL import Image, ImageOps

# -------- путь к весам --------
CKPT_PATH = os.getenv("CKPT_PATH", "static/checkpoints/flower_cnn_checkpoint.pth")

# -------- архитектура модели (как в твоём файле) --------
def build_model(num_classes: int = 16) -> nn.Module:
    return nn.Sequential(
        nn.Conv2d(3, 32, kernel_size=3, padding=1),
        nn.BatchNorm2d(32),
        nn.ReLU(inplace=True),
        nn.MaxPool2d(2),

        nn.Conv2d(32, 32, kernel_size=3, padding=1),
        nn.BatchNorm2d(32),
        nn.ReLU(inplace=True),
        nn.MaxPool2d(2),

        nn.Conv2d(32, 64, kernel_size=3, padding=1),
        nn.BatchNorm2d(64),
        nn.ReLU(inplace=True),
        nn.MaxPool2d(2),

        nn.Conv2d(64, 64, kernel_size=3, padding=1),
        nn.BatchNorm2d(64),
        nn.ReLU(inplace=True),
        nn.MaxPool2d(2),

        nn.Conv2d(64, 128, kernel_size=3, padding=1),
        nn.BatchNorm2d(128),
        nn.ReLU(inplace=True),
        nn.MaxPool2d(2),

        nn.Flatten(),
        nn.Linear(8192, 4096),
        nn.BatchNorm1d(4096),
        nn.Dropout(0.2),
        nn.ReLU(inplace=True),
        nn.Linear(4096, 2048),
        nn.BatchNorm1d(2048),
        nn.Dropout(0.2),
        nn.ReLU(inplace=True),
        nn.Linear(2048, 512),
        nn.BatchNorm1d(512),
        nn.Dropout(0.2),
        nn.ReLU(inplace=True),
        nn.Linear(512, num_classes)
    )

class FlowerClassifier:
    def __init__(self, ckpt_path: str = CKPT_PATH):
        device_str = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device_str)

        # загрузка чекпоинта
        ckpt = torch.load(ckpt_path, map_location=self.device)

        # восстановим список классов
        class_to_idx = ckpt["class_to_idx"]
        idx_to_class = {idx: name for name, idx in class_to_idx.items()}
        self.class_names: List[str] = [idx_to_class[i] for i in range(len(idx_to_class))]

        # целевой размер, который использовался в обучении
        self.img_size: int = ckpt.get("img_size", 128)

        # модель + веса
        self.model: nn.Module = build_model(num_classes=len(self.class_names)).to(self.device)
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.model.eval()

        # тот же препроцесс, что и на валидации при обучении
        self.transform = transforms.Compose([
            transforms.Lambda(lambda img: ImageOps.exif_transpose(img)),
            transforms.Lambda(lambda img: img.convert("RGB")),
            transforms.Resize((self.img_size, self.img_size), interpolation=IM.BICUBIC),
            transforms.ToTensor(),
            # если при обучении была Normalize(...), добавь её и здесь
        ])

    @torch.inference_mode()
    def predict_topk(self, pil_image: Image.Image, topk: int = 1) -> List[Tuple[str, float]]:
        x = self.transform(pil_image).unsqueeze(0).to(self.device)  # [1,3,H,W]
        logits = self.model(x)                                      # [1,C]
        probs = F.softmax(logits, dim=1)                            # [1,C]
        top_probs, top_idxs = probs.topk(topk, dim=1)
        probs_list = top_probs.squeeze(0).tolist()
        idxs_list = top_idxs.squeeze(0).tolist()
        return [(self.class_names[i], float(p)) for i, p in zip(idxs_list, probs_list)]

# -------- Singleton, чтобы модель грузилась один раз --------
_classifier: FlowerClassifier = None

def get_classifier() -> FlowerClassifier:
    global _classifier
    if _classifier is None:
        _classifier = FlowerClassifier(CKPT_PATH)
    return _classifier
