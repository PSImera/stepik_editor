$in = [Console]::In.ReadToEnd() | ConvertFrom-Json
$fp = $in.tool_input.file_path
if ($fp -match 'courses' -and ($fp -match '\.html$' -or $fp -match 'structure\.json$')) {
    @{systemMessage='ПРАВИЛО: это публичный материал. Проверь /public-materials: естественный русский, без слопа, без лишних anglicisms.'} | ConvertTo-Json -Compress
}
