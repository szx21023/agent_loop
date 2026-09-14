# agent-loop

An agentic knowledge-base assistant built around the **Agent Loop** pattern
(see `agent_loop.png`): a reasoning loop that decides its next step, calls tools,
evaluates results, and iterates until it can answer with sources.

## Architecture (target)

```
User → Chat UI (Web/App)
     → Backend (FastAPI)        # requests, sessions, context assembly
     → Agent (the loop)          # decide next step: tool call or final answer
         ├── Knowledge Tools     # RAG (vector), Graph (relations)
         ├── Action Tools        # Notion / Drive / Gmail / GitHub / Jira
         └── Memory              # conversation history, user profile

Storage: Graph DB (Neo4j) · Vector DB (Pinecone/Milvus) · SQL DB (PostgreSQL)
```

## The Agent Loop

1. User asks a question
2. Assemble context, call the LLM
3. LLM decides the next step
4. Need a tool? → yes: call it · no: go to step 8
5. Execute tool call (e.g. `search_graph`, `search_rag`)
6. Add tool result to context
7. Evaluate — enough info? keep searching? switch tools?
8. Goal met? → no: loop back to step 2 · yes: produce final answer
9. Final answer, with sources

## Status

Early scaffold. See `notion-kb-agent` for a minimal (BM25 + in-memory graph)
precursor of the Knowledge Tools layer.

## Getting started

_TBD — decide stack, then fill in._
