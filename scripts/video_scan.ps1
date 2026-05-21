# video_scan.ps1
# 영상 폴더 → 메타데이터 JSON + 썸네일 일괄 추출
# Usage: & video_scan.ps1 -Folder "D:\맥라렌"

param(
    [Parameter(Mandatory=$true)][string]$Folder,
    [string]$ThumbDir = "C:\tmp\auto_vlog\thumbs",
    [string]$OutJson = "C:\tmp\auto_vlog\scan.json",
    [int]$ThumbSec = 1,
    [int]$ThumbWidth = 360
)

# 0. 환경 점검
if (-not (Test-Path -LiteralPath $Folder)) {
    Write-Error "폴더가 없습니다: $Folder"
    exit 1
}

$ffmpeg = (Get-Command ffmpeg -ErrorAction SilentlyContinue).Source
$ffprobe = (Get-Command ffprobe -ErrorAction SilentlyContinue).Source
if (-not $ffmpeg -or -not $ffprobe) {
    Write-Error "ffmpeg/ffprobe가 PATH에 없습니다."
    exit 1
}

# 1. 출력 폴더 준비
New-Item -ItemType Directory -Force $ThumbDir | Out-Null
New-Item -ItemType Directory -Force (Split-Path $OutJson) | Out-Null

# 2. 영상 파일 수집 (mp4, mov)
$videos = Get-ChildItem -LiteralPath $Folder -File | Where-Object {
    $_.Extension -match '^\.(mp4|mov|MP4|MOV)$'
} | Sort-Object Name

if ($videos.Count -eq 0) {
    Write-Warning "영상 파일이 없습니다: $Folder"
    exit 0
}

Write-Host "총 $($videos.Count)개 영상 스캔 시작..." -ForegroundColor Cyan

# 3. 메타데이터 + 썸네일 추출
$results = @()
$i = 1
foreach ($v in $videos) {
    $idx = "{0:D2}" -f $i
    $safeName = ($v.BaseName -replace '[^a-zA-Z0-9]', '_').Substring(0, [Math]::Min(40, ($v.BaseName -replace '[^a-zA-Z0-9]', '_').Length))
    $thumbPath = Join-Path $ThumbDir "${idx}_${safeName}.jpg"

    # 비디오 메타
    $vmeta = & $ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate:format=duration,size -of json $v.FullName 2>$null | ConvertFrom-Json
    $width = $vmeta.streams[0].width
    $height = $vmeta.streams[0].height
    $fps = $vmeta.streams[0].r_frame_rate
    $duration = [double]$vmeta.format.duration

    # 오디오 메타
    $ameta = & $ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,sample_rate,channels -of json $v.FullName 2>$null | ConvertFrom-Json
    $hasAudio = $ameta.streams.Count -gt 0

    # 비율 분류
    $aspect = if ($height -gt $width) { "vertical" } elseif ($width -gt $height) { "horizontal" } else { "square" }

    # 썸네일 추출
    & $ffmpeg -y -ss $ThumbSec -i $v.FullName -vframes 1 -vf "scale=${ThumbWidth}:-1" $thumbPath 2>$null

    $results += [PSCustomObject]@{
        index    = $i
        file     = $v.Name
        path     = $v.FullName
        thumb    = $thumbPath
        width    = $width
        height   = $height
        aspect   = $aspect
        fps      = $fps
        duration = [Math]::Round($duration, 2)
        sizeMB   = [Math]::Round($v.Length / 1MB, 2)
        hasAudio = $hasAudio
        audioCodec = if ($hasAudio) { $ameta.streams[0].codec_name } else { $null }
    }

    Write-Host "[$idx] $($v.Name) → ${width}×${height} / ${duration}s / 오디오: $(if ($hasAudio) { '있음' } else { '없음' })" -ForegroundColor Green
    $i++
}

# 4. JSON 저장 (UTF-8, BOM 없음)
$json = $results | ConvertTo-Json -Depth 5
[System.IO.File]::WriteAllText($OutJson, $json, [System.Text.UTF8Encoding]::new($false))

# 5. 요약
$totalDur = ($results | Measure-Object -Property duration -Sum).Sum
$vCount = ($results | Where-Object { $_.aspect -eq 'vertical' }).Count
$hCount = ($results | Where-Object { $_.aspect -eq 'horizontal' }).Count

Write-Host ""
Write-Host "=== 스캔 완료 ===" -ForegroundColor Cyan
Write-Host "총 클립: $($results.Count)개"
Write-Host "총 길이: $([Math]::Round($totalDur, 1))초 ($([Math]::Round($totalDur/60, 1))분)"
Write-Host "세로($vCount) / 가로($hCount)"
Write-Host "썸네일: $ThumbDir"
Write-Host "메타 JSON: $OutJson"
