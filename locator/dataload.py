import os
import pickle
from pathlib import Path
from typing import Dict, List
from tqdm import tqdm


class DataLoader:

    def __init__(self, dataset_root: str):
        self.dataset_root = Path(dataset_root)
    def get_image_paths(self, directory: str) -> List[Path]:
        dir_path = Path(directory)
        if not dir_path.exists():
            return []
        extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        image_paths = []
        for ext in extensions:
            image_paths.extend(dir_path.glob(f'*{ext}'))
            image_paths.extend(dir_path.glob(f'*{ext.upper()}'))
        return image_paths

    def get_database_paths(self, mode='val') -> List[Path]:
        db_dir = self.dataset_root / mode / 'database'
        return self.get_image_paths(db_dir)

    def get_query_paths(self, mode='val') -> List[Path]:
        query_dir = self.dataset_root / mode / 'queries'
        if not query_dir.exists():
            query_dir = self.dataset_root / mode / 'queries_v1'
        return self.get_image_paths(query_dir)
    def save_features(self, features: Dict, paths: Dict, save_path: str):
        data = {
            'features': features,
            'paths': paths
        }
        with open(save_path, 'wb') as f:
            pickle.dump(data, f)
        print(f"Features saved to {save_path}")

    def load_features(self, load_path: str) -> tuple:
        with open(load_path, 'rb') as f:
            data = pickle.load(f)
        return data['features'], data['paths']