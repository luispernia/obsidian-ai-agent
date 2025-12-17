import argparse
import sys
from langchain_chroma import Chroma
from src.ai_provider import AIProvider
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from src import config

def query_rag(query_text):
    try:
        embeddings = AIProvider.get_embeddings()
        llm = AIProvider.get_llm()
    except Exception as e:
        print(f"Provider Error: {e}")
        return "System configuration error."
    
    vectorstore = Chroma(persist_directory=config.CHROMA_DB_ABS_PATH, embedding_function=embeddings)

    retriever = vectorstore.as_retriever()
    
    system_prompt = (
        "You are a helpful assistant for a personal knowledge base (Obsidian Vault). "
        "Use the following pieces of retrieved context to answer "
        "the question. If the answer is not in the context, say that you don't know "
        "but try to be as helpful as possible with general knowledge if applicable, "
        "marking it as 'General Knowledge'. "
        "Keep the answer concise."
        "\n\n"
        "{context}"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    response = rag_chain.invoke({"input": query_text})
    
    return response["answer"]

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query_text = sys.argv[1]
        answer = query_rag(query_text)
        print(f"Answer: {answer}")
    else:
        print("Please provide a query.")
