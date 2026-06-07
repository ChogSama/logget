import { Link } from "react-router-dom"
import Button from "../ui/components/Button"
import Card from "../ui/components/Card"
import Input from "../ui/components/Input"

export default function Home() {
    return (
        <div className="p-6 space-y-4">

            <h1 className="text-3xl font-bold">
                logget UI System
            </h1>

            <Card>
                <p className="mb-2">Test Input</p>
                <Input placeholder="Write something..." />
            </Card>

            <div className="flex gap-2">
                <Button>Primary</Button>
                <Button variant="secondary">Secondary</Button>
            </div>

            <div className="flex gap-4 mt-4 text-blue-500">
                <Link to="/login">Login</Link>
                <Link to="/log">Log</Link>
                <Link to="/dashboard">Dashboard</Link>
            </div>

            <button onClick={() => document.documentElement.classList.toggle("dark")}>
                Toggle Dark Mode
            </button>
        </div>
    )
}