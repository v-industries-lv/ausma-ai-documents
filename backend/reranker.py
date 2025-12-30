from sklearn.metrics.pairwise import cosine_similarity
import itertools
from typing import List
from langchain_core.embeddings import Embeddings

from settings import RAGSettings


def rerank(documents: List[dict], embedding: Embeddings, rag_settings: RAGSettings):
    relevant_documents = [x for x in documents if x["similarity_score"] < rag_settings.rag_cosine_distance_irrelevance_threshold]
    if len(relevant_documents) == 0:
        return relevant_documents
    min_score = min([x["similarity_score"] for x in relevant_documents])
    min_filtered_documents = [x for x in relevant_documents if x["similarity_score"] < min_score + rag_settings.rag_score_margin]

    embeddings = [embedding.embed_query(x["content"]) for x in min_filtered_documents]
    cs_embeddings = cosine_similarity(embeddings, embeddings)

    # When doing cosine similarity, the closer the value to 1, the more similar are the documents. Value of 1 means documents are the same
    similar_documents = []
    for document_index, cs_similarities in enumerate(cs_embeddings):
        documents_above_threshold = [i for i, v in enumerate(list(cs_similarities)) if v > rag_settings.rag_similarity_score_threshold]
        if len(documents_above_threshold) > 1:
            similar_documents.append(documents_above_threshold)

    similar_documents.sort()
    similar_documents_list = list(k for k, _ in itertools.groupby(similar_documents))

    # When comparing similarity scores from rag lookup, the lower the score, the more relevant is the document to the original query.
    skip_documents = []
    for document_group in similar_documents_list:
        most_relevant_document = None
        for document_index in document_group:
            if most_relevant_document is None:
                most_relevant_document = document_index
                continue
            if min_filtered_documents[document_index]["similarity_score"] < min_filtered_documents[most_relevant_document]["similarity_score"]:
                skip_documents.append(most_relevant_document)
                most_relevant_document = document_index
            else:
                skip_documents.append(document_index)

    relevant_documents = [v for i, v in enumerate(min_filtered_documents) if i not in skip_documents]

    return relevant_documents
