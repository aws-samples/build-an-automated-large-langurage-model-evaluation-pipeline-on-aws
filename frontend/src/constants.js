export const evaluationMetricsMap = {
  "RAGASEval-faithfulness": "faithfulness",
  "RAGASEval-answer_relevancy": "answer_relevancy",
  "RAGASEval-context_precision": "context_precision",
  "RAGASEval-context_recall": "context_recall",
  "FMEval-FactualKnowledge": "FactualKnowledge",
  "FMEval-QAAccuracy": "QAAccuracy",
  "FMEval-QAToxicity": "QAToxicity",
  "LLMEval-Cosine Metric": "Cosine Metric",
  "LLMEval-Accuracy Check": "Accuracy Check",
  "LLMEval-Compact Check": "Compact Check",
  "LLMEval-Form Check": "Form Check",
  "LLMEval-Redundancy Check": "Redundancy Check",
  "LLMEval-Relevancy Check": "Relevancy Check",
  "LLMEval-Sanity Check": "Sanity Check",
};

export const evalTemplates = ["Template 1", "Template 2", "Template 3"];

export const URL = process.env.REACT_APP_BACKEND_API_HOST;
export const columns = [
  {
    field: "Model",
    headerName: "Model",
    width: 500,
    headerClassName: "super-app-theme-header",
  },
  {
    field: "Latency",
    headerName: "Latency",
    width: 500,
    headerClassName: "super-app-theme-header",
  },
  {
    field: "Cost",
    headerName: "Cost",
    width: 250,
    headerClassName: "super-app-theme-header",
  },
];

export const API_URL = "http://" + window.location.hostname + ":5000";

export const defaultTemperature = 0.0;
export const defaultTopP = 1.0;
export const defaultTopK = 100;
export const defaultMaxTokens = 1000;
export const defaultStopSequences = [];
