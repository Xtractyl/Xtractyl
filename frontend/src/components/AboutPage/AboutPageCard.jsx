export default function AboutPage() {
  return (
<div className="min-h-screen bg-xtractyl-lightgreen/60 text-xtractyl-darktext px-6 py-16">
      <div className="w-full px-8 md:px-16 lg:px-24">
        <div className="mb-10">
          <div className="inline-flex items-center gap-2 rounded-full bg-xtractyl-offwhite/60 px-3 py-1 text-xs text-xtractyl-outline shadow-sm">
            <span className="h-2 w-2 rounded-full bg-xtractyl-lightgreen" />
            Research project · Local-first · Privacy-first
          </div>

          <h1 className="mt-4 text-3xl md:text-4xl font-semibold tracking-tight">
            About Xtractyl
          </h1>

          <p className="mt-3 text-xtractyl-outline leading-relaxed">
            This application is part of the Xtractyl research project. It is a local,
            privacy-first AI system under active development and intended for research
            and experimentation purposes only.
          </p>
        </div>

        <div className="rounded-2xl bg-xtractyl-offwhite/70 backdrop-blur-sm shadow-md border border-black/5 p-6 md:p-8">
          <h2 className=" text-xtractyl-outline/70ase font-medium mb-4">Links</h2>

          <div className="grid gap-3">
            <a
              href="https://www.xtractyl.com"
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-center justify-between rounded-xl border border-black/5 bg-xtractyl-offwhite/70 px-4 py-3 hover:bg-xtractyl-offwhite transition"
            >
              <div className="flex items-center gap-3">
                <span className="text-lg">🌐</span>
                <div>
                  <div className="font-medium">Website</div>
                  <div className="text-sm  text-xtractyl-outline/70">www.xtractyl.com</div>
                </div>
              </div>
              <span className=" text-xtractyl-outline/70 group-hover:translate-x-0.5 transition">↗</span>
            </a>

            <a
              href="https://github.com/Xtractyl/Xtractyl"
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-center justify-between rounded-xl border border-black/5 bg-xtractyl-offwhite/70 px-4 py-3 hover:bg-xtractyl-offwhite transition"
            >
              <div className="flex items-center gap-3">
                <span className="text-lg">💻</span>
                <div>
                  <div className="font-medium">GitHub Repository</div>
                  <div className="text-sm  text-xtractyl-outline/70">github.com/Xtractyl/Xtractyl</div>
                </div>
              </div>
              <span className=" text-xtractyl-outline/70 group-hover:translate-x-0.5 transition">↗</span>
            </a>

            <a
              href="https://github.com/Xtractyl/Xtractyl/blob/master/LICENSE"
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-center justify-between rounded-xl border border-black/5 bg-xtractyl-offwhite/70 px-4 py-3 hover:bg-xtractyl-offwhite transition"
            >
              <div className="flex items-center gap-3">
                <span className="text-lg">📄</span>
                <div>
                  <div className="font-medium">License</div>
                  <div className="text-sm  text-xtractyl-outline/70">Non-commercial license terms</div>
                </div>
              </div>
              <span className=" text-xtractyl-outline/70 group-hover:translate-x-0.5 transition">↗</span>
            </a>
          </div>
        </div>

        <div className="mt-8 rounded-2xl border border-black/5 bg-xtractyl-offwhite/50 p-6 text-sm text-xtractyl-outline/80 shadow-sm">
          <div className="flex flex-wrap gap-2 mb-3">
            <span className="rounded-full bg-xtractyl-offwhite/70 px-3 py-1">Not a medical device</span>
            <span className="rounded-full bg-xtractyl-offwhite/70 px-3 py-1">Synthetic example data</span>
            <span className="rounded-full bg-xtractyl-offwhite/70 px-3 py-1">Research-only</span>
          </div>

          <p>
            Xtractyl is not a medical device and is not intended for diagnostic or clinical use.
          </p>
          <p className="mt-2">
            All example data used within the application is synthetic.
          </p>
        </div>
        <div className="mt-12 text-sm  text-xtractyl-outline/70">
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