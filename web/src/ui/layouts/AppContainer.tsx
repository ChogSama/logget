import { useNavigate } from "react-router-dom"
import BottomNav from "./BottomNav"

type AppContainerProps = {
    title: string
    children: React.ReactNode
}

export default function AppContainer({
    title,
    children,
}: AppContainerProps) {

    const navigate = useNavigate()

    return (
        <>
            <main className="max-w-md mx-auto min-h-screen p-4 space-y-6">

                <header className="flex items-center gap-3 pb-4 border-b border-[var(--border)]">

                    <button
                        onClick={() => navigate(-1)}
                        className="text-sm text-[var(--muted)]"
                    >
                        ←
                    </button>

                    <h1 className="text-2xl font-bold">
                        {title}
                    </h1>

                </header>

                {children}

            </main>

            <BottomNav />
        </>
    )
}