// src/pages/ReviewAndUploadAnswer.jsx
import React from "react";
import UploadTasksCard from "../components/ReviewandUploadAnswerPage/ReviewandUploadAnswerCard.jsx";

export default function ReviewandUploadAnswerPage({ apiToken }) {
  return <UploadTasksCard apiToken={apiToken} />;
}