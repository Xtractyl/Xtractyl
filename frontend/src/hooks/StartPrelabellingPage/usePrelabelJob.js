// frontend/src/hooks/StartPrelabellingPage/usePrelabelJob.js
import { useReducer, useEffect } from "react";
import { useLocalStorage } from "./useLocalStorage";
import { prelabelProject, cancelPrelabel, getPrelabelStatus } from "../../api/StartPrelabellingPage/api.js";

const initialState = {
  preStatus: null,
  busy: false,
  statusMsg: "",
};

function prelabelReducer(state, action) {
  switch (action.type) {
    case "START_BUSY":
      return { ...state, busy: true, statusMsg: "" };
    case "JOB_STARTED":
      return { ...state, busy: false, statusMsg: "✅ Prelabeling started." };
    case "JOB_START_FAILED":
      return { ...state, busy: false, statusMsg: `❌ ${action.payload}` };
    case "STATUS_UPDATED":
      return { ...state, preStatus: action.payload };
    case "CANCEL_MSG":
      return { ...state, statusMsg: action.payload };
    case "JOB_FINISHED":
      return { ...state, preStatus: null, statusMsg: action.payload ?? "" };
    case "ERROR":
      return { ...state, statusMsg: `❌ ${action.payload}` };
    default:
      return state;
  }
}

export function usePrelabelJob() {
  const [preJobId, setPreJobId] = useLocalStorage("prelabelJobId", "");
  const [state, dispatch] = useReducer(prelabelReducer, initialState);

  const start = async (payload) => {
    dispatch({ type: "START_BUSY" });
    try {
      const result = await prelabelProject(payload);
      const jobId = result?.job_id;
      if (jobId) setPreJobId(jobId);
      dispatch({ type: "JOB_STARTED" });
    } catch (e) {
      dispatch({ type: "JOB_START_FAILED", payload: e?.message || "Failed to start." });
    }
  };

  const cancel = async () => {
    if (!preJobId) return;
    try {
      await cancelPrelabel(preJobId);
      const s = await getPrelabelStatus(preJobId);
      const st = String(s?.state || "").toUpperCase();
      const messages = {
        CANCEL_REQUESTED: "🛑 Cancel requested.",
        CANCELLED: "🛑 Cancelled.",
        SUCCEEDED: "ℹ️ Already finished.",
        DONE: "ℹ️ Already finished.",
        FAILED: "⚠️ Job failed.",
        ERROR: "⚠️ Job failed.",
      };
      dispatch({ type: "CANCEL_MSG", payload: messages[st] ?? `ℹ️ State: ${st || "unknown"}` });
    } catch (e) {
      dispatch({ type: "ERROR", payload: e?.message || "Cancel failed." });
    }
  };

  useEffect(() => {
    if (!preJobId) return;
    let cancelled = false;
    let timer = null;

    const schedule = (ms = 1500) => {
      if (!cancelled) timer = setTimeout(tick, ms);
    };

    const tick = async () => {
      try {
        const s = await getPrelabelStatus(preJobId);
        dispatch({ type: "STATUS_UPDATED", payload: s });
        const st = String(s?.state || "").toLowerCase();
        const pct = Number(s?.progress ?? 0);
        if (["done", "error", "failed", "cancelled", "succeeded"].includes(st)) {
          setPreJobId("");
          dispatch({ type: "JOB_FINISHED" });
          return;
        }
        if (st === "cancel_requested" && pct >= 100) {
          setPreJobId("");
          dispatch({ type: "JOB_FINISHED", payload: "✅ Job finished (cancel request acknowledged)." });
          return;
        }
        schedule();
     } catch (e) {
       if (e?.status === 404) {
         setPreJobId("");
         dispatch({ type: "JOB_FINISHED" });
         return;
       }
        schedule();
      }
    };

    tick();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [preJobId, setPreJobId]);

  const progressPct = Math.round(Number(state.preStatus?.progress ?? 0));

  return {
    preJobId,
    preStatus: state.preStatus,
    progressPct,
    busy: state.busy,
    statusMsg: state.statusMsg,
    start,
    cancel,
  };
}