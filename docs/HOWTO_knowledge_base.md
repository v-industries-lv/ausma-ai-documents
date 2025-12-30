# Knowledge bases
## What is a knowledge base?
A knowledge base is a selection of documents that have been converted for RAG (Retrieval Augmented Generation) purposes. 
Knowledge base contains information about the type of vector store used for document retrieval, what type of conversions have been made and what embedding model has been used to convert these documents to their vector representation.
## Configuration
To create a knowledge base we have to make a configuration for it through UI in the main app. Optionally, one can add a .json config directly to folder *knowledge_bases/configs* by following this pattern:  
```json
{
  "name": <knowledge_base_name>,
  "selection": [<pattern>, <pattern>, ...],
  "convertors": [<convertor>, <convertor>, ...],
  "embedding":
    {
      "model": <embedding_model>
    }
}
```
### Currently supported values
#### "store": 
- "chroma" - will use ChromaDB

#### "name":
- any non empty string

#### "selection":
- file system like selection pattern. For example, "\*\*/\*" will try to select all files inside *documents* folder or "\*\*/\*.pdf" will select only .pdf files inside *documents folder*

#### "convertors":
- Raw conversion. Will try to dump raw text from file. Will not extract information from images. Best use when documents are text only.
```json
{
  "conversion": "raw"
}
```
- OCR conversion. Will try to render each page of the document as an image and then perform OCR. Can extract textual information from images inside the page. Best used for mixed text and images documents.
```json
{
  "conversion": "ocr"
}
```
- OCR+LLM conversion. Same as OCR conversion, but may improve conversion result by fixing typos and OCR artifacts.
```json
{
  "conversion": "ocr_llm",
  "model": <text2textmodel>,
  "seed": <random_seed>,
  "temperature": <model_recommended_temperature>
}
```
- LLM conversion. Use with multi-modal LLM models, that support image processing. Best for general purpose document conversion. Similar to OCR, but also leverages LLM capabilities. Performance and speed greatly depends on the model used.
```json
{
  "conversion": "llm",
  "model": <multimodal_vision_model>,
  "seed": <random_seed>,
  "temperature": <model_recommended_temperature>
}
```

#### "embedding":
- Choose embedding supporting model. Best used with dedicated embedding models, although any embedding supporting model will work at the cost of performance.
```json
{
  "model": <embedding_model>
}
```