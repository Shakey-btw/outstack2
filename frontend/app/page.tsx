import Link from "next/link"

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-center font-mono text-sm">
        <h1 className="text-4xl font-bold text-center mb-4">
          Welcome to Outstack
        </h1>
        <p className="text-center text-gray-600 mb-8">
          Frontend and Backend are ready!
        </p>
        <div className="text-center">
          <Link
            href="/dashboard"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            View Dashboard
          </Link>
        </div>
      </div>
    </main>
  )
}

