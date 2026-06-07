import { ReactNode } from "react"

export default function Card({ children }: { children: ReactNode }) {
    return (
        <div className="bg-[var(--bg)] border border-[var(--border)] rounded-2xl p-4 shadow-sm hover:shadow-md transition">
            {children}
        </div>
    )
}