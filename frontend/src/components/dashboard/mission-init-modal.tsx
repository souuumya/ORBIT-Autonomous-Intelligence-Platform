'use client';

import React, { useState } from 'react';
import { Target, X, Loader2, AlertCircle, Sparkles } from 'lucide-react';
import { MissionInitPayload } from '@/lib/api-client';

interface MissionInitModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: MissionInitPayload) => Promise<string>;
  isInitializing?: boolean;
}

export const MissionInitModal: React.FC<MissionInitModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isInitializing = false,
}) => {
  const [title, setTitle] = useState('');
  const [objective, setObjective] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<'low' | 'medium' | 'high' | 'critical'>('high');
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !objective.trim()) {
      setError('Mission Title and Objective are required.');
      return;
    }

    setError(null);
    try {
      await onSubmit({
        mission_title: title,
        mission_objective: objective,
        mission_description: description,
        priority,
      });
      // Reset form and close on success
      setTitle('');
      setObjective('');
      setDescription('');
      setPriority('high');
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to initialize mission.';
      setError(msg);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl shadow-cyan-950/20">
        {/* Close Button */}
        <button
          onClick={onClose}
          disabled={isInitializing}
          className="absolute right-4 top-4 rounded-lg p-1 text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200 transition"
          aria-label="Close dialog"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Modal Header */}
        <div className="mb-5 flex items-center space-x-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-cyan-500/30 bg-cyan-500/10 text-cyan-400">
            <Target className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold tracking-tight text-zinc-100">
              Initialize Autonomous Mission
            </h2>
            <p className="text-xs text-zinc-400">
              Launch real-time multi-agent execution pipeline
            </p>
          </div>
        </div>

        {/* Error Notification */}
        {error && (
          <div className="mb-4 flex items-start space-x-2 rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        {/* Mission Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-mono font-medium text-zinc-300 uppercase tracking-wider mb-1.5">
              Mission Title <span className="text-cyan-400">*</span>
            </label>
            <input
              type="text"
              required
              disabled={isInitializing}
              placeholder="e.g., Autonomous Market Analysis & Launch Campaign"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-lg border border-zinc-800 bg-zinc-900/80 px-3.5 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 transition"
            />
          </div>

          <div>
            <label className="block text-xs font-mono font-medium text-zinc-300 uppercase tracking-wider mb-1.5">
              Mission Objective <span className="text-cyan-400">*</span>
            </label>
            <textarea
              required
              rows={3}
              disabled={isInitializing}
              placeholder="Describe the primary goal to be achieved by the multi-agent pipeline..."
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              className="w-full rounded-lg border border-zinc-800 bg-zinc-900/80 px-3.5 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 transition resize-none"
            />
          </div>

          <div>
            <label className="block text-xs font-mono font-medium text-zinc-300 uppercase tracking-wider mb-1.5">
              Description <span className="text-zinc-500 font-normal">(Optional)</span>
            </label>
            <input
              type="text"
              disabled={isInitializing}
              placeholder="Additional operational context or constraints"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-lg border border-zinc-800 bg-zinc-900/80 px-3.5 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 transition"
            />
          </div>

          <div>
            <label className="block text-xs font-mono font-medium text-zinc-300 uppercase tracking-wider mb-1.5">
              Execution Priority
            </label>
            <div className="grid grid-cols-4 gap-2">
              {(['low', 'medium', 'high', 'critical'] as const).map((p) => (
                <button
                  key={p}
                  type="button"
                  disabled={isInitializing}
                  onClick={() => setPriority(p)}
                  className={`rounded-lg border py-2 text-xs font-mono uppercase tracking-wider transition ${
                    priority === p
                      ? 'border-cyan-500/60 bg-cyan-500/20 font-semibold text-cyan-300 shadow-sm shadow-cyan-500/20'
                      : 'border-zinc-800 bg-zinc-900/40 text-zinc-400 hover:border-zinc-700 hover:text-zinc-200'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="mt-6 flex items-center justify-end space-x-3 pt-3 border-t border-zinc-900">
            <button
              type="button"
              disabled={isInitializing}
              onClick={onClose}
              className="rounded-lg border border-zinc-800 bg-zinc-900/60 px-4 py-2 text-xs font-medium text-zinc-300 hover:bg-zinc-800 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isInitializing}
              className="flex items-center space-x-2 rounded-lg border border-cyan-500/40 bg-gradient-to-r from-cyan-600 to-cyan-500 px-5 py-2 text-xs font-semibold text-zinc-950 hover:from-cyan-500 hover:to-cyan-400 transition shadow-lg shadow-cyan-500/20 disabled:opacity-50"
            >
              {isInitializing ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin text-zinc-950" />
                  <span>Initializing...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 text-zinc-950" />
                  <span>Start Mission</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
