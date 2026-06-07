type InputProps = {
    placeholder?: string
    value?: string
    onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void
}

export default function Input({ placeholder, value, onChange }: InputProps) {
    return (
        <input
            className="w-full px-3 py-2 border border-[var(--border)] rounded-xl outline-none bg-[var(--bg)] text-[var(--text)] focus:border-[var(--primary)] transition"
            placeholder={placeholder}
            value={value}
            onChange={onChange}
        />
    )
}