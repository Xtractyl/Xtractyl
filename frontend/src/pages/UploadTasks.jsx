// src/pages/UploadTasks.jsx
import React from "react";
import UploadTasksCard from "../components/UploadTasksPage/UploadTasksCard";

export default function UploadTasksPage({ apiToken, projectName }) {
  return <UploadTasksCard 
  apiToken={apiToken}
  projectName={projectName}
  />
  ;
}