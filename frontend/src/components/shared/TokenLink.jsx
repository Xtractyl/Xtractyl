// src/components/shared/TokenLink.jsx
const LS_BASE = import.meta.env.VITE_LS_BASE || "http://localhost:8080";

export default function TokenLink() {
  return (
    <div>
      <a
        href={`${LS_BASE}/user/account/legacy-token`}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-block bg-xtractyl-orange text-xtractyl-white font-medium px-5 py-2 rounded shadow hover:bg-xtractyl-orange/80 transition"
      >
        Get your legacy token
      </a>
      <p className="mt-2 text-sm text-xtractyl-outline/60">
        Return here after copying the token from Label Studio.
      </p>
      <p className="mt-1 text-sm text-xtractyl-outline/60">
      
        ⚠️ If you see no legacy token there, go to{" "}
        <a   
        href={`${LS_BASE}/organization/`}
        target="_blank"
        rel="noopener noreferrer"
        className="text-xtractyl-green hover:underline"
        >
        {LS_BASE}/organization
        </a>
        {" "} 
       
        and enable it via the API Tokens settings.
      </p>
    </div>
  );
}