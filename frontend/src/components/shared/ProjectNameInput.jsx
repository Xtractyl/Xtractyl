import React from "react";

export default function ProjectNameInput({ value, onChange }) {
  return (
    <div>
      <label className="block font-medium mb-1">Project name</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value.trim())}
        placeholder="identical to your current project, name as in label studio"
        required
        className="w-full p-2 border rounded"
      />
    </div>
  );
}