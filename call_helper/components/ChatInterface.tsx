"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}

interface Source {
  content: string;
  page?: number;
  source_type?: string;
  similarity?: number;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [userId] = useState(() => {
    // Generate or retrieve user ID (you can implement proper user management)
    if (typeof window !== "undefined") {
      let id = localStorage.getItem("user_id");
      if (!id) {
        id = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        localStorage.setItem("user_id", id);
      }
      return id;
    }
    return "anonymous";
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      role: "user",
      content: input
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: input,
          history: messages.map(m => ({ role: m.role, content: m.content })),
          user_id: userId,
          language: "ru"
        }),
      });

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      // Handle client type request
      if (data.requiresClientType) {
        const assistantMessage: Message = {
          role: "assistant",
          content: data.answer,
          sources: []
        };
        setMessages(prev => [...prev, assistantMessage]);
        return;
      }

      const assistantMessage: Message = {
        role: "assistant",
        content: data.answer,
        sources: data.sources
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error: any) {
      const errorMessage: Message = {
        role: "assistant",
        content: `Ошибка: ${error.message || "Не удалось получить ответ"}. Пожалуйста, попробуйте еще раз.`
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const exampleQuestions = [
    "Какие тарифы на интернет?",
    "Как подключить услугу?",
    "Что делать, если не работает интернет?",
    "Как оплатить услуги?"
  ];

  const handleExampleClick = (question: string) => {
    setInput(question);
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-md shadow-lg border-b border-gray-200/50 px-6 py-5">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
              <span className="text-2xl">📞</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                Help Desk Казахтелеком
              </h1>
              <p className="text-sm text-gray-600 mt-0.5">
                Виртуальный помощник по услугам и поддержке
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.length === 0 && (
            <div className="text-center mt-16">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-2xl mb-6 shadow-lg">
                <span className="text-4xl">👋</span>
              </div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">
                Добро пожаловать!
              </h2>
              <p className="text-gray-600 mb-8 max-w-md mx-auto">
                Задайте вопрос об услугах Казахтелеком, и я помогу найти нужную информацию или создам тикет для наших специалистов
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
                {exampleQuestions.map((question, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleExampleClick(question)}
                    className="text-left px-4 py-3 bg-white/80 backdrop-blur-sm rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all duration-200 text-sm text-gray-700 hover:text-blue-600"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message, idx) => (
            <div
              key={idx}
              className={`flex gap-4 ${message.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {message.role === "assistant" && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center flex-shrink-0 shadow-lg">
                  <span className="text-white text-sm">📞</span>
                </div>
              )}
              
              <div
                className={`max-w-[85%] md:max-w-[75%] rounded-2xl px-5 py-4 shadow-lg ${
                  message.role === "user"
                    ? "bg-gradient-to-br from-blue-500 to-indigo-600 text-white"
                    : "bg-white/90 backdrop-blur-sm text-gray-800 border border-gray-100"
                }`}
              >
                {message.role === "assistant" ? (
                  <div className="prose prose-sm max-w-none leading-relaxed">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        h1: ({...props}: any) => <h1 className="text-xl font-bold mt-4 mb-2 text-gray-900" {...props} />,
                        h2: ({...props}: any) => <h2 className="text-lg font-bold mt-3 mb-2 text-gray-900" {...props} />,
                        h3: ({...props}: any) => <h3 className="text-base font-bold mt-2 mb-1 text-gray-900" {...props} />,
                        p: ({...props}: any) => <p className="mb-2 text-gray-800" {...props} />,
                        ul: ({...props}: any) => <ul className="list-disc list-inside mb-2 space-y-1 text-gray-800" {...props} />,
                        ol: ({...props}: any) => <ol className="list-decimal list-inside mb-2 space-y-1 text-gray-800" {...props} />,
                        li: ({...props}: any) => <li className="ml-2" {...props} />,
                        strong: ({...props}: any) => <strong className="font-semibold text-gray-900" {...props} />,
                        em: ({...props}: any) => <em className="italic" {...props} />,
                        code: ({inline, ...props}: any) => 
                          inline ? (
                            <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800" {...props} />
                          ) : (
                            <code className="block bg-gray-100 p-2 rounded text-sm font-mono text-gray-800 overflow-x-auto" {...props} />
                          ),
                        blockquote: ({...props}: any) => (
                          <blockquote className="border-l-4 border-blue-300 pl-3 italic my-2 text-gray-700" {...props} />
                        ),
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <div className="whitespace-pre-wrap leading-relaxed">{message.content}</div>
                )}
                
                {message.sources && message.sources.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-200/50">
                    <p className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">
                      📚 Источники
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {message.sources.slice(0, 3).map((source, sIdx) => (
                        <div 
                          key={sIdx} 
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-50 rounded-lg text-xs text-gray-600 border border-gray-200"
                        >
                          {source.page && (
                            <span>Страница {source.page}</span>
                          )}
                          {source.similarity && (
                            <>
                              <span className="text-gray-400">•</span>
                              <span className="text-gray-500">Релевантность: {(source.similarity * 100).toFixed(0)}%</span>
                            </>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {message.role === "user" && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-400 to-gray-500 flex items-center justify-center flex-shrink-0 shadow-lg">
                  <span className="text-white text-sm">👤</span>
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-4 justify-start">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center flex-shrink-0 shadow-lg">
                <span className="text-white text-sm">📞</span>
              </div>
              <div className="bg-white/90 backdrop-blur-sm rounded-2xl px-5 py-4 shadow-lg border border-gray-100">
                <div className="flex space-x-2">
                  <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce"></div>
                  <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                  <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "0.4s" }}></div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="bg-white/80 backdrop-blur-md border-t border-gray-200/50 px-4 py-5 shadow-2xl">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSubmit} className="relative">
            <div className="flex items-end gap-3">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Задайте вопрос об услугах Казахтелеком..."
                  className="w-full px-5 py-4 pr-14 bg-white border-2 border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all shadow-sm text-gray-800 placeholder-gray-400"
                  disabled={loading}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSubmit(e);
                    }
                  }}
                />
                <div className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 text-xs">
                  Enter
                </div>
              </div>
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="px-6 py-4 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-2xl font-medium hover:from-blue-600 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl flex items-center gap-2 min-w-[120px] justify-center"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Отправка...</span>
                  </>
                ) : (
                  <>
                    <span>Отправить</span>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

