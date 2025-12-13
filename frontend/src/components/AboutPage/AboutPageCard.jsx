export default function AboutPage() {
  return (
<div className="min-h-screen bg-xtractyl-lightgreen/60 text-[#23211c] px-6 py-16">
      <div className="w-full px-8 md:px-16 lg:px-24">
        <div className="mb-10">
          <div className="inline-flex items-center gap-2 rounded-full bg-white/60 px-3 py-1 text-xs text-[#4a473f] shadow-sm">
            <span className="h-2 w-2 rounded-full bg-xtractyl-lightgreen" />
            Research project · Local-first · Privacy-first
          </div>

          <h1 className="mt-4 text-3xl md:text-4xl font-semibold tracking-tight">
            About Xtractyl
          </h1>

          <p className="mt-3 text-[#4a473f] leading-relaxed">
            This application is part of the Xtractyl research project. It is a local,
            privacy-first AI system under active development and intended for research
            and experimentation purposes only.
          </p>
        </div>

        <div className="rounded-2xl bg-white/70 backdrop-blur-sm shadow-md border border-black/5 p-6 md:p-8">
          <h2 className="text-base font-medium mb-4">Links</h2>

          <div className="grid gap-3">
            <a
              href="https://www.xtractyl.com"
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-center justify-between rounded-xl border border-black/5 bg-white/70 px-4 py-3 hover:bg-white transition"
            >
              <div className="flex items-center gap-3">
                <span className="text-lg">🌐</span>
                <div>
                  <div className="font-medium">Website</div>
                  <div className="text-sm text-[#6b675c]">www.xtractyl.com</div>
                </div>
              </div>
              <span className="text-[#6b675c] group-hover:translate-x-0.5 transition">↗</span>
            </a>

            <a
              href="https://github.com/Xtractyl/Xtractyl"
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-center justify-between rounded-xl border border-black/5 bg-white/70 px-4 py-3 hover:bg-white transition"
            >
              <div className="flex items-center gap-3">
                <span className="text-lg">💻</span>
                <div>
                  <div className="font-medium">GitHub Repository</div>
                  <div className="text-sm text-[#6b675c]">github.com/Xtractyl/Xtractyl</div>
                </div>
              </div>
              <span className="text-[#6b675c] group-hover:translate-x-0.5 transition">↗</span>
            </a>

            <a
              href="https://github.com/Xtractyl/Xtractyl/blob/master/LICENSE"
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-center justify-between rounded-xl border border-black/5 bg-white/70 px-4 py-3 hover:bg-white transition"
            >
              <div className="flex items-center gap-3">
                <span className="text-lg">📄</span>
                <div>
                  <div className="font-medium">License</div>
                  <div className="text-sm text-[#6b675c]">Non-commercial license terms</div>
                </div>
              </div>
              <span className="text-[#6b675c] group-hover:translate-x-0.5 transition">↗</span>
            </a>
          </div>
        </div>

        <div className="mt-8 rounded-2xl border border-black/5 bg-white/50 p-6 text-sm text-[#5a564c] shadow-sm">
          <div className="flex flex-wrap gap-2 mb-3">
            <span className="rounded-full bg-white/70 px-3 py-1">Not a medical device</span>
            <span className="rounded-full bg-white/70 px-3 py-1">Synthetic example data</span>
            <span className="rounded-full bg-white/70 px-3 py-1">Research-only</span>
          </div>

          <p>
            Xtractyl is not a medical device and is not intended for diagnostic or clinical use.
          </p>
          <p className="mt-2">
            All example data used within the application is synthetic.
          </p>
        </div>
        <div className="mt-12 text-sm text-[#6b675c]">
          Contact:{" "}
          <a
            href="mailto:chris@xtractyl.com"
            className="underline hover:opacity-80"
          >
            chris@xtractyl.com
          </a>
      </div>
      </div>
    </div>
    
  );
}