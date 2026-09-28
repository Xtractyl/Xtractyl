//frontend/src/utils/CreateProjectPage/splitlines.js
export function splitLines(value) {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}
