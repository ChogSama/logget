import AppContainer from "../ui/layouts/AppContainer"
import Card from "../ui/components/Card"

export default function Dashboard() {
    return (
        <AppContainer title="Dashboard">

            <Card>
                <h2 className="font-semibold">
                    Lifestyle Balance Score
                </h2>

                <p className="text-4xl font-bold">
                    78
                </p>
            </Card>

            <Card>
                <h2 className="font-semibold">
                    This Week
                </h2>

                <p>
                    5 logs completed
                </p>
            </Card>

            <Card>
                <h2 className="font-semibold">
                    AI Insight
                </h2>

                <p>
                    You tend to sleep later on days with heavy workload.
                </p>
            </Card>
            
        </AppContainer>
    )
}