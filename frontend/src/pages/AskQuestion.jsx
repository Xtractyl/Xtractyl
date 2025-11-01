// src/pages/AskQuestion.jsx
import React from "react";
import AskQuestionCard from "../components/AskQuestionPage/AskQuestionCard.jsx";

export default function AskQuestionPage({ apiToken }) {
  return <AskQuestionCard apiToken={apiToken} />;
}