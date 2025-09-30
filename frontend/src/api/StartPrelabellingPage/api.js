// src/api/StartPrelabellingPage/api.js

const OLLAMA_BASE = import.meta.env.VITE_OLLAMA_BASE || "http://localhost:11434";


export async function pullModel(model, onProgress, baseUrl = OLLAMA_BASE) {
    const res = await fetch(`${baseUrl}/api/pull`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: model }),
    });
  
    if (!res.ok || !res.body) {
      throw new Error(`Pull failed: HTTP ${res.status}`);
    }
  
    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
  
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
  
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
  
      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const obj = JSON.parse(line);
          if (
            typeof obj.total === "number" &&
            typeof obj.completed === "number" &&
            obj.total > 0
          ) {
            const pct = Math.round((obj.completed / obj.total) * 100);
            onProgress?.(`${pct}%`);
          } else if (obj.status) {
            onProgress?.(obj.status);
          }
        } catch {
          // ignore partial lines
        }
      }
    }
  }