import datetime
import os
import argparse
from langchain.text_splitter import CharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_ollama import OllamaEmbeddings
from metadata_utils.llm_keyword_extractor import LLM_Keyword_Extractor

def main(args):
    llm_model = args.llm_model
    embedding_model = args.embedding_model
    do_rework = args.rework
    input_path = args.document_path
    chroma_path = args.chroma_path if args.chroma_path is not None else "chroma"
    text_sources = os.listdir(input_path)

    print(f'LLM model: {llm_model}   Embedding model: {embedding_model}')
    embeddings = OllamaEmbeddings(temperature=0.7, model=embedding_model)
    keyword_extractor = LLM_Keyword_Extractor(model=llm_model)
    text_loader_kwargs = {'encoding': 'utf-8'}
    db_folder = os.path.join(chroma_path, embedding_model)
    os.makedirs(db_folder, exist_ok=True)
    for text_source in text_sources:
        print(text_source)
        loader = DirectoryLoader(
            os.path.join(input_path, text_source),
            loader_cls=TextLoader, loader_kwargs=text_loader_kwargs, sample_seed=42
        )
        folder_docs = loader.load()

        existing_documents = Chroma(persist_directory=db_folder, embedding_function=embeddings)
        documents = []
        parent_keywords = {}

        for doc in folder_docs:
            if not do_rework:
                if len(existing_documents.get(where={"source": doc.metadata['source']})["documents"]) > 0:
                    print(doc.metadata['source'], "Already in vector database")
                    continue
            doc.metadata["created"] = datetime.datetime.now(datetime.UTC).isoformat()
            doc.metadata["text_source"] = text_source
            doc.metadata["page_keywords"] = keyword_extractor.extract_keywords(doc.page_content).replace('; ', ';').lower()

            parent_file = doc.metadata["source"].split(os.sep)[-2]

            doc.metadata["parent_file"] = parent_file
            parent_keywords.setdefault(parent_file, [doc.metadata["page_keywords"]]).append(doc.metadata["page_keywords"])


        for doc in folder_docs:
            if not do_rework:
                if len(existing_documents.get(where={"source": doc.metadata['source']})["documents"]) > 0:
                    print(doc.metadata['source'], "Already in vector database")
                    continue
            doc.metadata["parent_keywords"] = ';'.join(
                set(
                    ';'.join(
                        parent_keywords[doc.metadata['parent_file']]
                    ).split(';')
                )
            )
            documents.append(doc)

        if len(documents) > 0:
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.split_documents(documents)
            vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings,
                                                persist_directory=db_folder)
            print(f"Vectorstore created with {vectorstore._collection.count()} documents")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--rework', action='store_true', help='Redo all databases.')
    parser.add_argument('--llm-model', help='LLM model.', required=True)
    parser.add_argument('--embedding-model', help='Embedding model.', required=True)
    parser.add_argument('--chroma-path', help='Chroma db path.', type=str, required=True)
    parser.add_argument('--document-path', help='Converted document path.', required=True)
    args = parser.parse_args()

    main(args)
