// src/pages/PDFLibrary.jsx
import React from "react";
import PDFLibraryCard from "../components/PDFLibraryPage/PDFLibraryCard.jsx";

export default function PDFLibraryPage({ apiToken }) {
  return <PDFLibraryCard apiToken={apiToken} />;
}