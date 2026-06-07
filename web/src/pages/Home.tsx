import { Link } from "react-router-dom"

export default function Home() {
    return (
        <div>
            <h1 className="text-3xl font-bold">Home</h1>

            <div className="flex gap-4 mt-4">
                <Link to="/login">Login</Link>
                <Link to="/log">Log</Link>
                <Link to="/dashboard">Dashboard</Link>
            </div>
        </div>
    )
}