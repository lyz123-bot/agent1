from tqdm import tqdm
from model import ImageLocalizer
from dataload import DataLoader


def build_database(dataset_root, mode='val', feature_type='sift', save_path=None):
    print(f"Building database for {mode} set...")
    localizer = ImageLocalizer(feature_type=feature_type)
    dataloader = DataLoader(dataset_root)
    db_paths = dataloader.get_database_paths(mode)
    print(f"Found {len(db_paths)} database images")
    if len(db_paths) == 0:
        raise ValueError(f"No database images found in {dataset_root}/{mode}/database")
    for img_path in tqdm(db_paths, desc="Extracting features"):
        try:
            keypoints, descriptors = localizer.extractor.extract(str(img_path))
            if descriptors is not None:
                img_name = img_path.name
                localizer.database_features[img_name] = descriptors
                localizer.database_paths[img_name] = str(img_path)
        except Exception as e:
            print(f"Error processing {img_path}: {e}")
    print(f"Successfully processed {len(localizer.database_features)} images")
    if len(localizer.database_features) == 0:
        raise ValueError("No features extracted from database images")
    if save_path:
        dataloader.save_features(
            localizer.database_features, 
            localizer.database_paths, 
            save_path
        )
    return localizer.database_features, localizer.database_paths


def extract_single_image_features(image_path, feature_type='sift'):
    localizer = ImageLocalizer(feature_type=feature_type)
    return localizer.extractor.extract(image_path)
