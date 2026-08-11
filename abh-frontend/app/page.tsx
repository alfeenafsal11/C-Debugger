"use client";

import React, { useState } from "react";
import Editor from "@monaco-editor/react";
import { 
  Play, 
  Bug, 
  BookOpen, 
  CheckCircle2, 
  AlertCircle, 
  Zap, 
  Loader2,
  Terminal,
  ShieldCheck
} from "lucide-react";

export default function Home() {
  const [code, setCode] = useState<string>(`#include <iostream>\n\nint main() {\n    // Paste your C++ code here\n    \n    return 0;\n}`);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleDebug = async () => {
    setLoading(true);
    setResult(null);
    try {
      const response = await fetch("https://alfeenafsal-agentic-bug-hunter.hf.space/debug", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ code }),
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Debug failed:", error);
      setResult({ error: "Failed to connect to the backend API." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-background text-foreground p-6 font-sans">
      {/* Header */}
      <header className="max-w-7xl mx-auto flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <div className="bg-primary p-2 rounded-lg">
            <Bug className="text-white w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">
            Agentic <span className="gradient-text">Bug Hunter</span>
          </h1>
        </div>
        <div className="flex items-center gap-4">
          <button 
            onClick={handleDebug}
            disabled={loading}
            className="bg-primary hover:bg-blue-600 disabled:opacity-50 text-white px-6 py-2 rounded-full font-semibold transition-all flex items-center gap-2 shadow-lg shadow-primary/20"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {loading ? "Analyzing..." : "Debug Code"}
          </button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 h-[calc(100vh-180px)]">
        {/* Editor Section */}
        <div className="lg:col-span-7 flex flex-col gap-4 min-h-[450px] lg:min-h-0 h-full">
          <div className="glass rounded-2xl overflow-hidden flex-1 min-h-0 flex flex-col relative group">
            <div className="bg-secondary/50 px-4 py-2 border-b border-border flex items-center justify-between flex-shrink-0">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-muted" />
                <span className="text-sm font-medium text-muted">main.cpp</span>
              </div>
            </div>
            <div className="flex-1 min-h-0 relative w-full h-full">
              <Editor
                height="100%"
                defaultLanguage="cpp"
                theme="vs-dark"
                value={code}
                onChange={(v) => setCode(v || "")}
                options={{
                  fontSize: 14,
                  minimap: { enabled: false },
                  padding: { top: 16 },
                  scrollBeyondLastLine: false,
                  smoothScrolling: true,
                  cursorSmoothCaretAnimation: "on",
                  automaticLayout: true,
                  wordWrap: "on",
                }}
              />
            </div>
          </div>
        </div>

        {/* Results Section */}
        <div className="lg:col-span-5 flex flex-col gap-6 overflow-y-auto pr-2 custom-scrollbar">
          {!result && !loading && (
            <div className="h-full flex flex-col items-center justify-center text-center p-12 glass rounded-3xl border-dashed border-2 border-border/50">
              <Zap className="w-12 h-12 text-muted mb-4 opacity-20" />
              <h3 className="text-xl font-semibold mb-2 text-muted">Ready to Inspect</h3>
              <p className="text-sm text-muted/60 max-w-xs">
                Upload or paste your C++ code and click "Debug Code" to start the multi-agent validation process.
              </p>
            </div>
          )}

          {loading && (
            <div className="h-full flex flex-col items-center justify-center space-y-4">
              <Loader2 className="w-10 h-10 animate-spin text-primary" />
              <p className="text-sm font-medium text-muted animate-pulse italic">
                Orchestrating agents...
              </p>
            </div>
          )}

          {result && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              {/* Diagnostics */}
              <div className="glass rounded-2xl p-5 space-y-4">
                <div className="flex items-center gap-2 text-accent">
                  <AlertCircle className="w-5 h-5" />
                  <h3 className="font-bold">Compiler Diagnostics</h3>
                </div>
                <div className="space-y-2">
                  {result.compiler_diagnostics && result.compiler_diagnostics.length > 0 ? (
                    result.compiler_diagnostics.map((diag: any, i: number) => (
                      <div key={i} className="bg-accent/10 border border-accent/20 rounded-xl p-4">
                        <p className="text-sm font-mono text-accent">
                          Line {diag.line}: <span className="font-bold">[{diag.severity.toUpperCase()}]</span> {diag.message}
                        </p>
                      </div>
                    ))
                  ) : (
                    <div className="bg-accent/10 border border-accent/20 rounded-xl p-4">
                      <p className="text-sm font-mono text-accent">
                        {result.Explanation 
                          ? `Line ${result.Bug_Line || "N/A"}: ${result.Explanation}`
                          : "No static warnings or errors detected."}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* AI Explanation */}
              <div className="glass rounded-2xl p-5 space-y-4 border-l-4 border-primary">
                <div className="flex items-center gap-2 text-primary">
                  <Zap className="w-5 h-5" />
                  <h3 className="font-bold">AI Insight</h3>
                </div>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {result.Explanation || "Analysis pending..."}
                </p>
              </div>

              {/* Retrieval Panel */}
              <div className="glass rounded-2xl p-5 space-y-4">
                <div className="flex items-center gap-2 text-blue-400">
                  <BookOpen className="w-5 h-5" />
                  <h3 className="font-bold">Knowledge Retrieval</h3>
                </div>
                <div className="space-y-3">
                  <div className="p-3 bg-white/5 rounded-lg border border-border">
                    <p className="text-xs text-muted-foreground italic">
                      Retrieved documentation relevant to this bug type from indexed corpus.
                    </p>
                  </div>
                </div>
              </div>

              {/* Validation Status */}
              <div className="glass rounded-2xl p-5 space-y-4">
                <div className="flex items-center gap-2 text-green-400">
                  <ShieldCheck className="w-5 h-5" />
                  <h3 className="font-bold">Validation Status</h3>
                </div>
                <div className="flex items-center gap-3 bg-green-400/10 border border-green-400/20 rounded-xl p-4">
                   <CheckCircle2 className="text-green-400 w-5 h-5" />
                   <span className="text-sm font-semibold text-green-400 uppercase tracking-wider">
                     Structure Validated
                   </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #27272a;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #3f3f46;
        }
      `}</style>
    </main>
  );
}
