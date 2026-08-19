import React from 'react';
import { motion } from 'framer-motion';
import { FileText, Settings, Search, Code, Brain, Database } from 'lucide-react';

const architectureSteps = [
    {
        number: '1',
        title: 'Authenticate the user',
        description: 'The backend issues and validates JWTs through /api/auth/register, /api/auth/login, /api/auth/refresh, and /api/auth/me so every request is tied to a real user.',
        icon: Brain,
        bgColor: 'bg-blue-950/20',
        borderColor: 'border-blue-500/30',
        circleColor: 'bg-blue-500/20',
        iconColor: 'text-blue-400',
    },
    {
        number: '2',
        title: 'Store uploads safely',
        description: 'Documents are accepted through /api/documents/upload, validated by file type and size, saved with safe generated filenames, and linked to the owning user.',
        icon: FileText,
        bgColor: 'bg-purple-950/20',
        borderColor: 'border-purple-500/30',
        circleColor: 'bg-purple-500/20',
        iconColor: 'text-purple-400',
    },
    {
        number: '3',
        title: 'Extract and chunk content',
        description: 'A background task parses the file, splits it into chunks, and keeps the page and section metadata so retrieval stays traceable.',
        icon: Search,
        bgColor: 'bg-green-950/20',
        borderColor: 'border-green-500/30',
        circleColor: 'bg-green-500/20',
        iconColor: 'text-green-400',
    },
    {
        number: '4',
        title: 'Create embeddings and index',
        description: 'Chunk text is embedded and stored for user-scoped semantic search, which powers grounded answers instead of keyword-only lookup.',
        icon: Settings,
        bgColor: 'bg-orange-950/20',
        borderColor: 'border-orange-500/30',
        circleColor: 'bg-orange-500/20',
        iconColor: 'text-orange-400',
    },
    {
        number: '5',
        title: 'Retrieve context and answer',
        description: 'The chat endpoint rewrites the query, loads recent conversation history, retrieves relevant chunks for the current user, and sends the context to the generator.',
        icon: Database,
        bgColor: 'bg-red-950/20',
        borderColor: 'border-red-500/30',
        circleColor: 'bg-red-500/20',
        iconColor: 'text-red-400',
    },
    {
        number: '6',
        title: 'Persist the response',
        description: 'The backend stores the assistant reply, sources, confidence, and processing time so the conversation can be revisited later.',
        icon: Code,
        bgColor: 'bg-cyan-950/20',
        borderColor: 'border-cyan-500/30',
        circleColor: 'bg-cyan-500/20',
        iconColor: 'text-cyan-400',
    },
];

const sampleChatRequest = `POST /api/chat
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "message": "Does this policy cover knee replacement, and what conditions apply?",
  "conversation_id": null,
  "document_ids": ["doc_123"],
  "action": "evaluate_claim"
}`;

const sampleChatResponse = `{
  "conversation_id": "conv_123",
  "message_id": "msg_456",
  "answer": "Yes, subject to the policy terms and waiting period.",
  "decision": "covered with conditions",
  "conditions": ["Policy must be active", "Waiting period must be completed"],
  "exclusions": ["Non-covered pre-existing limitations"],
  "sources": [
    {
      "document_id": "doc_123",
      "document_name": "policy.pdf",
      "page": 8,
      "section": "Surgery coverage",
      "text": "Knee replacement is covered after the waiting period...",
      "relevance_score": 0.9821
    }
  ],
  "confidence": 0.94,
  "processing_time": 1.284
}`;

const apiRows = [
    { method: 'POST', path: '/api/auth/register', detail: 'Create a new account and receive tokens.' },
    { method: 'POST', path: '/api/auth/login', detail: 'Log in and receive access and refresh tokens.' },
    { method: 'GET', path: '/api/auth/me', detail: 'Fetch the authenticated user profile.' },
    { method: 'POST', path: '/api/documents/upload', detail: 'Upload a document for indexing.' },
    { method: 'GET', path: '/api/documents', detail: 'List the current user’s uploaded documents.' },
    { method: 'GET', path: '/api/documents/{document_id}', detail: 'Read a single document record.' },
    { method: 'DELETE', path: '/api/documents/{document_id}', detail: 'Delete a document and its chunks.' },
    { method: 'POST', path: '/api/chat', detail: 'Ask a grounded question using stored documents.' },
];

