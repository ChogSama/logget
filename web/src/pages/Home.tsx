import { Link } from "react-router-dom"
import AppContainer from "../ui/layouts/AppContainer"
import Card from "../ui/components/Card"
import Button from "../ui/components/Button"

export default function Home() {
    return (
        <AppContainer title="logget">

            <Card>
                <p>
                    AI-powered Micro-Journaling for Student Well-Being
                </p>
            </Card>

            <Card>
                <h2 className="font-semibold">
                    Welcome back 👋
                </h2>

                <p className="text-[var(--muted)]">
                    Start tracking your daily lifestyle.
                </p>
            </Card>

            <div className="flex flex-col gap-3">

                <Link to="/login">
                    <Button>
                        Login
                    </Button>
                </Link>

                <Link to="/log">
                    <Button>
                        Create Log
                    </Button>
                </Link>

                <Link to="/dashboard">
                    <Button>
                        Dashboard
                    </Button>
                </Link>

            </div>

        </AppContainer>
    )
}