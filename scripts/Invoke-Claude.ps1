#Requires -Version 5.1
<#
.SYNOPSIS
    Stuur een prompt naar Claude API en laat Claude code bouwen / bestanden aanpassen.

.DESCRIPTION
    Gebruik dit script als lokale brug: jij typt een prompt, Claude voert uit.
    Sla je ANTHROPIC_API_KEY op in een omgevingsvariabele of geef hem mee via -ApiKey.

.EXAMPLE
    .\Invoke-Claude.ps1 "Pas main.py aan zodat trade size 0.1% van portfolio is"
    .\Invoke-Claude.ps1 -Prompt "Maak dashboard.py aan met Flask" -WorkDir "G:\claude"
    .\Invoke-Claude.ps1   # interactieve modus

.NOTES
    Vereist: ANTHROPIC_API_KEY omgevingsvariabele of -ApiKey parameter
#>
param(
    [Parameter(Position = 0)]
    [string]$Prompt,

    [string]$ApiKey = $env:ANTHROPIC_API_KEY,

    # Map waar bestanden gelezen/geschreven worden
    [string]$WorkDir = (Get-Location).Path,

    # Claude model
    [string]$Model = "claude-sonnet-4-6",

    # Toon ruwe API-respons voor debugging
    [switch]$Debug
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── helpers ──────────────────────────────────────────────────────────────────

function Write-Color([string]$Text, [string]$Color = "White") {
    Write-Host $Text -ForegroundColor $Color
}

function Ensure-ApiKey {
    if (-not $ApiKey) {
        Write-Color "ANTHROPIC_API_KEY niet gevonden." "Red"
        Write-Color "Stel in met: `$env:ANTHROPIC_API_KEY = 'sk-ant-...'" "Yellow"
        exit 1
    }
}

function Read-FilesInPrompt([string]$PromptText, [string]$Dir) {
    # Zoek bestandsnamen in de prompt, lees ze en voeg inhoud toe als context
    $extensions = @("*.py", "*.js", "*.ts", "*.json", "*.yaml", "*.yml", "*.ps1", "*.txt", "*.csv")
    $found = @{}

    foreach ($ext in $extensions) {
        Get-ChildItem -Path $Dir -Filter $ext -ErrorAction SilentlyContinue | ForEach-Object {
            $name = $_.Name
            if ($PromptText -match [regex]::Escape($name)) {
                $found[$name] = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
            }
        }
    }
    return $found
}

function Build-SystemPrompt([string]$Dir, [hashtable]$FileContents) {
    $fileSection = ""
    if ($FileContents.Count -gt 0) {
        $fileSection = "`n`n## Relevante bestanden in $Dir`n"
        foreach ($kv in $FileContents.GetEnumerator()) {
            $fileSection += "`n### $($kv.Key)`n``````python`n$($kv.Value)`n```````n"
        }
    }

    return @"
Je bent Claude Code, een AI-assistent die code schrijft en bestanden aanpast.
Werkmap: $Dir
$fileSection

## Instructies
- Beantwoord in het Nederlands tenzij anders gevraagd.
- Als je een bestand AANPAST, geef dan de VOLLEDIGE nieuwe bestandsinhoud terug in een codeblok.
- Zet boven elk codeblok een commentaarregel: # BESTAND: <bestandsnaam>
- Als je meerdere bestanden aanpast, geef elk bestand apart.
- Na de codeblokken: geef een korte samenvatting van wat je hebt veranderd.
"@
}

function Invoke-ClaudeAPI([string]$SystemMsg, [string]$UserMsg, [string]$Key, [string]$ModelId) {
    $headers = @{
        "x-api-key"         = $Key
        "anthropic-version" = "2023-06-01"
        "content-type"      = "application/json"
    }

    $body = @{
        model      = $ModelId
        max_tokens = 8096
        system     = $SystemMsg
        messages   = @(
            @{ role = "user"; content = $UserMsg }
        )
    } | ConvertTo-Json -Depth 10

    $response = Invoke-RestMethod `
        -Uri "https://api.anthropic.com/v1/messages" `
        -Method POST `
        -Headers $headers `
        -Body $body `
        -ContentType "application/json"

    return $response.content[0].text
}

function Save-GeneratedFiles([string]$Response, [string]$Dir) {
    # Zoek codeblokken met bestandsnaam-header
    $pattern = '# BESTAND: (.+?)\r?\n```[a-z]*\r?\n([\s\S]+?)```'
    $matches_ = [regex]::Matches($Response, $pattern)

    if ($matches_.Count -eq 0) { return }

    Write-Color "`n── Gegenereerde bestanden ──" "Cyan"
    foreach ($m in $matches_) {
        $filename = $m.Groups[1].Value.Trim()
        $content  = $m.Groups[2].Value

        # Veiligheidscheck: geen absolute paden buiten $Dir
        if ($filename -match '^[A-Za-z]:\\' -or $filename -match '^/') {
            $outPath = $filename
        } else {
            $outPath = Join-Path $Dir $filename
        }

        $confirm = Read-Host "Bestand opslaan: $outPath ? (j/n)"
        if ($confirm -eq "j") {
            $content | Set-Content -Path $outPath -Encoding UTF8
            Write-Color "  Opgeslagen: $outPath" "Green"
        } else {
            Write-Color "  Overgeslagen: $outPath" "Yellow"
        }
    }
}

# ── main ─────────────────────────────────────────────────────────────────────

Ensure-ApiKey

# Interactieve lus als geen prompt meegegeven
if (-not $Prompt) {
    Write-Color "Claude Code — interactieve modus (type 'exit' om te stoppen)" "Cyan"
    Write-Color "Werkmap: $WorkDir`n" "DarkGray"

    while ($true) {
        Write-Host "Jij> " -ForegroundColor Yellow -NoNewline
        $Prompt = Read-Host
        if ($Prompt -in @("exit", "quit", "stop")) { break }
        if (-not $Prompt.Trim()) { continue }

        $files  = Read-FilesInPrompt -PromptText $Prompt -Dir $WorkDir
        $system = Build-SystemPrompt -Dir $WorkDir -FileContents $files

        Write-Color "`nClaude denkt na..." "DarkGray"
        $reply = Invoke-ClaudeAPI -SystemMsg $system -UserMsg $Prompt -Key $ApiKey -ModelId $Model

        if ($Debug) { Write-Color "`n[DEBUG RAW]`n$reply" "DarkGray" }

        Write-Color "`nClaude>" "Green"
        Write-Host $reply
        Save-GeneratedFiles -Response $reply -Dir $WorkDir
        Write-Host ""
    }
    exit 0
}

# Eenmalige aanroep
$files  = Read-FilesInPrompt -PromptText $Prompt -Dir $WorkDir
$system = Build-SystemPrompt -Dir $WorkDir -FileContents $files

Write-Color "Claude denkt na..." "DarkGray"
$reply = Invoke-ClaudeAPI -SystemMsg $system -UserMsg $Prompt -Key $ApiKey -ModelId $Model

if ($Debug) { Write-Color "`n[DEBUG RAW]`n$reply" "DarkGray" }

Write-Host $reply
Save-GeneratedFiles -Response $reply -Dir $WorkDir