const ProblemStatement = () => {
    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="max-w-6xl mx-auto space-y-8">
            <div className="text-center space-y-4">
                <p className="text-sm uppercase tracking-[0.3em] text-purple-300">Current implementation</p>
                <h1 className="text-3xl sm:text-4xl font-bold text-gray-100">Problem Statement</h1>
                <p className="text-lg text-gray-400 max-w-3xl mx-auto">
                    CRuX GPT is no longer a generic demo. It is a backend-first, user-scoped document assistant built around authenticated uploads,
                    background indexing, and grounded question answering with traceable sources.
                </p>
            </div>
        
        {/* Q.1 Current implementation */}
        <motion.div 
            className="p-6 sm:p-8 rounded-lg bg-gray-800/50 border border-gray-700/50"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
        >
            <div className="flex items-center gap-3 mb-6">
                <div className="bg-black text-white px-3 py-1 rounded font-bold text-sm">Q.1</div>
                <h2 className="text-xl sm:text-2xl font-bold text-gray-100">What we are building now</h2>
            </div>
            
            <p className="text-base sm:text-lg leading-relaxed text-gray-200 mb-6">
                The current implementation is a FastAPI backend that accepts documents, processes them in the background, stores chunks per user,
                and answers chat questions using retrieval-augmented generation. Every response is grounded in the user’s own uploaded files.
            </p>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-blue-950/30 border-l-4 border-blue-400 p-4 rounded">
                    <h3 className="font-semibold text-blue-300 mb-3">What the backend handles</h3>
                    <ul className="space-y-2 text-gray-300">
                        <li>JWT-based authentication and user identity for every request.</li>
                        <li>Safe document uploads with file validation, ownership checks, and background processing.</li>
                        <li>Conversation memory, document-scoped retrieval, and answer generation with sources.</li>
                    </ul>
                </div>

                <div className="bg-purple-950/30 border-l-4 border-purple-400 p-4 rounded">
                    <h3 className="font-semibold text-purple-300 mb-3">Implementation details</h3>
                    <ul className="space-y-2 text-gray-300">
                        <li>Uploads are parsed, chunked, embedded, and indexed after the response returns.</li>
                        <li>Retrieved chunks are limited to the current user and optional selected documents.</li>
                        <li>The chat response includes answer, decision, conditions, exclusions, sources, confidence, and processing time.</li>
                    </ul>
                </div>
            </div>
        </motion.div>

        {/* Q.2 System workflow */}
        <motion.div 
            className="p-6 sm:p-8 rounded-lg bg-gray-800/50 border border-gray-700/50"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
        >
            <div className="flex items-center gap-3 mb-6">
                <div className="bg-black text-white px-3 py-1 rounded font-bold text-sm">Q.2</div>
                <h2 className="text-xl sm:text-2xl font-bold text-gray-100">How the backend works end-to-end</h2>
            </div>

            <p className="text-base sm:text-lg text-gray-200 mb-6">
                The flow below matches the actual services in the backend: auth, document processing, retrieval, generation, and persistence.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {architectureSteps.map((component, index) => (
                    <motion.div
                        key={component.number}
                        className={`p-4 rounded-lg ${component.bgColor} border ${component.borderColor} text-center`}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.3, delay: 0.1 * index }}
                    >
                        <div className={`w-12 h-12 rounded-full ${component.circleColor} flex items-center justify-center mx-auto mb-3`}>
                            <span className="text-white font-bold">{component.number}</span>
                        </div>
                        <component.icon className={`w-6 h-6 ${component.iconColor} mx-auto mb-2`} />
                        <h3 className="font-semibold text-gray-100 mb-1">{component.title}</h3>
                        <p className="text-sm text-gray-400">{component.description}</p>
                    </motion.div>
                ))}
            </div>
        </motion.div>

        {/* Q.3 Sample query and backend request */}
        <motion.div 
            className="p-6 sm:p-8 rounded-lg bg-gray-800/50 border border-gray-700/50"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
        >
            <div className="flex items-center gap-3 mb-6">
                <div className="bg-black text-white px-3 py-1 rounded font-bold text-sm">Q.3</div>
                <h2 className="text-xl sm:text-2xl font-bold text-gray-100">Sample query and backend request</h2>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-gray-700/30 p-4 rounded border border-gray-600">
                    <h3 className="font-semibold text-gray-200 mb-2">Sample query</h3>
                    <p className="text-gray-300 italic">
                        Does this policy cover knee replacement, and what conditions apply?
                    </p>
                    <p className="text-sm text-gray-500 mt-3">
                        From the backend point of view, this is treated as a grounded chat request that can optionally target specific uploaded documents.
                    </p>
                </div>

                <div className="bg-gray-700/30 p-4 rounded border border-gray-600">
                    <h3 className="font-semibold text-gray-200 mb-2">Backend request</h3>
                    <div className="bg-black p-3 rounded font-mono text-xs overflow-x-auto whitespace-pre">
                        <span className="text-gray-300">{sampleChatRequest}</span>
                    </div>
                </div>
            </div>

            <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-gray-700/30 p-4 rounded border border-gray-600">
                    <h3 className="font-semibold text-gray-200 mb-2">Expected backend response</h3>
                    <div className="bg-black p-3 rounded font-mono text-xs overflow-x-auto whitespace-pre max-h-72">
                        <span className="text-gray-300">{sampleChatResponse}</span>
                    </div>
                </div>

                <div className="bg-gray-700/30 p-4 rounded border border-gray-600">
                    <h3 className="font-semibold text-gray-200 mb-2">How the backend interprets it</h3>
                    <ul className="space-y-2 text-gray-300 text-sm leading-relaxed">
                        <li>If <span className="font-mono text-gray-100">conversation_id</span> is missing, a new conversation is created automatically.</li>
                        <li>The message is stored first so the user query is never lost if generation fails later.</li>
                        <li>The backend rewrites the query with recent history, retrieves user-scoped chunks, then returns grounded sources with the answer.</li>
                    </ul>
                </div>
            </div>
        </motion.div>

        {/* Q.4 API documentation */}
        <motion.div 
            className="p-6 sm:p-8 rounded-lg bg-gray-800/50 border border-gray-700/50"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
        >
            <div className="flex items-center gap-3 mb-6">
                <div className="bg-black text-white px-3 py-1 rounded font-bold text-sm">Q.4</div>
                <h2 className="text-xl sm:text-2xl font-bold text-gray-100">Current API surface</h2>
            </div>

            <div className="space-y-6">
                <div className="bg-gray-700/30 p-4 rounded border border-gray-600">
                    <h3 className="font-semibold text-gray-200 mb-2">Base URL</h3>
                    <div className="bg-black p-3 rounded font-mono text-sm overflow-x-auto">
                        <span className="text-green-400">http://localhost:8000</span>
                    </div>
                </div>

                <div className="bg-gray-700/30 p-4 rounded border border-gray-600">
                    <h3 className="font-semibold text-gray-200 mb-4">Implemented endpoints</h3>
                    <div className="space-y-3">
                        {apiRows.map((row) => (
                            <div key={row.path} className="bg-gray-800/50 p-3 rounded border border-gray-600 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                                <div className="flex items-center gap-2">
                                    <span className="bg-green-600 text-white px-2 py-1 rounded text-xs font-bold min-w-14 text-center">{row.method}</span>
                                    <span className="text-gray-200 font-mono text-sm">{row.path}</span>
                                </div>
                                <p className="text-gray-400 text-sm">{row.detail}</p>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="bg-gray-700/30 p-4 rounded border border-gray-600">
                    <h3 className="font-semibold text-gray-200 mb-2">Response shape returned by /api/chat</h3>
                    <ul className="space-y-2 text-gray-300 text-sm leading-relaxed">
                        <li><span className="font-mono text-gray-100">answer</span>, <span className="font-mono text-gray-100">decision</span>, <span className="font-mono text-gray-100">conditions</span>, and <span className="font-mono text-gray-100">exclusions</span> summarize the model output.</li>
                        <li><span className="font-mono text-gray-100">sources</span> carries the retrieved document references with page, section, and relevance score.</li>
                        <li><span className="font-mono text-gray-100">confidence</span> and <span className="font-mono text-gray-100">processing_time</span> make the response observable from the backend side.</li>
                    </ul>
                </div>
            </div>
        </motion.div>
    </motion.div>
    );
};

export default ProblemStatement;
