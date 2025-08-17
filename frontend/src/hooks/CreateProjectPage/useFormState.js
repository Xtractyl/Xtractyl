import { useState } from "react";

export default function useFormState(initial = { title: "", questions: "", labels: "" }) {
  const [title, setTitle] = useState(initial.title);
  const [questions, setQuestions] = useState(initial.questions);
  const [labels, setLabels] = useState(initial.labels);

  const resetForm = () => {
    setTitle("");
    setQuestions("");
    setLabels("");
  };

  return {
    title, setTitle,
    questions, setQuestions,
    labels, setLabels,
    resetForm,
  };
}