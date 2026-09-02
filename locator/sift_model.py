import cv2
import numpy as np
from typing import List, Tuple, Optional


class FeatureExtractor:
    def __init__(self, feature_type='sift'):
        self.feature_type = feature_type

        if feature_type == 'sift':
            self.detector = cv2.SIFT_create()
        elif feature_type == 'orb':
            self.detector = cv2.ORB_create()
        else:
            raise ValueError(f"Unsupported feature type: {feature_type}")

    def extract(self, image_path: str) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            return None, None

        keypoints, descriptors = self.detector.detectAndCompute(image, None)
        return keypoints, descriptors

class FeatureMatcher:
    def __init__(self, feature_type='sift', matcher_type='flann'):
        self.feature_type = feature_type
        self.matcher_type = matcher_type

        if matcher_type == 'flann':
            if feature_type == 'sift':
                index_params = dict(algorithm=1, trees=5)  # KDTREE
            else:  # ORB
                index_params = dict(algorithm=6, table_number=6, key_size=12, multi_probe_level=1)  # LSH
            search_params = dict(checks=50)
            self.matcher = cv2.FlannBasedMatcher(index_params, search_params)
        else:  # BF matcher
            if feature_type == 'sift':
                self.matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
            else:
                self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    def match(self, desc1: np.ndarray, desc2: np.ndarray) -> List:
        if desc1 is None or desc2 is None:
            return []

        try:
            if self.matcher_type == 'flann':
                matches = self.matcher.knnMatch(desc1, desc2, k=2)

                # Lowe's ratio test
                good_matches = []
                for match_pair in matches:
                    if len(match_pair) == 2:
                        m, n = match_pair
                        if m.distance < 0.7 * n.distance:
                            good_matches.append(m)
                return good_matches
            else:  # BF matcher
                matches = self.matcher.match(desc1, desc2)
                matches = sorted(matches, key=lambda x: x.distance)
                return matches[:len(matches) // 2]
        except:
            return []


class ImageLocalizer:
    def __init__(self, feature_type='sift', matcher_type='flann'):
        self.extractor = FeatureExtractor(feature_type)
        self.matcher = FeatureMatcher(feature_type, matcher_type)
        self.database_features = {}
        self.database_paths = {}

    def query_image(self, query_path: str, top_k: int = 5) -> List[Tuple[str, int]]:
        query_kp, query_desc = self.extractor.extract(query_path)
        if query_desc is None:
            return []
        similarities = []
        for db_name, db_desc in self.database_features.items():
            matches = self.matcher.match(query_desc, db_desc)
            similarity = len(matches)
            similarities.append((db_name, similarity))
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]