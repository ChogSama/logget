import { Routes, Route } from "react-router-dom"
import Test from "./pages/Test"

export default function App() {
  return (
    <Routes>
      <Route path="/" element={
        <button className="px-4 py-2 bg-purple-500 text-white rounded-xl">
          Test Tailwind
        </button>} />
      <Route path="/test" element={<Test />} />
    </Routes>
  )
}