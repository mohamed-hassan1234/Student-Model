# RAG Architecture

Flow:

question -> validation -> curriculum topic classification -> query embedding -> retrieval -> trust/permission filtering -> ranking -> context construction -> local model generation -> citation validation -> confidence calculation -> answer -> retrieval audit event.

If retrieval does not provide enough support, Technology Student returns `insufficient_evidence` instead of answering from unsupported model memory.
