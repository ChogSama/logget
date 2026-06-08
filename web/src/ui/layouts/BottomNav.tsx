import { Link } from "react-router-dom"

export default function BottomNav() {
    return (
        <nav
            className="
                fixed
                bottom-0
                left-0
                right-0
                border-t
                border-[var(--border)]
                bg-[var(--bg)]
                flex
                justify-around
                p-3
            "
        >
            <Link to="/">
                Home
            </Link>

            <Link to="/log">
                Log
            </Link>

            <Link to="/dashboard">
                Dashboard
            </Link>
        </nav>
    )
}