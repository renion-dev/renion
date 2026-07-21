import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.cluster import KMeans
from sentence_transformers import SentenceTransformer
import os

logger = logging.getLogger(__name__)

class HypothesisClusterer:
    """Кластеризує гіпотези за схожістю проблем."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Ініціалізує кластеризатор з embedding-моделлю.
        Якщо модель недоступна, використовуємо заглушку.
        """
        self.model_name = model_name
        self.model = None
        self._available = False
        
        try:
            self.model = SentenceTransformer(model_name)
            self._available = True
            logger.info(f"✅ SentenceTransformer model loaded: {model_name}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load SentenceTransformer: {e}. Using fallback.")
            self._available = False

    async def cluster_hypotheses(self, hypotheses: List[Dict[str, Any]], n_clusters: int = 5) -> Dict[str, Any]:
        """
        Кластеризує гіпотези на основі тексту проблеми.
        Повертає словник з кластерами та метаданими.
        """
        if not hypotheses:
            return {"clusters": [], "error": "No hypotheses to cluster"}
        
        if not self._available:
            logger.warning("Embedding model not available, returning single cluster")
            return {
                "clusters": [{
                    "id": 0,
                    "size": len(hypotheses),
                    "center": "All hypotheses",
                    "hypotheses": hypotheses,
                    "keywords": ["mixed"]
                }],
                "method": "fallback"
            }
        
        # Отримуємо тексти проблем
        texts = [h.get("metadata", {}).get("problem", "") or h.get("description", "") for h in hypotheses]
        
        # Перевіряємо, чи є текст
        if not any(texts):
            return {"clusters": [], "error": "No text data in hypotheses"}
        
        # Генеруємо embeddings
        try:
            embeddings = self.model.encode(texts, show_progress_bar=False)
            
            # Визначаємо оптимальну кількість кластерів
            n = min(n_clusters, len(hypotheses))
            if n < 2:
                return {
                    "clusters": [{
                        "id": 0,
                        "size": len(hypotheses),
                        "center": "Single cluster",
                        "hypotheses": hypotheses,
                        "keywords": []
                    }],
                    "method": "single"
                }
            
            # Кластеризуємо
            kmeans = KMeans(n_clusters=n, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings)
            
            # Формуємо результат
            clusters = []
            for cluster_id in range(n):
                cluster_indices = [i for i, label in enumerate(labels) if label == cluster_id]
                cluster_hypotheses = [hypotheses[i] for i in cluster_indices]
                
                # Центроїд кластера (середній вектор)
                center_vector = kmeans.cluster_centers_[cluster_id]
                
                # Знаходимо найближчу гіпотезу до центру
                distances = [np.linalg.norm(embeddings[i] - center_vector) for i in cluster_indices]
                if distances:
                    center_idx = cluster_indices[np.argmin(distances)]
                    center_text = texts[center_idx][:200] + "..." if len(texts[center_idx]) > 200 else texts[center_idx]
                else:
                    center_text = ""
                
                clusters.append({
                    "id": cluster_id,
                    "size": len(cluster_hypotheses),
                    "center": center_text,
                    "hypotheses": cluster_hypotheses,
                    "keywords": self._extract_keywords(cluster_hypotheses)
                })
            
            return {
                "clusters": clusters,
                "method": "kmeans",
                "n_clusters": n,
                "total": len(hypotheses)
            }
            
        except Exception as e:
            logger.error(f"Clustering error: {e}")
            return {
                "clusters": [{
                    "id": 0,
                    "size": len(hypotheses),
                    "center": "Error during clustering",
                    "hypotheses": hypotheses,
                    "keywords": []
                }],
                "error": str(e)
            }

    def _extract_keywords(self, hypotheses: List[Dict[str, Any]]) -> List[str]:
        """Витягує ключові слова з гіпотез (спрощено)."""
        # Тимчасово повертаємо порожній список
        # В майбутньому можна додати TF-IDF або ключові слова з LLM
        return []
