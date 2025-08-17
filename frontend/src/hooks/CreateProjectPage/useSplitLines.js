export default function useSplitLines() {
    const splitLines = (v) =>
      v
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean);
  
    return { splitLines };
  }