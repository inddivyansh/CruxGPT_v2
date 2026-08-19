import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, User as UserIcon, Loader2, Bot, Paperclip, X, ThumbsUp, ThumbsDown, Lightbulb, FileText, CheckCircle2, AlertCircle } from 'lucide-react';
import Textarea from './ui/Textarea';
import { useAuth } from '../contexts/AuthContext';
import * as api from '../services/api';

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB, matches backend MAX_FILE_SIZE_MB default
const ACCEPTED_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
];

// Polls a just-uploaded document until it's indexed or fails, so the UI can
// show "Uploading... -> Processing... -> Ready" per spec section 12.
function pollDocumentStatus(documentId, onUpdate) {
    const interval = setInterval(async () => {
        try {
            const doc = await api.getDocument(documentId);
            onUpdate(doc);
            if (doc.status === 'indexed' || doc.status === 'failed') {
                clearInterval(interval);
            }
        } catch {
            clearInterval(interval);
            onUpdate({ status: 'failed', error_message: 'Could not check document status.' });
        }
    }, 1500);
    return () => clearInterval(interval);
}

const Chat = ({ taskSuggestions = [], commonQueries = [], initialQuery = '', initialAction = 'general', initialConversationId = null }) => {
    const { isLoggedIn, openLoginModal } = useAuth();

    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Hello! I am CRuX AI. How can I assist you today?' }
    ]);
    const [conversationId, setConversationId] = useState(initialConversationId);
    const [input, setInput] = useState('');
    const [pendingAction, setPendingAction] = useState('general');
    const [isLoading, setIsLoading] = useState(false);
    const [attachedFiles, setAttachedFiles] = useState([]); // [{ localId, file, documentId, status, error }]
    const [storageUsage, setStorageUsage] = useState({
        used_bytes: 0,
        max_bytes: 100 * 1024 * 1024,
        remaining_bytes: 100 * 1024 * 1024,
        document_count: 0,
    });
    const [storageNotice, setStorageNotice] = useState(null);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [showTaskSwitcher, setShowTaskSwitcher] = useState(false);
    const [loadError, setLoadError] = useState(null);
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);
    const hasProcessedInitialQuery = useRef(false);
    const processedQuery = useRef('');
    const pollCleanupsRef = useRef({});
    const conversationIdRef = useRef(initialConversationId);
    const conversationCreationRef = useRef(null);

    const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const refreshStorageUsage = useCallback(async () => {
        if (!isLoggedIn) return;
        try {
            const usage = await api.getStorageUsage(conversationIdRef.current);
            if (usage && typeof usage.used_bytes === 'number') {
                setStorageUsage(usage);
            }
        } catch {
            // best-effort
        }
    }, [isLoggedIn]);

    useEffect(() => {
        refreshStorageUsage();
    }, [refreshStorageUsage, conversationId]);

    // --- BACKEND INTEGRATION POINT: hydrate an existing conversation ---
    useEffect(() => {
        if (!initialConversationId) return;
        (async () => {
            try {
                const conversation = await api.getConversation(initialConversationId);
                conversationIdRef.current = conversation.id;
                setConversationId(conversation.id);
                setMessages(
                    conversation.messages.map((m) => ({
                        role: m.role,
                        content: m.content,
                        id: m.role === 'assistant' ? m.id : undefined,
                        sources: m.sources,
                        feedback: undefined,
                    }))
                );
                refreshStorageUsage();
            } catch (err) {
                setLoadError(err.message || 'Could not load this conversation.');
            }
        })();
    }, [initialConversationId, refreshStorageUsage]);

    useEffect(() => {
        if (initialQuery !== processedQuery.current) {
            hasProcessedInitialQuery.current = false;
            processedQuery.current = initialQuery;
        }
    }, [initialQuery]);

    // --- BACKEND INTEGRATION POINT: real /api/chat call ---
    const sendToBackend = useCallback(async (messageContent, documentIds, action) => {
        const response = await api.sendMessage({
            message: messageContent,
            conversationId,
            documentIds,
            action,
        });
        conversationIdRef.current = response.conversation_id;
        setConversationId(response.conversation_id);
        return response;
    }, [conversationId]);

    const appendAssistantMessage = (response) => {
        setMessages((prev) => [
            ...prev,
            {
                role: 'assistant',
                content: response.answer,
                id: response.message_id,
                summary: response.summary,
                key_points: response.key_points || [],
                sources: response.sources || [],
                decision: response.decision,
                conditions: response.conditions || [],
                exclusions: response.exclusions || [],
                confidence: response.confidence,
                insufficient_context: response.insufficient_context,
            },
        ]);
    };

    const readyDocumentIds = () =>
        attachedFiles.filter((f) => f.status === 'ready' && f.documentId).map((f) => f.documentId);

    // Auto-send initial query if provided (only once per query)
    useEffect(() => {
        if (!initialQuery || !initialQuery.trim() || hasProcessedInitialQuery.current || isLoading) return;
        if (!isLoggedIn) {
            openLoginModal();
            return;
        }
        hasProcessedInitialQuery.current = true;

        const userMessage = { role: 'user', content: initialQuery };
        setMessages((prev) => [...prev, userMessage]);
        setIsLoading(true);

        sendToBackend(initialQuery, [], initialAction)
            .then(appendAssistantMessage)
            .catch((err) => {
                setMessages((prev) => [...prev, { role: 'assistant', content: err.message || 'Sorry, an error occurred.', isError: true }]);
            })
            .finally(() => setIsLoading(false));
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [initialQuery, isLoading, isLoggedIn]);

    // Show task switcher when user types
    useEffect(() => {
        setShowTaskSwitcher(input.trim().length > 10);
    }, [input]);

    // Clean up any in-flight polling on unmount
    useEffect(() => () => {
        Object.values(pollCleanupsRef.current).forEach((cleanup) => cleanup());
    }, []);

    const handleSend = async () => {
        if (input.trim() === '' || isLoading) return;

        if (!isLoggedIn) {
            openLoginModal();
            return;
        }

        const lastMessage = messages[messages.length - 1];
        if (lastMessage && lastMessage.role === 'user' && lastMessage.content === input.trim()) return;

        const messageContent = input;
        const action = pendingAction;
        const documentIds = readyDocumentIds();

        setMessages((prev) => [...prev, { role: 'user', content: messageContent }]);
        setInput('');
        setPendingAction('general');
        setIsLoading(true);
        setShowTaskSwitcher(false);

        try {
            const response = await sendToBackend(messageContent, documentIds, action);
            appendAssistantMessage(response);
        } catch (error) {
            setMessages((prev) => [...prev, { role: 'assistant', content: error.message || 'Sorry, an error occurred.', isError: true }]);
        } finally {
            setIsLoading(false);
        }
    };

    // --- BACKEND INTEGRATION POINT: real document upload + status polling ---
    const getConversationIdForUpload = async () => {
        if (conversationIdRef.current) return conversationIdRef.current;

        if (!conversationCreationRef.current) {
            conversationCreationRef.current = api
                .createConversation()
                .then((conversation) => {
                    conversationIdRef.current = conversation.id;
                    setConversationId(conversation.id);
                    return conversation.id;
                })
                .finally(() => {
                    conversationCreationRef.current = null;
                });
        }

        return conversationCreationRef.current;
    };

    const handleFileAttachment = async (event) => {
        if (!isLoggedIn) {
            openLoginModal();
            event.target.value = '';
            return;
        }

        const files = Array.from(event.target.files || []);
        event.target.value = ''; // allow re-selecting the same file later
        setStorageNotice(null);

        if (!files.length) return;

        const currentRemaining = storageUsage.remaining_bytes ?? (100 * 1024 * 1024);
        const remainingMb = (Math.max(0, currentRemaining) / (1024 * 1024)).toFixed(1);

        if (currentRemaining <= 0) {
            setStorageNotice("Storage limit reached (100 MB). Remove a document to upload another.");
            return;
        }

        const validCandidates = [];

        files.forEach((file) => {
            const localId = `${file.name}-${Date.now()}-${Math.random()}`;

            if (!ACCEPTED_TYPES.includes(file.type)) {
                setAttachedFiles((prev) => [
                    ...prev,
                    { localId, file, status: 'failed', error: 'Unsupported file type. Allowed: PDF, DOC, DOCX, TXT.' }
                ]);
                return;
            }
            if (file.size > MAX_FILE_SIZE) {
                const sizeMb = (file.size / (1024 * 1024)).toFixed(1);
                setAttachedFiles((prev) => [
                    ...prev,
                    { localId, file, status: 'failed', error: `${sizeMb} MB selected — maximum is 10 MB.` }
                ]);
                return;
            }

            validCandidates.push({ file, localId });
        });

        if (!validCandidates.length) return;

        // Quota check across valid candidates against remaining storage
        let accumulatedBytes = 0;
        const toUpload = [];

        for (const candidate of validCandidates) {
            if (accumulatedBytes + candidate.file.size > currentRemaining) {
                const totalMb = (candidate.file.size / (1024 * 1024)).toFixed(1);
                setAttachedFiles((prev) => [
                    ...prev,
                    {
                        localId: candidate.localId,
                        file: candidate.file,
                        status: 'failed',
                        error: `Not enough storage. ${remainingMb} MB remaining, but file is ${totalMb} MB.`
                    }
                ]);
                setStorageNotice(`Not enough storage. You have ${remainingMb} MB remaining, but selected files exceed your quota.`);
            } else {
                accumulatedBytes += candidate.file.size;
                toUpload.push(candidate);
            }
        }

        if (!toUpload.length) return;

        let uploadConversationId;
        try {
            uploadConversationId = await getConversationIdForUpload();
        } catch (err) {
            setAttachedFiles((prev) => [
                ...prev,
                ...toUpload.map(({ file, localId }) => ({
                    localId,
                    file,
                    status: 'failed',
                    error: err.message || 'Could not create conversation.',
                })),
            ]);
            return;
        }

        toUpload.forEach(({ file, localId }) => {
            setAttachedFiles((prev) => [...prev, { localId, file, status: 'uploading' }]);

            api
                .uploadDocument(file, uploadConversationId)
                .then((doc) => {
                    setAttachedFiles((prev) =>
                        prev.map((f) => (f.localId === localId ? { ...f, documentId: doc.id, status: 'processing' } : f))
                    );
                    refreshStorageUsage();

                    const cleanup = pollDocumentStatus(doc.id, (updated) => {
                        setAttachedFiles((prev) =>
                            prev.map((f) =>
                                f.localId === localId
                                    ? {
                                          ...f,
                                          status: updated.status === 'indexed' ? 'ready' : updated.status,
                                          error: updated.status === 'failed' ? updated.error_message || 'Document processing failed' : undefined,
                                      }
                                    : f
                            )
                        );
                        if (updated.status === 'indexed' || updated.status === 'failed') {
                            refreshStorageUsage();
                        }
                    });
                    pollCleanupsRef.current[localId] = cleanup;
                })
                .catch((err) => {
                    const rawMsg = err.message || '';
                    let friendlyError = rawMsg;
                    if (rawMsg.includes('100 MB') || rawMsg.includes('document limit') || rawMsg.includes('storage')) {
                        friendlyError = 'Upload would exceed the 100 MB storage limit.';
                    } else if (rawMsg.includes('10 MB') || rawMsg.includes('smaller than 10')) {
                        friendlyError = 'File is too large. Maximum file size is 10 MB.';
                    } else if (!friendlyError) {
                        friendlyError = 'Upload failed';
                    }

                    setAttachedFiles((prev) =>
                        prev.map((f) => (f.localId === localId ? { ...f, status: 'failed', error: friendlyError } : f))
                    );
                    refreshStorageUsage();
                });
        });
    };

    const removeFile = async (localId) => {
        pollCleanupsRef.current[localId]?.();
        delete pollCleanupsRef.current[localId];

        const target = attachedFiles.find((f) => f.localId === localId);
        setAttachedFiles((prev) => prev.filter((f) => f.localId !== localId));

        if (target?.documentId) {
            try {
                await api.deleteDocument(target.documentId);
            } catch {
                // best-effort
            }
            refreshStorageUsage();
        }
    };

    const handleSuggestionClick = (suggestion) => {
        setInput(suggestion);
        setShowSuggestions(false);
    };

    const handleTaskSelection = (task) => {
        setInput(task.query);
        setPendingAction(task.action || 'general');
        setShowTaskSwitcher(false);
    };

    // --- BACKEND INTEGRATION POINT: real feedback submission ---
    const handleFeedback = (messageId, isPositive) => {
        setMessages((prev) =>
            prev.map((msg) => (msg.id === messageId ? { ...msg, feedback: isPositive ? 'positive' : 'negative' } : msg))
        );
        api.submitFeedback(messageId, isPositive ? 'positive' : 'negative').catch(() => {
            // Non-critical - feedback is best-effort; UI already reflects the click.
        });
    };

    const filteredSuggestions = commonQueries.filter(
        (query) => query.toLowerCase().includes(input.toLowerCase()) && input.trim().length > 0
    );

    const usedMb = ((storageUsage.used_bytes || 0) / (1024 * 1024)).toFixed(1);
    const maxMb = ((storageUsage.max_bytes || (100 * 1024 * 1024)) / (1024 * 1024)).toFixed(0);
    const isStorageFull = (storageUsage.remaining_bytes ?? (100 * 1024 * 1024)) <= 0;

    return (
        <div className="flex-1 flex flex-col w-full max-w-4xl mx-auto h-full relative">
            <div className="flex-1 overflow-y-auto space-y-6 py-4 sm:py-8 px-2 sm:px-4">
                {loadError && <p className="text-sm text-red-400 text-center">{loadError}</p>}
                <AnimatePresence>
                    {messages.map((msg, index) => (
                        <motion.div key={msg.id || index} layout initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
                            <ChatMessage
                                message={msg}
                                onFeedback={msg.role === 'assistant' && msg.id ? (isPositive) => handleFeedback(msg.id, isPositive) : null}
                            />
                        </motion.div>
                    ))}
                </AnimatePresence>
                {isLoading && <LoadingBubble />}
                <div ref={messagesEndRef} />
            </div>

            {/* Task Switcher */}
            <AnimatePresence>
                {showTaskSwitcher && taskSuggestions.length > 0 && (
                    <motion.div
                        className="absolute bottom-32 left-4 right-4 bg-gray-900/95 border border-gray-700/50 rounded-lg p-4 backdrop-blur-sm"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 20 }}
                    >
                        <div className="flex items-center gap-2 mb-3">
                            <Lightbulb className="w-4 h-4 text-yellow-400" />
                            <span className="text-sm font-medium">Suggested actions for your query:</span>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                            {taskSuggestions.slice(0, 4).map((task, index) => (
                                <button
                                    key={index}
                                    onClick={() => handleTaskSelection(task)}
                                    className="flex items-center gap-2 p-2 bg-gray-800/50 hover:bg-gray-700/50 rounded-md text-sm transition-colors"
                                >
                                    <task.icon className="w-4 h-4 text-purple-400" />
                                    {task.title}
                                </button>
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Query Suggestions */}
            <AnimatePresence>
                {showSuggestions && filteredSuggestions.length > 0 && (
                    <motion.div
                        className="absolute bottom-32 left-4 right-4 bg-gray-900/95 border border-gray-700/50 rounded-lg p-2 backdrop-blur-sm max-h-32 overflow-y-auto"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 20 }}
                    >
                        {filteredSuggestions.slice(0, 5).map((suggestion, index) => (
                            <button
                                key={index}
                                onClick={() => handleSuggestionClick(suggestion)}
                                className="w-full text-left p-2 hover:bg-gray-700/50 rounded text-sm transition-colors"
                            >
                                {suggestion}
                            </button>
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Input Area */}
            <div className="p-2 sm:p-4 space-y-2">
                {/* Attached Files */}
                {attachedFiles.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                        {attachedFiles.map((f) => (
                            <AttachedFilePill key={f.localId} entry={f} onRemove={() => removeFile(f.localId)} />
                        ))}
                    </div>
                )}

                {/* Compact Storage Indicator & Notices */}
                <div className="flex items-center justify-between text-xs px-1 text-gray-400">
                    <div className="flex items-center gap-1.5" title={`${usedMb} MB used of ${maxMb} MB conversation storage`}>
                        <Paperclip className={`w-3.5 h-3.5 ${isStorageFull ? 'text-red-400' : 'text-purple-400'}`} />
                        <span className={isStorageFull ? 'text-red-400 font-medium' : 'text-gray-300'}>
                            Storage: {usedMb} MB / {maxMb} MB
                        </span>
                        {isStorageFull && (
                            <span className="text-red-400 font-semibold">(Limit reached)</span>
                        )}
                    </div>
                    {storageNotice && (
                        <div className="text-xs text-amber-400 flex items-center gap-1">
                            <span>{storageNotice}</span>
                            <button
                                type="button"
                                onClick={() => setStorageNotice(null)}
                                className="text-gray-400 hover:text-gray-200 ml-1"
                            >
                                <X className="w-3 h-3" />
                            </button>
                        </div>
                    )}
                </div>

                <div className="relative">
                    <Textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
                        onFocus={() => setShowSuggestions(true)}
                        onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                        placeholder="Ask a question..."
                        className="w-full pl-4 pr-20 py-3 text-sm sm:text-base"
                        rows="1"
                    />

                    <button
                        onClick={() => {
                            if (!isLoggedIn) {
                                openLoginModal();
                                return;
                            }
                            if (isStorageFull) {
                                setStorageNotice("Storage limit reached (100 MB). Remove a document to upload another.");
                                return;
                            }
                            fileInputRef.current?.click();
                        }}
                        disabled={isStorageFull}
                        className={`absolute right-12 sm:right-16 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center transition-colors z-10 ${
                            isStorageFull
                                ? 'text-gray-600 cursor-not-allowed opacity-50'
                                : 'text-gray-400 hover:text-white cursor-pointer'
                        }`}
                        title={
                            isStorageFull
                                ? 'Storage limit reached (100 MB). Remove a document to upload another.'
                                : `Attach files (Max 10 MB per file) · ${usedMb} MB / ${maxMb} MB used`
                        }
                        type="button"
                    >
                        <Paperclip className="w-4 h-4 sm:w-5 sm:h-5" />
                    </button>

                    <button
                        onClick={handleSend}
                        disabled={isLoading || !input.trim()}
                        className="absolute right-2 sm:right-4 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-purple-600 text-white disabled:bg-gray-600 hover:bg-purple-700 transition-colors cursor-pointer z-10 flex items-center justify-center"
                        type="button"
                    >
                        {isLoading ? <Loader2 className="w-4 h-4 sm:w-5 sm:h-5 animate-spin" /> : <Send className="w-4 h-4 sm:w-5 sm:h-5" />}
                    </button>

                    <input
                        ref={fileInputRef}
                        type="file"
                        multiple
                        accept=".pdf,.doc,.docx,.txt"
                        onChange={handleFileAttachment}
                        className="hidden"
                    />
                </div>
            </div>
        </div>
    );
};

const STATUS_LABELS = {
    uploading: 'Uploading...',
    uploaded: 'Processing...',
    processing: 'Processing...',
    ready: 'Ready',
    failed: 'Failed',
};

const AttachedFilePill = ({ entry, onRemove }) => {
    const { file, status, error } = entry;
    const isBusy = status === 'uploading' || status === 'uploaded' || status === 'processing';
    const isReady = status === 'ready';
    const isFailed = status === 'failed';

    return (
        <div
            className={`flex items-center gap-2 border rounded-lg px-3 py-1 ${
                isFailed ? 'bg-red-900/20 border-red-700/50' : 'bg-gray-800/50 border-gray-700/50'
            }`}
            title={error}
        >
            {isBusy && <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />}
            {isReady && <CheckCircle2 className="w-4 h-4 text-green-400" />}
            {isFailed && <AlertCircle className="w-4 h-4 text-red-400" />}
            {!isBusy && !isReady && !isFailed && <FileText className="w-4 h-4 text-gray-400" />}
            <span className="text-sm max-w-[10rem] truncate">{file.name}</span>
            <span className="text-xs text-gray-400">{isFailed ? error || 'Failed' : STATUS_LABELS[status] || status}</span>
            <button onClick={onRemove} className="text-gray-400 hover:text-white cursor-pointer">
                <X className="w-4 h-4" />
            </button>
        </div>
    );
};

const ChatMessage = ({ message, onFeedback }) => {
    const isAssistant = message.role === 'assistant';
    return (
        <div className={`flex items-start gap-2 sm:gap-4 ${!isAssistant && 'flex-row-reverse'}`}>
            <div className={`flex-shrink-0 w-6 h-6 sm:w-8 sm:h-8 rounded-full flex items-center justify-center ${isAssistant ? 'bg-purple-500/30' : 'bg-gray-600/40'}`}>
                {isAssistant ? <Bot className="w-3 h-3 sm:w-5 sm:h-5 text-purple-400" /> : <UserIcon className="w-3 h-3 sm:w-5 sm:h-5 text-gray-300" />}
            </div>
            <div className={`px-3 py-2 sm:px-5 sm:py-3 rounded-lg max-w-[85%] sm:max-w-lg border text-sm sm:text-base ${isAssistant ? 'bg-gray-800/80 border-gray-700/50 text-gray-100' : 'bg-purple-600/30 border-purple-500/50 text-gray-100'}`}>
                {isAssistant && message.insufficient_context && (
                    <div className="mb-2 px-2.5 py-1 rounded bg-yellow-500/10 border border-yellow-500/30 text-yellow-300 text-xs font-medium flex items-center gap-1.5">
                        <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                        <span>Insufficient document context found to answer fully.</span>
                    </div>
                )}

                {isAssistant && message.summary && (
                    <div className="mb-2.5 px-3 py-1.5 rounded bg-purple-900/30 border border-purple-700/40 text-xs sm:text-sm text-purple-200">
                        <span className="font-semibold text-purple-300">Summary: </span>
                        {message.summary}
                    </div>
                )}

                <p className="whitespace-pre-wrap break-words">{message.content}</p>

                {isAssistant && message.key_points?.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-gray-700/40 text-xs sm:text-sm">
                        <p className="font-semibold text-purple-300 mb-1">Key Points:</p>
                        <ul className="list-disc pl-4 space-y-1 text-gray-300">
                            {message.key_points.map((pt, idx) => (
                                <li key={idx}>{pt}</li>
                            ))}
                        </ul>
                    </div>
                )}

                {isAssistant && message.decision && (
                    <div className="mt-2 text-xs sm:text-sm text-gray-300">
                        <span className="font-semibold text-purple-300">Decision: </span>
                        {message.decision}
                    </div>
                )}

                {isAssistant && message.conditions?.length > 0 && (
                    <div className="mt-2 text-xs sm:text-sm text-gray-300">
                        <span className="font-semibold text-purple-300">Conditions: </span>
                        {message.conditions.join(', ')}
                    </div>
                )}

                {isAssistant && message.exclusions?.length > 0 && (
                    <div className="mt-2 text-xs sm:text-sm text-gray-300">
                        <span className="font-semibold text-purple-300">Exclusions: </span>
                        {message.exclusions.join(', ')}
                    </div>
                )}

                {isAssistant && message.sources?.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-gray-700/50 text-xs text-gray-400">
                        <p className="font-semibold text-purple-300 mb-1.5">Sources & Citations:</p>
                        <div className="flex flex-wrap gap-1.5">
                            {message.sources.map((src, idx) => (
                                <span
                                    key={idx}
                                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-gray-700/50 border border-gray-600/40 text-gray-300 text-[11px]"
                                >
                                    <span>📄</span>
                                    <span className="font-medium">{src.document_name}</span>
                                    {src.page_number && <span>(p. {src.page_number})</span>}
                                    {src.section && <span>— {src.section}</span>}
                                </span>
                            ))}
                        </div>
                    </div>
                )}

                {onFeedback && (
                    <div className="mt-3 pt-2 border-t border-gray-700/50 flex gap-2 justify-end">
                        <button
                            onClick={() => onFeedback(true)}
                            className={`p-1 rounded hover:bg-gray-700 ${message.feedback === 'positive' ? 'text-green-400' : 'text-gray-400'}`}
                            title="Helpful"
                        >
                            <ThumbsUp className="w-4 h-4" />
                        </button>
                        <button
                            onClick={() => onFeedback(false)}
                            className={`p-1 rounded hover:bg-gray-700 ${message.feedback === 'negative' ? 'text-red-400' : 'text-gray-400'}`}
                            title="Not helpful"
                        >
                            <ThumbsDown className="w-4 h-4" />
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

const LoadingBubble = () => (
    <div className="flex items-start gap-4">
        <div className="w-8 h-8 rounded-full bg-purple-500/30 flex items-center justify-center">
            <Bot className="w-5 h-5 text-purple-400" />
        </div>
        <div className="px-5 py-3 rounded-lg bg-gray-800/80 border border-gray-700/50 text-gray-100 flex items-center gap-2">
            <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />
            <span className="text-sm">Thinking...</span>
        </div>
    </div>
);

export default Chat;
