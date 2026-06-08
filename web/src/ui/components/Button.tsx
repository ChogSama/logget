import { ReactNode } from "react"

type ButtonProps = {
    children: ReactNode
    onClick?: () => void
    variant?: "primary" | "secondary"
}

export default function Button({
    children,
    onClick,
    variant = "primary",
}: ButtonProps) {
    const base = "px-4 py-2 rounded-xl font-medium transition duration-150 active:scale-95 focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"

    const styles = {
        primary: "bg-[var(--primary)] text-white hover:opacity-90",
        secondary: "bg-[var(--border)] text-[var(--text)] hover:opacity-80",
    }

    return (
        <button onClick={onClick} className={`${base} ${styles[variant]}`}>
            {children}
        </button>
    )
}