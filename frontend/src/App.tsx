import ChatWindow from './components/chat/ChatWindow'

export default function App() {
  return (
    <div className="h-screen flex flex-col">
      <header className="flex items-center gap-3 px-6 py-3 border-b border-gray-800 bg-gray-900">
        <div className="w-7 h-7 bg-brand-500 rounded-lg flex items-center justify-center text-white text-sm font-bold">
          G
        </div>
        <span className="font-semibold tracking-tight">GTM AI</span>
        <span className="ml-auto text-xs text-gray-500">Powered by Claude</span>
      </header>
      <main className="flex-1 overflow-hidden">
        <ChatWindow />
      </main>
    </div>
  )
}
