type Props = {
    label: string
    selected?: boolean
    onClick?: () => void
}

export default function ActivityCard({
    label,
    selected,
    onClick,
}: Props) {
    
    return (
        <button
            onClick={onClick}
            className={`
                p-4
                rounded-xl
                border
                transition
                text-left
                ${selected
                    ? "border-[var(--primary)]"
                    : "border-[var(--border)]"
                }
            `}
        >
            {label}
        </button>
    )
}