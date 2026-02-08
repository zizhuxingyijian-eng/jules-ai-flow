'use client';

import { useState } from 'react';
import { experimental_useObject as useObject } from '@ai-sdk/react';
import { z } from 'zod';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Loader2, CheckCircle, Save, Play, FileText, AlertCircle, RefreshCw } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

const WorkflowSchema = z.object({
  title: z.string(),
  detailedReport: z.string(),
  agentInstructions: z.string(),
  tags: z.array(z.string()),
  priority: z.enum(['High', 'Medium', 'Low'])
});

type WorkflowStatus = 'idle' | 'thinking' | 'review' | 'backing_up' | 'executing' | 'completed' | 'error';

const STATUS_LABELS: Record<string, string> = {
    idle: "空闲 / IDLE",
    thinking: "思考中 / THINKING",
    review: "审查 / REVIEW",
    backing_up: "存档 / BACKUP",
    executing: "执行 / EXECUTE",
    completed: "完成 / DONE",
    error: "错误 / ERROR"
};

export default function AssistantPage() {
  const [status, setStatus] = useState<WorkflowStatus>('idle');
  const [notionData, setNotionData] = useState<{ url: string; id: string } | null>(null);
  const [manusResult, setManusResult] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const { object, submit, isLoading, error: aiError, stop } = useObject({
    api: '/api/chat',
    schema: WorkflowSchema,
    onFinish: (result) => {
      if (result.error) {
        setStatus('error');
        setErrorMsg(result.error.message);
      } else {
        setStatus('review');
      }
    },
  });

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const input = formData.get('input') as string;
    if (!input.trim()) return;

    setStatus('thinking');
    setNotionData(null);
    setManusResult(null);
    setErrorMsg(null);

    submit({ messages: [{ role: 'user', content: input }] });
  };

  const handleBackup = async () => {
    if (!object) return;
    setStatus('backing_up');
    try {
      const res = await fetch('/api/notion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(object),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to backup');
      setNotionData(data);
      handleExecute(data.url, data.id);
    } catch (err: any) {
      setStatus('error');
      setErrorMsg(err.message);
    }
  };

  const handleExecute = async (url: string, id: string) => {
    setStatus('executing');
    try {
      const res = await fetch('/api/manus', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notionUrl: url, notionId: id }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to execute');
      setManusResult(data);
      setStatus('completed');
    } catch (err: any) {
      setStatus('error');
      setErrorMsg(err.message);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans p-4 md:p-8">
      <div className="max-w-4xl mx-auto space-y-8">

        {/* Header */}
        <header className="flex items-center space-x-3 pb-6 border-b border-gray-200">
          <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center text-white">
            <FileText size={24} />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">企业级 AI 工作流 / Enterprise AI Workflow</h1>
            <p className="text-sm text-gray-500">Gemini 智库 • Notion 记忆体 • Manus 代理 / Think Tank • Memory • Agent</p>
          </div>
        </header>

        {/* Status Bar */}
        <div className="flex items-center justify-between bg-white p-4 rounded-xl shadow-sm border border-gray-100 overflow-x-auto">
            {['idle', 'thinking', 'review', 'backing_up', 'executing', 'completed'].map((s, i) => {
                const isActive = status === s;
                const isPast = ['idle', 'thinking', 'review', 'backing_up', 'executing', 'completed'].indexOf(status) > i;
                return (
                    <div key={s} className="flex items-center space-x-2 min-w-max">
                         <div className={clsx(
                             "w-3 h-3 rounded-full",
                             isActive ? "bg-blue-500 animate-pulse" : isPast ? "bg-green-500" : "bg-gray-200"
                         )} />
                         <span className={clsx("text-xs uppercase font-medium", isActive ? "text-blue-600" : "text-gray-400")}>
                             {STATUS_LABELS[s]}
                         </span>
                         {i < 5 && <div className="w-8 h-px bg-gray-200 mx-2 hidden md:block" />}
                    </div>
                )
            })}
        </div>

        {/* Input Area */}
        {(status === 'idle' || status === 'completed' || status === 'error') && (
          <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 space-y-4">
            <h2 className="text-lg font-semibold">您的战略目标是什么？ / What is your strategic goal?</h2>
            <textarea
              name="input"
              className="w-full p-4 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none min-h-[120px]"
              placeholder="例如：进行市场分析... / e.g., Conduct a market analysis..."
            />
            <button
              type="submit"
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg flex items-center space-x-2 transition-colors"
            >
              <span>生成计划 / Generate Plan</span>
              <Play size={16} />
            </button>
          </form>
        )}

        {/* Error Message */}
        {errorMsg && (
            <div className="bg-red-50 text-red-600 p-4 rounded-lg flex items-center space-x-2">
                <AlertCircle size={20} />
                <span>{errorMsg}</span>
            </div>
        )}

        {/* Thinking / Review Area */}
        {(status === 'thinking' || status === 'review' || object) && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="p-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
                <h3 className="font-semibold text-gray-700 flex items-center space-x-2">
                    {isLoading ? <Loader2 className="animate-spin" size={18} /> : <CheckCircle size={18} className="text-green-500" />}
                    <span>已生成战略计划 / Generated Plan</span>
                </h3>
                {status === 'review' && (
                    <button
                        onClick={handleBackup}
                        className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg flex items-center space-x-2"
                    >
                        <Save size={16} />
                        <span>批准并执行 / Approve & Execute</span>
                    </button>
                )}
            </div>

            <div className="p-6 space-y-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <h1 className="text-2xl font-bold text-gray-900">{object?.title || "生成标题中... / Drafting Title..."}</h1>
                    <div className="flex space-x-2">
                        {object?.priority && (
                            <span className={clsx(
                                "px-2 py-1 rounded text-xs font-semibold",
                                object.priority === 'High' ? "bg-red-100 text-red-700" :
                                object.priority === 'Medium' ? "bg-yellow-100 text-yellow-700" : "bg-blue-100 text-blue-700"
                            )}>
                                {object.priority} Priority
                            </span>
                        )}
                        {object?.tags?.map((tag) => (
                            tag ? (
                            <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs font-medium border border-gray-200">
                                {tag}
                            </span>
                            ) : null
                        ))}
                    </div>
                </div>

                <div className="prose prose-sm max-w-none text-gray-700">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {object?.detailedReport || "分析中... / Analyzing..."}
                    </ReactMarkdown>
                </div>

                <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                    <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Manus 代理指令 / Agent Instructions</h4>
                    <p className="font-mono text-sm text-slate-700 whitespace-pre-wrap">
                        {object?.agentInstructions || "Drafting instructions..."}
                    </p>
                </div>
            </div>
          </div>
        )}

        {/* Execution Status */}
        {(status === 'backing_up' || status === 'executing' || status === 'completed') && (
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 space-y-4">
                <h3 className="font-semibold text-gray-900">执行日志 / Execution Log</h3>

                <div className="space-y-3">
                    <div className="flex items-center space-x-3">
                        {notionData ? <CheckCircle className="text-green-500" size={20} /> : <Loader2 className="animate-spin text-blue-500" size={20} />}
                        <div className="flex-1">
                            <p className="text-sm font-medium">备份至 Notion / Backup to Notion</p>
                            {notionData && (
                                <a href={notionData.url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:underline">
                                    查看 Notion 页面 / View Page
                                </a>
                            )}
                        </div>
                    </div>

                    <div className="flex items-center space-x-3">
                        {status === 'backing_up' ? (
                            <div className="w-5 h-5 rounded-full border-2 border-gray-200" />
                        ) : status === 'executing' ? (
                            <Loader2 className="animate-spin text-blue-500" size={20} />
                        ) : status === 'completed' ? (
                            <CheckCircle className="text-green-500" size={20} />
                        ) : (
                             <div className="w-5 h-5 rounded-full border-2 border-gray-200" />
                        )}
                        <div className="flex-1">
                            <p className="text-sm font-medium">Manus 代理执行 / Manus Execution</p>
                            {status === 'executing' && <p className="text-xs text-gray-500">代理正在执行... / Agent is working...</p>}
                            {status === 'completed' && <p className="text-xs text-green-600">任务已启动 / Task started</p>}
                        </div>
                    </div>
                </div>
            </div>
        )}

      </div>
    </div>
  );
}
