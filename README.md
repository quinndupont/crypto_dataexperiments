# Crypto data science experiments

# Forensic method for investigating software engineering behaviours, aka, how crypto is made
A PoC (with limited dataset) for an automatic Neo4J knowledge graph of crypto software development with RAG interface for forensic investigation of user behaviours. LangChain is used to extract pull requests and commits from the Bitcoin repo, construct a Neo4J knowledge graph, and then a RAG (natural language) interface queries the graph.

![neo4jkg](https://github.com/quinndupont/crypto_dataexperiments/blob/main/neo4j_KG_example.png)

![RAGinterface](https://github.com/quinndupont/crypto_dataexperiments/blob/main/KGRAG_PoC.png)
