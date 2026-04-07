# 에이전트 업데이트 - Claude Code 커스텀 스킬 최신화

GitHub 레포(aijunny0604-alt/claude-commands)에서 최신 에이전트/hook을 가져와서 설치합니다.

## 실행

다음 명령어를 실행:

```bash
curl -sSL https://raw.githubusercontent.com/aijunny0604-alt/claude-commands/master/update.sh | bash
```

또는 로컬에 클론한 레포가 있으면:

```bash
cd ~/claude-commands && git pull && bash update.sh
```

## 동작

1. 최신 레포 클론
2. `~/.claude/commands/` 에 모든 `.md` 에이전트 파일 덮어쓰기
3. `~/.claude/hooks/` 에 모든 `.sh` hook 스크립트 덮어쓰기 (chmod +x)
4. 완료 메시지 표시

## 주의

- **기존 파일이 덮어써집니다** — 로컬에서 수정한 내용이 있으면 레포에 먼저 push 후 업데이트
- **Claude Code 재시작 필요** — 업데이트 후 스킬이 즉시 반영되지 않으면 재시작
- **settings.json은 건드리지 않음** — hook 등록은 수동 (최초 1회만)
