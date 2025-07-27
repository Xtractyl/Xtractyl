import React from "react";

export default function ProjectNameInput({ value, onChange }) {
  return (
    <div>
      <label className="block font-medium mb-1">Project name</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value.trim())}
        placeholder="e.g. Oncology_July_2025"
        required
        className="w-full p-2 border rounded"
      />
    </div>
  );
}