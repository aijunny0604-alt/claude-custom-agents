# video_render.ps1
# 컷 정의 JSON → 일괄 정규화 렌더링 + concat 합본
# Usage: & video_render.ps1 -ConfigJson "C:\tmp\auto_vlog\config.json"
#
# config.json 형식:
# {
#   "outputPath": "D:\\맥라렌\\Output.mp4",
#   "outputSize": [1080, 1920],
#   "fps": 24,
#   "fontFile": "C:/Windows/Fonts/malgunbd.ttf",
#   "preserveAudio": true,
#   "workDir": "C:\\tmp\\auto_vlog",
#   "cuts": [
#     {"src": "D:/맥라렌/Clip01.mp4", "start": 0, "duration": 5, "subtitleFile": "C:/tmp/auto_vlog/subs/01.txt"},
#     {"src": "D:/맥라렌/Clip02.mp4", "start": 4, "duration": 11,
#      "subtitleSegments": [
#        {"file": "C:/tmp/auto_vlog/subs/02a.txt", "from": 0, "to": 6},
#        {"file": "C:/tmp/auto_vlog/subs/02b.txt", "from": 6, "to": 11}
#      ]}
#   ]
# }

param(
    [Parameter(Mandatory=$true)][string]$ConfigJson
)

if (-not (Test-Path -LiteralPath $ConfigJson)) {
    Write-Error "설정 파일이 없습니다: $ConfigJson"
    exit 1
}

$ffmpeg = (Get-Command ffmpeg -ErrorAction SilentlyContinue).Source
$ffprobe = (Get-Command ffprobe -ErrorAction SilentlyContinue).Source
if (-not $ffmpeg) {
    Write-Error "ffmpeg가 PATH에 없습니다."
    exit 1
}

$cfg = Get-Content -LiteralPath $ConfigJson -Raw -Encoding UTF8 | ConvertFrom-Json

# 기본값
$outW = $cfg.outputSize[0]
$outH = $cfg.outputSize[1]
$fps = if ($cfg.fps) { $cfg.fps } else { 24 }
$fontFile = if ($cfg.fontFile) { $cfg.fontFile } else { "C:/Windows/Fonts/malgunbd.ttf" }
$preserveAudio = if ($null -ne $cfg.preserveAudio) { $cfg.preserveAudio } else { $true }
$workDir = if ($cfg.workDir) { $cfg.workDir } else { "C:\tmp\auto_vlog" }
$cutsDir = Join-Path $workDir "cuts"

New-Item -ItemType Directory -Force $cutsDir | Out-Null

# Windows 경로 → ffmpeg drawtext 호환 (콜론 escape)
function Format-DrawPath([string]$p) {
    return ($p -replace '\\', '/') -replace '^([A-Za-z]):', '$1\:'
}
$fontEsc = Format-DrawPath $fontFile

# drawtext 필터 빌더
function Build-DrawText([string]$textFile, [string]$enable = $null) {
    $subEsc = Format-DrawPath $textFile
    $base = "drawtext=fontfile='${fontEsc}':textfile='${subEsc}':fontsize=55:fontcolor=white:borderw=5:bordercolor=black:x=(w-text_w)/2:y=h-text_h-280:box=1:boxcolor=black@0.45:boxborderw=20"
    if ($enable) {
        return "$base`:enable='$enable'"
    }
    return $base
}

# 각 컷 렌더링
$concatList = @()
$idx = 1
foreach ($cut in $cfg.cuts) {
    $cutIdx = "{0:D2}" -f $idx
    $cutOut = Join-Path $cutsDir "cut${cutIdx}.mp4"

    # 비디오 필터 체인: scale + 자막
    $vfChain = @("scale=${outW}:${outH}")

    # 자막: 단일 또는 시간 분기 세그먼트
    if ($cut.subtitleSegments) {
        foreach ($seg in $cut.subtitleSegments) {
            $vfChain += Build-DrawText $seg.file "between(t,$($seg.from),$($seg.to))"
        }
    } elseif ($cut.subtitleFile) {
        $vfChain += Build-DrawText $cut.subtitleFile
    }
    $vfStr = $vfChain -join ","

    # ffmpeg 명령
    $args = @(
        "-y",
        "-ss", $cut.start,
        "-t", $cut.duration,
        "-i", $cut.src
    )

    if (-not $preserveAudio) {
        $args += @(
            "-f", "lavfi",
            "-t", $cut.duration,
            "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-map", "0:v", "-map", "1:a"
        )
    }

    $args += @(
        "-vf", $vfStr,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", $fps,
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
        "-t", $cut.duration,
        $cutOut
    )

    Write-Host "[$cutIdx] 렌더링: $($cut.src) ($($cut.start)s, ${($cut.duration)}s)" -ForegroundColor Cyan
    & $ffmpeg @args 2>&1 | Select-Object -Last 2 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "[$cutIdx] 렌더링 실패"
        exit 1
    }

    $concatList += "file '$($cutOut -replace '\\', '/')'"
    $idx++
}

# concat 리스트 작성
$concatFile = Join-Path $workDir "concat.txt"
[System.IO.File]::WriteAllLines($concatFile, $concatList, [System.Text.UTF8Encoding]::new($false))

# 최종 합본
Write-Host ""
Write-Host "concat 합본..." -ForegroundColor Cyan
$outPath = $cfg.outputPath
New-Item -ItemType Directory -Force (Split-Path $outPath) | Out-Null

& $ffmpeg -y -f concat -safe 0 -i $concatFile -c copy $outPath 2>&1 | Select-Object -Last 3 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Error "concat 합본 실패"
    exit 1
}

# 검증
Write-Host ""
Write-Host "=== 출력 검증 ===" -ForegroundColor Cyan
$probe = & $ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,channels:format=duration,size -of json $outPath | ConvertFrom-Json
$videoStream = $probe.streams | Where-Object { $_.codec_type -eq 'video' } | Select-Object -First 1
$audioStream = $probe.streams | Where-Object { $_.codec_type -eq 'audio' } | Select-Object -First 1
$duration = [Math]::Round([double]$probe.format.duration, 2)
$sizeMB = [Math]::Round([int64]$probe.format.size / 1MB, 2)

Write-Host "출력: $outPath"
Write-Host "해상도: $($videoStream.width)x$($videoStream.height) ($($videoStream.codec_name))"
Write-Host "길이: ${duration}s"
Write-Host "용량: ${sizeMB}MB"
if ($audioStream) {
    Write-Host "오디오: $($audioStream.codec_name) / $($audioStream.channels)ch ✓" -ForegroundColor Green
} else {
    Write-Host "오디오: 없음 ⚠️" -ForegroundColor Yellow
}
