# processor/deduper.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def deduplicate_stories(stories, similarity_threshold=0.75):
    """
    Groups stories that are near-duplicates using TF-IDF and Cosine Similarity.
    Returns a list of "clusters". Each cluster is a list of stories.
    """
    print("\n--- STEP 3b: DEDUPLICATING STORIES ---")

    if not stories:
        return []

    # Combine title and summary for a richer embedding
    texts = [
        f"{s.get('clean_title', '')} {s.get('clean_summary', '')}"
        for s in stories
    ]

    # 1. Create Embeddings (TF-IDF for now)
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(texts)

    # 2. Calculate Cosine Similarity
    # This creates a matrix of shape (num_stories, num_stories)
    similarity_matrix = cosine_similarity(tfidf_matrix)

    # 3. Cluster (Greedy approach)
    visited = set()
    clusters = []

    for i in range(len(stories)):
        if i in visited:
            continue

        # Start a new cluster with story i
        current_cluster = [stories[i]]
        visited.add(i)

        # Find all other stories similar to story i
        for j in range(i + 1, len(stories)):
            if j in visited:
                continue

            if similarity_matrix[i][j] >= similarity_threshold:
                current_cluster.append(stories[j])
                visited.add(j)

        clusters.append(current_cluster)

    print(f"--- DEDUPED: {len(stories)} stories reduced to {len(clusters)} unique clusters ---\n")
    return clusters
