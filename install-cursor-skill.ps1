# Install skill into Cursor (run from repo root)

$skillDir = ".cursor\skills\serenity-twin"
New-Item -ItemType Directory -Force -Path $skillDir | Out-Null

$items = @(
    "SKILL.md",
    "corpus",
    "reasoning",
    "distillation",
    "scripts",
    "serenity_twin",
    "config.json"
)
foreach ($item in $items) {
    Copy-Item $item -Destination $skillDir -Recurse -Force
}
Copy-Item ".env.example" -Destination "$skillDir\.env.example" -Force

Write-Host "Installed serenity-twin skill to $skillDir"
Write-Host "Select DeepSeek in Cursor, then ask about a ticker via serenity-twin."
