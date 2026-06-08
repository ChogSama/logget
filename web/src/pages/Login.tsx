import AppContainer from "../ui/layouts/AppContainer"
import Input from "../ui/components/Input"
import Button from "../ui/components/Button"
import Card from "../ui/components/Card"

export default function Login() {
    return (
        <AppContainer title="Login">

            <div className="space-y-4">

                <Card>
                    <p>
                        Welcome back to logget.
                    </p>

                    <p className="text-[var(--muted)] text-sm">
                        Track your lifestyle and discover healthier habits.
                    </p>
                </Card>

                <Input
                    placeholder="Email"
                />

                <Input
                    placeholder="Password"
                />

                <div className="flex justify-center">
                    <Button>
                        Continue with Google
                    </Button>
                </div>

                <div className="flex justify-center">
                    <Button>
                        Sign In
                    </Button>
                </div>

                <p className="text-sm text-[var(--muted)] text-center">
                    Demo authentication screen
                </p>

            </div>

        </AppContainer>
    )
}