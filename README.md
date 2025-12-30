# Ausma.ai Documents

## Summary

Ausma.ai Documents is a locally hosted document retrieval and summarizing tool accessible via an AI assistant chat interface.

This tool was developed by ["V-Industries" SIA](https://v-industries.lv/en) for internal use before it was published to open source. It is actively being developed and major parts of it may be subject to change.

Homepage: <https://ausma.ai>

## Features

- Locally hosted - data does not leave your machine
- More than traditional text search - use RAG + vector database to get more context-relevant results and gain insights on your queries
- Document ingestion pipeline
  - Supports .pdf, .md, .txt formats.
  - Supports email loading (unstable)
- Customizable chatbot - use your preferred LLM for chatting.
- Uses Ollama - a locally deployed AI model runner. Features automatic setup for use with AMD and NVIDIA cards as well as running on CPU.
- User friendly web-interface

### Coming soon:

- More document formats - presentation files, spreadsheets, etc.
- Scalability features for multi-user solutions and large datasets.

## Installation

### Dependencies

Ausma.ai Documents has been developed and tested under Ubuntu Server 24.04 LTS and latest Tuxedo OS. It may work on related operating systems.

#### Ubuntu

```bash
sudo apt install python3.12-venv poppler-utils tesseract-ocr libtesseract-dev
```

### Running from source

- Clone the repository:

```bash
git clone [gitrepo]
```

- Run the setup from the project directory:

```bash
cd ausma-ai-documents &&
./setup_linux.sh
```

## How to use

- Put documents inside "documents" folder of the project. This folder is then used for knowledge base creation. See docs.

- Run the web-app and open in browser (see the URL in terminal):

```bash
./run_app.sh
```

- Create a room. You can also think of a room as a session or a conversion. The LLM will remember what you've talked about earlier. However, the longer the conversion goes the longer it will take to generate each consecutive answer. We recommend creating a separate room for each topic or unrelated question.
- When first joining the room you will be prompted to enter a username. This will be the name associated with the questions you ask from this browser.
- Join the room, by clicking "Join".
- Select knowledge base:
  - `None` - **does not use the documents you've loaded**, just runs the model in chat mode.
  - `<knowledge base name>` - model uses RAG approach - receives relevant documents from vectorstore based on your query. This enhances the response with document aware context.
- Choose a LLM model from the installed models and you are ready to ask your questions.

### Examples

The "knowledge" of Ausma.ai depends on the loaded documents and the LLM model.

If you load the relevant computer manuals you may ask something like:

```
What are the supported memory configurations for Lenovo Thinkstation P520?
```

or

```
How many SATA drives can I plug into a Asrock X399 Phantom Gaming 6 motherboard?
```

If you load the relevant documents from the EU Funding and Tenders Portal, it makes sense to ask:

```
How do I register to be able to submit proposals for EU tenders?
```

It is better to be specific in your queries.

```
Give a detailed step by step instructions on how to register for EU Tenders portal to be able to submit proposals,
```

The answers get better given more context.

```
We are a small Latvian I software company. We want to submit our solution proposals related to Data processing for the European project tenders.
Give a detailed step by step instructions on how to register for EU Tenders portal to be able to submit proposals,
```

Afterwards you can ask Ausma to explain each step in more details. Do use the relevant keywords and expressions for better answers. Again more context is better.
Bad example:

```
Please explain step 4 in more detail.
```

Good example:

```
Please explain getting the PIC number in more detail (step 4).
```

## Trivia

"Ausma" is a Latvian word that may be translated as "dawn" or "early daylight". The name was chosen because it runs locally, not on the cloud. "If you get rid of clouds, you can see daylight."

## Acknowledgements

Special thanks to "Solar Icons". SVG Icons are used and modified under CC Attribution License. Link: [https://www.svgrepo.com/collection/solar-outline-icons/](https://www.svgrepo.com/collection/solar-outline-icons/)

## Disclaimer

Ausma.ai is an assistant, it is not a lawyer, doctor, electrician, engineer nor any other kind of specialist. LLM models may hallucinate - produce/invent incorrect results that may appear believable. Be critical of the answers provided. Consult an actual specialist when appropriate.

This project is provided as-is.
By downloading this project you agree to take responsibility for any possible use, misuse and results of this product.
