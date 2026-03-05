import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Send, Paperclip, Sparkles, Loader2, FileCheck, Code, Server } from 'lucide-react';
import agentService from '../service/agent.service';

/* ── Компонент отдельного сообщения ── */
const Message = ({ msg }) => {
  const isUser = msg.role === 'user';
  
  return (
    <motion.div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.2 }}
    >
      <div
        className="max-w-[85%] px-4 py-3 rounded-2xl text-[13px] leading-relaxed shadow-lg"
        style={
          isUser
            ? {
                background: 'linear-gradient(135deg, #6d28d9, #4c1d95)',
                color: '#fff',
                borderBottomRightRadius: '4px',
              }
            : {
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(120,60,220,0.2)',
                color: '#e2e8f0',
                borderBottomLeftRadius: '4px',
              }
        }
      >
        {msg.text}

        {/* Если агент прислал технические характеристики (specs) */}
        {msg.specs && (
          <div className="mt-3 p-3 bg-black/40 rounded-xl border border-purple-500/30 font-mono text-[11px]">
            <div className="flex items-center gap-2 text-purple-400 mb-2 font-bold uppercase tracking-wider">
              <Server size={12} /> Рекомендуемая конфигурация
            </div>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(msg.specs).map(([key, val]) => (
                <div key={key} className="flex justify-between border-b border-white/5 pb-1">
                  <span className="text-slate-500">{key}:</span>
                  <span className="text-white">{val}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
};

/* ── Вспомогательный компонент: Индикатор печати ── */
const TypingIndicator = () => (
  <div className="flex gap-1 px-4 py-3 bg-white/5 rounded-2xl w-fit border border-white/5">
    {[0, 1, 2].map((i) => (
      <motion.div
        key={i}
        className="w-1.5 h-1.5 rounded-full bg-purple-500"
        animate={{ opacity: [0.4, 1, 0.4], y: [0, -3, 0] }}
        transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
      />
    ))}
  </div>
);

/* ── Основной компонент AI Chat ── */
const AiChat = () => {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const [projectRoot, setProjectRoot] = useState(null); // Храним путь к проекту на бэке
  const [uploading, setUploading] = useState(false);

  const bottomRef = useRef(null);
  const fileInputRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typing]);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 400);
  }, [open]);

  // Обработка загрузки файла/архива
  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    try {
      const result = await agentService.uploadProject(file);
      setProjectRoot(result.project_root);
      setMessages(prev => [...prev, { 
        role: 'ai', 
        text: `📁 Проект "${file.name}" успешно загружен и проиндексирован. Теперь я готов ответить на вопросы по его архитектуре и развертыванию.` 
      }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'ai', text: '❌ Ошибка при загрузке файла. Попробуйте другой формат.' }]);
    } finally {
      setUploading(false);
      e.target.value = ''; // Сброс инпута
    }
  };

  // Отправка сообщения агенту
  const handleSendMessage = async () => {
    const text = input.trim();
    if (!text || typing || uploading) return;

    setMessages(prev => [...prev, { role: 'user', text }]);
    setInput('');
    setTyping(true);

    try {
      // Вызов вашего бэкенда через сервис
      const data = await agentService.askAgent(text, projectRoot);
      
      setMessages(prev => [...prev, { 
        role: 'ai', 
        text: data.response,
        specs: data.specs, // Тот самый JSON с характеристиками из LangGraph
        docker: data.docker_created
      }]);
    } catch (err) {
      setMessages(prev => [...prev, { 
        role: 'ai', 
        text: '⚠️ Не удалось связаться с агентом. Проверьте соединение с сервером.' 
      }]);
    } finally {
      setTyping(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <>
      {/* Trigger Button */}
      <AnimatePresence>
        {!open && (
          <motion.button
            onClick={() => setOpen(true)}
            className="fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-3 rounded-2xl text-white font-bold shadow-2xl"
            style={{
              background: 'linear-gradient(135deg, #7c3aed, #4c1d95)',
              border: '1px solid rgba(255,255,255,0.1)',
            }}
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Sparkles size={18} className="animate-pulse" />
            <span className="text-sm tracking-wide">AI Assistant</span>
          </motion.button>
        )}
      </AnimatePresence>

      {/* Chat Window */}
      <AnimatePresence>
        {open && (
          <motion.div
            className="fixed bottom-6 right-6 z-[1000] flex flex-col w-[400px] h-[580px] rounded-[24px] bg-[#0a0812] border border-white/10 shadow-[0_32px_80px_rgba(0,0,0,0.8)] overflow-hidden"
            initial={{ opacity: 0, y: 40, scale: 0.95, transformOrigin: 'bottom right' }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 40, scale: 0.95 }}
          >
            {/* Header */}
            <div className="p-4 flex items-center justify-between border-b border-white/5 bg-white/[0.02]">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-purple-500/20 flex items-center justify-center border border-purple-500/30">
                  <Sparkles size={16} className="text-purple-400" />
                </div>
                <div>
                  <h4 className="text-white text-xs font-bold leading-none">Cloud Agent v1.0</h4>
                  <div className="flex items-center gap-1.5 mt-1">
                    <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                    <span className="text-[10px] text-slate-500 font-medium">System Ready</span>
                  </div>
                </div>
              </div>
              <button onClick={() => setOpen(false)} className="p-2 text-slate-500 hover:text-white transition-colors">
                <X size={18} />
              </button>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-2 scrollbar-hide">
              {messages.length === 0 && (
                <div className="h-full flex flex-col items-center justify-center text-center space-y-4 px-8">
                  <div className="w-16 h-16 rounded-3xl bg-white/5 border border-white/10 flex items-center justify-center">
                    <Code size={28} className="text-slate-600" />
                  </div>
                  <p className="text-slate-400 text-xs leading-relaxed">
                    Загрузите архив с вашим проектом или просто опишите задачу для настройки инфраструктуры.
                  </p>
                </div>
              )}
              {messages.map((msg, idx) => (
                <Message key={idx} msg={msg} />
              ))}
              {typing && <TypingIndicator />}
              <div ref={bottomRef} />
            </div>

            {/* Input Footer */}
            <div className="p-4 bg-white/[0.01] border-t border-white/5">
              <div className="relative flex items-end gap-2 bg-white/[0.03] border border-white/10 rounded-2xl p-2 focus-within:border-purple-500/40 transition-all">
                
                {/* File Upload Button */}
                <input 
                  type="file" 
                  className="hidden" 
                  ref={fileInputRef} 
                  onChange={handleFileChange} 
                  accept=".zip,.tar.gz,.rar,.tgz"
                />
                <button 
                  onClick={() => fileInputRef.current.click()}
                  disabled={uploading}
                  className={`p-2 rounded-xl transition-colors ${uploading ? 'text-purple-500' : 'text-slate-500 hover:text-white hover:bg-white/5'}`}
                >
                  {uploading ? <Loader2 size={18} className="animate-spin" /> : <Paperclip size={18} />}
                </button>

                {/* Text Input */}
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={onKeyDown}
                  placeholder={projectRoot ? "Спросите по коду проекта..." : "Введите запрос..."}
                  rows="1"
                  className="flex-1 bg-transparent border-none outline-none text-[13px] text-white placeholder:text-slate-600 py-2 resize-none max-h-32"
                />

                {/* Send Button */}
                <button
                  onClick={handleSendMessage}
                  disabled={!input.trim() || typing || uploading}
                  className="p-2 bg-purple-600 text-white rounded-xl hover:bg-purple-500 disabled:opacity-20 disabled:grayscale transition-all"
                >
                  <Send size={18} />
                </button>

                {/* Project Status Badge */}
                {projectRoot && (
                  <div className="absolute -top-3 left-3 px-2 py-0.5 bg-green-500/10 border border-green-500/20 rounded-md flex items-center gap-1.5 shadow-xl">
                    <FileCheck size={10} className="text-green-500" />
                    <span className="text-[9px] text-green-500 font-bold uppercase tracking-tighter">Context Active</span>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default AiChat;