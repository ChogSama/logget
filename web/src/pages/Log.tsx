import AppContainer from "../ui/layouts/AppContainer"
import ActivityCard from "../ui/components/ActivityCard"
import Input from "../ui/components/Input"
import Button from "../ui/components/Button"
import Card from "../ui/components/Card"

export default function Log() {

    return (
        <AppContainer title="Create Log">

            <Card>
                <p className="text-sm text-[var(--muted)]">
                    Select the activity that best describes your current moment.
                </p>
            </Card>

            <div className="grid grid-cols-2 gap-3">

                <ActivityCard label="Work" />
                <ActivityCard label="Sleep" />
                <ActivityCard label="Exercise" />
                <ActivityCard label="Social" />
                <ActivityCard label="Recovery" />

            </div>

            <Input
                placeholder="What happened today?"
            />

            <Button>
                Save Log
            </Button>

        </AppContainer>
    )
}